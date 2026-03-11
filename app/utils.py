"""Utility helpers for logging, file handling, and timing metadata."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import logging


def configure_logging() -> None:
    """Set up structured-ish logs for local runs."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def timestamp_slug() -> str:
    """Create a folder-safe timestamp."""

    return datetime.now().strftime("%Y%m%d-%H%M%S")


def create_cycle_output_dir(root: Path, cycle_index: int) -> Path:
    """Create a unique per-cycle directory."""

    folder = root / f"{timestamp_slug()}-cycle-{cycle_index:03d}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def write_json(path: Path, payload: dict) -> None:
    """Write a JSON file with consistent formatting."""

    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
