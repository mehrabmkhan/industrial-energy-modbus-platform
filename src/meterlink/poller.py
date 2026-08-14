from __future__ import annotations

import asyncio
from dataclasses import asdict

from .alarms import evaluate_alarms
from .client import DeviceConfig, MeterClient
from .store import insert_alarms, insert_reading, initialize_store


class PollingService:
    def __init__(self, config: DeviceConfig) -> None:
        self.config = config
        self.client = MeterClient(config)
        self.latest_values: dict[str, float | int] = {}
        self.latest_alarms: list[dict] = []
        self.running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        initialize_store()
        self.running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self.running = False
        if self._task:
            self._task.cancel()
        await self.client.disconnect()

    async def poll_once(self) -> dict[str, float | int]:
        values = await self.client.poll()
        alarms = evaluate_alarms(values)
        self.latest_values = values
        self.latest_alarms = alarms
        insert_reading(self.config.device_name, values, "ALARM" if alarms else "NORMAL")
        insert_alarms(alarms)
        return values

    async def _loop(self) -> None:
        while self.running:
            try:
                await self.poll_once()
            except Exception:
                pass
            await asyncio.sleep(self.config.poll_interval)

    def status(self) -> dict:
        stats = self.client.stats
        status = stats.status
        if stats.failed_polls and stats.successful_polls and stats.failed_polls > stats.successful_polls * 0.25:
            status = "DEGRADED"
        return {
            "device": asdict(self.config),
            "connection_status": status,
            "successful_polls": stats.successful_polls,
            "failed_polls": stats.failed_polls,
            "retries": stats.retries,
            "last_successful_communication": stats.last_successful_communication,
            "poll_latency_ms": stats.latency_ms,
            "average_response_time_ms": stats.average_latency_ms,
            "last_exception": stats.last_exception,
            "register_decode_errors": stats.decode_errors,
            "application_version": "1.0.0",
        }
