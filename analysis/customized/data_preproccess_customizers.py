"""Custom preprocessing filters for Garmin activity data.

These functions are applied after loading data via garmin_utils,
before any analysis. They do NOT modify garmin_utils.py.
"""

from datetime import time

import pandas as pd

_NIGHTTIME_START = time(22, 30)
_NIGHTTIME_END = time(4, 0)


def filter_nighttime_activities(df: pd.DataFrame) -> pd.DataFrame:
    """Remove activity records whose start time falls in the 22:30–04:00 window.

    Activities recorded during this window are likely erroneous (watch
    misclassifying sleep movements). The window crosses midnight, so both
    the late-night side (>= 22:30) and early-morning side (< 04:00) are
    filtered using OR logic.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame returned by ``garmin_utils.load_activities()``.
        Must contain a ``start_time`` column of datetime dtype.

    Returns
    -------
    pd.DataFrame
        Filtered copy with index reset. The input DataFrame is not mutated.

    Raises
    ------
    KeyError
        If ``start_time`` column is missing.
    TypeError
        If ``start_time`` column is not of datetime dtype.
    """
    if "start_time" not in df.columns:
        raise KeyError(
            "'start_time' column not found. Pass the DataFrame returned by load_activities()."
        )
    if not pd.api.types.is_datetime64_any_dtype(df["start_time"]):
        raise TypeError(
            "'start_time' must be datetime dtype. Pass the DataFrame returned by load_activities()."
        )

    t = df["start_time"].dt.time
    nighttime_mask = (t >= _NIGHTTIME_START) | (t < _NIGHTTIME_END)

    n_filtered = nighttime_mask.sum()
    print(f"Filtered {n_filtered} nighttime activities (22:30–04:00 window)")

    return df[~nighttime_mask].reset_index(drop=True)
