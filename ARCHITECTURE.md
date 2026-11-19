# Architecture

## Design goals

The codebase separates (1) dataset contracts, (2) supervised occupant models, (3) CityLearn simulation, (4) multi-agent control, (5) experiment tracking, and (6) a research dashboard. Scientific modules must remain importable without FastAPI or Flutter.

## System context

```
Flutter MVVM dashboard  --HTTP JSON-->  FastAPI
                                          |
                    +---------------------+---------------------+
                    |                     |                     |
              Dataset registry      ML modules            Simulation
              validators            comfort / occupancy   CityLearn adapter
              quality reports       uncertainty           disturbances
                                          |                     |
                                          +----------+----------+
                                                     |
                                              Safety filter
                                              Reward modules
                                              Experiment store (SQLite)
```

## Data flow (ASHRAE ↔ CityLearn)

These sources are **not** the same population and are never concatenated by row.

1. **Offline (ASHRAE GCDB II)**  
   Train a thermal sensation (TSV) model, optionally a TCV/acceptability model if missingness allows. Calibrate probabilities. Fit split conformal prediction on a held-out calibration split grouped by `building_id` when possible.

2. **Offline (CityLearn building CSVs)**  
   Train occupancy forecasts from `occupant_count` with causal lag features only. This series is building simulation occupancy, not ASHRAE survey respondents.

3. **Online (each CityLearn step)**  
   - Read local observations: indoor dry-bulb temperature, optional RH, occupant count, outdoor temperature, prices, carbon intensity, SOC, etc.  
   - Map a **documented subset** of those observations into the comfort-model feature vector. Missing ASHRAE-only features (`clo`, `met`, `vel`) are either omitted (if the deployed model was trained without them) or replaced by experiment-config constants.  
   - Produce TSV prediction, calibrated probabilities, conformal set, occupancy forecast, and uncertainty flags.  
   - Building agents propose actions. A coordination module may adjust proposals under district constraints.  
   - A **heuristic safety filter** may clip or replace actions. High uncertainty triggers a documented conservative fallback. This is not a certified safety controller.  
   - CityLearn executes the action list and returns the next observations and KPIs.

4. **Logging**  
   Every experiment writes an immutable run directory: config snapshot, package versions, git hash if available, metrics JSON, and logs.

## Backend layers

| Layer | Responsibility |
| --- | --- |
| `app/api` | HTTP contracts, job start/status, OpenAPI |
| `app/domain` | Entities and use-case interfaces |
| `app/data` | Loaders, validators, registries |
| `app/ml` | Comfort, occupancy, uncertainty, explainability |
| `app/reinforcement_learning` | Agents, algorithms, rewards, safety |
| `app/simulation` | CityLearn adapter, scenarios, disturbances |
| `app/evaluation` | Metrics, baselines, statistical tests |
| `app/infrastructure` | SQLite, files, background jobs |

Long RL training must not run inside a request worker. Phase 8 will attach an asynchronous job runner. Phase 1 only provides the health and registry endpoints.

## CityLearn control interface

CityLearn 3.5.0 (`CityLearnEnv`) follows Gymnasium: `reset` → `step`. Actions and observations are defined per schema. Public actions include storage, EV, deferrable loads, and, **when the building class supports it**, `cooling_device` / `heating_device` / `cooling_or_heating_device`.

**Mandatory Phase 5 gate:** inspect `action_names` and building class. If indoor temperature is an exogenous CSV replay (typical of Challenge 2022 battery-only setups), occupant-aware HVAC control is scientifically invalid for that scenario. Use a DynamicsBuilding / Challenge 2023-style dataset instead.

`central_agent=True` yields a single concatenated action. Decentralized execution uses one action array per building. CTDE training may use extra global features in the critic only.

## Flutter MVVM

```
View  ->  ViewModel (Riverpod)  ->  Repository  ->  Dio API
```

Views contain no HTTP, no training, and no numerical science. Each feature (`dashboard`, `datasets`, `comfort_analysis`, `occupancy_forecasting`, `experiments`, `reinforcement_learning`, `results`, `reports`) has its own view and viewmodel.

## Reward module contract

Each term is a separately named function with unit, normalization, and a weight that remains `null` until sensitivity analysis. The scalar used for RL is an explicit weighted sum recorded in the run config.

## Safety module contract

Inputs: proposed actions, action bounds, occupant prediction set, occupancy forecast, configured thresholds.  
Outputs: executed actions, whether a fallback was used, and a reason code.  
Non-claim: “safe RL”, “guaranteed comfort”, or “conformal safety”.
