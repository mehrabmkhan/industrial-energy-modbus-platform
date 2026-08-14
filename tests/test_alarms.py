from meterlink.alarms import AlarmRule, evaluate_alarms


def test_alarm_rule_trips_when_threshold_is_exceeded() -> None:
    alarms = evaluate_alarms(
        {"current_avg": 1001.0},
        [AlarmRule("High Current", "current_avg", ">", 950.0, "CRITICAL")],
    )

    assert alarms[0]["name"] == "High Current"
    assert alarms[0]["severity"] == "CRITICAL"
    assert alarms[0]["status"] == "ACTIVE"


def test_alarm_rule_stays_clear_when_value_is_normal() -> None:
    alarms = evaluate_alarms(
        {"power_factor_total": 0.96},
        [AlarmRule("Low Power Factor", "power_factor_total", "<", 0.90, "WARNING")],
    )

    assert alarms == []
