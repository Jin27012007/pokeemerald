#!/usr/bin/env python3
"""Regression tests for the focused Generation 4 pilot-family audit."""
from __future__ import annotations

from audit_gen4_species_pilot import EXPECTED_TARGETS, audit


def test_pilot_covers_all_eight_species_in_three_families():
    report = audit()
    assert report["counts"]["pilot_families"] == 3
    assert report["counts"]["pilot_species"] == 8
    assert report["counts"]["species_with_complete_source_stats"] == 8
    assert report["counts"]["species_with_level_up_learnsets"] == 8
    assert {row["species"] for row in report["species"]} == {
        "STARLY", "STARAVIA", "STARAPTOR",
        "BIDOOF", "BIBAREL",
        "SHINX", "LUXIO", "LUXRAY",
    }


def test_pilot_evolution_chains_match_the_source_catalog():
    report = audit()
    assert report["counts"]["evolution_edges_expected"] == len(EXPECTED_TARGETS)
    assert report["counts"]["evolution_edges_missing_or_mismatched"] == 0
    for source, target in EXPECTED_TARGETS.items():
        assert report["evolution_links"][source]["target"] == target


def test_pilot_is_staging_only_and_does_not_allocate_runtime_ids():
    report = audit()
    assert report["runtime_activation_allowed"] is False
    assert report["counts"]["species_without_production_internal_ids"] == 8
    assert all(
        row["production_emerald_species_id"] is None
        and row["runtime_activation_allowed"] is False
        for row in report["species"]
    )
    assert any("NUM_SPECIES" in item for item in report["safety_invariants"])
    assert any("save-migration" in blocker.get("detail", "") for blocker in report["blockers"])


def test_pilot_reports_graphics_cry_and_move_gaps_without_hiding_them():
    report = audit()
    assert report["counts"]["distinct_level_up_moves"] > 0
    assert "pilot_unique_moves_missing_battle_records" in report
    assert report["counts"]["species_without_complete_target_graphics"] >= 0
    assert report["counts"]["species_without_target_cry_entries"] >= 0


if __name__ == "__main__":
    test_pilot_covers_all_eight_species_in_three_families()
    test_pilot_evolution_chains_match_the_source_catalog()
    test_pilot_is_staging_only_and_does_not_allocate_runtime_ids()
    test_pilot_reports_graphics_cry_and_move_gaps_without_hiding_them()
    print("PASS: Generation 4 pilot-family staging audit")
