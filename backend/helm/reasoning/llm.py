"""LLM provider abstraction.

`LLMProvider` defines the contract. `GeminiProvider` calls Google Gemini.
`MockProvider` returns deterministic text derived from the prompt so tests and
offline runs are fully reproducible without a network or API key.
"""
from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod

from helm.core.config import Settings, get_settings
from helm.core.logging import get_logger

log = get_logger("helm.reasoning")


class LLMProvider(ABC):
    """Contract for text generation + embeddings used by agents/engines."""

    name: str = "abstract"

    @abstractmethod
    def generate(self, prompt: str, *, system: str | None = None, temperature: float = 0.2) -> str:
        ...

    @abstractmethod
    def generate_json(self, prompt: str, *, system: str | None = None) -> dict:
        ...

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        ...


class MockProvider(LLMProvider):
    """Deterministic, offline provider.

    Produces stable, prompt-derived output so the whole platform runs and is
    testable without any external dependency. Not a fallback of last resort —
    it is the default in CI and local dev without a key.
    """

    name = "mock"

    def generate(self, prompt: str, *, system: str | None = None, temperature: float = 0.2) -> str:
        head = prompt.strip().splitlines()[0][:160] if prompt.strip() else "(empty)"
        digest = hashlib.sha256(prompt.encode()).hexdigest()[:8]
        return (
            f"[mock:{digest}] Synthesised strategic narrative based on: {head}. "
            "Reasoning is grounded in the supplied evidence; confidence reflects "
            "data completeness and trend stability."
        )

    def generate_json(self, prompt: str, *, system: str | None = None) -> dict:
        digest = hashlib.sha256(prompt.encode()).hexdigest()[:8]
        return {
            "summary": self.generate(prompt, system=system),
            "confidence": 0.72,
            "trace": digest,
        }

    def embed(self, text: str) -> list[float]:
        # Deterministic pseudo-embedding (768-d) from the text hash.
        seed = int(hashlib.sha256(text.encode()).hexdigest(), 16)
        vec: list[float] = []
        for _ in range(768):
            seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
            vec.append((seed / 0x7FFFFFFF) * 2 - 1)
        return vec


class GeminiProvider(LLMProvider):
    """Google Gemini-backed provider."""

    name = "gemini"

    def __init__(self, settings: Settings) -> None:
        import google.generativeai as genai  # imported lazily

        genai.configure(api_key=settings.gemini_api_key)
        self._genai = genai
        self._model_name = settings.gemini_model
        self._embed_model = settings.gemini_embed_model
        self._model = genai.GenerativeModel(settings.gemini_model)

    def generate(self, prompt: str, *, system: str | None = None, temperature: float = 0.2) -> str:
        try:
            model = self._model
            if system:
                model = self._genai.GenerativeModel(self._model_name, system_instruction=system)
            resp = model.generate_content(
                prompt,
                generation_config={"temperature": temperature},
            )
            return (resp.text or "").strip()
        except Exception as exc:  # pragma: no cover - network path
            log.warning("gemini generate failed, using mock", extra={"context": {"error": str(exc)}})
            return MockProvider().generate(prompt, system=system, temperature=temperature)

    def generate_json(self, prompt: str, *, system: str | None = None) -> dict:
        instruction = (system or "") + "\nRespond ONLY with valid minified JSON."
        raw = self.generate(prompt, system=instruction, temperature=0.1)
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            log.warning("gemini returned non-JSON, using mock json")
            return MockProvider().generate_json(prompt, system=system)

    def embed(self, text: str) -> list[float]:
        try:
            resp = self._genai.embed_content(model=self._embed_model, content=text)
            return list(resp["embedding"])
        except Exception as exc:  # pragma: no cover - network path
            log.warning("gemini embed failed, using mock", extra={"context": {"error": str(exc)}})
            return MockProvider().embed(text)


_provider: LLMProvider | None = None


def get_llm(settings: Settings | None = None) -> LLMProvider:
    """Return the process-wide LLM provider (Gemini if a key exists, else Mock)."""
    global _provider
    if _provider is not None:
        return _provider
    settings = settings or get_settings()
    if settings.has_llm:
        try:
            _provider = GeminiProvider(settings)
            log.info("llm provider ready", extra={"context": {"provider": "gemini"}})
        except Exception as exc:  # pragma: no cover
            log.warning("gemini init failed, using mock", extra={"context": {"error": str(exc)}})
            _provider = MockProvider()
    else:
        _provider = MockProvider()
        log.info("llm provider ready", extra={"context": {"provider": "mock"}})
    return _provider
