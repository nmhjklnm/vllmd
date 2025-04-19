vllm serve \
  Qwen2.5-7B-Instruct-AWQ \
  --tensor-parallel-size 1 \
  --max-model-len 16384 \
  --enable-chunked-prefill \
  --long-prefill-token-threshold 4096 \
  --max-num-batched-tokens 65536 \
  --max-num-seqs 10 \
  --quantization awq \
  --gpu-memory-utilization 0.9
