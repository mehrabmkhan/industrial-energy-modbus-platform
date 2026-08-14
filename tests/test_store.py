from pathlib import Path

from meterlink.electrical import EnergyModel
from meterlink.store import export_readings_csv, initialize_store, insert_reading, latest_reading


def test_sqlite_store_records_and_exports_readings(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("METERLINK_DB", str(tmp_path / "meterlink.db"))
    initialize_store()

    values = EnergyModel().snapshot()
    insert_reading("ML-TEST", values, "NORMAL")

    latest = latest_reading()
    csv_output = export_readings_csv()

    assert latest is not None
    assert latest["device"] == "ML-TEST"
    assert "active_power_kw" in csv_output


def test_csv_export_accepts_time_range(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("METERLINK_DB", str(tmp_path / "meterlink.db"))
    initialize_store()

    insert_reading("ML-TEST", EnergyModel().snapshot(), "NORMAL")
    csv_output = export_readings_csv(start="2000-01-01T00:00:00Z", end="2999-01-01T00:00:00Z")

    assert "ML-TEST" in csv_output
