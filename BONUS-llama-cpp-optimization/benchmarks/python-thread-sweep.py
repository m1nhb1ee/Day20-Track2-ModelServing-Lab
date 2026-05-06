#!/usr/bin/env python3
"""CPU fallback thread sweep using llama-cpp-python.

This is used when native llama.cpp/llama-bench cannot be built on Windows.
It still measures the same tuning knob as the official bonus thread sweep:
decode throughput as a function of `n_threads`.
"""
from __future__ import annotations

import json
import statistics
import time
from pathlib import Path

from llama_cpp import Llama


PROMPT = "Explain why goodput at SLO is more useful than peak throughput."


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8", errors="ignore"))


def measure(model_path: str, threads: int, repeats: int = 2) -> dict:
    llm = Llama(
        model_path=model_path,
        n_threads=threads,
        n_ctx=512,
        n_batch=256,
        n_gpu_layers=0,
        verbose=False,
    )
    rates: list[float] = []
    ttfts: list[float] = []
    for _ in range(repeats):
        start = time.perf_counter()
        first = None
        tokens = 0
        for chunk in llm.create_completion(
            prompt=PROMPT,
            max_tokens=32,
            temperature=0.2,
            stream=True,
        ):
            text = chunk["choices"][0].get("text", "")
            if text:
                tokens += 1
                if first is None:
                    first = time.perf_counter()
        end = time.perf_counter()
        if first and tokens > 1:
            ttfts.append((first - start) * 1000.0)
            rates.append((tokens - 1) / max(end - first, 0.001))
    return {
        "threads": threads,
        "ttft_ms": round(statistics.median(ttfts), 1) if ttfts else 0.0,
        "decode_tok_s": round(statistics.median(rates), 2) if rates else 0.0,
    }


def main() -> int:
    active = load_json("models/active.json")
    hw = load_json("hardware.json")
    model_path = active["primary_model"]
    physical = hw["cpu"].get("cores_physical") or 4
    logical = hw["cpu"].get("cores_logical") or physical
    grid = sorted({1, 2, max(physical // 2, 1), physical, logical})

    rows = []
    print(f"==> python thread sweep on {Path(model_path).name}")
    for threads in grid:
        row = measure(model_path, threads)
        rows.append(row)
        print(
            f"threads={threads:2d}  "
            f"ttft={row['ttft_ms']:7.1f} ms  "
            f"decode={row['decode_tok_s']:5.2f} tok/s"
        )

    best = max(rows, key=lambda row: row["decode_tok_s"])
    baseline = next((row for row in rows if row["threads"] == 1), rows[0])
    speedup = best["decode_tok_s"] / max(baseline["decode_tok_s"], 0.001)

    out_dir = Path("benchmarks")
    out_dir.mkdir(exist_ok=True)
    md = "# Bonus - CPU thread sweep\n\n"
    md += f"Model: `{Path(model_path).name}`\n\n"
    md += "| threads | TTFT (ms) | decode (tok/s) |\n|---:|---:|---:|\n"
    md += "\n".join(
        f"| {row['threads']} | {row['ttft_ms']:.1f} | {row['decode_tok_s']:.2f} |"
        for row in rows
    )
    md += "\n\n"
    md += (
        f"Best: `{best['threads']}` threads at `{best['decode_tok_s']:.2f}` tok/s. "
        f"Baseline: `1` thread at `{baseline['decode_tok_s']:.2f}` tok/s. "
        f"Speedup: `~{speedup:.2f}x`.\n\n"
    )
    md += (
        "On this CPU fallback path, the useful tuning knob is thread count. "
        "Throughput improves as more physical cores are used, but the result should "
        "be checked rather than assumed because memory bandwidth and scheduler "
        "overhead can flatten or reverse the curve.\n"
    )
    (out_dir / "bonus-thread-sweep.md").write_text(md, encoding="utf-8")
    (out_dir / "bonus-thread-sweep.json").write_text(
        json.dumps(rows, indent=2),
        encoding="utf-8",
    )
    print("\n" + md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
