# Scientific Limitations and Protocol Boundaries

## 1. Conformal Prediction is Not Formal Safe Control
- **Exchangeability Assumption**: Standard split conformal prediction mathematically guarantees finite-sample coverage $1 - \alpha$ under the strict assumption that calibration data and test data are independent and identically distributed ($IID$) or exchangeable.
- **Violation in Building Energy and HVAC**:
  1. *Grouped Cross-Building Domain Shift*: ASHRAE data comes from different buildings across diverse climate zones, construction eras, and HVAC types. Between-building variation violates identical distribution.
  2. *Temporal Feedback & Non-stationarity*: In dynamic HVAC simulation (CityLearn), the agent's actions modify the indoor temperature trajectory. The resulting state transitions exhibit strong temporal autocorrelation and non-stationarity, completely breaking exchangeability.
- **Role in Project**: Conformal prediction sets serve as a heuristic uncertainty diagnostic and state-dependent risk filter, NOT a formal safety certificate or Lyapunov barrier certificate.

## 2. Subjective Comfort and Transfer Limits
- **TSV != TCV**: Thermal Sensation Vote (TSV, 7-point scale from cold -3 to hot +3) measures sensation, not comfort preference or Thermal Comfort Vote (TCV). Sensation of $\pm 1$ (slightly warm/cool) may be perfectly acceptable or preferred by occupants depending on adaptive behavior.
- **No Direct Row Merging**: ASHRAE survey participants must never be row-merged with CityLearn simulation timesteps.
- **Missing Covariates in Simulation**: CityLearn 2023 Phase 1 provides `indoor_dry_bulb_temperature` and `outdoor_dry_bulb_temperature` (and raw CSV humidity). Personal physiological factors (`clo`, `met`, `vel`) are not dynamically tracked in the environment. Transfer TSV models only use overlapping physical proxies (`ta, rh, t_out`), and predicted votes inside CityLearn are strictly diagnostic indicators.

## 3. Humidity Dynamics
- In CityLearn, indoor relative humidity is present in the raw building CSVs but is not an active controlled state variable driven by dynamic moisture balance equations in the simulation engine.
