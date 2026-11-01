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
    # A caught bit without the matching seen bit/copies is cleared.
    model.set_caught(1)
    assert not model.get_caught(1)
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

if __name__ == "__main__":
    main()
