# Research methodology

This document states the intended experimental method. It does **not** report results.

## Question

Under uncertain occupancy, noisy or missing sensors, and imperfect predictions, does an uncertainty-aware, occupant-sensitive, constraint-filtered multi-agent controller improve the energy–sensation–reliability trade-off relative to:

1. Business-as-usual (CityLearn BAU / no-control baseline provided by the environment, if available)
2. Rule-based control
3. Single-agent RL
4. Independent multi-agent RL
5. Comfort-aware RL with **fixed** constraints and no uncertainty gating

## Outcomes (not interchangeable)

| Outcome | Source | Meaning |
| --- | --- | --- |
| Thermal Sensation Vote (TSV) | ASHRAE `thermal_sensation` | Sensation on the ASHRAE scale |
| Thermal Comfort Vote (TCV) | ASHRAE `thermal_comfort` | Comfort 1–6, often missing |
| Acceptability | ASHRAE `thermal_acceptability` | acceptable / unacceptable |
| Indoor temperature tracking | CityLearn | Simulation state, not a vote |
| Occupancy-weighted sensation risk | Coupled interface | Predicted TSV risk while `occupant_count > 0` |

If TCV coverage is too low after Phase 2 EDA, the paper-facing occupant model is a **TSV model**. Simulation “comfort violations” must then be defined as temperature-band or predicted-TSV-risk events, not as measured TCV.

## Validation

### Thermal models

- Grouped splits by `building_id` (and `subject_id` if non-null density allows).
- No random row split as the sole reported protocol.
- Optional leave-one-study/building-out generalization.
- Metrics: accuracy, macro-F1, balanced accuracy, ordinal MAE, ECE, Brier, conformal coverage and set size.
- Model choice is not accuracy-only.

### Occupancy forecasts

- Walk-forward or expanding-window evaluation.
- Lags only from time `t-1` and earlier when predicting `t+h`.
- Persistence and a simple statistical baseline before ML.
- MAE/RMSE by horizon.
- Separate evaluation under synthetic occupancy shocks (labeled as simulation interventions).

### Control experiments

- Same CityLearn schema, episode window, and seeds across controllers.
- Development: seeds `{0,1,2}`.
- Final comparison target: 10 seeds if compute allows.
- Report mean, standard deviation, and a confidence interval only after runs exist.
- Statistical tests only if independence and distributional assumptions are checked.

## Uncertainty and control

Split conformal prediction provides finite-sample coverage **under exchangeability** of calibration and test points (Shafer and Vovk, 2008; Angelopoulos and Bates, 2023). Building time series and transfer from ASHRAE field studies to CityLearn dynamics **violate** that assumption. Coverage is an empirical diagnostic, not a control certificate.

The safety layer is a constrained action filter:

- If the conformal set is larger than a configured threshold, execute a conservative fallback (e.g. track setpoint / reduce storage cycling — exact rule documented per scenario).
- If the set is small and includes severe sensation classes, clip HVAC-related actions toward the configured band.

## Disturbances

Scenarios 1–10 in the master prompt are implemented as **labeled wrappers** with fixed seeds and magnitudes. They are not claimed to be field faults.

## What would count as a contribution

A contribution is **not** “we combined MAPPO, XGBoost, and conformal prediction.”

A contribution requires a clearly specified mechanism, for example:

> Agents condition on (i) predicted occupancy, (ii) predicted TSV distribution, and (iii) an uncertainty statistic; the coordination/safety module changes the feasible action set as a function of (iii); ablations show that removing (iii) degrades robustness under the documented disturbances.

Until those experiments exist, novelty is a **hypothesis**.
