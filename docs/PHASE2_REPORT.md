# Phase 2 report

## Implemented

Download + hash + quality JSON; grouped-split helper; CityLearn 2023 phase 1 schema inspection.

## Tests

`pytest backend/tests -q` after this phase (run locally).

## Limitations

- Dryad zip not obtained (401). ASHRAE files are CBE GitHub v2.1.0, which matches the published 109,033-row v2.1 size.
- No model training.
- HVAC causality inferred from schema (`LSTMDynamicsBuilding` + `cooling_device`), not yet from a stepped episode.

## Next

Phase 3: TSV models on grouped building splits; occupancy forecast on CityLearn `occupant_count`.
