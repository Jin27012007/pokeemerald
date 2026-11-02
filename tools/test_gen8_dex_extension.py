#!/usr/bin/env python3
"""Test the isolated Gen 8 National Dex extension envelope.

The C implementation is staging-only and is not connected to save IO.
"""
from __future__ import annotations

import struct
import unittest

MAGIC = 0x38445847
VERSION = 1
FLAG_BYTES = 61
COPY_COUNT = 4
HEADER_BYTES = 12
SIZE = HEADER_BYTES + FLAG_BYTES * COPY_COUNT
FIRST_EXTENDED_DEX = 413
LAST_DEX = 898


def checksum(blob: bytes) -> int:
    checksum_offset = 4
    h = 2166136261
    for index, value in enumerate(blob):
        if checksum_offset <= index < checksum_offset + 4:
            continue
        h ^= value
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def make_extension() -> bytearray:
    data = bytearray(SIZE)
    # Header: magic:u32, checksum:u32, version:u16, generation:u16.
    struct.pack_into("<IIHH", data, 0, MAGIC, 0, VERSION, 1)
    struct.pack_into("<I", data, 4, checksum(data))
    return data


def valid(data: bytes) -> bool:
    if len(data) != SIZE:
        return False
    magic, stored, version, generation = struct.unpack_from("<IIHH", data, 0)
    return (
        magic == MAGIC
        and version == VERSION
        and generation > 0
        and stored == checksum(data)
    )


def next_generation(data: bytearray) -> None:
    if not valid(data):
        raise ValueError("invalid extension")
    generation = struct.unpack_from("<H", data, 10)[0]
    if generation == 0xFFFF:
        raise OverflowError("generation exhausted")
    struct.pack_into("<H", data, 10, generation + 1)
    struct.pack_into("<I", data, 4, checksum(data))


def set_flag(data: bytearray, dex: int, owned: bool, value: bool) -> None:
    if not valid(data):
        raise ValueError("invalid extension")
    if not FIRST_EXTENDED_DEX <= dex <= LAST_DEX:
        raise ValueError("Dex outside extension domain")

    offset = HEADER_BYTES + (FLAG_BYTES if owned else 0)
    backup = offset + 2 * FLAG_BYTES
    index = dex - FIRST_EXTENDED_DEX
    mask = 1 << (index % 8)
    for start in (offset, backup):
        if value:
            data[start + index // 8] |= mask
        else:
            data[start + index // 8] &= ~mask

    generation = struct.unpack_from("<H", data, 10)[0]
    if generation == 0xFFFF:
        raise OverflowError("generation exhausted")
    struct.pack_into("<H", data, 10, generation + 1)
    struct.pack_into("<I", data, 4, checksum(data))


def get_flag(data: bytes, dex: int, owned: bool) -> bool:
    if not valid(data) or not FIRST_EXTENDED_DEX <= dex <= LAST_DEX:
        return False
    offset = HEADER_BYTES + (FLAG_BYTES if owned else 0)
    backup = offset + 2 * FLAG_BYTES
    index = dex - FIRST_EXTENDED_DEX
    mask = 1 << (index % 8)
    return bool(data[offset + index // 8] & mask) and bool(data[backup + index // 8] & mask)


class Gen8DexExtensionTests(unittest.TestCase):
    def test_layout_exactly_fills_reserved_window(self):
        self.assertEqual(HEADER_BYTES, 12)
        self.assertEqual(SIZE, 256)

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
        data[HEADER_BYTES + 2 * FLAG_BYTES] ^= 1
        struct.pack_into("<I", data, 4, checksum(data))
        self.assertFalse(get_flag(data, 500, False))

    def test_corruption_rejected(self):
        data = make_extension()
        data[HEADER_BYTES + 3] ^= 0x80
        self.assertFalse(valid(data))
        self.assertFalse(get_flag(data, 500, False))

    def test_generation_rollover_is_rejected(self):
        data = make_extension()
        struct.pack_into("<H", data, 10, 0xFFFF)
        struct.pack_into("<I", data, 4, checksum(data))
        self.assertTrue(valid(data))
        with self.assertRaises(OverflowError):
            next_generation(data)

    def test_wrong_version_and_header_rejected(self):
        data = make_extension()
        struct.pack_into("<H", data, 8, 99)
        struct.pack_into("<I", data, 4, checksum(data))
        self.assertFalse(valid(data))
        data = make_extension()
        struct.pack_into("<I", data, 0, 0)
        struct.pack_into("<I", data, 4, checksum(data))
        self.assertFalse(valid(data))


if __name__ == "__main__":
    unittest.main()
