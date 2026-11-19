# Phase 2 quality summary

Generated from local files by `backend/scripts/phase2_acquire_and_validate.py`. Counts below are from those files, not from publications.

## ASHRAE GCDB II v2.1.0

Source used: CBE GitHub `v2.1.0/db_measurements_v2.1.0.csv.gz` and `db_metadata.csv`.  
Dryad zip endpoint `https://datadryad.org/api/v2/datasets/doi%3A10.6078%2FD1F671/download` returned **HTTP 401** on 2026-11-19.

| Item | Value |
| --- | --- |
| Measurement rows | 109033 |
| Metadata rows / buildings | 809 / 809 unique `building_id`, 0 missing |
| Duplicate measurement rows | 0 |
| TSV non-null | 106171 (missing 2.62%) |
| TCV non-null | 38035 (missing 65.12%) |
| Acceptability non-null | 64814 (missing 40.56%) |
| `subject_id` non-null | 42934 (2651 unique) |

Missingness (selected): `ta` 0%, `rh` 6.24%, `vel` 14.23%, `clo` 6.37%, `met` 13.47%, `t_out` 36.43%.

**Target decision:** primary label is **TSV**. TCV is too incomplete to be the primary outcome.

**Splits:** by `building_id`, 70/15/15 via `assign_group` (`backend/app/data/validators/group_splits.py`). Row-level random split is not the reported protocol.

SHA-256: metadata `af6770a2...bfc10`; measurements gz `9722be58...c68380`.

## Zenodo complete-case extract

DOI 10.5281/zenodo.13884633, CC-BY-4.0.  
File MD5 **matches** deposit: `9deb23a64d9624c7d3ccd3dc97589e2d`.  
Rows: **10618** (matches deposit). Duplicates: 0. Missingness: 0 on all 14 columns.  
Target column in file: `Thermal sensation`. Degree-symbol headers decode poorly (`¡C`); treat as encoding, not a new variable.  
This is not a Turkey occupancy field study.

## CityLearn `citylearn_challenge_2023_phase_1`

3 buildings, type `LSTMDynamicsBuilding`.  
Active actions include **`cooling_device`**, `dhw_storage`, `electrical_storage`.  
Active observations include indoor dry-bulb temperature and `occupant_count`.  
CSV also has `indoor_relative_humidity`, but RH is **not** in the schema active observation list.  
Timestep: 3600 s.  
Compatibility gate: occupant-aware HVAC **supported** (temperature is not treated as battery-only exogenous).

No ASHRAE–CityLearn row merge was performed.
