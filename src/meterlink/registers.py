from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class RegisterDefinition:
    address: int
    name: str
    type: str
    access: str
    scale: float
    unit: str
    description: str

    @property
    def words(self) -> int:
        return 2 if self.type in {"float32", "uint32", "int32"} else 1


@dataclass(frozen=True)
class RegisterMap:
    byte_order: str
    word_order: str
    registers: list[RegisterDefinition]

    @property
    def block_start(self) -> int:
        return min(item.address for item in self.registers)

    @property
    def block_count(self) -> int:
        last = max(item.address + item.words for item in self.registers)
        return last - self.block_start

    def by_name(self, name: str) -> RegisterDefinition:
        for item in self.registers:
            if item.name == name:
                return item
        raise KeyError(name)


def load_register_map(path: str | Path = "config/register_map.yaml") -> RegisterMap:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return RegisterMap(
        byte_order=raw["byte_order"],
        word_order=raw["word_order"],
        registers=[RegisterDefinition(**item) for item in raw["registers"]],
    )


def _apply_word_order(words: list[int], word_order: str) -> list[int]:
    return list(reversed(words)) if word_order == "little" and len(words) > 1 else words


def encode_value(value: float | int, register_type: str, scale: float = 1.0, word_order: str = "big") -> list[int]:
    scaled = value / scale
    if register_type == "float32":
        raw = struct.pack(">f", float(scaled))
        words = [int.from_bytes(raw[0:2], "big"), int.from_bytes(raw[2:4], "big")]
        return _apply_word_order(words, word_order)
    if register_type == "uint32":
        integer = int(scaled) & 0xFFFFFFFF
        words = [(integer >> 16) & 0xFFFF, integer & 0xFFFF]
        return _apply_word_order(words, word_order)
    if register_type == "int32":
        integer = int(scaled)
        if integer < 0:
            integer = (1 << 32) + integer
        words = [(integer >> 16) & 0xFFFF, integer & 0xFFFF]
        return _apply_word_order(words, word_order)
    if register_type == "int16":
        integer = int(scaled)
        return [integer & 0xFFFF]
    return [int(scaled) & 0xFFFF]


def decode_value(registers: list[int], definition: RegisterDefinition, word_order: str = "big") -> float | int:
    words = _apply_word_order(list(registers[: definition.words]), word_order)
    if definition.type == "float32":
        raw = words[0].to_bytes(2, "big") + words[1].to_bytes(2, "big")
        return round(struct.unpack(">f", raw)[0] * definition.scale, 4)
    if definition.type == "uint32":
        return int(((words[0] << 16) | words[1]) * definition.scale)
    if definition.type == "int32":
        value = (words[0] << 16) | words[1]
        if value & (1 << 31):
            value -= 1 << 32
        return int(value * definition.scale)
    if definition.type == "int16":
        value = words[0] if words[0] < 32768 else words[0] - 65536
        return int(value * definition.scale)
    return int(words[0] * definition.scale)


def encode_measurements(values: dict[str, Any], register_map: RegisterMap) -> list[int]:
    block = [0] * register_map.block_count
    for definition in register_map.registers:
        encoded = encode_value(values[definition.name], definition.type, definition.scale, register_map.word_order)
        offset = definition.address - register_map.block_start
        block[offset : offset + definition.words] = encoded
    return block


def decode_block(registers: list[int], register_map: RegisterMap) -> dict[str, float | int]:
    if len(registers) < register_map.block_count:
        raise ValueError(f"Expected {register_map.block_count} registers, received {len(registers)}")
    decoded: dict[str, float | int] = {}
    for definition in register_map.registers:
        offset = definition.address - register_map.block_start
        decoded[definition.name] = decode_value(registers[offset : offset + definition.words], definition, register_map.word_order)
    return decoded
