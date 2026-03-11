"""TTS abstractions and local speech synthesis fallbacks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from array import array
from dataclasses import dataclass
from pathlib import Path
import io
import logging
import math
import os
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


@dataclass(slots=True)
class LayerConfig:
    """Voice layer configuration for chorus-style rendering."""

    provider: str
    gain_db: float = 0.0
    tld: str | None = None
    voice_id: str | None = None
    model_id: str | None = None


class CollectiveVoiceTTSClient(TTSClient):
    """Mixes multiple TTS renders for a collective/chorus-style voice."""

    def __init__(
        self,
        base_provider: str = "gtts",
        base_gtts_tld: str = "co.uk",
        elevenlabs_voice_id: str | None = None,
        elevenlabs_model_id: str = "eleven_multilingual_v2",
    ) -> None:
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.layers = [
            LayerConfig(
                provider=base_provider,
                gain_db=0.0,
                tld=base_gtts_tld,
                voice_id=elevenlabs_voice_id,
                model_id=elevenlabs_model_id,
            ),
            LayerConfig(provider="gtts", tld="us", gain_db=-8.0),
            LayerConfig(provider="gtts", tld="com.au", gain_db=-10.0),
            LayerConfig(provider="gtts", tld="co.in", gain_db=-11.5),
        ]

    async def synthesize(self, text: str, output_path: str) -> str:
        normalized = normalize_text(text)
        try:
            from pydub import AudioSegment

            rendered: list[AudioSegment] = []
            for cfg in self.layers:
                seg = self._synthesize_layer(normalized, cfg)
                rendered.append(seg + cfg.gain_db)

            if not rendered:
                raise RuntimeError("No TTS layers generated")

            base = rendered[0]
            target_ms = len(base)
            normalized_layers = [base]
            for seg in rendered[1:]:
                normalized_layers.append(force_length(seg, target_ms))

            offsets_ms = [0, 4, 9, 13]
            if len(offsets_ms) < len(normalized_layers):
                offsets_ms.extend([offsets_ms[-1]] * (len(normalized_layers) - len(offsets_ms)))

            mix_duration = target_ms + max(offsets_ms[: len(normalized_layers)])
            mix = AudioSegment.silent(duration=mix_duration)
            for seg, offset in zip(normalized_layers, offsets_ms):
                mix = mix.overlay(seg, position=offset)

            mix = mix - 2.0
            export_format = "mp3" if output_path.lower().endswith(".mp3") else "wav"
            mix.export(output_path, format=export_format)
            return output_path
        except Exception as exc:
            logger.error("collective synthesis failed, using tone fallback: %s", exc)
            return await LocalToneFallbackTTS().synthesize(normalized, output_path)

    def _synthesize_layer(self, text: str, cfg: LayerConfig):
        if cfg.provider == "gtts":
            return synthesize_gtts(text=text, tld=cfg.tld or "com")
        if cfg.provider == "elevenlabs":
            return synthesize_elevenlabs(
                text=text,
                api_key=self.elevenlabs_api_key,
                voice_id=cfg.voice_id or "",
                model_id=cfg.model_id or "eleven_multilingual_v2",
            )
        raise ValueError(f"Unsupported provider: {cfg.provider}")


def synthesize_gtts(text: str, tld: str = "com", lang: str = "en"):
    from gtts import gTTS
    from pydub import AudioSegment

    data = io.BytesIO()
    gTTS(text=text, lang=lang, tld=tld, slow=False).write_to_fp(data)
    data.seek(0)
    return AudioSegment.from_file(data, format="mp3")


def synthesize_elevenlabs(text: str, api_key: str | None, voice_id: str, model_id: str):
    from elevenlabs.client import ElevenLabs
    from pydub import AudioSegment

    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY is not set")
    if not voice_id:
        raise RuntimeError("ELEVENLABS_VOICE_ID is not configured")

    client = ElevenLabs(api_key=api_key)
    audio_stream = client.text_to_speech.convert(
        voice_id=voice_id,
        model_id=model_id,
        text=text,
    )
    audio_bytes = b"".join(audio_stream)
    return AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")


def change_speed(seg, speed: float):
    """Retimes pydub audio by modifying frame rate."""
    if speed <= 0:
        raise ValueError("speed must be > 0")

    altered = seg._spawn(seg.raw_data, overrides={"frame_rate": int(seg.frame_rate * speed)})
    return altered.set_frame_rate(seg.frame_rate)


def force_length(seg, target_ms: int):
    """Deterministically retime to target_ms and trim/pad exactly."""
    from pydub import AudioSegment

    if target_ms <= 0:
        return AudioSegment.silent(duration=0)

    orig_ms = len(seg)
    if orig_ms == 0:
        return AudioSegment.silent(duration=target_ms)

    speed_factor = orig_ms / target_ms
    adjusted = change_speed(seg, speed_factor)

    if len(adjusted) > target_ms:
        adjusted = adjusted[:target_ms]
    elif len(adjusted) < target_ms:
        adjusted += AudioSegment.silent(duration=(target_ms - len(adjusted)))

    return adjusted


def normalize_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned[:_MAX_CHARS]


def build_tts_client(
    provider: str,
    voice: str | None,
    rate: int,
    collective_base_provider: str = "gtts",
    collective_base_gtts_tld: str = "co.uk",
    collective_elevenlabs_voice_id: str | None = None,
    collective_elevenlabs_model_id: str = "eleven_multilingual_v2",
) -> TTSClient:
    lowered = provider.lower()
    if lowered == "pyttsx3":
        return Pyttsx3TTSClient(voice=voice, rate=rate)
    if lowered == "collective":
        return CollectiveVoiceTTSClient(
            base_provider=collective_base_provider,
            base_gtts_tld=collective_base_gtts_tld,
            elevenlabs_voice_id=collective_elevenlabs_voice_id,
            elevenlabs_model_id=collective_elevenlabs_model_id,
        )
    logger.info("Unknown TTS provider '%s', using tone fallback.", provider)
    return LocalToneFallbackTTS()
