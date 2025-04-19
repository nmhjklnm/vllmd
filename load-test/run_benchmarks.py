import asyncio
import json
import time
import logging
import os
from typing import List, Dict, Any, Optional, Union
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
from vllm_benchmark import run_benchmark, distributed_request_benchmark, print_results

async def execute_benchmark(
    config: Dict[str, Any], 
    vllm_url: str, 
    api_key: str, 
    use_long_context: bool, 
    model: str
) -> Dict[str, Any]:
    """执行单个基准测试，无论是并发模式还是分布式模式"""
    if "spread_mode" in config and "duration" in config:
        # 分布式模式
        console = Console()
        console.print(f"Running distributed benchmark with [bold]{config['num_requests']}[/bold] requests over "
                      f"[bold]{config['duration']}s[/bold] using [bold]{config['spread_mode']}[/bold] distribution...")
        
        return await distributed_request_benchmark(
            config['num_requests'], 
            config['duration'], 
            config['spread_mode'],
            config.get('output_tokens', 100), 
            vllm_url, 
            api_key,
            use_long_context, 
            model
        )
    else:
        # 并发模式
        console = Console()
        console.print(f"Running benchmark with [bold]{config['num_requests']}[/bold] requests, "
                      f"concurrency [bold]{config['concurrency']}[/bold]...")
        
        return await run_benchmark(
            config['num_requests'], 
            config['concurrency'], 
            config.get('request_timeout', 30),
            config.get('output_tokens', 100), 
            vllm_url, 
            api_key,
            use_long_context, 
            model
        )

def display_results_table(all_results: List[Dict[str, Any]]) -> None:
    """以表格形式显示多个测试结果的比较"""
    console = Console()
    table = Table(title="vLLM Benchmark Results")
    
    # 添加列头，按照要求的列索引
    table.add_column("Concurrency", style="cyan")
    table.add_column("Total", style="cyan")
    table.add_column("Success Rate", style="green")
    table.add_column("Req/s", style="yellow")
    table.add_column("Lat avg (s)", style="magenta")
    table.add_column("Lat P95 (s)", style="magenta")
    table.add_column("TTFT avg (s)", style="blue")
    table.add_column("Token/s avg", style="red")
    table.add_column("Token/s P95", style="red")
    
    # 填充数据
    for result in all_results:
        # 获取并转换需要的值
        if "concurrency" in result:
            concurrency = str(result["concurrency"])
        else:
            concurrency = f"{result['spread_mode']} ({result['total_requests']} reqs)"
            
        total = str(result["total_requests"])
        success_rate = f"{(result['successful_requests'] / result['total_requests']) * 100:.1f}%" if result["total_requests"] > 0 else "0%"
        req_per_sec = f"{result['requests_per_second']:.2f}"
        lat_avg = f"{result['latency']['average']:.2f}"
        lat_p95 = f"{result['latency']['p95']:.2f}"
        ttft_avg = f"{result['time_to_first_token']['average']:.2f}"
        tokens_per_sec_avg = f"{result['tokens_per_second']['average']:.2f}"
        tokens_per_sec_p95 = f"{result['tokens_per_second']['p95']:.2f}"
        
        # 添加行
        table.add_row(
            concurrency, total, success_rate, req_per_sec, 
            lat_avg, lat_p95, ttft_avg, 
            tokens_per_sec_avg, tokens_per_sec_p95
        )
    
    console.print(table)

def parse_config_option(ctx, param, value):
    """解析配置参数，可以是JSON字符串或文件路径"""
    if not value:
        return None
    
    try:
        # 尝试作为JSON字符串解析
        return json.loads(value)
    except json.JSONDecodeError:
        # 尝试作为文件路径解析
        try:
            with open(value, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            raise click.BadParameter(f"Invalid configuration: {str(e)}")

@click.command()
@click.option("--vllm_url", type=str, required=True, help="URL of the vLLM server")
@click.option("--api_key", type=str, required=True, help="API key for vLLM server")
@click.option("--use_long_context", is_flag=True, help="Use long context prompt pairs instead of short prompts")
@click.option("--model", type=str, required=True, help="Model name to use for benchmarking")
@click.option("--output_file", type=str, default="benchmark_results.json", help="Output file for JSON results")
@click.option("--config", callback=parse_config_option, help="Configuration as JSON string, JSON array string, or path to JSON file")
@click.option("--quiet", is_flag=True, help="Reduce output verbosity")
def main(
    vllm_url: str, 
    api_key: str, 
    use_long_context: bool, 
    model: str, 
    output_file: str, 
    config: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]],
    quiet: bool
) -> None:
    """Run one or more benchmarks for LLM models served by vLLM.
    
    You can provide configuration in three ways via --config option:
    
    1. As a JSON object string: --config '{"num_requests": 100, "concurrency": 10}'
    2. As a JSON array string: --config '[{"num_requests":20,"concurrency":5},{"num_requests":50,"concurrency":10}]'
    3. As a file path: --config path/to/config.json (file can contain a JSON object or array)
    
    Configuration parameters:
    - num_requests: Number of requests to make
    - concurrency: (For concurrent mode) Number of concurrent requests
    - request_timeout: (Optional) Timeout for each request in seconds
    - output_tokens: (Optional) Number of tokens to generate per request
    - spread_mode: (For distributed mode) Distribution mode (uniform/normal/exponential)
    - duration: (For distributed mode) Test duration in seconds
    """
    configs = []
    
    # 获取配置列表
    if config:
        configs = [config] if not isinstance(config, list) else config
    else:
        # 创建默认配置
        if click.confirm("No configuration provided. Run with default settings?", default=True):
            # 默认并发模式配置
            configs = [
                {"num_requests": 100, "concurrency": 10, "output_tokens": 100}
            ]
        else:
            raise click.UsageError("Please provide a configuration using --config")
    
    # 验证配置
    for cfg in configs:
        if "num_requests" not in cfg:
            raise click.BadParameter(f"Missing 'num_requests' in configuration: {cfg}")
        if "spread_mode" in cfg and "duration" in cfg:
            # 分布式模式配置检查
            if cfg["spread_mode"] not in ["uniform", "normal", "exponential"]:
                raise click.BadParameter(f"Invalid spread_mode '{cfg['spread_mode']}'. Must be one of: uniform, normal, exponential")
        elif "concurrency" not in cfg:
            # 并发模式需要 concurrency
            raise click.BadParameter(f"Missing 'concurrency' in configuration for concurrent mode: {cfg}")
    
    # 添加控制日志输出级别的选项
    logging_level = logging.WARNING if quiet else logging.INFO
    if os.environ.get("VLLM_BENCHMARK_DEBUG"):
        logging_level = logging.DEBUG
    logging.getLogger().setLevel(logging_level)
    
    # 确保http库的日志不干扰进度条
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # 执行基准测试
    console = Console()
    console.print(f"[bold]Running {len(configs)} benchmark configurations[/bold]")
    
    all_results = []
    
    # 移除总进度条，只使用单个测试内部的进度条
    for i, cfg in enumerate(configs):
        # 为每个配置创建描述
        if "spread_mode" in cfg:
            config_desc = f"分布式 ({cfg['spread_mode']}, {cfg['num_requests']}请求, {cfg['duration']}秒)"
        else:
            config_desc = f"并发测试 ({cfg['num_requests']}请求, 并发{cfg['concurrency']})"
            
        # 使用简单的文本输出代替总进度条
        console.print(f"[green]执行测试 {i+1}/{len(configs)}: {config_desc}[/green]")
        
        # 执行测试
        result = asyncio.run(execute_benchmark(cfg, vllm_url, api_key, use_long_context, model))
        all_results.append(result)
        
        # 如果不是最后一个配置，等待一下系统冷却
        if i < len(configs) - 1:
            console.print(f"[yellow]等待系统冷却 5 秒...[/yellow]")
            time.sleep(5)
    
    # 根据结果数量显示不同形式的输出
    if len(all_results) == 1:
        # 单个测试结果，使用详细表格
        print_results(all_results[0])
    else:
        # 多个测试结果，使用比较表格
        display_results_table(all_results)
    
    # 保存结果
    with open(output_file, 'w') as f:
        json.dump(all_results if len(all_results) > 1 else all_results[0], f, indent=2)
    
    console.print(f"Benchmark results saved to [bold green]{output_file}[/bold green]")

if __name__ == "__main__":
    main()

