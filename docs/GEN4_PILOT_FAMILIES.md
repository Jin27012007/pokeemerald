# Generation 4 pilot families — pre-runtime preparation

## Scope

This pilot selects three evolutionary families from Generation 4, covering eight species:

| Family | National Dex |
|---|---:|
| Starly → Staravia → Staraptor | #396–#398 |
| Bidoof → Bibarel | #399–#400 |
| Shinx → Luxio → Luxray | #403–#405 |

The focused audit reads the already-generated Generation 4 SpeciesInfo batch, runtime mapping, level-up learnsets, evolution catalog, graphics catalog, cry catalog and pending battle-move inventory.

## What this change does

- Verifies that all eight species have complete source stat records and non-empty level-up learnsets.
- Checks the five expected evolution links between the selected families.
- Lists the selected families' moves that still lack target Emerald battle-move records.
- Reports missing target graphics and cry entries.
- Confirms that no production Emerald species ID has been allocated to any selected species.

The audit output is generated at reports/gen8-conversion/gen4_species_pilot.json by CI. Regression tests run against the same generated source tables used by the existing Generation 4 readiness audit.

## What this change deliberately does not do

It does not add these species to gSpeciesInfo, assign internal IDs, change NUM_SPECIES or SPECIES_EGG, move the Unown auxiliary range, alter save layout, or modify the live graphics, cry, battle, learnset or evolution tables. National Dex values are never treated as runtime array indexes.

That restraint is required by the repository's current Gen 4 readiness contract: the global index-consumer review and save/runtime migration must be validated before production IDs are assigned. This PR is a bounded, testable pilot-preparation step, not a claim that the eight Pokémon are already playable.

## Next implementation gate

Once this pilot report passes, the next steps are to close the listed move and evolution dependencies, import and verify Emerald-format graphics and cries, audit the selected species' ability behavior, then complete the global species-index and save migration work before any runtime activation.
