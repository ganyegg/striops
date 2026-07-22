"""LLM provider abstraction.

`LLMProvider` defines the contract. `GeminiProvider` calls Google Gemini via the
current ``google-genai`` SDK (with a legacy ``google-generativeai`` fallback).
`MockProvider` returns deterministic text for CI / offline runs.
"""
from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod

from striops.core.config import Settings, get_settings
from striops.core.logging import get_logger

log = get_logger("striops.reasoning")


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
    """Deterministic, offline provider for CI / local dev without a key."""

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
        seed = int(hashlib.sha256(text.encode()).hexdigest(), 16)
        vec: list[float] = []
        for _ in range(768):
            seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
            vec.append((seed / 0x7FFFFFFF) * 2 - 1)
        return vec


class GeminiError(RuntimeError):
    """Raised when Gemini cannot produce a usable response."""


class GeminiProvider(LLMProvider):
    """Google Gemini-backed provider (new SDK preferred, legacy as fallback)."""

    name = "gemini"

    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.gemini_api_key
        self._model_name = settings.gemini_model
        self._embed_model = settings.gemini_embed_model
        self._backend = "none"
        self._client = None
        self._legacy = None

        # Prefer the current google-genai SDK (supports gemini-2.5-flash cleanly).
        try:
            from google import genai

            self._client = genai.Client(api_key=self._api_key)
            self._backend = "google-genai"
            log.info("gemini client ready", extra={"context": {"sdk": "google-genai", "model": self._model_name}})
            return
        except Exception as exc:
            log.warning("google-genai unavailable, trying legacy SDK", extra={"context": {"error": str(exc)}})

        # Legacy google-generativeai (older deploys / pinned requirements).
        try:
            import google.generativeai as genai_legacy

            genai_legacy.configure(api_key=self._api_key)
            self._legacy = genai_legacy
            self._legacy_model = genai_legacy.GenerativeModel(self._model_name)
            self._backend = "google-generativeai"
            log.info(
                "gemini client ready",
                extra={"context": {"sdk": "google-generativeai", "model": self._model_name}},
            )
        except Exception as exc:
            raise GeminiError(f"no usable Gemini SDK: {exc}") from exc

    def generate(self, prompt: str, *, system: str | None = None, temperature: float = 0.2) -> str:
        try:
            if self._backend == "google-genai" and self._client is not None:
                from google.genai import types

                config = types.GenerateContentConfig(
                    temperature=temperature,
                    system_instruction=system or None,
                )
                resp = self._client.models.generate_content(
                    model=self._model_name,
                    contents=prompt,
                    config=config,
                )
                text = (getattr(resp, "text", None) or "").strip()
                if not text:
                    raise GeminiError("empty Gemini response")
                return text

            if self._legacy is not None:
                model = self._legacy_model
                if system:
                    model = self._legacy.GenerativeModel(self._model_name, system_instruction=system)
                resp = model.generate_content(
                    prompt,
                    generation_config={"temperature": temperature},
                )
                text = (getattr(resp, "text", None) or "").strip()
                if not text:
                    raise GeminiError("empty Gemini response (legacy SDK)")
                return text

            raise GeminiError("Gemini provider not initialised")
        except GeminiError:
            raise
        except Exception as exc:
            log.warning("gemini generate failed", extra={"context": {"error": str(exc), "sdk": self._backend}})
            raise GeminiError(str(exc)) from exc

    def generate_json(self, prompt: str, *, system: str | None = None) -> dict:
        instruction = (system or "") + "\nRespond ONLY with valid minified JSON."
        raw = self.generate(prompt, system=instruction, temperature=0.1)
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise GeminiError(f"non-JSON Gemini response: {raw[:200]}") from exc

    def embed(self, text: str) -> list[float]:
        try:
            if self._backend == "google-genai" and self._client is not None:
                resp = self._client.models.embed_content(model=self._embed_model, contents=text)
                # google-genai returns .embeddings[0].values or similar shapes across versions
                emb = getattr(resp, "embeddings", None) or getattr(resp, "embedding", None)
                if emb is None and isinstance(resp, dict):
                    emb = resp.get("embeddings") or resp.get("embedding")
                if hasattr(emb, "__iter__") and emb is not None:
                    first = emb[0] if not isinstance(emb, dict) else emb
                    values = getattr(first, "values", None) or (
                        first if isinstance(first, list) else None
                    )
                    if values:
                        return list(values)
                raise GeminiError("unexpected embed response shape")

            if self._legacy is not None:
                resp = self._legacy.embed_content(model=self._embed_model, content=text)
                return list(resp["embedding"])

            raise GeminiError("Gemini provider not initialised")
        except Exception as exc:
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


def reset_llm() -> None:
    """Test helper — clear the process-wide provider."""
    global _provider
    _provider = None
