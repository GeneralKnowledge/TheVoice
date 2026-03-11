"""Cellular automata visual generation and metadata summarization."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import logging
from typing import Any
import random

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AutomataConfig:
    width: int
    height: int
    cell_size: int
    seed_density: float
    fps: int


class CellularAutomataEngine:
    """Conway's Game of Life renderer with optional PIL GIF output."""

    def __init__(self, cfg: AutomataConfig, rule: str = "life") -> None:
        self.cfg = cfg
        self.rule = rule
        self.grid = [
            [1 if random.random() < cfg.seed_density else 0 for _ in range(cfg.width)]
            for _ in range(cfg.height)
        ]
        self.generation = 0

    def step(self) -> float:
        next_grid = [[0] * self.cfg.width for _ in range(self.cfg.height)]
        changed = 0
        for y in range(self.cfg.height):
            for x in range(self.cfg.width):
                neighbors = 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        neighbors += self.grid[(y + dy) % self.cfg.height][(x + dx) % self.cfg.width]
                current = self.grid[y][x]
                nxt = 1 if neighbors == 3 or (current == 1 and neighbors == 2) else 0
                next_grid[y][x] = nxt
                if nxt != current:
                    changed += 1
        self.grid = next_grid
        self.generation += 1
        return changed / (self.cfg.width * self.cfg.height)

    def summarize_state(self, change_rate: float) -> dict[str, Any]:
        alive = sum(sum(row) for row in self.grid)
        density = alive / (self.cfg.width * self.cfg.height)
        pattern = "sparse embers" if density < 0.12 else "drifting islands" if density < 0.35 else "crowded storm"
        return {
            "generation": self.generation,
            "density": density,
            "change_rate": change_rate,
            "dominant_pattern": pattern,
        }

    def export_gif(
        self,
        output_path: Path,
        steps: int,
        alive_color: tuple[int, int, int] = (136, 255, 188),
        dead_color: tuple[int, int, int] = (8, 11, 18),
    ) -> tuple[str, dict[str, Any]]:
        """Export animated output. Uses GIF when PIL exists, text frames otherwise."""

        frames = []
        change = 0.0
        for _ in range(steps):
            change = self.step()
            frames.append([row[:] for row in self.grid])

        try:
            from PIL import Image

            images = []
            for frame in frames:
                img = Image.new("RGB", (self.cfg.width, self.cfg.height), dead_color)
                pixels = img.load()
                for y, row in enumerate(frame):
                    for x, val in enumerate(row):
                        if val:
                            pixels[x, y] = alive_color
                images.append(
                    img.resize(
                        (self.cfg.width * self.cfg.cell_size, self.cfg.height * self.cfg.cell_size),
                        Image.Resampling.NEAREST,
                    )
                )
            images[0].save(
                output_path,
                save_all=True,
                append_images=images[1:],
                loop=0,
                duration=max(20, int(1000 / max(1, self.cfg.fps))),
            )
            final_path = output_path
        except Exception as exc:
            logger.warning("PIL unavailable for GIF export (%s). Writing text frame dump.", exc)
            final_path = output_path.with_suffix(".txt")
            lines = []
            for i, frame in enumerate(frames):
                lines.append(f"frame {i}")
                lines.extend("".join("#" if v else "." for v in row) for row in frame)
            final_path.write_text("\n".join(lines), encoding="utf-8")

        return str(final_path), self.summarize_state(change)
