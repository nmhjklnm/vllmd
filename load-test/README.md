# vLLM Benchmark

This repository contains scripts for benchmarking the performance of large language models (LLMs) served using vLLM. It's designed to test the scalability and performance of LLM deployments under various concurrency levels.

## Features

- Benchmark LLMs with different concurrency levels
- Measure key performance metrics:
  - Requests per second
  - Latency
  - Tokens per second
  - Time to first token
- Easy to run with customizable parameters
- Generates JSON output for further analysis or visualization

## Requirements

- Python 3.7+
- `openai` Python package
- `numpy` Python package

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/vllm-benchmark.git
   cd vllm-benchmark
   ```

2. Install the required packages:
   ```
   pip install openai numpy
   ```

## Usage

### Command Line Options

To run a single benchmark:

```
python run_benchmarks.py --vllm_url "http://localhost:8000/v1" --api_key "your-api-key" --model "model-name" --config '{"num_requests": 100, "concurrency": 10, "output_tokens": 100}'
```

Or with distribution scheduling:

```
python run_benchmarks.py --vllm_url "http://localhost:8000/v1" --api_key "your-api-key" --model "model-name" --config '{"num_requests": 100, "spread_mode": "uniform", "duration": 60, "output_tokens": 100}'
```

### Using Configuration Files

You can provide benchmark configurations as JSON files:

#### Single Configuration

Create a JSON file (e.g., `single_config.json`):
```json
{
  "num_requests": 100,
  "concurrency": 10,
  "output_tokens": 100,
  "request_timeout": 30
}
```

Then run:
```
python run_benchmarks.py --vllm_url "http://localhost:8000/v1" --api_key "your-api-key" --model "model-name" --config single_config.json
```

#### Multiple Configurations

Create a JSON file with an array of configurations (e.g., `multi_config.json`):
```json
[
  {
    "num_requests": 20,
    "concurrency": 5,
    "output_tokens": 100
  },
  {
    "num_requests": 50,
    "concurrency": 10,
    "output_tokens": 100
  },
  {
    "num_requests": 100,
    "spread_mode": "uniform",
    "duration": 60,
    "output_tokens": 100
  }
]
```

Then run:
```
python run_benchmarks.py --vllm_url "http://localhost:8000/v1" --api_key "your-api-key" --model "model-name" --config multi_config.json
```

### Configuration Parameters

Parameters for concurrent mode:
- `num_requests`: Total number of requests to make
- `concurrency`: Number of concurrent requests
- `output_tokens`: Number of tokens to generate per request (default: 100)
- `request_timeout`: Timeout for each request in seconds (default: 30)

Parameters for distributed mode:
- `num_requests`: Total number of requests to make
- `spread_mode`: Distribution mode for request scheduling (uniform/normal/exponential)
- `duration`: Total test duration in seconds
- `output_tokens`: Number of tokens to generate per request (default: 100)

### Example Shell Script

You can also use a shell script to run multiple benchmark configurations:

```bash
#!/bin/bash

# 单测模式
python run_benchmarks.py \
    --vllm_url "http://localhost:8000/v1" \
    --api_key "your-api-key" \
    --model "Qwen2.5-7B-Instruct-AWQ" \
    --config '{"num_requests": 100, "spread_mode": "uniform", "duration": 60, "output_tokens": 100}'

# 批量测试模式
python run_benchmarks.py \
    --vllm_url "http://localhost:8000/v1" \
    --api_key "your-api-key" \
    --model "Qwen2.5-7B-Instruct-AWQ" \
    --config '[
        {"num_requests": 20, "spread_mode": "uniform", "duration": 60, "output_tokens": 100},
        {"num_requests": 100, "spread_mode": "uniform", "duration": 60, "output_tokens": 100},
        {"num_requests": 50, "concurrency": 10, "output_tokens": 100}
    ]'
```

### Multiple Benchmark Runs

To run multiple benchmarks with different configurations:

```
python run_benchmarks.py --batch --vllm_url "http://localhost:8000/v1" --api_key "your-api-key" --model "model-name"
```

With distributed mode:

```
python run_benchmarks.py --batch --spread_mode uniform --duration 60 --vllm_url "http://localhost:8000/v1" --api_key "your-api-key" --model "model-name"
```

This script will run multiple benchmarks with different concurrency levels or request counts, displaying a summary table and saving detailed results to `benchmark_results.json`.

## Output

The benchmark results are saved in JSON format, containing detailed metrics for each run, including:

- Total requests and successful requests
- Requests per second
- Total output tokens
- Latency (average, p50, p95, p99)
- Tokens per second (average, p50, p95, p99)
- Time to first token (average, p50, p95, p99)

## Results

Please see the results directory for benchmarks on [Backprop](https://backprop.co) instances.

## Contributing

Contributions to improve the benchmarking scripts or add new features are welcome! Please feel free to submit pull requests or open issues for any bugs or feature requests.

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.
