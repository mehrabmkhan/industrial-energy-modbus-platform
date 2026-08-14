import asyncio
import contextlib
import socket

import pytest

from meterlink.client import DeviceConfig, MeterClient
from meterlink.simulator import run_server


def unused_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.mark.asyncio
async def test_simulator_serves_decoded_measurements() -> None:
    port = unused_tcp_port()
    server_task = asyncio.create_task(run_server("127.0.0.1", port))
    await asyncio.sleep(0.5)

    client = MeterClient(DeviceConfig(port=port, timeout=1.0))
    try:
        values = await client.poll()
    finally:
        await client.disconnect()
        server_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await server_task

    assert values["status_word"] & 1 == 1
    assert 590 <= values["voltage_avg"] <= 610
    assert values["active_power_kw"] > 0
