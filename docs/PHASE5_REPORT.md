# Phase 5 Report: CityLearn Integration and Baseline Controllers

Evaluation conducted on **`citylearn_challenge_2023_phase_1`** local schema (`data/raw/citylearn/citylearn_challenge_2023_phase_1/schema.json`) for 720 timesteps (30 days, 1-hour timesteps) across 3 buildings (`Building_1`, `Building_2`, `Building_3`) of class `LSTMDynamicsBuilding`.

Metrics loaded directly from `artifacts/reports/phase5_baselines.json` and logged experiment runs under `experiments/runs/`.

---

## 1. Schema Inspection & Live Environment Compatibility

- **Dataset**: `citylearn_challenge_2023_phase_1`
- **Building Class**: `LSTMDynamicsBuilding` (3 buildings)
- **Active Actions**: `['dhw_storage', 'electrical_storage', 'cooling_device']` (Action bounds: DHW $[-1, 1]$, Battery $[-1, 1]$, Cooling $[0, 1]$)
- **Active Observations**: 29 per building (including `indoor_dry_bulb_temperature`, `indoor_dry_bulb_temperature_cooling_set_point`, `occupant_count`, `cooling_demand`, `dhw_demand`, `electricity_pricing`, `carbon_intensity`)
- **Compatibility Verification (`assess_scenario`)**:
  - `occupant_aware_hvac_supported = True`
  - `indoor_temperature_actionable = True`
  - `has_occupancy = True`
  - `cooling_device` is verified present in active action spaces at runtime.

---

## 2. Baseline Controllers Description

Four distinct baselines were executed on the exact same 720-timestep episode window (seed 0):

1. **Business-As-Usual (`business_as_usual`)**:
   - Zero-action baseline: `dhw_storage = 0.0`, `electrical_storage = 0.0`, `cooling_device = 0.0`.
   - Represents a passive building without active storage shifting or cooling commands.
2. **CityLearn BasicRBC (`basic_rbc`)**:
   - Official built-in CityLearn Rule-Based Controller (`citylearn.agents.rbc.BasicRBC`).
3. **Comfort-Price RBC (`comfort_price_rbc`)**:
   - Documented custom rule-based controller balancing time-of-use electricity pricing, storage SOC, and indoor temperature setpoints:
     - **Battery Storage**: Charge ($+0.5$) during low-price/off-peak hours ($\le 6$ h) when $\text{SOC} < 0.85$; discharge ($-0.5$) during peak hours ($17..21$ h) when $\text{SOC} > 0.20$.
     - **DHW Storage**: Pre-charge ($+0.4$) on cheap electricity; discharge ($-0.4$) during expensive peak hours when DHW demand exists.
     - **Cooling Device**: Boost cooling ($0.80$) if $T_{\text{in}} > T_{\text{set}} + 0.5$ °C; throttle ($0.10$) if $T_{\text{in}} < T_{\text{set}} - 0.5$ °C; economize ($0.20$) on peak price when within setpoint; comfort priority ($0.60$) when occupants are present and $T_{\text{in}} > T_{\text{set}}$; nominal ($0.40$) otherwise.
4. **Random Action (`random`)**:
   - Uniform random sampling within valid action bounds per building (seed 0).

---

## 3. District-Level Comparative Results

| Baseline | Total Electricity (kWh) | CityLearn Cost KPI | CityLearn Carbon KPI | Mean Setpoint Violation Rate | Total Occupant-Weighted Violation (Deg-Hours) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`business_as_usual`** | **1,096.9 kWh** | 0.382 | 0.408 | 98.2% | 31,229.9 |
| **`basic_rbc`** | 4,942.5 kWh | 1.837 | 1.881 | **0.0%** | **0.9** |
| **`comfort_price_rbc`** | **2,504.0 kWh** | **0.905** | **0.974** | **7.2%** | **163.9** |
| **`random`** | 4,315.0 kWh | 1.587 | 1.634 | 3.1% | 87.8 |

*Key Findings:*
1. **The BAU Failure Mode**: While `business_as_usual` consumes the least electricity (1,096.9 kWh) by leaving heat pumps at zero command, it causes catastrophic thermal discomfort: mean indoor temperatures climb to 33.6–34.7 °C, leading to a 98.2% violation rate and over 31,229 occupant-weighted violation degree-hours.
2. **The BasicRBC Overcooling Waste**: CityLearn's default `BasicRBC` eliminates overheating violations (0.0% violation rate), but it does so by drastically overcooling (mean temperature in Building 1 drops to 13.9 °C), burning 4,942.5 kWh and producing high cost (1.837) and carbon (1.881) KPIs.
3. **The Multi-Objective Sweet Spot of `comfort_price_rbc`**: By coupling setpoint feedback with price-aware storage dispatch, `comfort_price_rbc` cuts electricity consumption by **49.3%** and cost by **50.7%** relative to `BasicRBC` (2,504.0 kWh vs 4,942.5 kWh), while keeping mean temperatures within comfort range (22.3–23.6 °C) and holding violations to only 7.2%.

---

## 4. Building-Level Breakdown

| Baseline | Building | Electricity (kWh) | Mean Temp (°C) | Setpoint Viol. Rate (%) | Max Overheat Delta (°C) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`business_as_usual`** | Building_1 | 408.0 | 33.63 | 98.2% | +14.88 |
| | Building_2 | 220.4 | 34.70 | 98.2% | +16.03 |
| | Building_3 | 468.5 | 33.94 | 98.2% | +14.94 |
| **`basic_rbc`** | Building_1 | 2,090.1 | 13.93 | 0.0% | +0.47 |
| | Building_2 | 1,206.4 | 20.18 | 0.0% | +0.42 |
| | Building_3 | 1,646.1 | 20.38 | 0.0% | +0.45 |
| **`comfort_price_rbc`** | Building_1 | 934.8 | 22.25 | 3.5% | +1.34 |
| | Building_2 | 693.5 | 23.65 | 14.7% | +1.57 |
| | Building_3 | 875.7 | 23.20 | 3.5% | +1.30 |
| **`random`** | Building_1 | 1,795.1 | 15.47 | 0.6% | +0.76 |
| | Building_2 | 1,076.5 | 20.50 | 7.0% | +1.28 |
| | Building_3 | 1,443.4 | 21.05 | 1.8% | +0.86 |

---

## 5. Diagnostic TSV Predictions (Phase 3/4 Model Transfer)

> [!WARNING]
> **Domain-Shift Warning**: Predicted TSV values are generated using the Phase 3 Random Forest model on mapped features (`ta, rh, t_out`). Personal physiological variables (`clo, met, vel`) are absent from the CityLearn environment. These values serve strictly as diagnostic indicators, NOT as measured thermal comfort votes.

- Under `business_as_usual`, mean predicted TSV is **+2.70 to +2.79** (severe hot discomfort across 98.7%–99.6% of hours).
- Under `basic_rbc`, mean predicted TSV is **-1.91 to -2.27** (severe cold discomfort due to excessive heat pump chill).
- Under `comfort_price_rbc`, mean predicted TSV is **-0.86 to -1.56** (closer to neutral comfort band, with up to 33.7% in $[-1, +1]$).

---

## 6. Disturbance Wrapper Smoke Test

- `ObservationSanitizer` and `ObservationDisturbanceWrapper` were tested for NaN detection and imputation (fallback filling), providing the stub interface for future Phase 7 robustness testing.
