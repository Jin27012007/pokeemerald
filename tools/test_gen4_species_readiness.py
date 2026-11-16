#!/usr/bin/env python3
"""Regression tests for the Generation 4 pre-runtime readiness audit."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "audit_gen4_species_readiness", ROOT / "tools/audit_gen4_species_readiness.py"
)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


def test_generation_4_identity_and_source_coverage():
    report = module.audit(**module.load_inputs())
    assert report["scope"]["generation"] == 4
    assert report["scope"]["national_dex_range"] == [387, 493]
    assert report["counts"]["national_dex_species"] == 107
    assert report["counts"]["species_info_source_records"] == 107
    assert report["counts"]["level_up_learnset_records"] == 107
    assert report["counts"]["species_info_records_missing_required_fields"] == 0
    assert report["readiness"]["required_species_statistics_and_fields_complete"] is True


def test_generation_4_blockers_are_isolated_and_not_misreported_as_runtime_ready():
    report = module.audit(**module.load_inputs())
    counts = report["counts"]
    readiness = report["readiness"]
    assert counts["species_without_production_internal_id"] == 107
    assert counts["distinct_level_up_moves_missing_battle_records"] == 137
    assert counts["distinct_unmapped_held_items"] == 0
    assert counts["distinct_held_item_behaviors_pending_audit"] == 6
    assert counts["species_missing_target_graphics"] == 107
    assert counts["species_missing_target_cry_entries"] == 107
    assert readiness["production_species_ids_allocated"] is False
    assert readiness["all_level_up_moves_have_battle_records"] is False
    assert readiness["all_held_items_have_target_data"] is True
    assert readiness["all_held_item_behaviors_audited"] is False
    assert readiness["all_target_graphics_assets_present"] is False
    assert readiness["all_target_cry_entries_present"] is False
    assert readiness["runtime_activation_allowed"] is False


def test_species_ids_and_save_layout_are_not_mutated():
    report = module.audit(**module.load_inputs())
    assert len(report["species_without_production_internal_id"]) == 107
    assert any("NUM_SPECIES" in item for item in report["invariants"])
    assert any("save layout" in item for item in report["invariants"])


if __name__ == "__main__":
    test_generation_4_identity_and_source_coverage()
    test_generation_4_blockers_are_isolated_and_not_misreported_as_runtime_ready()
    test_species_ids_and_save_layout_are_not_mutated()
    print("PASS: Generation 4 source coverage, 107 species, blocker isolation and runtime safety gates.")
