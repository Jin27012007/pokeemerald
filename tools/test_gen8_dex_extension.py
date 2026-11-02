#!/usr/bin/env python3
"""Test the Gen 8 Dex envelope C implementation and SaveBlock1 integration."""
from __future__ import annotations

import struct
import unittest
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]

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
        index = 500 - FIRST_EXTENDED_DEX
        data[HEADER_BYTES + 2 * FLAG_BYTES + index // 8] ^= 1 << (index % 8)
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



class RuntimeIntegrationTests(unittest.TestCase):
    def test_live_pokedex_routes_extended_flags_through_validated_envelope(self):
        source = (ROOT / "src/pokedex.c").read_text(encoding="utf-8")
        self.assertIn('#include "gen8_dex_extension.h"', source)
        self.assertIn("GetGen8DexExtension", source)
        self.assertIn("Gen8DexExtensionReadFlag(extension, nationalDexNo", source)
        self.assertIn("Gen8DexExtensionWriteFlag(extension, nationalDexNo", source)
        self.assertIn("Gen8DexExtensionInit(GetGen8DexExtension())", source)
        self.assertIn("nationalDexNo > GEN8_DEX_COUNT", source)
        self.assertIn("nationalDexNo > GEN8_DEX_LEGACY_COUNT", source)

        reset_start = source.index("void ResetPokedex(void)")
        reset_end = source.index("void ResetPokedexScrollPositions", reset_start)
        self.assertIn("Gen8DexExtensionInit(GetGen8DexExtension())", source[reset_start:reset_end])

    def test_saveblock_reserved_window_is_exact_and_fixed(self):
        source = (ROOT / "include/global.h").read_text(encoding="utf-8")
        self.assertIn("dexFlagExtension[0x100]", source)
        self.assertIn("sizeof(struct Gen8DexExtension)", source)
        self.assertIn("__builtin_offsetof(struct SaveBlock1, dexFlagExtension) == 0x3598", source)

    def test_compile_and_execute_real_c_extension(self):
        compiler = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
        self.assertIsNotNone(compiler, "A C compiler is required for the Gen 8 extension test")

        with tempfile.TemporaryDirectory(prefix="gen8-dex-c-test-") as directory:
            temp = Path(directory)
            (temp / "global.h").write_text(
                """#ifndef TEST_GLOBAL_H
#define TEST_GLOBAL_H
#include <stdint.h>
#include <stddef.h>
#include <string.h>
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int32_t bool32;
#define TRUE 1
#define FALSE 0
#define GEN8_SPECIES_DEX_LAST 898
#define GEN8_DEX_EXT_MAGIC_VALUE 0x38445847
#define GEN8_DEX_EXT_FORMAT_VERSION 1
#define GEN8_DEX_EXT_FLAG_BYTES 61
#define STATIC_ASSERT(expr, name) typedef char name[(expr) ? 1 : -1]
struct Gen8DexExtension
{
    u32 magic;
    u32 checksum;
    u16 version;
    u16 generation;
    u8 seen[GEN8_DEX_EXT_FLAG_BYTES];
    u8 owned[GEN8_DEX_EXT_FLAG_BYTES];
    u8 seenBackup[GEN8_DEX_EXT_FLAG_BYTES];
    u8 ownedBackup[GEN8_DEX_EXT_FLAG_BYTES];
};
static inline void CpuFill32(u32 value, void *destination, u32 size)
{
    memset(destination, (int)value, size);
}
#endif
""",
                encoding="utf-8",
            )
            header = (ROOT / "include/gen8_dex_extension.h").read_text(encoding="utf-8")
            (temp / "gen8_dex_extension.h").write_text(header, encoding="utf-8")
            (temp / "test.c").write_text(
                """#include "gen8_dex_extension.h"
int main(void)
{
    struct Gen8DexExtension extension;
    Gen8DexExtensionInit(&extension);
    if (!Gen8DexExtensionValidate(&extension)) return 1;
    if (Gen8DexExtensionWriteFlag(&extension, 413, FALSE, TRUE) != GEN8_DEX_EXTENSION_OK) return 2;
    if (!Gen8DexExtensionReadFlag(&extension, 413, FALSE)) return 3;
    if (Gen8DexExtensionWriteFlag(&extension, 898, TRUE, TRUE) != GEN8_DEX_EXTENSION_OK) return 4;
    if (!Gen8DexExtensionReadFlag(&extension, 898, TRUE)) return 5;
    if (Gen8DexExtensionReadFlag(&extension, 412, FALSE)) return 6;
    if (Gen8DexExtensionReadFlag(&extension, 899, FALSE)) return 7;
    extension.seenBackup[0] ^= 1;
    extension.checksum = Gen8DexExtensionChecksum(&extension);
    if (Gen8DexExtensionReadFlag(&extension, 413, FALSE)) return 8;
    extension.checksum ^= 1;
    if (Gen8DexExtensionValidate(&extension)) return 9;
    return 0;
}
""",
                encoding="utf-8",
            )
            executable = temp / "gen8-dex-test"
            subprocess.run(
                [
                    compiler, "-std=c11", "-Wall", "-Wextra", "-Werror",
                    "-I", str(temp), str(ROOT / "src/gen8_dex_extension.c"),
                    str(temp / "test.c"), "-o", str(executable),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run([str(executable)], check=True, capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
