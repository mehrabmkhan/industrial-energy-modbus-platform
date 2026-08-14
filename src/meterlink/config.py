from __future__ import annotations

import os
from pathlib import Path

import yaml

from .client import DeviceConfig


def load_device_config(path: str | Path = "config/default_device.yaml") -> DeviceConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return DeviceConfig(
        device_name=os.getenv("METERLINK_DEVICE_NAME", raw["device_name"]),
        host=os.getenv("METERLINK_MODBUS_HOST", raw["host"]),
        port=int(os.getenv("METERLINK_MODBUS_PORT", raw["port"])),
        unit_id=int(os.getenv("METERLINK_UNIT_ID", raw["unit_id"])),
        poll_interval=float(os.getenv("METERLINK_POLL_INTERVAL", raw["poll_interval"])),
        timeout=float(os.getenv("METERLINK_TIMEOUT", raw["timeout"])),
        retries=int(os.getenv("METERLINK_RETRIES", raw["retries"])),
        nominal_voltage=float(os.getenv("METERLINK_NOMINAL_VOLTAGE", raw["nominal_voltage"])),
        ct_primary_rating=int(os.getenv("METERLINK_CT_PRIMARY", raw["ct_primary_rating"])),
        ct_secondary_rating=int(os.getenv("METERLINK_CT_SECONDARY", raw["ct_secondary_rating"])),
        pt_ratio=float(os.getenv("METERLINK_PT_RATIO", raw["pt_ratio"])),
    )


def validate_device_config(config: DeviceConfig) -> list[str]:
    errors: list[str] = []
    if not config.device_name.strip():
        errors.append("Meter name is required")
    if not 1 <= config.port <= 65535:
        errors.append("Modbus TCP port must be between 1 and 65535")
    if not 1 <= config.unit_id <= 247:
        errors.append("Unit ID must be between 1 and 247")
    if config.poll_interval < 0.25:
        errors.append("Polling interval must be at least 0.25 seconds")
    if config.timeout <= 0:
        errors.append("Timeout must be positive")
    if config.nominal_voltage <= 0:
        errors.append("Nominal voltage must be positive")
    if config.ct_primary_rating <= config.ct_secondary_rating:
        errors.append("CT primary rating must be greater than CT secondary rating")
    if config.pt_ratio <= 0:
        errors.append("PT ratio must be positive")
    return errors
