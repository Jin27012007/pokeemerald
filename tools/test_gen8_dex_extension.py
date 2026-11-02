#!/usr/bin/env python3
"""Test the isolated Gen 8 National Dex extension envelope.

The C runtime implementation remains staging-only and is not connected to
SaveBlock1/SaveBlock2 or live Pokédex flags.
"""
from __future__ import annotations

import struct
import unittest

MAGIC = 0x38445847
VERSION = 1
FLAG_BYTES = 61
COPY_COUNT = 4
SIZE = 256
FIRST_EXTENDED_DEX = 413
LAST_DEX = 898


def checksum(blob: bytes) -> int:
    checksum_offset = 12
    h = 2166136261
    for index, value in enumerate(blob):
        if checksum_offset <= index < checksum_offset + 4:
            continue
        h ^= value
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def make_extension() -> bytearray:
    data = bytearray(SIZE)
    struct.pack_into("<IHHII", data, 0, MAGIC, VERSION, 244, 1, 0)
    struct.pack_into("<I", data, 12, checksum(data))
    return data


def valid(data: bytes) -> bool:
    if len(data) != SIZE:
        return False
    magic, version, payload, generation, stored = struct.unpack_from("<IHHII", data, 0)
    return (
        magic == MAGIC
        and version == VERSION
        and payload == FLAG_BYTES * COPY_COUNT
        and generation > 0
        and stored == checksum(data)
    )


def set_flag(data: bytearray, dex: int, owned: bool, value: bool) -> None:
    if not valid(data):
        raise ValueError("invalid extension")
    if not FIRST_EXTENDED_DEX <= dex <= LAST_DEX:
        raise ValueError("Dex outside extension domain")
    offset = 16 + (FLAG_BYTES if owned else 0)
    backup = offset + 2 * FLAG_BYTES
    index = dex - FIRST_EXTENDED_DEX
    mask = 1 << (index % 8)
    for start in (offset, backup):
        if value:
            data[start + index // 8] |= mask
        else:
            data[start + index // 8] &= ~mask
    generation = struct.unpack_from("<I", data, 8)[0] + 1
    struct.pack_into("<I", data, 8, generation)
    struct.pack_into("<I", data, 12, checksum(data))


def get_flag(data: bytes, dex: int, owned: bool) -> bool:
    if not valid(data) or not FIRST_EXTENDED_DEX <= dex <= LAST_DEX:
        return False
    offset = 16 + (FLAG_BYTES if owned else 0)
    backup = offset + 2 * FLAG_BYTES
    index = dex - FIRST_EXTENDED_DEX
    mask = 1 << (index % 8)
    return bool(data[offset + index // 8] & mask) and bool(data[backup + index // 8] & mask)


class Gen8DexExtensionTests(unittest.TestCase):
    def test_layout_exactly_fills_reserved_window(self):
        self.assertEqual(16 + FLAG_BYTES * COPY_COUNT, SIZE)

    def test_initialized_header_and_checksum(self):
        data = make_extension()
        self.assertEqual(len(data), SIZE)
        self.assertTrue(valid(data))

    def test_first_and_last_extended_dex_bits(self):
        data = make_extension()
        set_flag(data, 413, False, True)
        set_flag(data, 898, True, True)
        self.assertTrue(get_flag(data, 413, False))
        self.assertTrue(get_flag(data, 898, True))
        self.assertFalse(get_flag(data, 413, True))
        self.assertFalse(get_flag(data, 898, False))

    def test_rejects_legacy_dex_and_out_of_range_values(self):
        data = make_extension()
        with self.assertRaises(ValueError):
            set_flag(data, 412, False, True)
        with self.assertRaises(ValueError):
            set_flag(data, 899, False, True)

    def test_backup_disagreement_fails_closed(self):
        data = make_extension()
        set_flag(data, 500, False, True)
        data[16 + 2 * FLAG_BYTES] ^= 1
        struct.pack_into("<I", data, 12, checksum(data))
        self.assertFalse(get_flag(data, 500, False))

    def test_corruption_rejected(self):
        data = make_extension()
        data[32] ^= 0x80
        self.assertFalse(valid(data))
        self.assertFalse(get_flag(data, 500, False))

    def test_wrong_version_and_header_rejected(self):
        data = make_extension()
        struct.pack_into("<H", data, 4, 99)
        struct.pack_into("<I", data, 12, checksum(data))
        self.assertFalse(valid(data))
        data = make_extension()
        struct.pack_into("<I", data, 0, 0)
        struct.pack_into("<I", data, 12, checksum(data))
        self.assertFalse(valid(data))


if __name__ == "__main__":
    unittest.main()
