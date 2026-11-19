# Limitations

These limitations are known **before** implementation. They are not experimental findings.

## Scientific

1. **Domain shift.** ASHRAE GCDB II is a multi-study field survey. CityLearn is a district energy simulator. Predicted TSV on CityLearn states is a transfer, not a measurement.
2. **Feature mismatch.** Clothing, metabolic rate, and air speed are core PMV/TSV covariates and are absent from standard CityLearn observations.
3. **TSV vs comfort.** Using sensation as a proxy for comfort is a modeling choice and must be labeled as such.
4. **Humidity dynamics.** RH in CityLearn files is not described as a controlled dynamical state.
5. **Action causality.** Battery-only CityLearn scenarios do not let agents change indoor temperature. Comfort-conditioned HVAC claims require DynamicsBuilding-style actions.
6. **Occupancy.** `occupant_count` is a scenario time series, not ASHRAE `subject_id`.
7. **Conformal prediction** assumes exchangeability; that fails under temporal dependence and dataset shift. Coverage in simulation is empirical.
8. **No physical plant.** Nothing here is a deployed BMS controller.
9. **Zenodo 13884633** is a complete-case ASHRAE extract, not a Turkey occupancy study.
10. **Reward weights** are not scientifically identified until sensitivity analysis exists.
11. **Safety language.** The filter is heuristic. No CBF/barrier certificate is claimed in Phase 1.

## Technical

1. Default Python on this machine is 3.14; the project requires 3.11.
2. CityLearn 3.5.0 depends on `torch`. Install time and GPU availability will constrain RL experiments.
3. Flutter UI cannot visualize results that have not been written to disk.
4. Phase 1 does not download Dryad/Zenodo files (network, license acceptance, and size).
