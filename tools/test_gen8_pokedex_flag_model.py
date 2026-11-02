#!/usr/bin/env python3
"""Model the current duplicated National Dex flag semantics for 898 entries.

This is a pure host-side model; it does not write flash or modify save structs.
It proves the required behavior for seen (3 copies) and caught (2 copies).
"""
from __future__ import annotations

DEX_COUNT = 898
FLAG_BYTES = (DEX_COUNT + 7) // 8

class DexFlagModel:
    def __init__(self):
        self.sb2_seen = bytearray(FLAG_BYTES)
        self.sb1_seen_a = bytearray(FLAG_BYTES)
        self.sb1_seen_b = bytearray(FLAG_BYTES)
        self.sb2_owned = bytearray(FLAG_BYTES)

    @staticmethod
    def _loc(dex):
        if not 1 <= dex <= DEX_COUNT:
            raise ValueError(f"National Dex must be 1..{DEX_COUNT}: {dex}")
        index = (dex - 1) // 8
        mask = 1 << ((dex - 1) % 8)
        return index, mask

    @staticmethod
    def _set(buf, i, mask):
        buf[i] |= mask

    @staticmethod
    def _clear(buf, i, mask):
        buf[i] &= ~mask & 0xFF

    @staticmethod
    def _get(buf, i, mask):
        return bool(buf[i] & mask)

    def set_seen(self, dex):
        i, m = self._loc(dex)
        self._set(self.sb2_seen, i, m)
        self._set(self.sb1_seen_a, i, m)
        self._set(self.sb1_seen_b, i, m)

    def set_caught(self, dex):
        i, m = self._loc(dex)
        self._set(self.sb2_owned, i, m)

    def get_seen(self, dex):
        i, m = self._loc(dex)
        a, b, c = (self._get(x, i, m) for x in
                   (self.sb2_seen, self.sb1_seen_a, self.sb1_seen_b))
        if a and a == b == c:
            return True
        if a or b or c:
            self._clear(self.sb2_seen, i, m)
            self._clear(self.sb1_seen_a, i, m)
            self._clear(self.sb1_seen_b, i, m)
        return False

    def get_caught(self, dex):
        i, m = self._loc(dex)
        a, b = self._get(self.sb2_owned, i, m), self._get(self.sb2_seen, i, m)
        c, d = self._get(self.sb1_seen_a, i, m), self._get(self.sb1_seen_b, i, m)
        if a and a == b == c == d:
            return True
        if a or b or c or d:
            self._clear(self.sb2_owned, i, m)
            self._clear(self.sb2_seen, i, m)
            self._clear(self.sb1_seen_a, i, m)
            self._clear(self.sb1_seen_b, i, m)
        return False

    def flip_copy_for_test(self, copy_name, dex):
        i, m = self._loc(dex)
        buf = getattr(self, copy_name)
        if self._get(buf, i, m):
            self._clear(buf, i, m)
        else:
            self._set(buf, i, m)

def main():
    model = DexFlagModel()
    assert FLAG_BYTES == 113
    assert 4 * FLAG_BYTES == 452
    # Every national index can be seen and caught, including final dex 898.
    for dex in range(1, DEX_COUNT + 1):
        model.set_seen(dex)
        model.set_caught(dex)
    assert all(model.get_seen(dex) for dex in range(1, DEX_COUNT + 1))
    assert all(model.get_caught(dex) for dex in range(1, DEX_COUNT + 1))
    # A divergent mirror copy causes the current Emerald corruption policy:
    # invalidate the flag in all redundant copies.
    model.flip_copy_for_test("sb1_seen_b", 898)
    assert not model.get_seen(898)
    # GET_SEEN repairs only the three seen copies; owned remains set, so the
    # next GET_CAUGHT detects the seen/owned mismatch and clears all four.
    assert not model.get_caught(898)
    assert model.get_seen(897)
    assert model.get_caught(897)
    # A caught bit without any matching seen copies is cleared on a fresh save.
    caught_only = DexFlagModel()
    caught_only.set_caught(1)
    assert not caught_only.get_caught(1)
    # Independent mirror divergence for a different National Dex entry.
    model.set_seen(500)
    model.set_caught(500)
    model.flip_copy_for_test("sb1_seen_a", 500)
    assert not model.get_caught(500)
    assert not model.get_seen(500)
    # Bound checks: national 0 and 899 must not be silently accepted.
    for invalid in (0, 899):
        try:
            model.set_seen(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted invalid National Dex index {invalid}")
    print("PASS: 898 National Dex flags, seen/owned redundancy and recovery model.")
    print(f"PASS: {FLAG_BYTES} bytes per flag array; four copies total {4*FLAG_BYTES} bytes.")



# Staged SaveBlock1 extension layout. The existing 412-entry arrays remain
# byte-for-byte compatible; extra entries use a dedicated 244-byte extension
# area in the 0x180-byte reserved window. The runtime migration is not enabled
# until all direct consumers are routed through accessors.
LEGACY_DEX_COUNT = 412
LEGACY_FLAG_BYTES = (LEGACY_DEX_COUNT + 7) // 8
EXTENSION_DEX_COUNT = DEX_COUNT - LEGACY_DEX_COUNT
EXTENSION_FLAG_BYTES = (EXTENSION_DEX_COUNT + 7) // 8
EXTENSION_WINDOW_BYTES = 0x180
EXTENSION_HEADER_BYTES = 16
EXTENSION_PAYLOAD_BYTES = EXTENSION_WINDOW_BYTES - EXTENSION_HEADER_BYTES
EXTENSION_COPY_COUNT = 4
EXTENSION_REQUIRED_BYTES = EXTENSION_COPY_COUNT * EXTENSION_FLAG_BYTES
EXTENSION_MAGIC = b"DEX8"
EXTENSION_VERSION = 1


def test_extension_layout_and_legacy_compatibility():
    assert LEGACY_FLAG_BYTES == 52
    assert EXTENSION_DEX_COUNT == 486
    assert EXTENSION_FLAG_BYTES == 61
    assert EXTENSION_COPY_COUNT == 4
    assert EXTENSION_REQUIRED_BYTES == 244
    assert EXTENSION_REQUIRED_BYTES <= EXTENSION_PAYLOAD_BYTES
    assert EXTENSION_PAYLOAD_BYTES - EXTENSION_REQUIRED_BYTES == 124
    assert EXTENSION_WINDOW_BYTES == 384
    # Original Trainer Hill fields remain after the entire reserved window.
    assert 0x3598 + EXTENSION_WINDOW_BYTES == 0x3718


def test_extension_migration_is_idempotent_and_preserves_legacy():
    class Extension:
        def __init__(self, raw=None):
            self.raw = bytearray(raw if raw is not None else EXTENSION_WINDOW_BYTES)

        def migrate(self, legacy_seen, legacy_owned):
            if self.raw[:4] == EXTENSION_MAGIC and self.raw[4] == EXTENSION_VERSION:
                return False
            # Do not overwrite nonzero, unrecognized bytes. This protects
            # unknown historical data until a version-specific migration exists.
            if any(self.raw):
                raise ValueError("unrecognized non-empty dex extension")
            if len(legacy_seen) != LEGACY_FLAG_BYTES or len(legacy_owned) != LEGACY_FLAG_BYTES:
                raise ValueError("legacy arrays must retain their 52-byte layout")
            self.raw[:4] = EXTENSION_MAGIC
            self.raw[4] = EXTENSION_VERSION
            self.raw[5] = 0  # reserved flags
            self.raw[6:8] = (EXTENSION_DEX_COUNT).to_bytes(2, "little")
            # 8..15 reserved for future checksums / migration markers.
            return True

    legacy_seen = bytearray([0xA5] * LEGACY_FLAG_BYTES)
    legacy_owned = bytearray([0x5A] * LEGACY_FLAG_BYTES)
    ext = Extension()
    assert ext.migrate(legacy_seen, legacy_owned) is True
    snapshot = bytes(ext.raw)
    assert ext.migrate(legacy_seen, legacy_owned) is False
    assert bytes(ext.raw) == snapshot
    assert legacy_seen == bytearray([0xA5] * LEGACY_FLAG_BYTES)
    assert legacy_owned == bytearray([0x5A] * LEGACY_FLAG_BYTES)

    # Unknown non-empty extension data is not silently erased.
    unknown = Extension(bytes([0x7F]) + bytes(EXTENSION_WINDOW_BYTES - 1))
    try:
        unknown.migrate(legacy_seen, legacy_owned)
    except ValueError:
        pass
    else:
        raise AssertionError("unknown non-empty extension must not be overwritten")


def test_extension_bit_index_boundaries():
    def locate(dex):
        if not LEGACY_DEX_COUNT < dex <= DEX_COUNT:
            raise ValueError(dex)
        offset = dex - LEGACY_DEX_COUNT - 1
        return offset // 8, 1 << (offset % 8)

    assert locate(413) == (0, 1)
    assert locate(420) == (0, 128)
    assert locate(421) == (1, 1)
    assert locate(898) == (60, 32)
    for invalid in (0, 412, 899):
        try:
            locate(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid extension dex accepted: {invalid}")


if __name__ == "__main__":
    main()
    test_extension_layout_and_legacy_compatibility()
    test_extension_migration_is_idempotent_and_preserves_legacy()
    test_extension_bit_index_boundaries()
    print("PASS: staged SaveBlock1 extension layout, migration guard and boundary tests.")
