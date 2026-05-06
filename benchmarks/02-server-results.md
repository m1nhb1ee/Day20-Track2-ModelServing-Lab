# 02 - Server Results (CPU fallback)

Runtime: `python -m llama_cpp.server` on Windows, CPU mode (`n_gpu_layers=0`, `n_threads=8`, `n_ctx=1024`).

## Smoke test

- `POST /v1/chat/completions`: pass
- `GET /v1/models`: pass
- `/metrics`: not exposed by this fallback server build

## Locust summary

| Concurrency | Total requests | Failures | Failure rate | Approx RPS | E2E P50 (ms) | E2E P95 (ms) | E2E P99 (ms) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 39 | 0 | 0.00% | 0.66 | 12000 | 17000 | 18000 |
| 50 | 38 | 17 | 44.74% | 0.64 | 25000 | 32000 | 32000 |

## Observation

At `u=50`, latency rose sharply and timeout failures appeared, which indicates CPU saturation and queueing under contention.
