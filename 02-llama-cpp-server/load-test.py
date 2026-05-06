"""Locust load test against llama-server's OpenAI-compat endpoint.

80% short prompts (chat-style), 20% long prompts (RAG-style with a fake context).
Run with:
    locust -f 02-llama-cpp-server/load-test.py --headless \
        -u 10 -r 1 -t 1m --host http://localhost:8080
"""
from __future__ import annotations

import random

from locust import HttpUser, between, task

SHORT_PROMPTS = [
    "Define TTFT in one sentence.",
    "What's the difference between throughput and goodput?",
    "Why is FlashAttention IO-aware?",
    "When would you use Q4_K_M over Q8_0?",
    "Explain continuous batching to a junior.",
    "What is PagedAttention's main contribution?",
    "Name two reasons to enable prefix caching.",
    "What does --parallel do in llama-server?",
]

LONG_CONTEXT = """
PagedAttention stores KV cache in pages to reduce memory fragmentation.
RadixAttention reuses shared prefixes to skip repeated prefill work.
Goodput@SLO focuses on requests meeting latency targets, not peak throughput.
""".strip()

LONG_PROMPTS = [
    "Summarize the document above in three bullet points.",
    "Based on the document above, when does disaggregated serving NOT help?",
    "Given the doc above, explain APC to a backend engineer who knows caches.",
]


class LlamaServerUser(HttpUser):
    wait_time = between(0.2, 1.5)

    @task(4)
    def short_prompt(self):
        msg = random.choice(SHORT_PROMPTS)
        self._chat([{"role": "user", "content": msg}], max_tokens=12, name="short")

    @task(1)
    def long_prompt_rag(self):
        msg = random.choice(LONG_PROMPTS)
        messages = [
            {"role": "system", "content": "You answer using the document provided."},
            {"role": "user", "content": LONG_CONTEXT + "\n\nQuestion: " + msg},
        ]
        self._chat(messages, max_tokens=20, name="long-rag")

    def _chat(self, messages, max_tokens: int, name: str) -> None:
        self.client.post(
            "/v1/chat/completions",
            json={
                "model": "local",
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.5,
            },
            timeout=30,
            name=name,
        )
