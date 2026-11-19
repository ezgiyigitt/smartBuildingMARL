# Phase 3 report

Trained on local Phase 2 files. TSV is not TCV. No ASHRAE–CityLearn row merge.

## Thermal sensation (grouped by `building_id`, seed 0)

Complete-case full features (`ta,rh,vel,clo,met,t_out`): n=47890 (train 36016 / val 6153 / test 5721).

Test metrics:

| Model | Accuracy | Macro-F1 | Balanced acc. (in JSON) | Ordinal MAE |
| --- | --- | --- | --- | --- |
| logreg | 0.200 | 0.175 | see JSON | 1.502 |
| random_forest | 0.310 | **0.252** | see JSON | 1.108 |
| xgboost | **0.474** | 0.175 | see JSON | **0.733** |
| lightgbm | 0.467 | 0.186 | see JSON | 0.737 |

Selected by **validation macro-F1 then ordinal MAE**: `random_forest`. Accuracy was not the selection rule. XGBoost/LightGBM have higher test accuracy and lower ordinal MAE; RF has the best macro-F1 (class imbalance). Transfer features (`ta,rh,t_out` only) are weaker; same selection.

## Occupancy (CityLearn 2023 phase 1, 3 buildings, 2160 raw rows)

Chronological 70/15/15 after lag construction. Lags 1,2,3,24. No LSTM (short series).

| Horizon | Selected (val MAE) | Test MAE |
| --- | --- | --- |
| 1 h | persistence | 0.332 |
| 6 h | ridge | 0.639 |
| 24 h | persistence | 0.396 |

## Tests

`pytest backend/tests` after this phase.

## Limits

Grouped building split still has domain shift; TSV 7-class macro-F1 is low. Occupancy series is short (~one month × 3 buildings). Models are baselines, not a paper result freeze.
