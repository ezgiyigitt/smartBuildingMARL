import pandas as pd

from app.ml.occupancy_forecasting.features import occupancy_matrix


def test_lags_do_not_use_future_occupant_count() -> None:
    frame = pd.DataFrame(
        {
            "hour": list(range(1, 31)),
            "day_type": [1] * 30,
            "occupant_count": list(range(30)),
        }
    )
    data = occupancy_matrix(frame, horizon=1)
    # y at a row is next occupant; lag1 is previous occupant, never y itself.
    assert (data["y"] - data["occupant_count_lag1"]).abs().min() >= 0
    row = data.iloc[0]
    # First usable index after lag 24 dropna is t=24 (0-based 24), y is occupant at 25.
    assert row["occupant_count_lag1"] != row["y"]
