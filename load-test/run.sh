#!/bin/bash

# 批量测试模式
python run_benchmarks.py \
    --vllm_url "http://localhost:8000/v1" \
    --api_key "your-api-key" \
    --model "Qwen2.5-7B-Instruct-AWQ" \
    --config '[
        {"num_requests": 20, "spread_mode": "uniform", "duration": 20, "output_tokens": 100},
        {"num_requests": 50, "spread_mode": "uniform", "duration": 20, "output_tokens": 100},
    ]' \
    --use_long_context