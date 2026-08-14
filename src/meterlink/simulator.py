from __future__ import annotations

import argparse
import asyncio

from pymodbus.constants import ExcCodes
from pymodbus.server import StartAsyncTcpServer
from pymodbus.simulator.simdata import DataType, SimData
from pymodbus.simulator.simdevice import SimDevice

from .electrical import EnergyModel, MeterSettings
from .registers import encode_measurements, load_register_map


class MeterSimulator:
    def __init__(self, unit_id: int = 1, nominal_voltage: float = 600.0, base_current: float = 420.0) -> None:
        self.unit_id = unit_id
        self.register_map = load_register_map()
        self.model = EnergyModel(MeterSettings(nominal_voltage=nominal_voltage, base_current=base_current))

    async def action(
        self,
        function_code: int,
        start_address: int,
        address: int,
        count: int,
        current_registers: list[int],
        set_values: list[int] | list[bool] | None,
    ) -> ExcCodes | None:
        if function_code != 3:
            return None
        encoded = encode_measurements(self.model.snapshot(), self.register_map)
        offset = self.register_map.block_start - start_address
        for index, value in enumerate(encoded):
            target = offset + index
            if 0 <= target < len(current_registers):
                current_registers[target] = value
        return None

    def device(self) -> SimDevice:
        initial = encode_measurements(self.model.snapshot(), self.register_map)
        coils = [SimData(0, values=[False], datatype=DataType.BITS, readonly=False)]
        discrete_inputs = [SimData(0, values=[False], datatype=DataType.BITS, readonly=True)]
        holding = [SimData(self.register_map.block_start, values=initial, datatype=DataType.REGISTERS, readonly=True)]
        input_registers = [SimData(0, values=[0], datatype=DataType.REGISTERS, readonly=True)]
        return SimDevice(
            id=self.unit_id,
            simdata=(coils, discrete_inputs, holding, input_registers),
            action=self.action,
        )


async def run_server(host: str = "127.0.0.1", port: int = 15020, unit_id: int = 1, nominal_voltage: float = 600.0) -> None:
    simulator = MeterSimulator(unit_id=unit_id, nominal_voltage=nominal_voltage)
    await StartAsyncTcpServer(simulator.device(), address=(host, port))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the MeterLink software Modbus TCP meter")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=15020)
    parser.add_argument("--unit-id", type=int, default=1)
    parser.add_argument("--nominal-voltage", type=float, default=600.0)
    args = parser.parse_args()
    asyncio.run(run_server(args.host, args.port, args.unit_id, args.nominal_voltage))


if __name__ == "__main__":
    main()
