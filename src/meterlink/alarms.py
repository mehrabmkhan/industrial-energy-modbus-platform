from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class AlarmRule:
    name: str
    measurement: str
    operator: str
    threshold: float
    severity: str


DEFAULT_RULES = [
    AlarmRule("High Voltage", "voltage_avg", ">", 635.0, "WARNING"),
    AlarmRule("Low Voltage", "voltage_avg", "<", 570.0, "WARNING"),
    AlarmRule("High Current", "current_avg", ">", 950.0, "CRITICAL"),
    AlarmRule("Low Power Factor", "power_factor_total", "<", 0.90, "WARNING"),
    AlarmRule("Frequency High", "frequency", ">", 60.3, "INFO"),
    AlarmRule("Frequency Low", "frequency", "<", 59.7, "INFO"),
    AlarmRule("High Active Power", "active_power_kw", ">", 850.0, "CRITICAL"),
]


def evaluate_alarms(values: dict[str, float | int], rules: list[AlarmRule] | None = None) -> list[dict]:
    active: list[dict] = []
    for rule in rules or DEFAULT_RULES:
        current = float(values.get(rule.measurement, 0))
        tripped = current > rule.threshold if rule.operator == ">" else current < rule.threshold
        if tripped:
            active.append(
                {
                    "timestamp": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
                    "name": rule.name,
                    "severity": rule.severity,
                    "measurement": rule.measurement,
                    "threshold": rule.threshold,
                    "current_value": round(current, 4),
                    "status": "ACTIVE",
                    "acknowledged": 0,
                }
            )
    return active
