# Phase 4 Report: Uncertainty Calibration, Conformal Prediction, and Explainability

Generated from `artifacts/reports/phase4_uncertainty.json` on local ASHRAE v2.1 data with grouped-by-`building_id` split (seed 0).

TSV is not TCV. ASHRAE occupants are never row-merged with CityLearn timesteps.

---

## 1. Probability Calibration (Temperature Scaling)

Fitted post-hoc on the **validation split** (buildings in validation set) via cross-entropy minimization on temperature parameter $T > 0$. Evaluated on the held-out **test split** (unseen buildings).

### Test Split Metrics

| Feature Set | Model | Opt. Temp $T$ | Uncal. ECE | Cal. ECE | Uncal. Brier | Cal. Brier |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Full Features** (`ta,rh,vel,clo,met,t_out`) | **Random Forest** (selected) | **0.8244** | **0.0496** | **0.0524** | **0.7666** | **0.7650** |
| | XGBoost | 1.0592 | 0.0302 | 0.0508 | 0.6713 | 0.6739 |
| | Logistic Regression | 0.7077 | 0.0776 | 0.0807 | 0.8281 | 0.8251 |
| **Transfer Features** (`ta,rh,t_out`) | **Random Forest** (selected) | **0.8407** | **0.0651** | **0.0662** | **0.8020** | **0.8023** |
| | XGBoost | 1.1353 | 0.0471 | 0.0850 | 0.6834 | 0.6903 |
| | Logistic Regression | 0.6137 | 0.1462 | 0.1227 | 0.8363 | 0.8305 |

*Notes:*
- Random Forest is slightly underconfident on validation ($T = 0.8244 < 1.0$). Brier score improves from 0.7666 to 0.7650.
- Logistic Regression benefits significantly from calibration on transfer features (ECE drops from 0.1462 to 0.1227).

---

## 2. Split Conformal Prediction (Prediction Sets)

- **Calibration Split**: Validation buildings ($n = 6153$ complete cases for full features, $n = 9184$ for transfer features).
- **Test Split**: Unseen test buildings ($n = 5721$ for full features, $n = 8198$ for transfer features).
- **Target Coverage**: $1 - \alpha = 0.90$ (90.0%).
- **Non-conformity Score**: Least Ambiguous Set (LAC), $s_i = 1 - \hat{p}(y_i \mid x_i)$.
- **Non-empty Guarantee**: Sets with empty threshold default to top-1 predicted class.

### Test Split Conformal Results

| Feature Set | Model | Conformal Quantile $q$ | Target Coverage | Empirical Coverage | Mean Set Size (out of 7) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Full Features** | **Random Forest** | **0.8878** | **90.0%** | **91.44%** | **4.01** |
| | XGBoost | 0.8711 | 90.0% | 92.36% | 3.60 |
| | Logistic Regression | 0.8863 | 90.0% | 93.13% | 4.66 |
| **Transfer Features** | **Random Forest** | **0.8931** | **90.0%** | **90.36%** | **4.31** |
| | XGBoost | 0.8778 | 90.0% | 92.89% | 3.84 |
| | Logistic Regression | 0.8876 | 90.0% | 91.63% | 4.61 |

### Set Size Distribution (Random Forest - Full Features)

| Set Size | Proportion of Test Samples |
| :--- | :--- |
| Size 1 | 0.9% |
| Size 2 | 3.5% |
| Size 3 | 24.3% |
| Size 4 | 43.6% |
| Size 5 | 22.8% |
| Size 6 | 4.6% |
| Size 7 | 0.2% |

*Interpretation:*
- Empirical coverage exceeds nominal 90% (91.44% on full, 90.36% on transfer).
- Mean set size is relatively wide (~4.0 classes out of 7), directly reflecting the substantial intrinsic ambiguity and noise in 7-point subjective thermal sensation votes across different buildings.

---

## 3. Explainability and Feature Importance

Permutation feature importance on the held-out test split measures the mean drop in validation/test `macro_f1` when each feature column is permuted (5 repeats, seed 0).

### Full Features (`ta,rh,vel,clo,met,t_out`) on Selected Random Forest

| Rank | Feature | Permutation Importance ($\Delta$ Macro-F1) | Physical Description |
| :--- | :--- | :--- | :--- |
| 1 | `ta` | **+0.0977** | Indoor air dry-bulb temperature (°C) |
| 2 | `t_out` | **+0.0481** | Outdoor dry-bulb temperature (°C) |
| 3 | `rh` | **+0.0293** | Indoor relative humidity (%) |
| 4 | `clo` | **+0.0245** | Clothing insulation (clo) |
| 5 | `met` | **+0.0157** | Metabolic rate (met) |
| 6 | `vel` | **+0.0082** | Air velocity (m/s) |

### Transfer Features (`ta,rh,t_out`) on Selected Random Forest

| Rank | Feature | Permutation Importance ($\Delta$ Macro-F1) |
| :--- | :--- | :--- |
| 1 | `ta` | **+0.0732** |
| 2 | `t_out` | **+0.0421** |
| 3 | `rh` | **+0.0326** |

### Interpretation & Scientific Boundaries
1. **Dominance of `ta` and `t_out`**: Indoor air temperature `ta` is by far the most predictive single variable. Outdoor temperature `t_out` acts as a crucial proxy for seasonal adaptation and building envelope heat load.
2. **Missing Personal Variables in CityLearn**: In CityLearn transfer settings, `clo`, `met`, and `vel` are unavailable. Their absence forces models to rely strictly on environmental proxies (`ta`, `rh`, `t_out`), which explains the reduced precision and slightly larger conformal set size (4.31 vs 4.01).
3. **No Causal Overclaim**: High predictive importance indicates statistical correlation and classification utility; it does not constitute a causal DAG or proof that manipulating `t_out` directly shifts thermal sensation independently of indoor setpoints.

---

## 4. Safety & Gating Interface Stub (Phase 6 Integration Hook)

A heuristic diagnostic layer (`ComfortGatingFilter`) was tested against the prediction sets:
- **Uncertainty Flag**: Set size $|C(x)| > 2$.
- **Discomfort Risk Flag**: Any class in $C(x)$ has $|TSV| \ge 2$ (severe cold $\le -2$ or warm $\ge +2$).
- **Conservative Action Recommendation**: Triggered if either uncertain or at discomfort risk.

### Diagnostics on Test Split (Random Forest - Full Features)

- **Total Test Samples**: 5,721
- **Uncertainty Flag Rate**: 95.6%
- **Severe Discomfort Risk Flag Rate**: 96.0%
- **Conservative Action Rate**: 97.3%

*Why is the conservative flag rate high?*
Because the 7-class TSV models exhibit substantial epistemic and aleatoric uncertainty on unseen buildings, a high coverage (90%) prediction set frequently includes neighbor classes like $-2$ or $+2$ in its support. In Phase 6, this demonstrates why a pure binary hard cutoff is too restrictive; the gating interface should provide a graded penalty or state-dependent risk metric rather than an outright freeze.
