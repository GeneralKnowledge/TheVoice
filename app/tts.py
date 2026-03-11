"""TTS abstractions and local speech synthesis fallbacks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from array import array
from pathlib import Path
import logging
import math
import re
import wave
from typing import Final

logger = logging.getLogger(__name__)
_MAX_CHARS: Final[int] = 420


class TTSClient(ABC):
    @abstractmethod
    async def synthesize(self, text: str, output_path: str) -> str:
        """Synthesize text to an audio file and return path."""


class LocalToneFallbackTTS(TTSClient):
    """Creates a simple sine-tone signal if real TTS is unavailable."""

    async def synthesize(self, text: str, output_path: str) -> str:
        target = Path(output_path)
        sample_rate = 24000
        duration = min(2 + len(text) / 90.0, 7)
        frame_count = int(sample_rate * duration)
        pcm = array("h")
        for i in range(frame_count):
            t = i / sample_rate
            value = 0.25 * math.sin(2 * math.pi * 220 * t) + 0.1 * math.sin(2 * math.pi * 330 * t)
            pcm.append(int(max(-1.0, min(1.0, value)) * 32767))

        with wave.open(str(target), "wb") as wavf:
            wavf.setnchannels(1)
            wavf.setsampwidth(2)
            wavf.setframerate(sample_rate)
            wavf.writeframes(pcm.tobytes())
        return str(target)


class Pyttsx3TTSClient(TTSClient):
    def __init__(self, voice: str | None = None, rate: int = 165) -> None:
        self.voice = voice
        self.rate = rate

    async def synthesize(self, text: str, output_path: str) -> str:
        normalized = normalize_text(text)
        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.setProperty("rate", self.rate)
            if self.voice:
                engine.setProperty("voice", self.voice)
            engine.save_to_file(normalized, output_path)
            engine.runAndWait()
            return output_path
        except Exception as exc:
            logger.error("pyttsx3 synthesis failed, using tone fallback: %s", exc)
            return await LocalToneFallbackTTS().synthesize(normalized, output_path)


def normalize_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned[:_MAX_CHARS]


def build_tts_client(provider: str, voice: str | None, rate: int) -> TTSClient:
    if provider.lower() == "pyttsx3":
        return Pyttsx3TTSClient(voice=voice, rate=rate)
    logger.info("Unknown TTS provider '%s', using tone fallback.", provider)
    return LocalToneFallbackTTS()
