from __future__ import annotations

import pandas as pd

from app.data.validators.group_splits import assign_group

FEATURES_FULL = ["ta", "rh", "vel", "clo", "met", "t_out"]
FEATURES_TRANSFER = ["ta", "rh", "t_out"]
TARGET = "thermal_sensation"


def load_measurements(path) -> pd.DataFrame:
    return pd.read_csv(path, compression="infer", low_memory=False)


def make_tsv_frame(measurements: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    frame = measurements.loc[:, ["building_id", TARGET, *features]].copy()
    frame[TARGET] = pd.to_numeric(frame[TARGET], errors="coerce")
    for col in features:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame = frame.dropna(subset=[TARGET, "building_id", *features])
    frame["tsv_class"] = frame[TARGET].round().clip(-3, 3).astype(int)
    frame["split"] = frame["building_id"].map(lambda x: assign_group(x, seed=0))
    return frame
