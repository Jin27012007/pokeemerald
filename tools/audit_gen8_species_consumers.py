#!/usr/bin/env python3
"""Inventory species-ID consumers and audit sentinel/form index safety.

This is a static source audit. It reports evidence and conservative warnings;
it does not claim to prove C runtime safety or allocate species IDs.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "reports/gen8-conversion/species_id_consumers"


SOURCE_SUFFIXES = {".c", ".h", ".inc"}
EXCLUDED_PARTS = {
    ".git", "build", "tools/vendor", "reports", "data", "graphics",
    "sound", "ASSETS", "tests",
}
SPECIAL_PATTERNS = {
    "none": re.compile(r"\bSPECIES_NONE\b"),
    "egg": re.compile(r"\bSPECIES_EGG\b"),
    "unown": re.compile(r"\bSPECIES_UNOWN_[A-Z0-9_]+\b|\bSPECIES_UNOWN\b"),
    "num_species": re.compile(r"\bNUM_SPECIES\b"),
}
TABLE_PATTERNS = {
    "species_info": re.compile(r"\bgSpeciesInfo\s*\[\s*([^\]]+)\s*\]"),
    "evolution": re.compile(r"\bgEvolutionTable\s*\[\s*([^\]]+)\s*\]"),
    "learnset": re.compile(r"\bg(?:LevelUpLearnsets?|TMHMLearnsets?)\s*\[\s*([^\]]+)\s*\]"),
    "front_pic": re.compile(r"\bgMonFrontPicTable\s*\[\s*([^\]]+)\s*\]"),
    "back_pic": re.compile(r"\bgMonBackPicTable\s*\[\s*([^\]]+)\s*\]"),
    "palette": re.compile(r"\bgMon(?:Shiny)?PaletteTable\s*\[\s*([^\]]+)\s*\]"),
    "icon": re.compile(r"\bgMonIcon(?:Table|PaletteIndices|PaletteTable)\s*\[\s*([^\]]+)\s*\]"),
    "footprint": re.compile(r"\bgMonFootprintTable\s*\[\s*([^\]]+)\s*\]"),
    "animation": re.compile(r"\bsSpeciesTo[A-Za-z0-9_]*(?:Anim|Animation)[A-Za-z0-9_]*\s*\[\s*([^\]]+)\s*\]"),
}
INDEX_PATTERNS = [
    re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\[\s*([^\]]+)\s*\]"),
]
FORM_PATTERNS = {
    "form_species_table": re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*FormSpeciesIdTable\b"),
    "form_change_table": re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*FormChangeTable\b"),
    "form_species_end": re.compile(r"\bFORM_SPECIES_END\b"),
    "form_change_end": re.compile(r"\bFORM_CHANGE_END\b"),
    "personality_form": re.compile(r"\bGet(?:Icon)?Species(?:NoPersonality)?\b|\bGetSpeciesForm\b|\bGetMonData\([^\n]*PERSONALITY"),
}
FUNCTION_HINTS = (
    ("persistence", ("BoxMon", "Pokemon", "MON_DATA_SPECIES", "Save", "Trade", "Link")),
    ("battle", ("Battle", "Battler", "Transform", "Evolution", "Evo")),
    ("dex", ("Pokedex", "PokedexNum", "National", "Hoenn", "Dex")),
    ("visual_audio", ("Pic", "Sprite", "Palette", "Icon", "Cry", "Anim", "Footprint")),
    ("form", ("Form", "Unown", "Castform", "Deoxys")),
)


def included(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    if any(part in rel for part in EXCLUDED_PARTS):
        return False
    return path.suffix.lower() in SOURCE_SUFFIXES


def classify(path: str, line: str, expression: str | None) -> str:
    text = f"{path} {line}"
    if any(token in text for token in ("MON_DATA_SPECIES", "BoxMon", "Pokemon", "Save", "Trade")):
        return "persistence"
    if expression and re.search(r"\b(?:species|targetSpecies|preEvoSpecies|postEvoSpecies)\b", expression, re.I):
        if any(t in text.lower() for t in ("battle", "battler", "evolution", "evo")):
            return "battle/evolution"
        if any(t in text.lower() for t in ("pic", "sprite", "palette", "icon")):
            return "visual/audio"
        return "species-index"
    for category, hints in FUNCTION_HINTS:
        if any(h in text for h in hints):
            return category
    return "other/unclassified"


def risk_for(line: str, expression: str | None, table: str | None, specials: set[str]) -> tuple[str, list[str]]:
    risks = []
    if table:
        risks.append("direct_table_index")
    if specials & {"egg", "none", "unown"} and table:
        risks.append("sentinel_token_near_table_index")
    if expression and re.search(r"\b(?:species|targetSpecies|preEvoSpecies|postEvoSpecies)\b", expression, re.I):
        risks.append("species_derived_index")
    lower = line.lower()
    if "num_species" in lower or "species_egg" in lower or "species_unown" in lower:
        risks.append("sentinel_or_bound_logic")
    if re.search(r"\b(?:species|targetSpecies)\s*(?:>=|>|==|!=|<=|<)", line):
        risks.append("species_range_or_sentinel_comparison")
    if re.search(r"\b(?:species|targetSpecies)\s*=", line):
        risks.append("species_value_assignment")
    level = "high" if "sentinel_token_near_table_index" in risks or (
        "species_derived_index" in risks and table in {"species_info", "evolution", "learnset", "front_pic", "back_pic", "palette"}
    ) else ("medium" if risks else "low")
    return level, risks


def scan_source() -> tuple[list[dict], dict]:
    findings = []
    files = sorted(p for p in ROOT.rglob("*") if p.is_file() and included(p))
    for path in files:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(ROOT).as_posix()
        for line_no, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("//") or stripped.startswith("*"):
                continue
            special = {name for name, pattern in SPECIAL_PATTERNS.items() if pattern.search(line)}
            table_matches = []
            for table, pattern in TABLE_PATTERNS.items():
                for match in pattern.finditer(line):
                    table_matches.append((table, match.group(1).strip()))
            generic_indexes = []
            for pattern in INDEX_PATTERNS:
                for match in pattern.finditer(line):
                    base, expr = match.group(1), match.group(2).strip()
                    if base.startswith(("gSpecies", "gEvolution", "gLevelUp", "gMon", "sSpeciesTo")):
                        generic_indexes.append((base, expr))
            form_tags = {name for name, pattern in FORM_PATTERNS.items() if pattern.search(line)}
            if not (special or table_matches or generic_indexes or form_tags):
                continue
            if table_matches:
                refs = table_matches
            else:
                refs = [(name, expr) for name, expr in generic_indexes]
            if not refs:
                refs = [(None, None)]
            for table, expr in refs:
                level, risks = risk_for(line, expr, table, special)
                findings.append({
                    "path": rel,
                    "line": line_no,
                    "category": classify(rel, line, expr),
                    "table": table or "",
                    "index_expression": expr or "",
                    "special_values": sorted(special),
                    "form_markers": sorted(form_tags),
                    "risk": level,
                    "risk_reasons": risks,
                    "source": stripped[:500],
                })
    counts = Counter()
    for item in findings:
        counts[f"risk_{item['risk']}"] += 1
        counts[f"category_{item['category']}"] += 1
        if item["table"]:
            counts[f"table_{item['table']}"] += 1
        for special in item["special_values"]:
            counts[f"special_{special}"] += 1
    summary = {
        "scanned_source_files": len(files),
        "finding_count": len(findings),
        "counts": dict(sorted(counts.items())),
        "unclassified_count": sum(1 for f in findings if f["category"] == "other/unclassified"),
        "high_risk_count": sum(1 for f in findings if f["risk"] == "high"),
        "medium_risk_count": sum(1 for f in findings if f["risk"] == "medium"),
        "low_risk_count": sum(1 for f in findings if f["risk"] == "low"),
    }
    return findings, summary


def parse_species_constants() -> dict:
    text = (ROOT / "include/constants/species.h").read_text(encoding="utf-8")
    numeric = {}
    for name, value in re.findall(r"^#define\s+(SPECIES_[A-Z0-9_]+)\s+(\d+)\s*$", text, re.M):
        numeric[name] = int(value)
    egg = re.search(r"^#define\s+SPECIES_EGG\s+(\d+)\s*$", text, re.M)
    num = re.search(r"^#define\s+NUM_SPECIES\s+(SPECIES_[A-Z0-9_]+|\d+)\s*$", text, re.M)
    unown = re.findall(r"^#define\s+(SPECIES_UNOWN_(?:[B-Z]|EMARK|QMARK))\s+\([^\n]+\)\s*$", text, re.M)
    ordinary = [value for name, value in numeric.items() if name not in {"SPECIES_NONE", "SPECIES_EGG"} and not name.startswith("SPECIES_OLD_UNOWN_")]
    return {
        "numeric_species_constants": len(numeric),
        "unique_numeric_values": len(set(numeric.values())),
        "numeric_collisions": {str(v): [n for n, x in numeric.items() if x == v] for v in sorted(set(numeric.values())) if sum(1 for x in numeric.values() if x == v) > 1},
        "max_explicit_ordinary_id": max(ordinary, default=0),
        "egg_sentinel": int(egg.group(1)) if egg else None,
        "num_species_expression": num.group(1) if num else None,
        "unown_calculated_constants": [{"symbol": name, "expression": expr.strip()} for name, expr in unown],
        "unown_calculated_count": len(unown),
    }


def test_index_safety_helpers() -> None:
    def valid(index: int, size: int) -> bool:
        return 0 <= index < size

    assert valid(0, 898)
    assert valid(897, 898)
    assert not valid(898, 898)
    assert not valid(-1, 898)
    # Sentinels and Unown auxiliary IDs are never ordinary table indices.
    egg = 412
    none = 0
    unown_aux = 413
    for value in (none, egg, unown_aux):
        assert not valid(value, 898) or value == 0  # zero only valid as an array slot placeholder
    # An actual table-access contract must reject NONE as data even if index 0 exists.
    def species_data_index(value: int, first: int, count: int) -> bool:
        return first <= value < first + count
    assert not species_data_index(none, 1, 898)
    assert not species_data_index(egg, 1, 898)
    assert not species_data_index(unown_aux, 1, 898)
    assert species_data_index(1, 1, 898)
    assert species_data_index(898, 1, 898)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--check", action="store_true", help="fail if any high-risk or unclassified finding exists")
    args = parser.parse_args()

    findings, summary = scan_source()
    summary["species_namespace"] = parse_species_constants()
    test_index_safety_helpers()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / "species_id_consumers.json"
    csv_path = args.out_dir / "species_id_consumers.csv"
    json_path.write_text(json.dumps({"summary": summary, "findings": findings}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "path", "line", "category", "table", "index_expression",
            "special_values", "form_markers", "risk", "risk_reasons", "source",
        ])
        writer.writeheader()
        for finding in findings:
            row = dict(finding)
            row["special_values"] = ",".join(row["special_values"])
            row["form_markers"] = ",".join(row["form_markers"])
            row["risk_reasons"] = ",".join(row["risk_reasons"])
            writer.writerow(row)

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if args.check and (summary["high_risk_count"] or summary["unclassified_count"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
