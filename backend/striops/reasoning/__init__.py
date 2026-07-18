"""Reasoning layer: the swappable LLM provider interface.

The LLM is a *narrator and synthesiser* over the reasoning core — never the
source of truth. Everything here is behind an interface so Gemini can be
swapped for another provider, or a deterministic mock (offline / CI).
"""
from striops.reasoning.llm import (
    GeminiProvider,
    LLMProvider,
    MockProvider,
    get_llm,
)

__all__ = ["LLMProvider", "GeminiProvider", "MockProvider", "get_llm"]
