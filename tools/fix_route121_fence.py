#!/usr/bin/env python3
"""Correct the misplaced beige vertical fence metatiles in Route 121.

Route121 uses the Lilycove secondary tileset. The current layout uses
METATILE_SecretBase_Fence_Vertical (0x233) at the vertical fence runs,
which renders as a pale/beige fence. Replace those layout entries with
METATILE_Lilycove_Fence_Vertical_Blue (0x346), preserving all other
metatile flags and the rest of the map.
"""
from pathlib import Path
import struct

path = Path("data/layouts/Route121/map.bin")
data = bytearray(path.read_bytes())
if len(data) % 2:
    raise SystemExit(f"Unexpected odd map size: {len(data)} bytes")

values = list(struct.unpack("<" + "H" * (len(data) // 2), data))
old_id = 0x233
new_id = 0x346
changed = 0

for i, value in enumerate(values):
    metatile_id = value & 0x03FF
    if metatile_id == old_id:
        values[i] = (value & ~0x03FF) | new_id
        changed += 1

if changed != 23:
    raise SystemExit(
        f"Expected 23 misplaced vertical fence metatiles, found {changed}; "
        "refusing to modify an unexpected map version."
    )

path.write_bytes(struct.pack("<" + "H" * len(values), *values))
print(f"Route121: replaced {changed} beige vertical fence metatiles (0x233) with blue Lilycove fence (0x346).")
