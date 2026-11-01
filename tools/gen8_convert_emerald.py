#!/usr/bin/env python3
"""Generate a conservative Gen 8 -> vanilla Emerald conversion package.

This stage extracts canonical Dex identities, species stat fields that overlap
Emerald, learnsets, and dependency inventories. It does NOT edit production C
tables, assign new species/move IDs, or increase NUM_SPECIES.
"""
from __future__ import annotations
import argparse, csv, json, re, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
V=ROOT/"tools/vendor/pokeemerald-expansion"
OUT=ROOT/"reports/gen8-conversion"
SRC_SPECIES=V/"include/constants/species.h"
SRC_MOVES=V/"include/constants/moves.h"
SRC_INFO=V/"src/data/pokemon/species_info/gen_8_families.h"
SRC_LEARN=V/"src/data/pokemon/level_up_learnsets/gen_8.h"
DST_SPECIES=ROOT/"include/constants/species.h"
DST_MOVES=ROOT/"include/constants/moves.h"
DST_INFO=ROOT/"src/data/pokemon/species_info.h"
DST_LEARN=ROOT/"src/data/pokemon/level_up_learnsets.h"
DST_EVO=ROOT/"src/data/pokemon/evolution.h"
DST_DEX=ROOT/"src/data/pokemon/pokedex_entries.h"
DST_ORDERS=ROOT/"src/data/pokemon/pokedex_orders.h"
DST_CRY=ROOT/"sound/cry_tables.inc"

# Canonical species that are represented in the source header by a base-form
# alias. These map to the base species identity, not another Dex entry.
BASE_ALIASES={
 "CASTFORM_NORMAL":"CASTFORM", "DEOXYS_NORMAL":"DEOXYS",
 "BURMY_PLANT":"BURMY", "WORMADAM_PLANT":"WORMADAM",
 "MOTHIM_PLANT":"MOTHIM", "CHERRIM_OVERCAST":"CHERRIM",
 "SHELLOS_WEST":"SHELLOS", "GASTRODON_WEST":"GASTRODON",
 "GIRATINA_ALTERED":"GIRATINA", "SHAYMIN_LAND":"SHAYMIN",
 "ARCEUS_NORMAL":"ARCEUS", "BASCULIN_RED_STRIPED":"BASCULIN",
 "DARMANITAN_STANDARD":"DARMANITAN", "TORNADUS_INCARNATE":"TORNADUS",
 "THUNDURUS_INCARNATE":"THUNDURUS", "LANDORUS_INCARNATE":"LANDORUS",
 "KYUREM_NORMAL":"KYUREM", "KELDEO_ORDINARY":"KELDEO",
 "MELOETTA_ARIA":"MELOETTA", "LYCANROC_MIDDAY":"LYCANROC",
 "WISHIWASHI_SOLO":"WISHIWASHI", "ZYGARDE_50":"ZYGARDE",
 "MINIOR_METEOR_RED":"MINIOR", "TOXTRICITY_AMPED":"TOXTRICITY",
 "EISCUE_ICE":"EISCUE", "INDEEDEE_MALE":"INDEEDEE",
 "MORPEKO_FULL_BELLY":"MORPEKO", "ZACIAN_HERO":"ZACIAN",
 "ZAMAZENTA_HERO":"ZAMAZENTA", "ETERNATUS":"ETERNATUS",
 "URSHIFU_SINGLE_STRIKE":"URSHIFU"
}
# Only fields present in vanilla Emerald's SpeciesInfo are copied.
COMPATIBLE_FIELDS={
 "baseHP","baseAttack","baseDefense","baseSpeed","baseSpAttack","baseSpDefense",
 "types","catchRate","expYield","evYield_HP","evYield_Attack","evYield_Defense",
 "evYield_Speed","evYield_SpAttack","evYield_SpDefense","itemCommon","itemRare",
 "genderRatio","eggCycles","friendship","growthRate","eggGroups","abilities",
 "safariZoneFleeRate","bodyColor","noFlip"
}
FIELD_ALIASES={"types":"types"}
def read(p):
 if not p.is_file(): raise RuntimeError(f"Missing input: {p.relative_to(ROOT)}")
 return p.read_text(encoding="utf-8")
def enum_rows(text,prefix):
 out=[]
 rx=re.compile(rf"^\s*{re.escape(prefix)}([A-Z0-9_]+)\s*=\s*(0x[0-9a-fA-F]+|\d+)\s*,?\s*(?://.*)?$",re.M)
 for m in rx.finditer(text): out.append({"symbol":m.group(1),"id":int(m.group(2),0)})
 return out
def define_rows(text,prefix):
 out=[]
 rx=re.compile(rf"^#define\s+{re.escape(prefix)}([A-Z0-9_]+)\s+(0x[0-9a-fA-F]+|\d+)\s*$",re.M)
 for m in rx.finditer(text): out.append({"symbol":m.group(1),"id":int(m.group(2),0)})
 return out
def balanced_records(text):
 rx=re.compile(r"^\s*\[SPECIES_([A-Z0-9_]+)\]\s*=\s*\{",re.M)
 rows=[]
 for m in rx.finditer(text):
  i=rx.lastindex if False else m.end()
  depth=1; quoted=False; escaped=False
  while i<len(text) and depth:
   c=text[i]
   if quoted:
    if escaped: escaped=False
    elif c=="\\": escaped=True
    elif c=='"': quoted=False
   else:
    if c=='"': quoted=True
    elif c=="{": depth+=1
    elif c=="}": depth-=1
   i+=1
  if depth==0:
   rows.append((m.group(1),text[m.end():i-1].strip()))
 return rows
def extract_moves(text):
 rx=re.compile(r"static const struct LevelUpMove s([A-Za-z0-9]+)LevelUpLearnset\[\]\s*=\s*\{([\s\S]*?)\n\};")
 rows=[]
 for m in rx.finditer(text):
  moves=[{"level":int(a),"move":b} for a,b in re.findall(r"LEVEL_UP_MOVE\(\s*(\d+)\s*,\s*MOVE_([A-Z0-9_]+)\s*\)",m.group(2))]
  rows.append({"source_species":m.group(1),"moves":moves})
 return rows
def normalize_species(slug):
 return slug.upper().replace("-","_").replace(".","")
def write_json(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--check",action="store_true")
 args=ap.parse_args()
 try:
  ss=read(SRC_SPECIES); sm=read(SRC_MOVES); si=read(SRC_INFO); sl=read(SRC_LEARN)
  ts=read(DST_SPECIES); tm=read(DST_MOVES); ti=read(DST_INFO)
  read(DST_LEARN); read(DST_EVO); read(DST_DEX); read(DST_ORDERS); read(DST_CRY)
  source_species=enum_rows(ss,"SPECIES_")
  target_species=define_rows(ts,"SPECIES_")
  source_moves=enum_rows(sm,"MOVE_")
  target_moves=define_rows(tm,"MOVE_")
  # The base-form values are explicit aliases in the source enum. Ignore
  # duplicate alias lines and use the single concrete identifier for each Dex.
  by_id={}
  for r in source_species:
   if 1<=r["id"]<=898 and r["symbol"] not in BASE_ALIASES:
    by_id.setdefault(r["id"],r["symbol"])
  # The Expansion header assigns national dex IDs to the base-form symbols
  # (Castform_Normal, Deoxys_Normal, etc.). Include those as canonical identities
  # and then normalize their symbol aliases below. Each Dex number must appear once.
  by_id={}
  seen_ids=set()
  for r in source_species:
   if 1<=r["id"]<=898 and r["id"] not in seen_ids:
    by_id[r["id"]]=r["symbol"]
    seen_ids.add(r["id"])
  if sorted(by_id)!=list(range(1,899)):
   missing=sorted(set(range(1,899))-set(by_id))
   raise RuntimeError(f"Canonical Dex mapping incomplete; missing Dex IDs: {missing[:20]}")
  target_names={x["symbol"] for x in target_species}
  species_map=[]
  for dex,symbol in sorted(by_id.items()):
   target_symbol=BASE_ALIASES.get(symbol,symbol)
   existing=target_symbol in target_names
   species_map.append({"national_dex":dex,"source_symbol":symbol,"normalized_symbol":target_symbol,
      "emerald_symbol":target_symbol if existing else None,
      "emerald_internal_id":None if not existing else next(x["id"] for x in target_species if x["symbol"]==target_symbol),
      "status":"existing_emerald_species" if existing else "new_species_id_required"})
  new_species=[x for x in species_map if x["status"]=="new_species_id_required"]
  learnsets=extract_moves(sl)
  used_moves=sorted({m["move"] for l in learnsets for m in l["moves"]})
  target_move_names={x["symbol"] for x in target_moves}
  source_move_by_name={x["symbol"]:x for x in source_moves}
  move_rows=[]
  for name,r in source_move_by_name.items():
   if r["id"]<=354: continue
   move_rows.append({"source_symbol":name,"source_id":r["id"],"emerald_id":None,
    "used_by_gen8_learnset":name in used_moves,
    "status":"requires_battle_and_contest_definition"})
  missing_learn_moves=sorted(set(used_moves)-target_move_names)
  # Extract full SpeciesInfo blocks, retaining raw source text and identifying
  # the overlapping Emerald fields. No raw macro expression is executed.
  info_rows=[]
  for symbol,body in balanced_records(si):
   fields={}
   for m in re.finditer(r"^\s*\.([A-Za-z0-9_]+)\s*=\s*([^,\n]+)",body,re.M):
    key,value=m.group(1),m.group(2).strip()
    if key in COMPATIBLE_FIELDS: fields[key]=value
   info_rows.append({"species_symbol":symbol,"compatible_field_candidates":fields,"raw_fields":body})
  target_fields=set(re.findall(r"^\s*\.([A-Za-z0-9_]+)\s*=",ti,re.M))
  source_fields=set(re.findall(r"^\s*\.([A-Za-z0-9_]+)\s*=",si,re.M))
  extra_fields=sorted(source_fields-target_fields)
  report={
   "scope":"National Dex 1-898, canonical base forms only",
   "production_tables_modified":False,"species_ids_or_NUM_SPECIES_modified":False,
   "counts":{"canonical_dex_entries":len(species_map),"new_species":len(new_species),
    "source_move_constants":len(source_moves),"new_move_constants_after_gen3":len(move_rows),
    "learnset_blocks":len(learnsets),"distinct_learnset_move_names":len(used_moves),
    "missing_learnset_move_names":len(missing_learn_moves),"species_info_blocks":len(info_rows)},
   "species_mapping":species_map,"move_mapping":move_rows,
   "missing_learnset_move_names":missing_learn_moves,
   "species_info_field_names_not_in_emerald":extra_fields,
   "readiness":{"dex_identity_map_complete":True,"species_ids_assigned":False,
    "all_learnset_moves_available":not bool(missing_learn_moves),
    "species_info_fields_semantically_converted":False,"evolution_table_generated":False,
    "pokedex_text_generated":False,"cry_mapping_generated":False,"runtime_ready":False}
  }
  if args.check:
   print(json.dumps(report["counts"],indent=2))
   print("Runtime conversion remains blocked; production C tables untouched.")
   return 0
  OUT.mkdir(parents=True,exist_ok=True)
  write_json(OUT/"conversion_report.json",report)
  write_json(OUT/"species_id_mapping.json",species_map)
  write_json(OUT/"new_species_mapping.json",new_species)
  write_json(OUT/"species_info_compatible_candidates.json",info_rows)
  write_json(OUT/"learnsets_raw.json",learnsets)
  write_json(OUT/"move_mapping_template.json",move_rows)
  write_json(OUT/"missing_learnset_moves.json",missing_learn_moves)
  with (OUT/"move_dependencies.csv").open("w",newline="",encoding="utf-8") as f:
   w=csv.DictWriter(f,fieldnames=["source_symbol","source_id","emerald_id","used_by_gen8_learnset","status"])
   w.writeheader();w.writerows(move_rows)
  print("Generated conversion package in reports/gen8-conversion")
  print(json.dumps(report["counts"],indent=2))
  return 0
 except (OSError,RuntimeError,ValueError,KeyError,StopIteration) as e:
  print(f"GEN8 CONVERSION FAILED: {e}",file=sys.stderr);return 2
if __name__=="__main__": raise SystemExit(main())
