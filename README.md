# LLM服务器性能测试与部署工具

这个项目提供了一套完整的工具，用于评估服务器硬件在运行大型语言模型(LLM)时的性能和容量。它能帮助您确定特定硬件配置能支持的并发用户数量，优化服务器配置，以及模拟真实世界的用户负载情况。

## 项目背景与解决的问题

在部署LLM推理服务时，我们常常面临以下挑战：

- **硬件容量评估困难**：难以确定特定服务器配置能够支持多少并发用户
- **资源利用优化复杂**：为特定硬件找到最佳的服务配置需要大量试错
- **性能瓶颈识别**：难以确定系统的性能瓶颈是在CPU、内存、GPU还是网络
- **负载应对能力未知**：不清楚服务器在各种负载模式下的稳定性和响应能力

本项目提供了一套端到端的服务器评估解决方案，让您能够快速下载模型、启动优化配置的服务，并进行真实的负载测试，从而确定服务器的实际承载能力和性能极限。

## 项目架构

项目由三个核心单元组成：

1. **模型加速下载单元** (`hfd.sh`)
   - 快速从Hugging Face下载LLM模型
   - 支持并行下载、断点续传
   - 灵活的文件过滤机制

2. **推理引擎优化启动单元** (`serve.sh`)
   - 使用硬件优化配置启动vLLM推理引擎
   - 根据服务器规格自动调整最佳参数
   - 支持内存优化、量化加速和多GPU并行

3. **服务器负载测试单元** (`load-test`)
   - 评估硬件能支持的最大并发用户数
   - 测试不同负载模式下的服务器稳定性
   - 识别系统性能瓶颈和极限

## 快速开始

### 1. 下载模型

```bash
# 下载模型（例如Qwen2.5-7B-Instruct）
./hfd.sh meta-llama/Llama-2-7b-chat-hf --hf_username YOUR_USERNAME --hf_token YOUR_TOKEN
```

### 2. 启动LLM服务

```bash
# 启动优化配置的vLLM服务
./serve.sh
```

### 3. 运行性能测试

```bash
# 执行服务器负载测试
cd load-test
./run.sh
```

## 详细使用指南

### 模型下载工具 (hfd.sh)

`hfd.sh`脚本提供了高效的模型下载功能，支持从Hugging Face下载模型或数据集：

```bash
# 基本用法
./hfd.sh <REPO_ID> [选项]

# 示例：下载Qwen2.5-7B模型，排除某些文件
./hfd.sh Qwen/Qwen2.5-7B --exclude *.md --hf_token YOUR_TOKEN

# 使用aria2c加速下载（默认）
./hfd.sh meta-llama/Llama-2-7b --tool aria2c -x 4 -j 5
```

完整选项列表可通过`./hfd.sh --help`查看。

### LLM服务启动 (serve.sh)

`serve.sh`脚本封装了vLLM服务的启动参数，针对当前硬件进行了优化：

```bash
# 默认启动（使用当前目录下的模型）
./serve.sh

# 修改参数（如果需要）
vi serve.sh
```

主要配置参数：
- `--tensor-parallel-size`: GPU并行数量
- `--max-model-len`: 最大上下文长度
- `--quantization`: 量化方式（如awq）
- `--gpu-memory-utilization`: GPU内存利用率

### 服务器负载测试工具 (load-test)

服务器负载测试工具支持多种测试模式：

```bash
# 单次测试
cd load-test
python run_benchmarks.py --vllm_url "http://localhost:8000/v1" --api_key "your-api-key" --model "Qwen2.5-7B-Instruct-AWQ" --config '{"num_requests": 100, "concurrency": 10}'

# 批量测试多种配置
python run_benchmarks.py --vllm_url "http://localhost:8000/v1" --api_key "your-api-key" --model "Qwen2.5-7B-Instruct-AWQ" --config '[
    {"num_requests": 20, "spread_mode": "uniform", "duration": 20, "output_tokens": 100},
    {"num_requests": 50, "concurrency": 10, "output_tokens": 20}
]'
```

测试结果会以JSON格式保存，并在控制台显示关键指标，包括：
- 请求成功率
- 每秒请求数
- 平均延迟和P95延迟
- 首字时间（TTFT）
- 每秒生成的token数

## 配置文件参考

### 并发测试模式配置

```json
{
  "num_requests": 100,   // 总请求数
  "concurrency": 10,     // 并发数
  "output_tokens": 100,  // 生成的token数量
  "request_timeout": 30  // 请求超时时间（秒）
}
```

### 分布式请求测试配置

```json
{
  "num_requests": 100,        // 总请求数
  "spread_mode": "uniform",   // 分布模式：uniform/normal/exponential
  "duration": 60,             // 测试持续时间（秒）
  "output_tokens": 100        // 生成的token数量
}
```

## 系统要求

- Python 3.10+
- CUDA 11.8+（用于GPU加速）
- 推荐：至少一张NVIDIA GPU（16GB+内存）
- 依赖库：openai, numpy, rich, click

## 未来规划

项目的终极目标是提供一键测试功能，能够：
- 自动检测硬件配置并优化服务参数
- 执行多阶段渐进式负载测试
- 生成详细的性能报告和用户容量估算
- 提供性能优化建议

## 贡献

欢迎贡献代码、报告问题或提出新功能建议。请通过Issue或Pull Request参与项目开发。

## 许可证

本项目采用Apache 2.0许可证。详情请参见LICENSE文件。
