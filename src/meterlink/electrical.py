from __future__ import annotations

import math
import time
from dataclasses import dataclass


@dataclass
class MeterSettings:
    nominal_voltage: float = 600.0
    base_current: float = 420.0
    frequency: float = 60.0
    power_factor: float = 0.94


class EnergyModel:
    def __init__(self, settings: MeterSettings | None = None) -> None:
        self.settings = settings or MeterSettings()
        self.started = time.monotonic()
        self.last_update = self.started
        self.energy_kwh = 12080.0
        self.reactive_kvarh = 3180.0

    def snapshot(self) -> dict[str, float | int]:
        now = time.monotonic()
        elapsed_hours = max(now - self.last_update, 0.0) / 3600
        runtime = now - self.started
        load_factor = 0.72 + 0.18 * math.sin(runtime / 18.0) + 0.06 * math.sin(runtime / 5.0)
        imbalance = 1.0 + 0.015 * math.sin(runtime / 7.0)
        voltage_ln = self.settings.nominal_voltage / math.sqrt(3)
        voltage_variation = 1.0 + 0.006 * math.sin(runtime / 11.0)
        pf = max(0.82, min(0.99, self.settings.power_factor + 0.025 * math.sin(runtime / 23.0)))
        frequency = self.settings.frequency + 0.025 * math.sin(runtime / 17.0)

        current_a = self.settings.base_current * load_factor
        current_b = current_a * imbalance
        current_c = current_a * (2.0 - imbalance)
        current_avg = (current_a + current_b + current_c) / 3
        neutral_current = abs(current_b - current_c) * 0.18
        voltage_l1n = voltage_ln * voltage_variation
        voltage_l2n = voltage_ln * (1.0 - 0.003 * math.sin(runtime / 13.0))
        voltage_l3n = voltage_ln * (1.0 + 0.004 * math.sin(runtime / 9.0))
        voltage_l1l2 = voltage_l1n * math.sqrt(3)
        voltage_l2l3 = voltage_l2n * math.sqrt(3)
        voltage_l3l1 = voltage_l3n * math.sqrt(3)
        voltage_avg = (voltage_l1l2 + voltage_l2l3 + voltage_l3l1) / 3

        apparent_kva = math.sqrt(3) * voltage_avg * current_avg / 1000
        active_kw = apparent_kva * pf
        reactive_kvar = math.sqrt(max(apparent_kva**2 - active_kw**2, 0))
        self.energy_kwh += active_kw * elapsed_hours
        self.reactive_kvarh += reactive_kvar * elapsed_hours
        self.last_update = now

        alarm_bit = 1 if pf < 0.9 or voltage_avg > self.settings.nominal_voltage * 1.06 else 0
        return {
            "voltage_l1n": round(voltage_l1n, 2),
            "voltage_l2n": round(voltage_l2n, 2),
            "voltage_l3n": round(voltage_l3n, 2),
            "voltage_l1l2": round(voltage_l1l2, 2),
            "voltage_l2l3": round(voltage_l2l3, 2),
            "voltage_l3l1": round(voltage_l3l1, 2),
            "voltage_avg": round(voltage_avg, 2),
            "current_a": round(current_a, 2),
            "current_b": round(current_b, 2),
            "current_c": round(current_c, 2),
            "neutral_current": round(neutral_current, 2),
            "current_avg": round(current_avg, 2),
            "frequency": round(frequency, 3),
            "active_power_kw": round(active_kw, 3),
            "reactive_power_kvar": round(reactive_kvar, 3),
            "apparent_power_kva": round(apparent_kva, 3),
            "power_factor_total": round(pf, 4),
            "energy_import_kwh": round(self.energy_kwh, 4),
            "energy_reactive_kvarh": round(self.reactive_kvarh, 4),
            "status_word": 1 | (alarm_bit << 1),
        }
