#!/usr/bin/env python3
"""Validate canonical Gen 8 intake envelopes; deliberately independent of runtime IDs."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/gen8-conversion"
CANONICAL = REPORT / "species_info_by_national_dex.json"
MAPPING = REPORT / "conversion_report.json"
ALLOWED_PROVENANCE = {"existing_emerald_runtime_record", "expansion_source_initializer"}
REQUIRED_ENVELOPE = {
    "national_dex", "national_symbol", "source_record_symbol",
    "record_provenance", "source_generation", "source_fields_present",
    "source_missing_fields", "source_unresolved_fields",
    "source_fields_resolved", "target_mapping_compatible",
    "runtime_gaps", "unresolved_fields",
}

def fail(message: str) -> None:
    raise SystemExit("INTAKE VALIDATION FAILED: " + message)

def main() -> int:
    if not CANONICAL.is_file() or not MAPPING.is_file():
        fail("run tools/gen8_convert_emerald.py first; canonical staging reports are missing")
    rows = json.loads(CANONICAL.read_text(encoding="utf-8"))
    report = json.loads(MAPPING.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or len(rows) != 898:
        fail(f"expected 898 canonical rows, got {len(rows) if isinstance(rows, list) else type(rows).__name__}")
    seen = set()
    for row in rows:
        missing = REQUIRED_ENVELOPE - set(row)
        if missing:
            fail(f"Dex row missing envelope keys: {sorted(missing)}")
        dex = row["national_dex"]
        if not isinstance(dex, int) or not 1 <= dex <= 898:
            fail(f"invalid National Dex key: {dex!r}")
        if dex in seen:
            fail(f"duplicate National Dex key: {dex}")
        seen.add(dex)
        if row["record_provenance"] not in ALLOWED_PROVENANCE:
            fail(f"Dex {dex}: invalid provenance {row['record_provenance']!r}")
        if not row["national_symbol"] or not row["source_record_symbol"]:
            fail(f"Dex {dex}: empty identity symbol")
        if row["record_provenance"] == "expansion_source_initializer":
            if row.get("source_national_dex_symbol") != row["national_symbol"]:
                fail(
                    f"Dex {dex}: Expansion natDexNum mismatch "
                    f"({row.get('source_national_dex_symbol')!r} != {row['national_symbol']!r})"
                )
            if row.get("source_national_dex_matches_selected") is not True:
                fail(f"Dex {dex}: Expansion record lacks verified canonical Dex identity")
        elif row["record_provenance"] == "existing_emerald_runtime_record":
            if not row["source_record_symbol"].startswith("SPECIES_"):
                fail(f"Dex {dex}: native Emerald record has invalid source symbol")
        if not isinstance(row["source_fields_present"], list):
            fail(f"Dex {dex}: source_fields_present must be a list")
        if not isinstance(row["source_missing_fields"], list) or not isinstance(row["source_unresolved_fields"], list):
            fail(f"Dex {dex}: missing/unresolved fields must be explicit lists")
        if not isinstance(row["runtime_gaps"], list) or not isinstance(row["unresolved_fields"], list):
            fail(f"Dex {dex}: runtime gaps/unresolved fields must be explicit lists")
        if row["source_missing_fields"] or row["source_unresolved_fields"] or row["unresolved_fields"]:
            # Inventory is still valid; this row is not promotable.
            pass
        if row["target_mapping_compatible"] and row["runtime_gaps"]:
            fail(f"Dex {dex}: target marked compatible while runtime gaps exist")
    if seen != set(range(1, 899)):
        fail(f"canonical Dex key set incomplete: missing={sorted(set(range(1,899))-seen)[:20]}")
    provenance = {
        "existing_emerald_runtime_record": sum(1 for row in rows if row["record_provenance"] == "existing_emerald_runtime_record"),
        "expansion_source_initializer": sum(1 for row in rows if row["record_provenance"] == "expansion_source_initializer"),
    }
    if provenance != {"existing_emerald_runtime_record": 386, "expansion_source_initializer": 512}:
        fail(f"expected provenance split 386 native + 512 Expansion, got {provenance}")
    counts = report.get("counts", {})
    if counts.get("canonical_species_info_covered") != 898:
        fail("conversion report coverage count disagrees with canonical table")
    if counts.get("canonical_species_info_native_emerald_preserved_rows") != 386:
        fail("conversion report must contain exactly 386 preserved Emerald records")
    if counts.get("canonical_species_info_expansion_source_rows") != 512:
        fail("conversion report must contain exactly 512 selected Expansion records")
    if counts.get("canonical_species_info_source_dex_mismatches") != 0:
        fail("conversion report contains source National Dex identity mismatches")
    if counts.get("canonical_species_info_identity_conflicts") != 0:
        fail("conversion report contains unresolved canonical identity conflicts")
    if len(report.get("species_mapping", [])) != 898:
        fail("species ID mapping must contain 898 canonical rows")
    print("PASS: 898 canonical intake envelopes are structurally valid and uniquely keyed.")
    promotable = sum(
        1 for r in rows
        if r["source_fields_resolved"] and r["target_mapping_compatible"]
        and not r["source_missing_fields"] and not r["source_unresolved_fields"]
        and not r["runtime_gaps"] and not r["unresolved_fields"]
    )
    print(f"PROMOTABLE_FOR_RUNTIME={promotable}/898")
    if promotable != 898:
        print("BLOCKED: intake catalog is structurally valid, but not runtime promotable.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
