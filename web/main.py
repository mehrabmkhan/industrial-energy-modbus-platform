from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from meterlink.alarms import DEFAULT_RULES
from meterlink.config import load_device_config, validate_device_config
from meterlink.poller import PollingService
from meterlink.registers import load_register_map
from meterlink.simulator import run_server
from meterlink.store import acknowledge_alarm, alarm_history, export_readings_csv, latest_reading, recent_readings, save_device_config


BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
poller: PollingService | None = None
simulator_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global poller, simulator_task
    config = load_device_config()
    if os.getenv("METERLINK_START_SIMULATOR", "true").lower() == "true":
        simulator_task = asyncio.create_task(run_server("127.0.0.1", config.port, config.unit_id, config.nominal_voltage))
        await asyncio.sleep(0.4)
    poller = PollingService(config)
    await poller.start()
    yield
    await poller.stop()
    if simulator_task:
        simulator_task.cancel()


app = FastAPI(title="MeterLink Industrial", version="1.0.0", lifespan=lifespan)


def service() -> PollingService:
    assert poller is not None
    return poller


def dashboard_context(window: str = "5m") -> dict:
    register_map = load_register_map()
    limits = {"5m": 300, "30m": 1800, "1h": 3600}
    reading_limit = min(limits.get(window, 300), 7200)
    latest = service().latest_values or latest_reading() or {}
    return {
        "latest": latest,
        "status": service().status(),
        "readings": recent_readings(reading_limit),
        "window": window,
        "alarms": service().latest_alarms,
        "alarm_history": alarm_history(),
        "registers": register_map.registers,
        "rules": DEFAULT_RULES,
    }


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, window: str = Query("5m")) -> HTMLResponse:
    return templates.TemplateResponse(request, "dashboard.html", dashboard_context(window))


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_alias(request: Request, window: str = Query("5m")) -> HTMLResponse:
    return dashboard(request, window)


@app.get("/api/meters")
def api_meters() -> list[dict]:
    return [service().status()["device"]]


@app.get("/api/meters/{meter_id}/measurements")
def api_measurements(meter_id: int) -> dict:
    return {"meter_id": meter_id, "measurements": service().latest_values}


@app.get("/api/meters/{meter_id}/status")
def api_status(meter_id: int) -> dict:
    return {"meter_id": meter_id, **service().status()}


@app.get("/api/meters/{meter_id}/alarms")
def api_alarms(meter_id: int) -> dict:
    return {"meter_id": meter_id, "active": service().latest_alarms, "history": alarm_history()}


@app.get("/api/meters/{meter_id}/registers")
def api_registers(meter_id: int) -> list[dict]:
    return [definition.__dict__ for definition in load_register_map().registers]


@app.post("/api/meters/{meter_id}/test")
async def api_test_communication(meter_id: int) -> dict:
    values = await service().poll_once()
    return {"meter_id": meter_id, "status": "OK", "sample": values}


@app.post("/alarms/{alarm_id}/ack")
def ack_alarm(alarm_id: int) -> dict:
    acknowledge_alarm(alarm_id)
    return {"acknowledged": alarm_id}


@app.post("/configuration")
def save_configuration(
    device_name: str = Form(...),
    host: str = Form(...),
    port: int = Form(...),
    unit_id: int = Form(...),
    poll_interval: float = Form(...),
    timeout: float = Form(...),
    nominal_voltage: float = Form(...),
    ct_primary_rating: int = Form(...),
    ct_secondary_rating: int = Form(...),
    pt_ratio: float = Form(...),
) -> dict:
    from meterlink.client import DeviceConfig

    candidate = DeviceConfig(
        device_name=device_name,
        host=host,
        port=port,
        unit_id=unit_id,
        poll_interval=poll_interval,
        timeout=timeout,
        nominal_voltage=nominal_voltage,
        ct_primary_rating=ct_primary_rating,
        ct_secondary_rating=ct_secondary_rating,
        pt_ratio=pt_ratio,
    )
    errors = validate_device_config(candidate)
    if not errors:
        save_device_config(asdict(candidate))
        if poller:
            poller.config = candidate
    return {"saved": not errors, "errors": errors}


@app.get("/export/readings.csv")
def export_readings(start: str | None = None, end: str | None = None) -> Response:
    return Response(
        export_readings_csv(start=start, end=end),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=meterlink_readings.csv"},
    )
