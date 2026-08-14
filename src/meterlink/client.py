from __future__ import annotations

import time
from dataclasses import dataclass, field

from pymodbus.client import AsyncModbusTcpClient

from .registers import RegisterMap, decode_block, load_register_map


@dataclass
class DeviceConfig:
    device_name: str = "ML-600V-DEMO"
    host: str = "127.0.0.1"
    port: int = 15020
    unit_id: int = 1
    poll_interval: float = 1.0
    timeout: float = 1.5
    retries: int = 2
    nominal_voltage: float = 600.0
    ct_primary_rating: int = 1200
    ct_secondary_rating: int = 5
    pt_ratio: float = 1.0


@dataclass
class CommunicationStats:
    successful_polls: int = 0
    failed_polls: int = 0
    retries: int = 0
    last_successful_communication: str | None = None
    last_exception: str = ""
    latency_ms: float = 0.0
    decode_errors: int = 0
    status: str = "OFFLINE"
    latencies: list[float] = field(default_factory=list)

    @property
    def average_latency_ms(self) -> float:
        return round(sum(self.latencies) / len(self.latencies), 2) if self.latencies else 0.0


class MeterClient:
    def __init__(self, config: DeviceConfig, register_map: RegisterMap | None = None) -> None:
        self.config = config
        self.register_map = register_map or load_register_map()
        self.client: AsyncModbusTcpClient | None = None
        self.stats = CommunicationStats()

    async def connect(self) -> bool:
        self.client = AsyncModbusTcpClient(
            self.config.host,
            port=self.config.port,
            timeout=self.config.timeout,
            retries=self.config.retries,
        )
        connected = await self.client.connect()
        self.stats.status = "ONLINE" if connected else "OFFLINE"
        return bool(connected)

    async def disconnect(self) -> None:
        if self.client:
            self.client.close()
        self.stats.status = "OFFLINE"

    async def poll(self) -> dict[str, float | int]:
        if self.client is None or not self.client.connected:
            connected = await self.connect()
            if not connected:
                self._record_failure("connection refused or device offline")
                raise ConnectionError(self.stats.last_exception)
        start = time.perf_counter()
        assert self.client is not None
        try:
            response = await self.client.read_holding_registers(
                self.register_map.block_start,
                count=self.register_map.block_count,
                device_id=self.config.unit_id,
            )
            latency = (time.perf_counter() - start) * 1000
            self.stats.latency_ms = round(latency, 2)
            self.stats.latencies.append(self.stats.latency_ms)
            self.stats.latencies = self.stats.latencies[-50:]
            if response.isError():
                self._record_failure(str(response))
                raise IOError(str(response))
            decoded = decode_block(response.registers, self.register_map)
            self.stats.successful_polls += 1
            self.stats.status = "ONLINE"
            self.stats.last_exception = ""
            self.stats.last_successful_communication = time.strftime("%Y-%m-%d %H:%M:%S")
            return decoded
        except Exception as exc:
            self._record_failure(str(exc))
            await self.disconnect()
            raise

    def _record_failure(self, message: str) -> None:
        self.stats.failed_polls += 1
        self.stats.last_exception = message
        self.stats.status = "DEGRADED" if self.stats.successful_polls else "OFFLINE"
