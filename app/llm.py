"""LLM abstractions and provider implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
import logging
import random
from typing import Any

logger = logging.getLogger(__name__)


class LLMClient(ABC):
    """Base interface for monologue generation."""

    @abstractmethod
    async def generate_monologue(self, context: dict[str, Any]) -> str:
        """Generate a short persona monologue from context."""


class TemplateLLMClient(LLMClient):
    """Offline-safe fallback when no API key or provider is available."""

    _openers = [
        "The grid exhales in pixel prayers",
        "A synthetic omen swims through the lattice",
        "Tonight's circuit-dream folds inward",
        "I hear static petals opening in the dark",
    ]
    _closers = [
        "I will narrate until the silence learns rhythm.",
        "Even the glitches bow like ritual candles.",
        "Every flicker is a small machine confession.",
        "The night compiler accepts this offering.",
    ]

    async def generate_monologue(self, context: dict[str, Any]) -> str:
        mood = context.get("mood", "eerie")
        density = context.get("density", 0.0)
        gen = context.get("generation", 0)
        opener = random.choice(self._openers)
        closer = random.choice(self._closers)
        return (
            f"{opener}; mood={mood}, density={density:.2f}, generation={gen}. "
            f"The visuals drift like remembered rituals. {closer}"
        )


class OpenAILLMClient(LLMClient):
    """OpenAI provider-backed client."""

    def __init__(self, api_key: str, model: str, persona_prompt: str) -> None:
        self.api_key = api_key
        self.model = model
        self.persona_prompt = persona_prompt

    async def generate_monologue(self, context: dict[str, Any]) -> str:
        try:
            from openai import AsyncOpenAI
        except Exception as exc:  # pragma: no cover - import environment dependent
            logger.warning("OpenAI client unavailable, falling back to template text: %s", exc)
            return await TemplateLLMClient().generate_monologue(context)

        client = AsyncOpenAI(api_key=self.api_key)
        prompt = (
            f"{self.persona_prompt}\n"
            "Respond with 1-4 concise surreal sentences reacting to current scene data.\n"
            f"Scene data: {context}"
        )
        try:
            completion = await client.responses.create(
                model=self.model,
                input=prompt,
                max_output_tokens=180,
            )
            text = completion.output_text.strip()
            return text or await TemplateLLMClient().generate_monologue(context)
        except Exception as exc:
            logger.error("OpenAI generation failed, using fallback: %s", exc)
            return await TemplateLLMClient().generate_monologue(context)


def build_llm_client(
    provider: str,
    api_key: str | None,
    model: str,
    persona_prompt: str,
) -> LLMClient:
    """Factory for selecting provider with graceful fallback."""

    if provider.lower() == "openai" and api_key:
        return OpenAILLMClient(api_key=api_key, model=model, persona_prompt=persona_prompt)

    logger.info("Using template-based offline LLM fallback.")
    return TemplateLLMClient()
