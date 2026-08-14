import pytest
import socket

from meterlink.client import DeviceConfig, MeterClient


def unused_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.mark.asyncio
async def test_client_reports_connection_failure() -> None:
    client = MeterClient(DeviceConfig(port=unused_tcp_port(), timeout=0.2, retries=0))

    with pytest.raises(ConnectionError):
        await client.poll()

    assert client.stats.failed_polls == 1
    assert client.stats.status == "OFFLINE"
