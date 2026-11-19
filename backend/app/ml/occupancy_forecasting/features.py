from __future__ import annotations

import pandas as pd

LAGS = (1, 2, 3, 24)


def add_lags(frame: pd.DataFrame, column: str = "occupant_count") -> pd.DataFrame:
    out = frame.copy()
    for lag in LAGS:
        out[f"{column}_lag{lag}"] = out[column].shift(lag)
    return out


def occupancy_matrix(frame: pd.DataFrame, horizon: int = 1) -> pd.DataFrame:
    out = add_lags(frame)
    out["y"] = out["occupant_count"].shift(-horizon)
    lag_cols = [f"occupant_count_lag{lag}" for lag in LAGS]
    cols = ["hour", "day_type", *lag_cols, "y"]
    return out.loc[:, [c for c in cols if c in out.columns]].dropna()
