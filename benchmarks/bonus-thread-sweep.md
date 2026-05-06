# Bonus - CPU thread sweep

Model: `qwen2.5-1.5b-instruct-q4_k_m.gguf`

| threads | TTFT (ms) | decode (tok/s) |
|---:|---:|---:|
| 1 | 213.5 | 12.04 |
| 2 | 192.4 | 15.12 |
| 4 | 199.3 | 14.34 |
| 8 | 204.7 | 10.57 |
| 12 | 224.1 | 8.26 |

Best: `2` threads at `15.12` tok/s. Baseline: `1` thread at `12.04` tok/s. Speedup: `~1.26x`.

On this CPU fallback path, the useful tuning knob is thread count. Throughput improves as more physical cores are used, but the result should be checked rather than assumed because memory bandwidth and scheduler overhead can flatten or reverse the curve.
