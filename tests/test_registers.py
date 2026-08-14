from meterlink.electrical import EnergyModel
import pytest

from meterlink.registers import RegisterDefinition, decode_block, decode_value, encode_measurements, encode_value, load_register_map


def test_float_register_round_trip() -> None:
    register_map = load_register_map()
    definition = register_map.by_name("voltage_avg")
    padding_before = [0] * (definition.address - register_map.block_start)
    padding_after = [0] * (register_map.block_count - len(padding_before) - definition.words)
    registers = padding_before + encode_value(600.25, "float32") + padding_after

    assert decode_block(registers, register_map)["voltage_avg"] == 600.25


def test_complete_measurement_block_matches_register_count() -> None:
    register_map = load_register_map()
    values = EnergyModel().snapshot()
    encoded = encode_measurements(values, register_map)
    decoded = decode_block(encoded, register_map)

    assert len(encoded) == register_map.block_count
    assert decoded["status_word"] & 1 == 1
    assert 590 <= decoded["voltage_avg"] <= 610
    assert 0.82 <= decoded["power_factor_total"] <= 0.99


def test_little_word_order_round_trip() -> None:
    definition = RegisterDefinition(0, "test_value", "float32", "ro", 1, "V", "test")
    encoded = encode_value(123.5, "float32", word_order="little")

    assert decode_value(encoded, definition, word_order="little") == 123.5


def test_malformed_register_block_is_rejected() -> None:
    with pytest.raises(ValueError, match="Expected"):
        decode_block([1, 2, 3], load_register_map())
