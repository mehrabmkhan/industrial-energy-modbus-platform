from __future__ import annotations

import asyncio

from .client import MeterClient
from .config import load_device_config


async def _poll_once() -> None:
    client = MeterClient(load_device_config())
    values = await client.poll()
    await client.disconnect()
    for key, value in values.items():
        print(f"{key}: {value}")


def poll_once_main() -> None:
    asyncio.run(_poll_once())
