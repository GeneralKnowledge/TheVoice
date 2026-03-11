"""Configuration loading for the local autonomous streamer prototype."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(slots=True)
class AppConfig:
    """Runtime configuration for orchestrating a local performance loop."""

    output_root: Path = Path("assets/output")
    loop_interval_seconds: float = 12.0
    cycles: int = 1

    enable_llm_speech: bool = True
    enable_visuals: bool = True
    enable_strudel: bool = True
    enable_slow_audio: bool = True

    persona_prompt: str = (
        "You are an uncanny late-night synthetic host narrating emergent patterns "
        "as dreams, rituals, and machine omens."
    )

    llm_provider: str = "openai"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    tts_provider: str = "pyttsx3"
    tts_voice: str | None = None
    tts_rate: int = 165

    automata_rule: str = "life"
    automata_width: int = 128
    automata_height: int = 96
    automata_cell_size: int = 6
    automata_steps_per_cycle: int = 36
    automata_seed_density: float = 0.22
    automata_fps: int = 12

    strudel_headless: bool = True
    strudel_base_url: str = "https://strudel.cc"

    slow_audio_source: Path = Path("assets/audio/source.wav")
    slow_audio_factor: float = 100.0


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def load_config() -> AppConfig:
    """Load app config from environment variables with safe defaults."""

    return AppConfig(
        output_root=Path(os.getenv("BOT_OUTPUT_ROOT", "assets/output")),
        loop_interval_seconds=float(os.getenv("BOT_LOOP_INTERVAL_SECONDS", "12")),
        cycles=int(os.getenv("BOT_CYCLES", "1")),
        enable_llm_speech=_as_bool(os.getenv("BOT_ENABLE_LLM_SPEECH"), True),
        enable_visuals=_as_bool(os.getenv("BOT_ENABLE_VISUALS"), True),
        enable_strudel=_as_bool(os.getenv("BOT_ENABLE_STRUDEL"), True),
        enable_slow_audio=_as_bool(os.getenv("BOT_ENABLE_SLOW_AUDIO"), True),
        persona_prompt=os.getenv(
            "BOT_PERSONA_PROMPT",
            "You are an uncanny late-night synthetic host narrating emergent patterns as dreams, rituals, and machine omens.",
        ),
        llm_provider=os.getenv("BOT_LLM_PROVIDER", "openai"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("BOT_OPENAI_MODEL", "gpt-4o-mini"),
        tts_provider=os.getenv("BOT_TTS_PROVIDER", "pyttsx3"),
        tts_voice=os.getenv("BOT_TTS_VOICE"),
        tts_rate=int(os.getenv("BOT_TTS_RATE", "165")),
        automata_rule=os.getenv("BOT_AUTOMATA_RULE", "life"),
        automata_width=int(os.getenv("BOT_AUTOMATA_WIDTH", "128")),
        automata_height=int(os.getenv("BOT_AUTOMATA_HEIGHT", "96")),
        automata_cell_size=int(os.getenv("BOT_AUTOMATA_CELL_SIZE", "6")),
        automata_steps_per_cycle=int(os.getenv("BOT_AUTOMATA_STEPS", "36")),
        automata_seed_density=float(os.getenv("BOT_AUTOMATA_SEED_DENSITY", "0.22")),
        automata_fps=int(os.getenv("BOT_AUTOMATA_FPS", "12")),
        strudel_headless=_as_bool(os.getenv("BOT_STRUDEL_HEADLESS"), True),
        strudel_base_url=os.getenv("BOT_STRUDEL_URL", "https://strudel.cc"),
        slow_audio_source=Path(os.getenv("BOT_SLOW_AUDIO_SOURCE", "assets/audio/source.wav")),
        slow_audio_factor=float(os.getenv("BOT_SLOW_AUDIO_FACTOR", "100")),
    )
