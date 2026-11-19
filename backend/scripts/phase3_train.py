"""Train TSV classifiers and occupancy baselines on local Phase 2 files only."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.ml.comfort_prediction.evaluate import classification_metrics
from app.ml.comfort_prediction.prepare import FEATURES_FULL, FEATURES_TRANSFER, load_measurements, make_tsv_frame
from app.ml.occupancy_forecasting.features import occupancy_matrix

MEAS = ROOT / "data/raw/ashrae_gcdb2/extracted/v2.1.0/db_measurements_v2.1.0.csv.gz"
CL_DIR = ROOT / "data/raw/citylearn/citylearn_challenge_2023_phase_1"
ART = ROOT / "artifacts/models"
REP = ROOT / "artifacts/reports"


def _models_clf():
    models = {
        "logreg": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(max_iter=400, class_weight="balanced")),
            ]
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=80, max_depth=12, min_samples_leaf=5, n_jobs=-1, random_state=0, class_weight="balanced"
        ),
    }
    try:
        from xgboost import XGBClassifier

        models["xgboost"] = XGBClassifier(
            n_estimators=80, max_depth=6, learning_rate=0.1, subsample=0.8, colsample_bytree=0.8,
            n_jobs=-1, random_state=0, eval_metric="mlogloss",
        )
    except Exception as exc:
        models["xgboost_error"] = str(exc)
    try:
        from lightgbm import LGBMClassifier

        models["lightgbm"] = LGBMClassifier(
            n_estimators=80, max_depth=6, learning_rate=0.1, subsample=0.8, colsample_bytree=0.8,
            n_jobs=-1, random_state=0, verbose=-1,
        )
    except Exception as exc:
        models["lightgbm_error"] = str(exc)
    return models


def train_comfort(features: list[str], tag: str) -> dict:
    frame = make_tsv_frame(load_measurements(MEAS), features)
    x_cols = features
    y_col = "tsv_class"
    splits = {name: frame[frame["split"] == name] for name in ("train", "validation", "test")}
    counts = {name: int(len(df)) for name, df in splits.items()}
    y_map = {c: i for i, c in enumerate(sorted(frame[y_col].unique()))}
    inv = {i: c for c, i in y_map.items()}
    results = {"n_rows": int(len(frame)), "split_counts": counts, "classes": sorted(y_map), "features": features}
    fitted = {}
    for name, model in _models_clf().items():
        if name.endswith("_error"):
            results[name] = model
            continue
        x_train = splits["train"][x_cols]
        y_train_raw = splits["train"][y_col]
        if name == "xgboost":
            y_train = y_train_raw.map(y_map)
        else:
            y_train = y_train_raw
        model.fit(x_train, y_train)
        split_metrics = {}
        for split_name, df in splits.items():
            pred = model.predict(df[x_cols])
            if name == "xgboost":
                pred = np.array([inv[int(p)] for p in pred])
            split_metrics[split_name] = classification_metrics(df[y_col], pred)
        fitted[name] = {"metrics": split_metrics}
        joblib.dump(model, ART / f"tsv_{tag}_{name}.joblib")
    # Selection: validation macro-F1, then lower ordinal MAE. Not accuracy alone.
    ranked = []
    for name, payload in fitted.items():
        val = payload["metrics"]["validation"]
        ranked.append((name, val["macro_f1"], -val["ordinal_mae"], val["accuracy"]))
    ranked.sort(key=lambda t: (t[1], t[2]), reverse=True)
    results["models"] = fitted
    results["selected"] = ranked[0][0] if ranked else None
    results["selection_rule"] = "max validation macro_f1, then min ordinal_mae"
    return results


def train_occupancy() -> dict:
    frames = []
    for csv in sorted(CL_DIR.glob("Building_*.csv")):
        df = pd.read_csv(csv)
        df["building"] = csv.stem
        frames.append(df)
    raw = pd.concat(frames, ignore_index=True)
    report = {"n_raw_rows": int(len(raw)), "buildings": sorted(raw["building"].unique().tolist()), "horizons": {}}
    for horizon in (1, 6, 24):
        per_b = []
        for _, g in raw.groupby("building", sort=False):
            per_b.append(occupancy_matrix(g.reset_index(drop=True), horizon=horizon))
        data = pd.concat(per_b, ignore_index=True)
        n = len(data)
        i70, i85 = int(n * 0.70), int(n * 0.85)
        train, val, test = data.iloc[:i70], data.iloc[i70:i85], data.iloc[i85:]
        x_cols = [c for c in data.columns if c != "y"]
        persist_mae = {}
        # Persistence uses lag1 (last observed occupancy), valid for all horizons as naive baseline.
        for split_name, df in (("train", train), ("validation", val), ("test", test)):
            yhat = df["occupant_count_lag1"]
            persist_mae[split_name] = {
                "mae": float(mean_absolute_error(df["y"], yhat)),
                "rmse": float(mean_squared_error(df["y"], yhat) ** 0.5),
            }
        ridge = Pipeline([("scaler", StandardScaler()), ("m", Ridge(alpha=1.0))])
        rf = RandomForestRegressor(n_estimators=60, max_depth=10, min_samples_leaf=4, n_jobs=-1, random_state=0)
        models = {"ridge": ridge, "random_forest": rf}
        try:
            from lightgbm import LGBMRegressor

            models["lightgbm"] = LGBMRegressor(n_estimators=80, max_depth=6, learning_rate=0.1, random_state=0, verbose=-1)
        except Exception as exc:
            models["lightgbm_error"] = str(exc)
        fitted = {"persistence": persist_mae}
        for name, model in models.items():
            if name.endswith("_error"):
                fitted[name] = model
                continue
            model.fit(train[x_cols], train["y"])
            metrics = {}
            for split_name, df in (("train", train), ("validation", val), ("test", test)):
                pred = model.predict(df[x_cols])
                metrics[split_name] = {
                    "mae": float(mean_absolute_error(df["y"], pred)),
                    "rmse": float(mean_squared_error(df["y"], pred) ** 0.5),
                }
            fitted[name] = metrics
            joblib.dump(model, ART / f"occ_h{horizon}_{name}.joblib")
        val_mae = {k: v["validation"]["mae"] for k, v in fitted.items() if isinstance(v, dict) and "validation" in v}
        selected = min(val_mae, key=val_mae.get)
        report["horizons"][str(horizon)] = {
            "n_rows": n,
            "split_counts": {"train": int(len(train)), "validation": int(len(val)), "test": int(len(test))},
            "models": fitted,
            "selected": selected,
            "selection_rule": "min validation MAE",
            "split": "chronological 70/15/15 after lag/horizon dropna; no future columns",
        }
    return report


def main() -> int:
    ART.mkdir(parents=True, exist_ok=True)
    REP.mkdir(parents=True, exist_ok=True)
    out = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "target_definition": "tsv_class = round(clip(thermal_sensation, -3, 3)). TSV is not TCV.",
        "comfort_full_features": train_comfort(FEATURES_FULL, "full"),
        "comfort_transfer_features": train_comfort(FEATURES_TRANSFER, "transfer"),
        "occupancy": train_occupancy(),
    }
    (REP / "phase3_metrics.json").write_text(
        json.dumps(out, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o)),
        encoding="utf-8",
    )
    print(json.dumps({
        "comfort_full_selected": out["comfort_full_features"]["selected"],
        "comfort_transfer_selected": out["comfort_transfer_features"]["selected"],
        "occ_h1_selected": out["occupancy"]["horizons"]["1"]["selected"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
