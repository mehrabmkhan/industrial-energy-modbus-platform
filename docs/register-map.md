# Register Map

The demo meter exposes a zero-based holding-register block starting at address `0`. Most measurements are encoded as big-endian IEEE-754 `float32` values across two 16-bit Modbus registers. `status_word` is a single unsigned 16-bit bitfield.

| Address | Name | Type | Unit | Description |
|---:|---|---|---|---|
| 0 | voltage_l1n | float32 | V | Phase L1 to neutral voltage |
| 2 | voltage_l2n | float32 | V | Phase L2 to neutral voltage |
| 4 | voltage_l3n | float32 | V | Phase L3 to neutral voltage |
| 6 | voltage_l1l2 | float32 | V | Line L1 to L2 voltage |
| 8 | voltage_l2l3 | float32 | V | Line L2 to L3 voltage |
| 10 | voltage_l3l1 | float32 | V | Line L3 to L1 voltage |
| 12 | voltage_avg | float32 | V | Average line-to-line voltage |
| 14 | current_a | float32 | A | Phase A current |
| 16 | current_b | float32 | A | Phase B current |
| 18 | current_c | float32 | A | Phase C current |
| 20 | neutral_current | float32 | A | Calculated neutral imbalance current |
| 22 | current_avg | float32 | A | Average phase current |
| 24 | frequency | float32 | Hz | System frequency |
| 26 | active_power_kw | float32 | kW | Total active power |
| 28 | reactive_power_kvar | float32 | kvar | Total reactive power |
| 30 | apparent_power_kva | float32 | kVA | Total apparent power |
| 32 | power_factor_total | float32 | pf | Total power factor |
| 34 | energy_import_kwh | float32 | kWh | Imported active energy counter |
| 36 | energy_reactive_kvarh | float32 | kvarh | Reactive energy counter |
| 38 | status_word | uint16 | bitfield | Bit 0 online, bit 1 active alarm |

The source of truth is `config/register_map.yaml`. The Python encoder and decoder use that file at runtime so documentation and behavior stay aligned.
