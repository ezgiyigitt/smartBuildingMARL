# Dataset documentation

Status: **schema-level**. Files have not been downloaded in Phase 1. Record counts below are from **published sources**, not from a local file hash.

## Dataset A — ASHRAE Global Thermal Comfort Database II

| Item | Value |
| --- | --- |
| Purpose | Supervised occupant thermal sensation (and TCV if usable) |
| Dryad | https://datadryad.org/dataset/doi:10.6078/D1F671 |
| DOI | 10.6078/D1F671 |
| Codebook | https://github.com/CenterForTheBuiltEnvironment/ashrae-db-II |
| Paper | Földváry Ličina et al., *Building and Environment*, 2018, DOI 10.1016/j.buildenv.2018.06.022 |
| Layout | `metadata.csv` (building-level) + `measurements.csv.gz` (UTF-8, human-readable header) |
| Published size | Original 2018 paper: 81,846 rows after QA; version 2.1 update: 6,441–6,566 new rows; CBE/Dryad text cites **109,033** entries in v2.1 |

### License

Dryad metadata describes **CC0 1.0**. The 2018 paper states **Open Database License (ODbL)**. Both statements are recorded in `configs/dataset_registry.yaml`. Do not redistribute a cleaned copy until the operator records which terms they follow.

### Measurement columns (official codebook)

Environmental: `ta`, `ta_h/m/l`, `top`, `tr`, `tg*`, `rh`, `vel*`, `met`, `clo`, `clo_d`.  
Subjective: `thermal_sensation`, `thermal_comfort` (1–6), `thermal_acceptability`, `thermal_preference`.  
Indices: `pmv`, `ppd`, `set`, CE variants.  
Outdoor: `t_out`, `rh_out`, ISD-derived fields.  
IDs: `building_id`, `subject_id`, `timestamp`, `season`.

**TSV ≠ TCV.** `thermal_sensation` is not a comfort vote. `thermal_comfort` is often incomplete; Phase 2 must report non-null rates before any TCV model is claimed.

### Leakage controls

- Join metadata on `building_id` only.  
- Prefer grouped validation on buildings/publications.  
- `subject_id` is documented for future repeated measures and may be sparse.  
- Do not use PMV/PPD as features if the research claim is “data-driven sensation from physical variables” unless the paper explicitly studies index-vs-ML comparison.

## Dataset B — Zenodo complete-case TSV subset

| Item | Value |
| --- | --- |
| URL | https://zenodo.org/records/13884633 |
| DOI | 10.5281/zenodo.13884633 |
| License | CC-BY-4.0 |
| Authors | Merve Kuru Erdem, Gulben Calis, Osman Gokalp |
| File | `Thermal Sensation Classification Database based on ASHRAE Global Thermal Comfort Database II.xlsx` |
| Rows | **10,618** complete cases from ASHRAE DB II **v2.01** |

Columns described by the deposit: `Tair`, `Vair`, `RH`, `SET`, `CLO`, `MET`, `Age`, `Sex`, `Tout`, `Season`, `Building Operation Mode`, `Building type`, `TSV`.

### What this dataset is not

It is **not** a Turkish field campaign of building occupants. It is a complete-case classification extract of the global ASHRAE database, curated by the listed authors. Using it does not localize CityLearn buildings to Turkey.

Use it as a smaller, fully observed TSV benchmark and as a sensitivity check against the full Dryad tables.

## Dataset C — CityLearn public scenarios

| Item | Value |
| --- | --- |
| Software | CityLearn **3.5.0** (PyPI, MIT) |
| Docs | https://www.citylearn.net/ |
| API | `CityLearnEnv(schema_name_or_path)` |
| List names | `DataSet().get_dataset_names()` |

Building CSV contract (docs): calendar fields, `indoor_dry_bulb_temperature`, end-use demands, `solar_generation`; optional `occupant_count`, `indoor_relative_humidity`, setpoints, `hvac_mode`.

Weather: outdoor temperature/humidity and solar, plus forecast columns.  
Pricing and carbon intensity: optional files referenced by schema.

### Scenario incompatibility (critical)

Historically, many CityLearn challenge environments **always met** heating/cooling demand and used **batteries** for flexibility. Indoor temperature in the CSV then does **not** change with agent actions (CityLearn Challenge 2023 control-track maintainer clarification). Occupant-aware HVAC research requires a scenario where `cooling_device` / `heating_device` (or equivalent) and temperature dynamics (`DynamicsBuilding` / LSTM) are active, e.g. NeurIPS 2023-style control datasets.

Phase 5 will print `action_names` and refuse to attach the comfort safety layer to battery-only environments.

Humidity is not a dynamically simulated state in the maintainer description; treat RH as an observation if present.

## Coupling rules

| Allowed | Forbidden |
| --- | --- |
| Train TSV on ASHRAE; infer on CityLearn-mapped features | Concatenate ASHRAE rows with CityLearn hours |
| Train occupancy on CityLearn `occupant_count` | Call ASHRAE subjects the occupants of CityLearn buildings |
| Document default `clo`/`met`/`vel` in the experiment config | Silently impute those features from another building’s surveys |
| Label sensor noise as a disturbance wrapper | Present noisy simulations as measured faults |

## Acquisition (Phase 2)

1. Download Dryad files into `data/raw/ashrae_gcdb2/` and record license, version, and SHA-256.  
2. Download the Zenodo xlsx into `data/raw/zenodo_tsv_subset/`.  
3. Copy a named CityLearn dataset from the installed package cache into `data/raw/citylearn/<name>/` for inspection.  
4. Run validators; write quality reports under `artifacts/reports/`.
