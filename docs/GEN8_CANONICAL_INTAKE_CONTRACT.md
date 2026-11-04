# Gen 8 canonical species intake contract

Status: staging-only. This contract does not allocate production IDs, alter NUM_SPECIES,
change save layouts, or make data runtime-visible.

## Identity model
- National Dex number 1..898 is the canonical identity key, never an internal array index.
- Exactly one canonical record is selected per Dex number.
- Alternate forms remain separately inventoried and must declare their relationship to a canonical row.
- Cosmetic forms are metadata; persistent gameplay identities require an explicit policy and tests.
- Temporary battle forms are state, not permanent species IDs.
- SPECIES_NONE, SPECIES_EGG, legacy Unown values and calculated Unown auxiliary codes are
  special domains. They must not be promoted to canonical species records.

## Required canonical record envelope
Each accepted record must preserve:
- national_dex (integer 1..898), national_symbol, source_record_symbol
- source_file, source_generation, record_provenance
- raw_initializer and expanded_fields (separate, never conflated)
- source_missing_fields, source_unresolved_fields
- target_mapping_status and runtime_gap_codes
- form_policy (canonical, cosmetic, persistent_separate, temporary_battle)
- evidence for target mapping of every compact field

A field absent in source is not a parser default. An unresolved macro is not a resolved value.
No implicit zero, NONE, first-form or numeric-enum fallback is allowed.

## Promotion gates
A record may be staged as candidate only when identity/provenance and required fields resolve.
A species table may be published only when all 898 canonical identities are unique and complete.
Runtime activation remains blocked until every required target symbol maps, all target widths and
enum domains are compatible, dependencies (moves, evolutions, dex text, cries, graphics, forms)
are supplied, and the storage migration design passes round-trip, interrupted-write,
corruption-recovery and old-save tests.

## Invariants
- 898 canonical Dex keys exactly equal set(1..898), no duplicates.
- Existing 386 Emerald internal IDs remain unchanged in any future allocation proposal.
- 512 new canonical species are a separate proposed set, not assigned by this intake contract.
- Egg and Unown auxiliary values are never counted among the 898.
- Every indexed consumer declares accepted domain, lower/upper bounds and sentinel handling.
- Generator output is deterministic and includes source snapshot and tool versions.
