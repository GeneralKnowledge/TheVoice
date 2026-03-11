"""Entry point for the local autonomous streamer bot prototype."""

from __future__ import annotations

import asyncio
import json

from .config import load_config
from .orchestrator import PerformanceOrchestrator
from .utils import configure_logging


async def _run() -> None:
    cfg = load_config()
    orchestrator = PerformanceOrchestrator(cfg)
    results = await orchestrator.run()
    print("\n=== Local Performance Summary ===")
    print(json.dumps(results, indent=2))


def main() -> None:
    configure_logging()
    asyncio.run(_run())


if __name__ == "__main__":
    main()
