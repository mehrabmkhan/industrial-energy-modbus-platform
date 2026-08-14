# Modbus Client Notes

The client uses `AsyncModbusTcpClient` from PyModbus and polls a single contiguous holding-register block. The read operation is intentionally simple because many industrial meters publish telemetry in dense read-only blocks.

## Error Handling

The client records:

- successful and failed poll counts
- last successful communication timestamp
- last exception text
- most recent latency
- rolling average latency
- connection status

If a connection fails before any successful poll, the status is `OFFLINE`. If failures occur after prior successful communication, status becomes `DEGRADED`.

## Field Adaptation

For real hardware, update:

- `config/default_device.yaml` for the target IP, unit ID, timeout, and polling interval
- `config/register_map.yaml` for the vendor register map
- alarm thresholds in `src/meterlink/alarms.py`

This demo does not write Modbus registers. It is read-only by design.
