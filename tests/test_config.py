from meterlink.client import DeviceConfig
from meterlink.config import validate_device_config


def test_valid_device_config_passes_validation() -> None:
    assert validate_device_config(DeviceConfig()) == []


def test_invalid_device_config_returns_actionable_errors() -> None:
    config = DeviceConfig(device_name="", port=70000, unit_id=300, poll_interval=0.1, ct_primary_rating=5, ct_secondary_rating=5)
    errors = validate_device_config(config)

    assert "Meter name is required" in errors
    assert "Modbus TCP port must be between 1 and 65535" in errors
    assert "Unit ID must be between 1 and 247" in errors
    assert "Polling interval must be at least 0.25 seconds" in errors
    assert "CT primary rating must be greater than CT secondary rating" in errors
