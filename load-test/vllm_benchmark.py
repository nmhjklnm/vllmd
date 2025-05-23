import asyncio
import time
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from openai import AsyncOpenAI
import logging
import json
import random
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn, TimeElapsedColumn

# 设置日志记录 - 默认为INFO级别，但详细请求信息改为DEBUG级别
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# 将openai库的日志级别设为WARNING，避免HTTP请求日志干扰进度条
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# 短提示列表
SHORT_PROMPTS = [
    "Explain the concept of artificial intelligence in simple terms.",
    "What are the main causes of climate change?",
    "Describe the process of photosynthesis in plants.",
    "How does the human immune system work?",
    "What were the main causes of World War II?",
    "Explain the theory of relativity in layman's terms.",
    "What are the key principles of effective leadership?",
    "How does blockchain technology work?",
    "What are the main theories about the origin of the universe?",
    "Describe the water cycle and its importance for life on Earth.",
    "What are the major differences between capitalism and socialism?",
    "How does the human brain process and store memories?",
    "What are the main challenges in space exploration?",
    "Explain the concept of supply and demand in economics.",
]

# 长上下文提示对
LONG_PROMPT_PAIRS = [
    {
        "prompt": "Explain the concept of artificial intelligence in simple terms.",
        "context": "Artificial intelligence (AI) is a rapidly evolving field of computer science that aims to create intelligent machines that can perform tasks that typically require human intelligence. These tasks include visual perception, speech recognition, decision-making, and language translation. AI systems are designed to learn from experience, adjust to new inputs, and perform human-like tasks. The field of AI encompasses various subfields, including machine learning, neural networks, and deep learning, which have led to significant advancements in areas such as autonomous vehicles, virtual assistants, and recommendation systems."
    },
    {
        "prompt": "What are the main causes of climate change?",
        "context": "Climate change is a complex global phenomenon primarily driven by human activities that release greenhouse gases into the atmosphere. The burning of fossil fuels for energy, deforestation, industrial processes, and agriculture are major contributors to the increased concentration of carbon dioxide and other heat-trapping gases. These gases form a 'blanket' around the Earth, causing the planet to warm at an unprecedented rate. The resulting changes in temperature patterns lead to more frequent and severe weather events, rising sea levels, and disruptions to ecosystems worldwide."
    },
    {
        "prompt": "Describe the process of photosynthesis in plants.",
        "context": "Photosynthesis is a fundamental biological process that allows plants to convert light energy into chemical energy. This process occurs in the chloroplasts of plant cells, specifically in structures called thylakoids. Chlorophyll, the pigment that gives plants their green color, is crucial in capturing light energy. During photosynthesis, plants take in carbon dioxide from the air through tiny pores called stomata and water from the soil through their roots. Using light energy, they combine these ingredients to produce glucose and oxygen. This process not only provides energy for the plant but also releases oxygen as a byproduct, which is essential for most life on Earth."
    },
    {
        "prompt": "How does the human immune system work?",
        "context": "The human immune system is a complex network of cells, tissues, and organs that work together to defend the body against harmful pathogens. It consists of two main parts: the innate immune system, which provides a quick, non-specific response to invaders, and the adaptive immune system, which develops targeted defenses against specific pathogens. Key components include white blood cells (such as neutrophils, macrophages, and lymphocytes), antibodies, and the complement system. The immune system has the remarkable ability to distinguish between the body's own cells and foreign invaders, allowing it to target threats while minimizing damage to healthy tissue."
    },
    {
        "prompt": "What were the main causes of World War II?",
        "context": "World War II, which lasted from 1939 to 1945, was one of the deadliest conflicts in human history. Its origins can be traced to several complex factors. The harsh terms of the Treaty of Versailles, which ended World War I, left Germany economically devastated and resentful. This paved the way for the rise of fascism and the Nazi Party under Adolf Hitler. Aggressive expansionist policies by Nazi Germany, Fascist Italy, and Imperial Japan, combined with the policy of appeasement by Western powers, allowed these regimes to gain territory unchecked. The immediate trigger for the war in Europe was Germany's invasion of Poland in September 1939, while the attack on Pearl Harbor in 1941 brought the United States into the conflict."
    },
    {
        "prompt": "Explain the theory of relativity in layman's terms.",
        "context": "Albert Einstein's theory of relativity, developed in the early 20th century, revolutionized our understanding of space, time, and gravity. It consists of two parts: special relativity and general relativity. Special relativity, introduced in 1905, deals with objects moving at very high speeds. It proposes that the speed of light is constant for all observers and that time and space are not absolute but relative to the observer's motion. This leads to phenomena like time dilation and length contraction. General relativity, published in 1915, extends these ideas to include gravity. Einstein proposed that massive objects curve the fabric of spacetime, and this curvature is what we experience as gravity. These theories have been consistently supported by experimental evidence and have practical applications in technologies like GPS satellites."
    },
    {
        "prompt": "What are the key principles of effective leadership?",
        "context": "Effective leadership is crucial in guiding organizations, teams, and individuals towards achieving their goals. While leadership styles may vary, several key principles are widely recognized as essential for success. These include clear communication, which ensures that vision and expectations are understood by all; integrity, which builds trust and respect; adaptability, allowing leaders to navigate changing environments; empathy, fostering strong relationships and understanding team dynamics; decision-making skills, enabling timely and informed choices; vision, providing direction and inspiration; and the ability to empower others, encouraging growth and innovation within the team. Effective leaders also demonstrate accountability, both for their own actions and those of their team, and continuously seek personal growth and learning opportunities."
    },
    {
        "prompt": "How does blockchain technology work?",
        "context": "Blockchain is a decentralized, distributed ledger technology that underlies cryptocurrencies like Bitcoin, but has potential applications far beyond digital currencies. At its core, a blockchain is a chain of blocks, each containing a list of transactions. Every block is linked to the previous one through cryptographic hashes, creating an immutable record. The key innovation of blockchain is its ability to achieve consensus in a decentralized network without requiring trust in any single entity. This is typically achieved through consensus mechanisms like Proof of Work or Proof of Stake. When a new transaction occurs, it is broadcast to a network of computers (nodes) for validation. Once validated, the transaction is combined with others to create a new block, which is then added to the chain. This process ensures transparency, security, and resistance to tampering, making blockchain suitable for various applications beyond finance, including supply chain management, voting systems, and digital identity verification."
    },
    {
        "prompt": "What are the main theories about the origin of the universe?",
        "context": "The origin of the universe has been a subject of intense scientific inquiry and philosophical debate for centuries. Currently, the most widely accepted scientific theory is the Big Bang model, which proposes that the universe began as an infinitely dense and hot singularity about 13.8 billion years ago, and has been expanding and cooling ever since. This theory is supported by observational evidence such as the cosmic microwave background radiation and the abundance of light elements in the universe. However, questions remain about what happened before the Big Bang and what caused it. Other theories include the Steady State theory, which suggests that the universe has always existed and is constantly creating new matter as it expands, though this theory has fallen out of favor due to lack of supporting evidence. More speculative ideas include the concept of a cyclic universe, where big bangs and big crunches occur in an endless cycle, and the idea of a multiverse, where our universe is just one of many existing universes."
    },
    {
        "prompt": "Describe the water cycle and its importance for life on Earth.",
        "context": "The water cycle, also known as the hydrologic cycle, is the continuous movement of water within the Earth and atmosphere. It is a complex system involving the processes of evaporation, transpiration, condensation, precipitation, and runoff. Water evaporates from the Earth's surface, primarily from oceans, lakes, and rivers, due to solar energy. Plants also release water vapor through transpiration. As this water vapor rises in the atmosphere, it cools and condenses to form clouds. Eventually, it falls back to Earth as precipitation in the form of rain, snow, or hail. Some of this water flows over the land as surface runoff, returning to bodies of water, while some seeps into the ground, replenishing groundwater reserves. This cycle is crucial for life on Earth as it redistributes water around the globe, shapes landscapes through erosion and deposition, regulates global temperatures, and provides fresh water essential for all living organisms. Understanding and protecting the water cycle is vital for managing water resources and addressing environmental challenges like climate change and water scarcity."
    },
    {
        "prompt": "What are the major differences between capitalism and socialism?",
        "context": "Capitalism and socialism are two contrasting economic and political systems that have shaped much of modern history. Capitalism is characterized by private ownership of the means of production, where individuals or corporations own businesses and property. It operates on the principles of free market competition, with prices determined by supply and demand. Profit is a key motivator in capitalist systems, and government intervention is generally limited. In contrast, socialism advocates for collective or governmental ownership and administration of the means of production and distribution of goods. It aims to create a more equitable society by reducing class distinctions and distributing resources according to need rather than ability to pay. In socialist systems, the government plays a much larger role in economic planning and the provision of social services. While pure forms of either system are rare, many countries adopt mixed economies incorporating elements of both capitalism and socialism to varying degrees."
    },
    {
        "prompt": "How does the human brain process and store memories?",
        "context": "The human brain's ability to process and store memories is a complex and fascinating process involving various regions and neural networks. When we experience something, sensory information is first processed in the relevant cortical areas (e.g., visual cortex for sight, auditory cortex for sound). This information is then integrated in the hippocampus, a seahorse-shaped structure crucial for forming new memories. The hippocampus helps bind different aspects of an experience into a cohesive memory and plays a key role in converting short-term memories into long-term ones. Long-term memories are thought to be stored through changes in synaptic connections between neurons across widespread areas of the cortex. This process, known as consolidation, can take days or even years. Different types of memories (e.g., episodic, semantic, procedural) involve different brain regions and processes. The retrieval of memories involves reactivating these neural patterns, which explains why memories can be influenced by our current state and environment. Understanding these processes is crucial for addressing memory-related disorders and developing potential therapies."
    },
    {
        "prompt": "What are the main challenges in space exploration?",
        "context": "Space exploration, while offering immense potential for scientific discovery and technological advancement, faces numerous challenges. One of the primary obstacles is the hostile environment of space itself. The vacuum of space, extreme temperatures, and harmful radiation pose significant risks to both human astronauts and sensitive equipment. Prolonged exposure to microgravity can lead to health issues for astronauts, including muscle atrophy and bone density loss. Logistical challenges are also substantial: the enormous distances involved in space travel require advanced propulsion systems and careful resource management. Launching payloads into orbit remains extremely expensive, limiting the scope and frequency of missions. Communication delays become increasingly problematic for deep space missions, necessitating a high degree of autonomy in spacecraft and rovers. Additionally, space debris orbiting Earth poses a growing threat to satellites and spacecraft. As we look towards long-term goals like establishing bases on the Moon or Mars, we face new challenges in creating sustainable habitats and managing psychological effects on crew members during extended missions. Despite these obstacles, ongoing research and technological innovations continue to push the boundaries of what's possible in space exploration."
    },
    {
        "prompt": "Explain the concept of supply and demand in economics.",
        "context": "Supply and demand is a fundamental concept in economics that describes how the price and quantity of a good or service in a market are determined through the interaction between buyers and sellers. The law of demand states that, all else being equal, as the price of a product increases, the quantity demanded by consumers decreases. This is typically represented by a downward-sloping demand curve. Conversely, the law of supply states that as the price of a product increases, the quantity that producers are willing to supply increases, represented by an upward-sloping supply curve. The point where these two curves intersect is called the equilibrium point, determining the market price and quantity. This model helps explain how prices fluctuate in response to changes in supply or demand. For instance, if demand increases while supply remains constant, prices will rise. If supply increases while demand remains constant, prices will fall. Understanding supply and demand is crucial for analyzing market behavior, predicting price changes, and formulating economic policies."
    },
]

async def process_stream(stream) -> Tuple[Optional[float], int]:
    """处理流式响应并计算首字时间和生成的令牌数"""
    first_token_time = None
    total_tokens = 0
    async for chunk in stream:
        if first_token_time is None:
            first_token_time = time.time()
        if chunk.choices[0].delta.content:
            total_tokens += 1
        if chunk.choices[0].finish_reason is not None:
            break
    return first_token_time, total_tokens

async def make_request(
    client: AsyncOpenAI, 
    model: str, 
    output_tokens: int, 
    request_timeout: int, 
    use_long_context: bool
) -> Optional[Tuple[int, float, float, float]]:
    """发送单个请求并返回相关指标"""
    start_time = time.time()
    if use_long_context:
        prompt_pair = random.choice(LONG_PROMPT_PAIRS)
        content = f"{prompt_pair['context']}\n\n{prompt_pair['prompt']}"
    else:
        content = random.choice(SHORT_PROMPTS)

    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": content}
            ],
            max_tokens=output_tokens,
            stream=True
        )
        first_token_time, total_tokens = await asyncio.wait_for(process_stream(stream), timeout=request_timeout)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        ttft = first_token_time - start_time if first_token_time else None
        tokens_per_second = total_tokens / elapsed_time if elapsed_time > 0 else 0
        return total_tokens, elapsed_time, tokens_per_second, ttft

    except asyncio.TimeoutError:
        logging.warning(f"Request timed out after {request_timeout} seconds")
        return None
    except Exception as e:
        logging.error(f"Error during request: {str(e)}")
        return None

async def worker(
    client: AsyncOpenAI, 
    semaphore: asyncio.Semaphore, 
    queue: asyncio.Queue, 
    results: List[Tuple[int, float, float, float]], 
    model: str, 
    output_tokens: int, 
    request_timeout: int, 
    use_long_context: bool,
    progress_task=None,
    progress=None
) -> None:
    """工作线程函数，处理队列中的请求"""
    while True:
        async with semaphore:
            task_id = await queue.get()
            if task_id is None:
                queue.task_done()
                break
            logging.debug(f"Starting request {task_id}")
            result = await make_request(client, model, output_tokens, request_timeout, use_long_context)
            if result:
                results.append(result)
            else:
                logging.warning(f"Request {task_id} failed")
            queue.task_done()
            logging.debug(f"Finished request {task_id}")
            # 更新进度条（如果提供）
            if progress and progress_task is not None:
                progress.update(progress_task, advance=1)

def calculate_percentile(values: List[float], percentile: int, reverse: bool = False) -> Optional[float]:
    """计算百分位数"""
    if not values:
        return None
    if reverse:
        return np.percentile(values, 100 - percentile)
    return np.percentile(values, percentile)

async def run_benchmark(
    num_requests: int, 
    concurrency: int, 
    request_timeout: int, 
    output_tokens: int, 
    vllm_url: str, 
    api_key: str, 
    use_long_context: bool, 
    model: str
) -> Dict[str, Any]:
    """运行并发基准测试"""
    client = AsyncOpenAI(base_url=vllm_url, api_key=api_key)
    semaphore = asyncio.Semaphore(concurrency)
    queue = asyncio.Queue()
    results = []

    # 创建进度条
    with Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        TimeElapsedColumn(),
        console=Console()
    ) as progress:
        task = progress.add_task(f"[cyan]Processing {num_requests} requests", total=num_requests)
        
        # 向队列中添加任务
        for i in range(num_requests):
            await queue.put(i)
        
        # 添加哨兵值以停止工作线程
        for _ in range(concurrency):
            await queue.put(None)

        # 创建工作线程任务
        workers = [
            asyncio.create_task(
                worker(client, semaphore, queue, results, model, output_tokens, request_timeout, use_long_context, task, progress)
            ) for _ in range(concurrency)
        ]

        start_time = time.time()
        
        # 等待所有任务完成
        await queue.join()
        await asyncio.gather(*workers)

    end_time = time.time()

    # 计算指标
    total_elapsed_time = end_time - start_time
    total_tokens = sum(tokens for tokens, _, _, _ in results if tokens is not None)
    latencies = [elapsed_time for _, elapsed_time, _, _ in results if elapsed_time is not None]
    tokens_per_second_list = [tps for _, _, tps, _ in results if tps is not None]
    ttft_list = [ttft for _, _, _, ttft in results if ttft is not None]

    successful_requests = len(results)
    requests_per_second = successful_requests / total_elapsed_time if total_elapsed_time > 0 else 0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    avg_tokens_per_second = sum(tokens_per_second_list) / len(tokens_per_second_list) if tokens_per_second_list else 0
    avg_ttft = sum(ttft_list) / len(ttft_list) if ttft_list else 0
    
    # 计算百分位数
    percentiles = [50, 95, 99]
    latency_percentiles = [calculate_percentile(latencies, p) for p in percentiles]
    tps_percentiles = [calculate_percentile(tokens_per_second_list, p, reverse=True) for p in percentiles]
    ttft_percentiles = [calculate_percentile(ttft_list, p) for p in percentiles]
    
    return {
        "total_requests": num_requests,
        "successful_requests": successful_requests,
        "concurrency": concurrency,
        "request_timeout": request_timeout,
        "max_output_tokens": output_tokens,
        "use_long_context": use_long_context,
        "model": model,
        "total_time": total_elapsed_time,
        "requests_per_second": requests_per_second,
        "total_output_tokens": total_tokens,
        "latency": {
            "average": avg_latency,
            "p50": latency_percentiles[0],
            "p95": latency_percentiles[1],
            "p99": latency_percentiles[2]
        },
        "tokens_per_second": {
            "average": avg_tokens_per_second,
            "p50": tps_percentiles[0],
            "p95": tps_percentiles[1],
            "p99": tps_percentiles[2]
        },
        "time_to_first_token": {
            "average": avg_ttft,
            "p50": ttft_percentiles[0],
            "p95": ttft_percentiles[1],
            "p99": ttft_percentiles[2]
        }
    }

async def distributed_request_benchmark(
    num_requests: int, 
    duration: int, 
    spread_mode: str, 
    output_tokens: int, 
    vllm_url: str, 
    api_key: str, 
    use_long_context: bool, 
    model: str
) -> Dict[str, Any]:
    """运行分布式请求调度基准测试"""
    client = AsyncOpenAI(base_url=vllm_url, api_key=api_key)
    results = []
    tasks = []
    
    # 生成请求时间点
    if spread_mode == 'uniform':
        request_times = np.random.uniform(0, duration, num_requests)
    elif spread_mode == 'normal':
        request_times = np.random.normal(duration / 2, duration / 6, num_requests)
        request_times = np.clip(request_times, 0, duration)
    elif spread_mode == 'exponential':
        request_times = np.random.exponential(scale=duration / 3, size=num_requests)
        request_times = np.clip(request_times, 0, duration)
    else:
        raise ValueError(f"Unknown spread mode: {spread_mode}")
    
    request_times = sorted(request_times)
    
    start_time = time.time()
    end_time = start_time + duration
    
    logging.debug(f"Starting distributed benchmark with {num_requests} requests over {duration} seconds")
    
    # 创建进度条 - 使用单一的console对象
    console = Console()
    with Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        progress_task_id = progress.add_task(f"[cyan]Running {spread_mode} distribution test", total=num_requests)
        
        # 先调度所有请求
        for i, req_time in enumerate(request_times):
            wait_time = req_time - (time.time() - start_time)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            
            if time.time() >= end_time:
                logging.debug(f"Duration {duration}s reached, stopping after {i} requests")
                break
                
            task = asyncio.create_task(make_request(client, model, output_tokens, duration, use_long_context))
            tasks.append(task)
            
            # 更新进度条
            progress.update(progress_task_id, advance=1)
    
        # 等待所有请求完成
        for i, task in enumerate(tasks):
            try:
                result = await task
                if result:
                    results.append(result)
                else:
                    logging.debug(f"Request {i} failed")
            except asyncio.CancelledError:
                logging.debug(f"Request {i} was cancelled")
            except Exception as e:
                logging.error(f"Error in request {i}: {str(e)}")
    
    final_time = time.time()
    actual_duration = final_time - start_time
    
    # 计算指标（与并发模式类似）
    total_tokens = sum(tokens for tokens, _, _, _ in results if tokens is not None)
    latencies = [elapsed_time for _, elapsed_time, _, _ in results if elapsed_time is not None]
    tokens_per_second_list = [tps for _, _, tps, _ in results if tps is not None]
    ttft_list = [ttft for _, _, _, ttft in results if ttft is not None]

    successful_requests = len(results)
    requests_per_second = successful_requests / actual_duration if actual_duration > 0 else 0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    avg_tokens_per_second = sum(tokens_per_second_list) / len(tokens_per_second_list) if tokens_per_second_list else 0
    avg_ttft = sum(ttft_list) / len(ttft_list) if ttft_list else 0
    
    percentiles = [50, 95, 99]
    latency_percentiles = [calculate_percentile(latencies, p) for p in percentiles]
    tps_percentiles = [calculate_percentile(tokens_per_second_list, p, reverse=True) for p in percentiles]
    ttft_percentiles = [calculate_percentile(ttft_list, p) for p in percentiles]
    
    return {
        "total_requests": num_requests,
        "successful_requests": successful_requests,
        "spread_mode": spread_mode,
        "planned_duration": duration,
        "actual_duration": actual_duration,
        "request_timeout": duration,
        "max_output_tokens": output_tokens,
        "use_long_context": use_long_context,
        "model": model,
        "requests_per_second": requests_per_second,
        "total_output_tokens": total_tokens,
        "latency": {
            "average": avg_latency,
            "p50": latency_percentiles[0],
            "p95": latency_percentiles[1],
            "p99": latency_percentiles[2]
        },
        "tokens_per_second": {
            "average": avg_tokens_per_second,
            "p50": tps_percentiles[0],
            "p95": tps_percentiles[1],
            "p99": tps_percentiles[2]
        },
        "time_to_first_token": {
            "average": avg_ttft,
            "p50": ttft_percentiles[0],
            "p95": ttft_percentiles[1],
            "p99": ttft_percentiles[2]
        }
    }

def print_results(results: Dict[str, Any]) -> None:
    """打印单个测试结果的详细信息"""
    console = Console()
    
    # 创建并显示美观的结果表
    table = Table(title=f"Benchmark Results: {results['model']}")
    
    # 添加表头
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    # 添加基本信息
    table.add_row("Total Requests", str(results["total_requests"]))
    table.add_row("Successful Requests", str(results["successful_requests"]))
    success_rate = (results["successful_requests"] / results["total_requests"]) * 100 if results["total_requests"] > 0 else 0
    table.add_row("Success Rate", f"{success_rate:.2f}%")
    
    if "concurrency" in results:
        table.add_row("Concurrency", str(results["concurrency"]))
    if "spread_mode" in results:
        table.add_row("Distribution Mode", results["spread_mode"])
        table.add_row("Test Duration", f"{results['actual_duration']:.2f}s")
    
    table.add_row("Requests per Second", f"{results['requests_per_second']:.2f}")
    table.add_row("Total Output Tokens", str(results["total_output_tokens"]))
    
    # 添加延迟信息
    table.add_row("Latency (avg)", f"{results['latency']['average']:.4f}s")
    table.add_row("Latency (p50)", f"{results['latency']['p50']:.4f}s")
    table.add_row("Latency (p95)", f"{results['latency']['p95']:.4f}s")
    table.add_row("Latency (p99)", f"{results['latency']['p99']:.4f}s")
    
    # 添加生成速度信息
    table.add_row("Tokens per Second (avg)", f"{results['tokens_per_second']['average']:.2f}")
    table.add_row("Tokens per Second (p50)", f"{results['tokens_per_second']['p50']:.2f}")
    table.add_row("Tokens per Second (p95)", f"{results['tokens_per_second']['p95']:.2f}")
    table.add_row("Tokens per Second (p99)", f"{results['tokens_per_second']['p99']:.2f}")
    
    # 添加首字时间信息
    table.add_row("Time to First Token (avg)", f"{results['time_to_first_token']['average']:.4f}s")
    table.add_row("Time to First Token (p50)", f"{results['time_to_first_token']['p50']:.4f}s")
    table.add_row("Time to First Token (p95)", f"{results['time_to_first_token']['p95']:.4f}s")
    table.add_row("Time to First Token (p99)", f"{results['time_to_first_token']['p99']:.4f}s")
    
    console.print(table)
    
    # 仍然输出 JSON 以便保存
    print(json.dumps(results, indent=2))

# 主函数被 run_benchmarks.py 中的统一接口替代，但保留外部导入的函数
__all__ = ['run_benchmark', 'distributed_request_benchmark', 'print_results']
