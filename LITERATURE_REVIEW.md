# Literature review

Only sources that were checked against publisher or repository pages are listed. If a DOI could not be confirmed, the canonical URL is given instead. This review supports a **research gap hypothesis**; it does not prove novelty.

## 1. Occupant thermal sensation data

Földváry Ličina et al. (2018) describe ASHRAE Global Thermal Comfort Database II: paired field measurements and right-here-right-now subjective votes, originally about 81,846 rows after quality assurance, published in *Building and Environment* ([DOI: 10.1016/j.buildenv.2018.06.022](https://doi.org/10.1016/j.buildenv.2018.06.022)). The public data files are hosted on Dryad ([DOI: 10.6078/D1F671](https://doi.org/10.6078/D1F671)). The Center for the Built Environment maintains the version 2.1 codebook (metadata + measurements; `thermal_sensation` vs `thermal_comfort` 1–6) at [github.com/CenterForTheBuiltEnvironment/ashrae-db-II](https://github.com/CenterForTheBuiltEnvironment/ashrae-db-II).

Kuru Erdem, Calis, and Gokalp (2024) released a **10,618-row complete-case TSV classification extract** of ASHRAE DB II v2.01 on Zenodo ([DOI: 10.5281/zenodo.13884633](https://doi.org/10.5281/zenodo.13884633), CC-BY-4.0). It is useful as a fully observed subset. It is **not** an independent Turkish occupancy field study.

Chen, Meng, and Zhang (IEEE *Transactions on Sustainable Computing*, 2023) use ASHRAE Database II inside a meta-learning thermal-preference model coupled to **model-based offline RL** in EnergyPlus, not CityLearn ([DOI: 10.1109/TSUSC.2023.3251302](https://doi.org/10.1109/TSUSC.2023.3251302)). That work personalizes preference from occupant feedback; it does not evaluate split conformal prediction or district MARL.

## 2. CityLearn and MARL for buildings

Vázquez-Canteli, Kämpf, Henze, and Nagy (2019) introduced CityLearn as a Gym environment for demand-response RL benchmarking (ACM BuildSys; [DOI: 10.1145/3360322.3360998](https://doi.org/10.1145/3360322.3360998)).

Nweye, Nagy, et al. (NeurIPS 2022 Competitions Track, PMLR 220:85–103, published record 2023) summarize CityLearn Challenge 2022: **battery-only** load shifting on a real-world neighborhood digital twin; the winning team combined forecasting with **MAPPO** (parameter sharing) and a stochastic optimizer ([https://proceedings.mlr.press/v220/nweye23a.html](https://proceedings.mlr.press/v220/nweye23a.html)). That result is **not** occupant-thermal-sensation-aware HVAC control.

The 2023 control track added heat-pump actions and LSTM indoor-temperature dynamics (`DynamicsBuilding`). Maintainer posts on the AIcrowd forum state that earlier setups met thermal loads ideally and that CSV indoor temperature was static at runtime, whereas the 2023 LSTM path lets cooling/heating energy change indoor temperature ([forecasting-track clarification](https://discourse.aicrowd.com/t/clarifying-forecasting-track-challenge/9131); [indoor temp/RH thread](https://discourse.aicrowd.com/t/role-of-indoor-temp-and-rh-and-setpoint-variables-in-csv-files/9172)).

Heterogeneous vs homogeneous MARL in CityLearn is studied in a BuildSys 2023 paper using MARLlib (HAPPO/HATRPO vs MAPPO) ([DOI: 10.1145/3600100.3626276](https://doi.org/10.1145/3600100.3626276)). Scalable CTDE with attention for large CityLearn districts is reported as AAC-MADRL in *Applied Energy* ([DOI: 10.1016/j.apenergy.2025.125993](https://doi.org/10.1016/j.apenergy.2025.125993)). These papers optimize energy/cost/peaks, not ASHRAE-trained TSV uncertainty.

MAPPO itself is Yu, Velu, Vinitsky, Gao, Wang, Bayen, and Wu, NeurIPS 2022, “The Surprising Effectiveness of PPO in Cooperative Multi-Agent Games” ([DOI: 10.52202/068431-1787](https://doi.org/10.52202/068431-1787); arXiv: [2103.01955](https://arxiv.org/abs/2103.01955)).

## 3. Uncertainty-aware HVAC control

An, Ding, Rathee, and Du, CLUE (BuildSys 2023), use Gaussian-process epistemic uncertainty inside model-based RL / MPPI for HVAC and report fewer comfort-band violations with little data ([DOI: 10.1145/3600100.3623742](https://doi.org/10.1145/3600100.3623742)). Uncertainty is on **building dynamics**, not on an ASHRAE TSV classifier, and the plant is a five-zone EnergyPlus HVAC simulation rather than CityLearn MARL.

Conformal prediction theory: Shafer and Vovk, *JMLR* 9:371–421, 2008 ([https://jmlr.org/papers/v9/shafer08a.html](https://jmlr.org/papers/v9/shafer08a.html)); Angelopoulos and Bates, *Foundations and Trends in Machine Learning*, 2023 ([DOI: 10.1561/2200000101](https://doi.org/10.1561/2200000101)). Finite-sample coverage requires exchangeability (or a stated relaxation).

Conformal methods have been applied to building **load** forecasting (e.g. Energies 2024, [DOI: 10.3390/en17174348](https://doi.org/10.3390/en17174348)) and to tightening constraints in model-based controllers (Chee et al., L4DC / PMLR 242, 2024, [https://proceedings.mlr.press/v242/chee24a.html](https://proceedings.mlr.press/v242/chee24a.html)). Those guarantees do not automatically transfer to CityLearn MARL with a transferred TSV model.

## 4. Gap (hypothesis, not a claim of uniqueness)

Closest prior combinations:

| Work | Occupant model from ASHRAE | District MARL in CityLearn | Prediction-set gating | Robustness suite |
| --- | --- | --- | --- | --- |
| CityLearn Challenge 2022 winners | No | Yes (batteries, MAPPO) | No | Competition phases |
| Chen et al. 2023 | Yes (preference / meta-learning) | No (EnergyPlus) | No | Limited online feedback |
| An et al. 2023 (CLUE) | Comfort band, GP dynamics | No | Uncertainty in MPPI | Data-efficiency HVAC |
| AAC-MADRL 2025 | No | Yes (CTDE, large n) | Attention, not conformal | Seasonal scenarios |

**Open question this project is designed to test:** whether an ASHRAE-trained, calibrated TSV (or TCV) model, with explicitly non-guaranteed conformal diagnostics, can modulate a CityLearn multi-building policy and a heuristic safety filter so that energy–sensation-risk trade-offs degrade less under missing/noisy observations than fixed-constraint MARL.

That question is only answered after Phase 7 experiments. Combining named algorithms is not itself a contribution.

## 5. Software versions used for this review

CityLearn **3.5.0** documentation and PyPI metadata (Gymnasium `>=0.28.1,<2.0.0`) were retrieved on 2026-11-19. Dataset schemas were taken from the CBE README and CityLearn Dataset/Actions references, not from local files.
