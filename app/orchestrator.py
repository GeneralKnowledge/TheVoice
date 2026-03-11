"""Core asynchronous performance loop orchestration."""

from __future__ import annotations

import asyncio
from pathlib import Path
import logging
from typing import Any

from .config import AppConfig
from .llm import build_llm_client
from .slow_audio import SlowAudioProcessor
from .strudel_client import StrudelClient
from .tts import build_tts_client
from .utils import create_cycle_output_dir, write_json
from .visuals import AutomataConfig, CellularAutomataEngine

logger = logging.getLogger(__name__)


class PerformanceOrchestrator:
    """Coordinates speech, visuals, and audio generation into local artifacts."""

    def __init__(self, cfg: AppConfig) -> None:
        self.cfg = cfg
        self.llm = build_llm_client(cfg.llm_provider, cfg.openai_api_key, cfg.openai_model, cfg.persona_prompt)
        self.tts = build_tts_client(cfg.tts_provider, cfg.tts_voice, cfg.tts_rate)
        self.visuals = CellularAutomataEngine(
            AutomataConfig(
                width=cfg.automata_width,
                height=cfg.automata_height,
                cell_size=cfg.automata_cell_size,
                seed_density=cfg.automata_seed_density,
                fps=cfg.automata_fps,
            ),
            rule=cfg.automata_rule,
        )
        self.strudel = StrudelClient(base_url=cfg.strudel_base_url, headless=cfg.strudel_headless)
        self.slow_audio = SlowAudioProcessor()

    async def run(self) -> list[dict[str, Any]]:
        """Run configured cycles and return artifact summaries."""

        self.cfg.output_root.mkdir(parents=True, exist_ok=True)
        results: list[dict[str, Any]] = []
        if self.cfg.enable_strudel:
            await self.strudel.start()

        try:
            for cycle_idx in range(1, self.cfg.cycles + 1):
                summary = await self._run_cycle(cycle_idx)
                results.append(summary)
                await asyncio.sleep(max(0.0, self.cfg.loop_interval_seconds))
        finally:
            await self.strudel.stop()

        self._write_session_summary(results)
        return results

    async def _run_cycle(self, cycle_idx: int) -> dict[str, Any]:
        cycle_dir = create_cycle_output_dir(self.cfg.output_root, cycle_idx)
        logger.info("Starting cycle %s in %s", cycle_idx, cycle_dir)

        artifact_summary: dict[str, Any] = {
            "cycle": cycle_idx,
            "directory": str(cycle_dir),
            "config_snapshot": self._config_snapshot(),
            "artifacts": {},
        }

        visual_context: dict[str, Any] = {"generation": 0, "density": 0.0, "change_rate": 0.0, "dominant_pattern": "n/a"}
        if self.cfg.enable_visuals:
            try:
                gif_path, visual_context = self.visuals.export_gif(
                    cycle_dir / "automata.gif",
                    steps=self.cfg.automata_steps_per_cycle,
                )
                artifact_summary["artifacts"]["visual_gif"] = gif_path
                artifact_summary["visual_metadata"] = visual_context
            except Exception as exc:
                logger.error("Visual generation failed: %s", exc)

        mood = self._mood_from_visual_context(visual_context)
        context = {**visual_context, "mood": mood}

        if self.cfg.enable_llm_speech:
            try:
                monologue = await self.llm.generate_monologue(context)
                artifact_summary["artifacts"]["monologue_text"] = monologue
                speech_file = cycle_dir / "speech.wav"
                speech_path = await self.tts.synthesize(monologue, str(speech_file))
                artifact_summary["artifacts"]["speech_audio"] = speech_path
            except Exception as exc:
                logger.error("LLM/TTS path failed: %s", exc)

        if self.cfg.enable_strudel:
            try:
                pattern = self.strudel.generate_pattern(context)
                artifact_summary["artifacts"]["strudel_pattern"] = pattern
                injected = await self.strudel.set_pattern(pattern)
                artifact_summary["artifacts"]["strudel_injected"] = injected
                (cycle_dir / "strudel_pattern.strudel").write_text(pattern, encoding="utf-8")
            except Exception as exc:
                logger.error("Strudel integration failed: %s", exc)

        if self.cfg.enable_slow_audio:
            try:
                source = self.cfg.slow_audio_source
                if source.exists():
                    slowed = self.slow_audio.slow_file(
                        str(source),
                        str(cycle_dir / f"slowed_x{int(self.cfg.slow_audio_factor)}.wav"),
                        factor=self.cfg.slow_audio_factor,
                    )
                    artifact_summary["artifacts"]["slowed_audio"] = slowed
                else:
                    artifact_summary["artifacts"]["slowed_audio"] = "source file missing"
            except Exception as exc:
                logger.error("Slow audio processing failed: %s", exc)

        write_json(cycle_dir / "summary.json", artifact_summary)
        return artifact_summary


    def _config_snapshot(self) -> dict[str, Any]:
        snapshot: dict[str, Any] = {}
        for key in self.cfg.__dataclass_fields__:
            value = getattr(self.cfg, key)
            snapshot[key] = str(value) if isinstance(value, Path) else value
        return snapshot

    def _write_session_summary(self, summaries: list[dict[str, Any]]) -> None:
        session_path = self.cfg.output_root / "latest_session_summary.json"
        write_json(session_path, {"cycles": summaries})

        html = ["<html><body><h1>Autonomous Streamer Local Session</h1><ul>"]
        for cycle in summaries:
            html.append(f"<li>Cycle {cycle['cycle']}:<pre>{cycle['artifacts']}</pre></li>")
        html.append("</ul></body></html>")
        (self.cfg.output_root / "latest_session_summary.html").write_text("\n".join(html), encoding="utf-8")

    @staticmethod
    def _mood_from_visual_context(context: dict[str, Any]) -> str:
        density = float(context.get("density", 0.0))
        change = float(context.get("change_rate", 0.0))
        if change > 0.35:
            return "glitchy"
        if density < 0.1:
            return "sparse"
        if density > 0.38:
            return "ritualistic"
        return "eerie"
