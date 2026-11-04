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



# Runtime SaveBlock1 extension layout. It holds four raw 61-byte mirrors:
# three seen copies and one owned copy. There is no migration header.
LEGACY_DEX_COUNT = 412
LEGACY_FLAG_BYTES = (LEGACY_DEX_COUNT + 7) // 8
EXTENSION_DEX_COUNT = DEX_COUNT - LEGACY_DEX_COUNT
EXTENSION_FLAG_BYTES = (EXTENSION_DEX_COUNT + 7) // 8
EXTENSION_WINDOW_BYTES = 0x100
EXTENSION_HEADER_BYTES = 0
EXTENSION_COPY_COUNT = 4
EXTENSION_REQUIRED_BYTES = EXTENSION_COPY_COUNT * EXTENSION_FLAG_BYTES


def test_extension_layout_and_legacy_compatibility():
    assert LEGACY_FLAG_BYTES == 52
    assert EXTENSION_DEX_COUNT == 486
    assert EXTENSION_FLAG_BYTES == 61
    assert EXTENSION_COPY_COUNT == 4
    assert EXTENSION_REQUIRED_BYTES == 244
    assert EXTENSION_HEADER_BYTES == 0
    assert EXTENSION_REQUIRED_BYTES <= EXTENSION_WINDOW_BYTES
    assert EXTENSION_WINDOW_BYTES - EXTENSION_REQUIRED_BYTES == 12
    assert EXTENSION_WINDOW_BYTES == 256
    # Preserve the original 0x180-byte reserved range and Trainer Hill offset.
    assert 0x3598 + 0x180 == 0x3718
    assert EXTENSION_WINDOW_BYTES <= 0x180


def test_extension_read_write_mirrors_and_boundaries():
    class ExtensionModel:
        def __init__(self):
            self.raw = bytearray(EXTENSION_WINDOW_BYTES)

        @staticmethod
        def locate(dex):
            if not LEGACY_DEX_COUNT < dex <= DEX_COUNT:
                raise ValueError(dex)
            offset = dex - LEGACY_DEX_COUNT - 1
            return offset // 8, 1 << (offset % 8)

        def set_flag(self, mirror, dex):
            byte, mask = self.locate(dex)
            self.raw[mirror * EXTENSION_FLAG_BYTES + byte] |= mask

        def get_flag(self, mirror, dex):
            byte, mask = self.locate(dex)
            return bool(self.raw[mirror * EXTENSION_FLAG_BYTES + byte] & mask)

    ext = ExtensionModel()
    # Every Gen 8 entry is kept independently in all four redundant copies.
    for dex in range(413, 899):
        for mirror in range(EXTENSION_COPY_COUNT):
            ext.set_flag(mirror, dex)
    assert all(ext.get_flag(mirror, dex)
               for mirror in range(EXTENSION_COPY_COUNT)
               for dex in range(413, 899))
    assert ext.raw[0] & 0x01  # Dex 413, first bit.
    assert ext.raw[60] & 0x20  # Dex 898, final used bit.
    assert ext.raw[61] & 0x01  # Owned mirror begins at 3 * 61 bytes.
    assert ext.raw[3 * EXTENSION_FLAG_BYTES + 60] & 0x20
    assert len(ext.raw) == 256
    assert sum(1 for x in ext.raw[:EXTENSION_REQUIRED_BYTES] if x) > 0
    # Invalid National Dex values are rejected, not aliased into the buffer.
    for invalid in (0, 412, 899):
        try:
            ext.set_flag(0, invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid extension dex accepted: {invalid}")
    # The last 12 bytes are reserved and untouched by the four mirrors.
    assert ext.raw[EXTENSION_REQUIRED_BYTES:] == bytearray(12)


if __name__ == "__main__":
    main()
    test_extension_layout_and_legacy_compatibility()
    test_extension_read_write_mirrors_and_boundaries()
    print("PASS: staged SaveBlock1 extension layout, four mirror read/write boundaries.")
