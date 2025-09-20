"""Entry point for running the offline RSPS server."""

from __future__ import annotations

import asyncio
import contextlib
from pathlib import Path

from .config import ServerConfig
from .network import start_server
from .world import GameWorld


async def run() -> None:
    config_path = Path(__file__).resolve().parent / "config.json"
    config = ServerConfig.load(config_path)
    world = GameWorld(config)
    world_task = asyncio.create_task(world.run())
    try:
        await start_server(world, config)
    finally:
        world_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await world_task


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
