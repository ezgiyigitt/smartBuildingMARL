# Experiment protocol

No comparative experiments have been run. This protocol is the intended procedure.

## Run identity

Each run has a UUID and a directory:

```
experiments/runs/<utc_timestamp>_<algorithm>_<seed>/
  config.yaml
  versions.json
  git.txt
  metrics.json
  logs/
  checkpoints/   # optional, git-ignored
```

`versions.json` records Python, CityLearn, NumPy, PyTorch, scikit-learn, and Flutter/API versions used to *launch* the run.

## Development vs final

| Stage | Seeds | Purpose |
| --- | --- | --- |
| Dev | 0, 1, 2 | Debugging, reward shaping, do not over-claim |
| Final | up to 10 | Baseline comparison, if compute allows |

## Controllers (validity checked per schema)

1. BAU / environment baseline  
2. Rule-based (documented if-then on SOC, price, temperature band)  
3. Single-agent RL (`central_agent=True`)  
4. Independent PPO or independent SAC  
5. Fixed-constraint comfort-aware RL  
6. Proposed: CTDE (MAPPO candidate) + uncertainty-gated filter  

If MAPPO is unstable or incompatible with the action spaces, the proposed method is recorded as “CTDE PPO variant actually implemented,” not as MAPPO.

## Metrics

Energy: kWh, cost, carbon if the schema provides carbon intensity, peak demand.  
Occupant-related: occupancy-weighted predicted TSV risk, temperature-band violations, constraint events.  
RL: episode return, seed variance.  
Robustness: delta vs. Scenario 1 for each disturbance.

## Reporting rule

Tables and dashboard charts bind only to `metrics.json` files on disk. Empty results show “not run,” never a fabricated number.
