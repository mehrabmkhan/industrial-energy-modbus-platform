# Hardware Roadmap

MeterLink Industrial is built around synthetic meter data, but the design leaves a clear path to real hardware.

## Next Integration Steps

1. Confirm the target meter's Modbus TCP address, unit ID, register map, data types, scaling, and byte order.
2. Create a vendor-specific register map file under `config/`.
3. Validate reads in a lab network before connecting to production equipment.
4. Add device-specific alarm thresholds and operational ranges.
5. Store readings in a durable database if retention matters.
6. Add authentication and network allowlisting before internet exposure.

## Safety Notes

The demo client performs read-only holding-register reads. Any future write capability should be isolated behind explicit access controls, audit logs, dry-run mode, and a formal change-management process.
