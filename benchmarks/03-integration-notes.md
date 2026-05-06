# 03 - Integration Notes

Connected pieces:

- N16 (Cloud/IaC): local-only stub (no remote cluster in this run)
- N17 (Data pipeline): stub retrieval logic in `pipeline.py`
- N18 (Lakehouse): stub (in-memory docs)
- N19 (Vector + Feature Store): stub keyword overlap on `TOY_DOCS`
- N20 (Serving): real local `llama_cpp.server` endpoint on `http://localhost:8080/v1`

Latency observation (from `pipeline.py` run):

- retrieve: ~0.0 ms
- llama-server: ~7.0-8.7 s
- total: ~7.0-8.7 s

Main bottleneck is model inference in llama-server (CPU decode), not retrieval.
