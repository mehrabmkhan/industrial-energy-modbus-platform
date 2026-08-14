from __future__ import annotations

import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_DB = Path("data/meterlink.db")


def db_path() -> Path:
    return Path(os.getenv("METERLINK_DB", str(DEFAULT_DB)))


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_store() -> None:
    with connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                device TEXT NOT NULL,
                voltage_avg REAL NOT NULL,
                current_avg REAL NOT NULL,
                frequency REAL NOT NULL,
                active_power_kw REAL NOT NULL,
                reactive_power_kvar REAL NOT NULL,
                apparent_power_kva REAL NOT NULL,
                power_factor_total REAL NOT NULL,
                energy_import_kwh REAL NOT NULL,
                alarm_status TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS alarm_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                name TEXT NOT NULL,
                severity TEXT NOT NULL,
                measurement TEXT NOT NULL,
                threshold REAL NOT NULL,
                current_value REAL NOT NULL,
                status TEXT NOT NULL,
                acknowledged INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS device_config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                device_name TEXT NOT NULL,
                host TEXT NOT NULL,
                port INTEGER NOT NULL,
                unit_id INTEGER NOT NULL,
                poll_interval REAL NOT NULL,
                timeout REAL NOT NULL,
                retries INTEGER NOT NULL,
                nominal_voltage REAL NOT NULL,
                ct_primary_rating INTEGER NOT NULL,
                ct_secondary_rating INTEGER NOT NULL,
                pt_ratio REAL NOT NULL
            );
            """
        )
        connection.commit()


def insert_reading(device: str, values: dict[str, float | int], alarm_status: str) -> None:
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO readings (
                timestamp, device, voltage_avg, current_avg, frequency, active_power_kw,
                reactive_power_kvar, apparent_power_kva, power_factor_total, energy_import_kwh, alarm_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
                device,
                values["voltage_avg"],
                values["current_avg"],
                values["frequency"],
                values["active_power_kw"],
                values["reactive_power_kvar"],
                values["apparent_power_kva"],
                values["power_factor_total"],
                values["energy_import_kwh"],
                alarm_status,
            ),
        )
        connection.commit()


def insert_alarms(alarms: list[dict]) -> None:
    if not alarms:
        return
    with connect() as connection:
        connection.executemany(
            """
            INSERT INTO alarm_history (
                timestamp, name, severity, measurement, threshold, current_value, status, acknowledged
            )
            VALUES (:timestamp, :name, :severity, :measurement, :threshold, :current_value, :status, :acknowledged)
            """,
            alarms,
        )
        connection.commit()


def recent_readings(limit: int = 120) -> list[dict]:
    with connect() as connection:
        rows = connection.execute("SELECT * FROM readings ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(row) for row in reversed(rows)]


def latest_reading() -> dict | None:
    with connect() as connection:
        row = connection.execute("SELECT * FROM readings ORDER BY id DESC LIMIT 1").fetchone()
    return dict(row) if row else None


def alarm_history(limit: int = 50) -> list[dict]:
    with connect() as connection:
        rows = connection.execute("SELECT * FROM alarm_history ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(row) for row in rows]


def acknowledge_alarm(alarm_id: int) -> None:
    with connect() as connection:
        connection.execute("UPDATE alarm_history SET acknowledged = 1, status = 'ACKNOWLEDGED' WHERE id = ?", (alarm_id,))
        connection.commit()


def save_device_config(config: dict[str, Any]) -> None:
    initialize_store()
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO device_config (
                id, device_name, host, port, unit_id, poll_interval, timeout, retries,
                nominal_voltage, ct_primary_rating, ct_secondary_rating, pt_ratio
            )
            VALUES (1, :device_name, :host, :port, :unit_id, :poll_interval, :timeout, :retries,
                :nominal_voltage, :ct_primary_rating, :ct_secondary_rating, :pt_ratio)
            ON CONFLICT(id) DO UPDATE SET
                device_name = excluded.device_name,
                host = excluded.host,
                port = excluded.port,
                unit_id = excluded.unit_id,
                poll_interval = excluded.poll_interval,
                timeout = excluded.timeout,
                retries = excluded.retries,
                nominal_voltage = excluded.nominal_voltage,
                ct_primary_rating = excluded.ct_primary_rating,
                ct_secondary_rating = excluded.ct_secondary_rating,
                pt_ratio = excluded.pt_ratio
            """,
            config,
        )
        connection.commit()


def export_readings_csv(start: str | None = None, end: str | None = None) -> str:
    conditions: list[str] = []
    params: list[str] = []
    if start:
        conditions.append("timestamp >= ?")
        params.append(start)
    if end:
        conditions.append("timestamp <= ?")
        params.append(end)
    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    with connect() as connection:
        frame = pd.read_sql_query(f"SELECT * FROM readings{where} ORDER BY timestamp", connection, params=params)
    return frame.to_csv(index=False)
