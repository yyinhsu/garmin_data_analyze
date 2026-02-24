"""Build an enriched per-night feature DataFrame for sleep interventional analysis.

All feature engineering for sleep_deep_analysis.ipynb lives here so the
notebook stays focused on analysis. Call `build_sleep_features()` to get the
full feature matrix.

Design notes:
- monitoring tables (658K–817K rows) are loaded once and queried with
  numpy.searchsorted — no per-row SQL.
- NaN is used consistently for missing data (never 0 as a sentinel).
- `filter_nighttime_activities` is applied internally before exercise features.
- CONTROLLABILITY dict tags each feature for the interventional analysis section.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Path helpers (mirrors garmin_utils pattern)
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DB_DIR = _PROJECT_ROOT / "HealthData" / "DBs"

_DB = {
    "garmin": _DB_DIR / "garmin.db",
    "activities": _DB_DIR / "garmin_activities.db",
    "monitoring": _DB_DIR / "garmin_monitoring.db",
    "summary": _DB_DIR / "garmin_summary.db",
}


def _sql(query: str, db: str, **kw) -> pd.DataFrame:
    with sqlite3.connect(str(_DB[db])) as conn:
        return pd.read_sql_query(query, conn, **kw)


# ---------------------------------------------------------------------------
# Controllability metadata
# ---------------------------------------------------------------------------

#: Maps feature name (or prefix) → controllability level.
#: HIGH  = directly actionable (bedtime, workout timing, intensity)
#: MEDIUM = indirectly actionable (accumulated debt, consistency)
#: LOW   = context / physiological state, not easily changed
CONTROLLABILITY: dict[str, str] = {
    # Temporal
    "sleep_start_hour": "HIGH",
    "time_in_bed_hours": "HIGH",
    "bedtime_consistency_7d": "MEDIUM",
    "is_weekend": "LOW",
    "weekday": "LOW",
    "month": "LOW",
    "sleep_start_minute": "HIGH",
    "wake_hour": "HIGH",
    # Lag / rolling / debt
    "sleep_debt_7d": "MEDIUM",
    "rolling_3d_sleep_avg": "MEDIUM",
    "rolling_7d_sleep_avg": "MEDIUM",
    "rolling_7d_score_avg": "MEDIUM",
    "prev1_total_sleep": "LOW",
    "prev1_score": "LOW",
    "prev1_rem_hours": "LOW",
    "prev1_deep_hours": "LOW",
    "prev1_qualifier_encoded": "LOW",
    "prev1_sleep_start_hour": "LOW",
    "prev2_total_sleep": "LOW",
    "prev3_total_sleep": "LOW",
    # Streaks
    "consecutive_poor_sleep": "LOW",
    "consecutive_good_sleep": "LOW",
    "consecutive_exercise_days": "MEDIUM",
    "consecutive_rest_days": "MEDIUM",
    "days_since_last_good_sleep": "LOW",
    # Exercise
    "had_exercise": "HIGH",
    "n_activities": "HIGH",
    "total_workout_duration_h": "HIGH",
    "latest_workout_end_hour": "HIGH",
    "hours_workout_to_sleep": "HIGH",
    "primary_sport": "HIGH",
    "vigorous_ratio": "HIGH",
    "training_load": "HIGH",
    "training_load_7d": "MEDIUM",
    "hrz_high_intensity_min": "HIGH",
    "moderate_activity_h": "HIGH",
    "vigorous_activity_h": "HIGH",
    "intensity_score": "HIGH",
    # Body battery
    "bb_max": "LOW",
    "bb_min": "LOW",
    "bb_charged": "LOW",
    "bb_range": "LOW",
    # Physiology
    "rhr": "LOW",
    "inactive_hr_avg": "LOW",
    "avg_spo2": "LOW",
    "avg_rr": "LOW",
    "rr_waking_avg": "LOW",
    # Pre-sleep windows — HR
    **{f"pre_sleep_hr_avg_{n}h": "MEDIUM" for n in [1, 2, 4, 6, 8]},
    **{f"pre_sleep_hr_min_{n}h": "LOW" for n in [1, 2, 4, 6, 8]},
    **{f"pre_sleep_hr_std_{n}h": "LOW" for n in [1, 2, 4, 6, 8]},
    **{f"pre_sleep_hr_trend_{n}h": "HIGH" for n in [1, 2, 4, 6, 8]},
    # Pre-sleep windows — stress
    **{f"pre_sleep_stress_avg_{n}h": "HIGH" for n in [1, 2, 4, 6, 8]},
    **{f"pre_sleep_stress_max_{n}h": "MEDIUM" for n in [1, 2, 4, 6, 8]},
    **{f"pre_sleep_high_stress_min_{n}h": "HIGH" for n in [1, 2, 4, 6, 8]},
    # Pre-sleep windows — HRV proxy
    **{f"pre_sleep_rr_avg_{n}h": "MEDIUM" for n in [1, 2]},
    **{f"pre_sleep_rr_std_{n}h": "LOW" for n in [1, 2]},
    # Pre-sleep windows — activity
    **{f"pre_sleep_steps_{n}h": "HIGH" for n in [1, 2, 4, 8]},
    **{f"pre_sleep_active_cal_{n}h": "HIGH" for n in [1, 2, 4, 8]},
    # Sleep architecture
    "time_to_first_deep_min": "LOW",
    "time_to_first_rem_min": "LOW",
    "n_awakenings": "LOW",
    "longest_uninterrupted_sleep_h": "LOW",
}

# Features known to have partial coverage (< 100% of nights)
_PARTIAL_COVERAGE = {
    "time_to_first_deep_min",
    "time_to_first_rem_min",
    "n_awakenings",
    "longest_uninterrupted_sleep_h",
}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_QUALIFIER_ENCODE = {"POOR": 0, "FAIR": 1, "GOOD": 2, "EXCELLENT": 3}


def _time_str_to_hours(series: pd.Series) -> pd.Series:
    """Convert 'HH:MM:SS.f' duration strings to float hours."""
    def _parse(val):
        if pd.isna(val) or val == 0:
            return np.nan
        try:
            parts = str(val).split(":")
            h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
            return h + m / 60 + s / 3600
        except Exception:
            return np.nan
    return series.map(_parse)


def _streak_counter(bool_series: pd.Series) -> pd.Series:
    """Count consecutive True values up to and including the current row."""
    out = np.zeros(len(bool_series), dtype=int)
    count = 0
    for i, val in enumerate(bool_series):
        if val:
            count += 1
        else:
            count = 0
        out[i] = count
    return pd.Series(out, index=bool_series.index)


def _days_since_last_true(bool_series: pd.Series) -> pd.Series:
    """Number of days since the last True value (0 if today is True)."""
    out = np.full(len(bool_series), np.nan)
    last = np.nan
    for i, val in enumerate(bool_series):
        if val:
            last = i
        out[i] = (i - last) if not np.isnan(last) else np.nan
    return pd.Series(out, index=bool_series.index)


# ---------------------------------------------------------------------------
# Feature group builders
# ---------------------------------------------------------------------------

def _build_base(sleep: pd.DataFrame) -> pd.DataFrame:
    """Return sorted sleep DataFrame with target columns."""
    df = sleep.copy()
    df["day"] = pd.to_datetime(df["day"])
    df = df.sort_values("day").reset_index(drop=True)

    # Parse start/end times
    df["_start"] = pd.to_datetime(df["start"], errors="coerce")
    df["_end"] = pd.to_datetime(df["end"], errors="coerce")

    # Duration columns already in hours from load_sleep_data; re-compute if missing
    for col in ["total_sleep", "deep_sleep", "rem_sleep", "light_sleep", "awake"]:
        h_col = f"{col}_hours"
        if h_col not in df.columns:
            df[h_col] = _time_str_to_hours(df[col])

    return df


def _temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    df["weekday"] = df["day"].dt.day_name()
    df["is_weekend"] = df["day"].dt.dayofweek.isin([5, 6])
    df["month"] = df["day"].dt.month

    valid = df["_start"].notna()
    df["sleep_start_hour"] = np.nan
    df["sleep_start_minute"] = np.nan
    df.loc[valid, "sleep_start_hour"] = (
        df.loc[valid, "_start"].dt.hour + df.loc[valid, "_start"].dt.minute / 60
    )
    df.loc[valid, "sleep_start_minute"] = df.loc[valid, "_start"].dt.minute

    valid_end = df["_end"].notna()
    df["wake_hour"] = np.nan
    df.loc[valid_end, "wake_hour"] = (
        df.loc[valid_end, "_end"].dt.hour + df.loc[valid_end, "_end"].dt.minute / 60
    )

    df["time_in_bed_hours"] = np.nan
    both = valid & valid_end
    df.loc[both, "time_in_bed_hours"] = (
        (df.loc[both, "_end"] - df.loc[both, "_start"]).dt.total_seconds() / 3600
    )
    return df


def _lag_features(df: pd.DataFrame) -> pd.DataFrame:
    df["prev1_total_sleep"] = df["total_sleep_hours"].shift(1)
    df["prev1_score"] = df["score"].shift(1)
    df["prev1_rem_hours"] = df["rem_sleep_hours"].shift(1)
    df["prev1_deep_hours"] = df["deep_sleep_hours"].shift(1)
    df["prev1_qualifier_encoded"] = df["qualifier"].map(_QUALIFIER_ENCODE).shift(1)
    df["prev1_sleep_start_hour"] = df["sleep_start_hour"].shift(1)
    df["prev2_total_sleep"] = df["total_sleep_hours"].shift(2)
    df["prev3_total_sleep"] = df["total_sleep_hours"].shift(3)
    return df


def _rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    df["rolling_3d_sleep_avg"] = (
        df["total_sleep_hours"].shift(1).rolling(3, min_periods=1).mean()
    )
    df["rolling_7d_sleep_avg"] = (
        df["total_sleep_hours"].shift(1).rolling(7, min_periods=1).mean()
    )
    df["rolling_7d_score_avg"] = (
        df["score"].shift(1).rolling(7, min_periods=1).mean()
    )
    weekly_sum = df["total_sleep_hours"].shift(1).rolling(7, min_periods=1).sum()
    df["sleep_debt_7d"] = (7 * 7 - weekly_sum).clip(lower=0)
    return df


def _streak_features(df: pd.DataFrame, exercise_dates: set) -> pd.DataFrame:
    is_poor = (df["score"] < 60) | (df["qualifier"] == "POOR")
    is_good = (df["score"] >= 75) & (df["qualifier"].isin(["GOOD", "EXCELLENT"]))
    had_ex = df["day"].dt.normalize().isin(exercise_dates)
    no_ex = ~had_ex

    df["consecutive_poor_sleep"] = _streak_counter(is_poor.fillna(False))
    df["consecutive_good_sleep"] = _streak_counter(is_good.fillna(False))
    df["consecutive_exercise_days"] = _streak_counter(had_ex)
    df["consecutive_rest_days"] = _streak_counter(no_ex)
    df["days_since_last_good_sleep"] = _days_since_last_true(is_good.fillna(False))
    return df


def _bedtime_consistency(df: pd.DataFrame) -> pd.DataFrame:
    df["bedtime_consistency_7d"] = (
        df["sleep_start_hour"].shift(1).rolling(7, min_periods=3).std()
    )
    return df


def _exercise_features(df: pd.DataFrame, acts: pd.DataFrame) -> pd.DataFrame:
    """Merge per-day exercise aggregates onto df (keyed by day)."""
    if acts.empty:
        for col in [
            "had_exercise", "n_activities", "total_workout_duration_h",
            "latest_workout_end_hour", "hours_workout_to_sleep",
            "primary_sport", "vigorous_ratio", "training_load",
        ]:
            df[col] = np.nan
        return df

    # stop_time to hours
    acts = acts.copy()
    acts["stop_time"] = pd.to_datetime(acts["stop_time"], errors="coerce")
    acts["stop_hour"] = acts["stop_time"].dt.hour + acts["stop_time"].dt.minute / 60

    # HR zone times to minutes
    for z in range(1, 6):
        acts[f"hrz_{z}_min"] = _time_str_to_hours(acts[f"hrz_{z}_time"]) * 60

    # elapsed_time to hours if not already present
    if "elapsed_time_hours" not in acts.columns:
        acts["elapsed_time_hours"] = _time_str_to_hours(acts["elapsed_time"])

    # vigorous proxy: hrz_4 + hrz_5 minutes
    acts["vigorous_min"] = acts["hrz_4_min"].fillna(0) + acts["hrz_5_min"].fillna(0)

    # training_load: numeric, may need coercion
    acts["training_load_num"] = pd.to_numeric(acts["training_load"], errors="coerce")

    def _primary_sport(x):
        mode = x.mode()
        return mode.iloc[0] if len(mode) > 0 else np.nan

    daily = acts.groupby("date").agg(
        n_activities=("activity_id", "count"),
        total_workout_duration_h=("elapsed_time_hours", "sum"),
        latest_workout_end_hour=("stop_hour", "max"),
        primary_sport=("sport", _primary_sport),
        total_vigorous_min=("vigorous_min", "sum"),
        total_mod_min=("elapsed_time_hours", lambda x: (x * 60).sum()),
        training_load_day=("training_load_num", "sum"),
        hrz_high_intensity_min=("vigorous_min", "sum"),
    ).reset_index()

    daily["vigorous_ratio"] = daily["total_vigorous_min"] / (daily["total_mod_min"] + 1e-9)
    daily["had_exercise"] = True

    # rolling 7-day training load
    daily = daily.sort_values("date")
    daily["training_load_7d"] = daily["training_load_day"].rolling(7, min_periods=1).sum()

    # Merge
    df = df.merge(
        daily[["date", "had_exercise", "n_activities", "total_workout_duration_h",
               "latest_workout_end_hour", "primary_sport", "vigorous_ratio",
               "training_load_day", "training_load_7d", "hrz_high_intensity_min"]],
        left_on="day", right_on="date", how="left",
    )
    df = df.drop(columns=["date"], errors="ignore")
    df["had_exercise"] = df["had_exercise"].fillna(False)
    df["n_activities"] = df["n_activities"].fillna(0).astype(int)
    df = df.rename(columns={"training_load_day": "training_load"})

    # hours_workout_to_sleep: NaN on rest days
    valid = df["had_exercise"] & df["sleep_start_hour"].notna() & df["latest_workout_end_hour"].notna()
    df["hours_workout_to_sleep"] = np.nan
    df.loc[valid, "hours_workout_to_sleep"] = (
        df.loc[valid, "sleep_start_hour"] - df.loc[valid, "latest_workout_end_hour"]
    )
    # Handle cases where sleep_start is next day (e.g. 01:00 and workout ended at 21:00)
    # sleep_start_hour wraps (0-6 is actually after midnight), add 24 if negative
    neg = valid & (df["hours_workout_to_sleep"] < 0)
    df.loc[neg, "hours_workout_to_sleep"] += 24

    return df


def _bb_and_physio_features(df: pd.DataFrame, daily: pd.DataFrame, days_summary: pd.DataFrame) -> pd.DataFrame:
    daily = daily.copy()
    daily["day"] = pd.to_datetime(daily["day"])

    days_summary = days_summary.copy()
    days_summary["day"] = pd.to_datetime(days_summary["day"])

    # BB — load_sleep_data() already joins daily_summary, so these may already exist
    for col in ["bb_max", "bb_min", "bb_charged"]:
        if col in daily.columns and col not in df.columns:
            df = df.merge(daily[["day", col]], on="day", how="left")
    df["bb_range"] = pd.to_numeric(df.get("bb_max"), errors="coerce") - pd.to_numeric(df.get("bb_min"), errors="coerce")

    # Physiology from daily_summary
    for col in ["rhr", "rr_waking_avg"]:
        if col in daily.columns and col not in df.columns:
            df = df.merge(daily[["day", col]], on="day", how="left")

    # avg_spo2, avg_rr from sleep (already on df)

    # inactive_hr_avg from days_summary
    if "inactive_hr_avg" in days_summary.columns:
        df = df.merge(days_summary[["day", "inactive_hr_avg"]], on="day", how="left")

    # Intensity from daily_summary
    for col in ["moderate_activity_time", "vigorous_activity_time"]:
        h_col = col.replace("_time", "_h")
        if col in daily.columns:
            tmp = daily[["day", col]].copy()
            tmp[h_col] = _time_str_to_hours(tmp[col])
            df = df.merge(tmp[["day", h_col]], on="day", how="left")

    if "moderate_activity_h" in df.columns and "vigorous_activity_h" in df.columns:
        df["intensity_score"] = (
            df["moderate_activity_h"].fillna(0) + 2 * df["vigorous_activity_h"].fillna(0)
        )

    return df


# ---------------------------------------------------------------------------
# Pre-sleep monitoring windows
# ---------------------------------------------------------------------------

_WINDOWS = [1, 2, 4, 6, 8]
_WINDOWS_RR = [1, 2]
_WINDOWS_STEPS = [1, 2, 4, 8]


def _load_monitoring_table(table: str, db: str, ts_col: str, value_cols: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """Load a monitoring table, return (timestamps_ns, values_array) sorted."""
    cols = ", ".join([ts_col] + value_cols)
    df = _sql(f"SELECT {cols} FROM {table}", db)
    df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce")
    df = df.dropna(subset=[ts_col]).sort_values(ts_col).reset_index(drop=True)
    ts_ns = df[ts_col].values.astype("datetime64[ns]").astype("int64")  # nanoseconds
    vals = df[value_cols].values
    return ts_ns, vals


def _window_slice(ts_ns: np.ndarray, start_ns: int, end_ns: int):
    """Return slice indices [lo, hi) for timestamps in [start_ns, end_ns)."""
    lo = np.searchsorted(ts_ns, start_ns, side="left")
    hi = np.searchsorted(ts_ns, end_ns, side="right")
    return lo, hi


def _pre_sleep_hr(sleep_starts: pd.Series, hr_ts: np.ndarray, hr_vals: np.ndarray) -> pd.DataFrame:
    """Compute pre-sleep HR features for each window."""
    rows = []
    for ts in sleep_starts:
        row = {}
        if pd.isna(ts):
            for n in _WINDOWS:
                for suffix in ["avg", "min", "std", "trend", "n_readings"]:
                    row[f"pre_sleep_hr_{suffix}_{n}h"] = np.nan
            rows.append(row)
            continue

        end_ns = ts.value
        for n in _WINDOWS:
            start_ns = (ts - pd.Timedelta(hours=n)).value
            lo, hi = _window_slice(hr_ts, start_ns, end_ns)
            vals = hr_vals[lo:hi, 0].astype(float)
            vals = vals[~np.isnan(vals)]  # drop NaN sentinel values
            n_valid = len(vals)
            row[f"pre_sleep_hr_n_readings_{n}h"] = n_valid
            if n_valid == 0:
                row[f"pre_sleep_hr_avg_{n}h"] = np.nan
                row[f"pre_sleep_hr_min_{n}h"] = np.nan
                row[f"pre_sleep_hr_std_{n}h"] = np.nan
                row[f"pre_sleep_hr_trend_{n}h"] = np.nan
            else:
                row[f"pre_sleep_hr_avg_{n}h"] = float(np.mean(vals))
                row[f"pre_sleep_hr_min_{n}h"] = float(np.min(vals))
                row[f"pre_sleep_hr_std_{n}h"] = float(np.std(vals)) if n_valid > 1 else np.nan
                # Trend: second-half avg minus first-half avg (negative = HR dropping = relaxing)
                mid = n_valid // 2
                if mid > 0:
                    row[f"pre_sleep_hr_trend_{n}h"] = float(np.mean(vals[mid:]) - np.mean(vals[:mid]))
                else:
                    row[f"pre_sleep_hr_trend_{n}h"] = np.nan
        rows.append(row)
    return pd.DataFrame(rows, index=sleep_starts.index)


def _pre_sleep_stress(sleep_starts: pd.Series, st_ts: np.ndarray, st_vals: np.ndarray) -> pd.DataFrame:
    rows = []
    for ts in sleep_starts:
        row = {}
        if pd.isna(ts):
            for n in _WINDOWS:
                row[f"pre_sleep_stress_avg_{n}h"] = np.nan
                row[f"pre_sleep_stress_max_{n}h"] = np.nan
                row[f"pre_sleep_high_stress_min_{n}h"] = np.nan
            rows.append(row)
            continue

        end_ns = ts.value
        for n in _WINDOWS:
            start_ns = (ts - pd.Timedelta(hours=n)).value
            lo, hi = _window_slice(st_ts, start_ns, end_ns)
            vals = st_vals[lo:hi, 0].astype(float)
            vals = vals[~np.isnan(vals)]
            if len(vals) == 0:
                row[f"pre_sleep_stress_avg_{n}h"] = np.nan
                row[f"pre_sleep_stress_max_{n}h"] = np.nan
                row[f"pre_sleep_high_stress_min_{n}h"] = np.nan
            else:
                row[f"pre_sleep_stress_avg_{n}h"] = float(np.mean(vals))
                row[f"pre_sleep_stress_max_{n}h"] = float(np.max(vals))
                row[f"pre_sleep_high_stress_min_{n}h"] = float(np.sum(vals > 50))
        rows.append(row)
    return pd.DataFrame(rows, index=sleep_starts.index)


def _pre_sleep_rr(sleep_starts: pd.Series, rr_ts: np.ndarray, rr_vals: np.ndarray) -> pd.DataFrame:
    rows = []
    for ts in sleep_starts:
        row = {}
        if pd.isna(ts):
            for n in _WINDOWS_RR:
                row[f"pre_sleep_rr_avg_{n}h"] = np.nan
                row[f"pre_sleep_rr_std_{n}h"] = np.nan
            rows.append(row)
            continue

        end_ns = ts.value
        for n in _WINDOWS_RR:
            start_ns = (ts - pd.Timedelta(hours=n)).value
            lo, hi = _window_slice(rr_ts, start_ns, end_ns)
            vals = rr_vals[lo:hi, 0].astype(float)
            vals = vals[~np.isnan(vals)]
            if len(vals) == 0:
                row[f"pre_sleep_rr_avg_{n}h"] = np.nan
                row[f"pre_sleep_rr_std_{n}h"] = np.nan
            else:
                row[f"pre_sleep_rr_avg_{n}h"] = float(np.mean(vals))
                row[f"pre_sleep_rr_std_{n}h"] = float(np.std(vals)) if len(vals) > 1 else np.nan
        rows.append(row)
    return pd.DataFrame(rows, index=sleep_starts.index)


def _pre_sleep_activity(sleep_starts: pd.Series, mon_ts: np.ndarray, mon_vals: np.ndarray) -> pd.DataFrame:
    """mon_vals columns: [steps, active_calories]"""
    rows = []
    for ts in sleep_starts:
        row = {}
        if pd.isna(ts):
            for n in _WINDOWS_STEPS:
                row[f"pre_sleep_steps_{n}h"] = np.nan
                row[f"pre_sleep_active_cal_{n}h"] = np.nan
            rows.append(row)
            continue

        end_ns = ts.value
        for n in _WINDOWS_STEPS:
            start_ns = (ts - pd.Timedelta(hours=n)).value
            lo, hi = _window_slice(mon_ts, start_ns, end_ns)
            if lo >= hi:
                row[f"pre_sleep_steps_{n}h"] = np.nan
                row[f"pre_sleep_active_cal_{n}h"] = np.nan
            else:
                row[f"pre_sleep_steps_{n}h"] = float(np.nansum(mon_vals[lo:hi, 0]))
                row[f"pre_sleep_active_cal_{n}h"] = float(np.nansum(mon_vals[lo:hi, 1]))
        rows.append(row)
    return pd.DataFrame(rows, index=sleep_starts.index)


def _build_pre_sleep_features(df: pd.DataFrame) -> pd.DataFrame:
    """Load all monitoring tables and compute pre-sleep window features."""
    print("Loading monitoring_hr...", flush=True)
    hr_ts, hr_vals = _load_monitoring_table("monitoring_hr", "monitoring", "timestamp", ["heart_rate"])

    print("Loading stress...", flush=True)
    st_ts, st_vals = _load_monitoring_table("stress", "garmin", "timestamp", ["stress"])

    print("Loading monitoring_rr...", flush=True)
    rr_ts, rr_vals = _load_monitoring_table("monitoring_rr", "monitoring", "timestamp", ["rr"])

    print("Loading monitoring (steps/calories)...", flush=True)
    mon_ts, mon_vals = _load_monitoring_table(
        "monitoring", "monitoring", "timestamp", ["steps", "active_calories"]
    )

    sleep_starts = df["_start"]

    print("Computing pre-sleep HR features...", flush=True)
    hr_feats = _pre_sleep_hr(sleep_starts, hr_ts, hr_vals)

    print("Computing pre-sleep stress features...", flush=True)
    st_feats = _pre_sleep_stress(sleep_starts, st_ts, st_vals)

    print("Computing pre-sleep RR features...", flush=True)
    rr_feats = _pre_sleep_rr(sleep_starts, rr_ts, rr_vals)

    print("Computing pre-sleep activity features...", flush=True)
    act_feats = _pre_sleep_activity(sleep_starts, mon_ts, mon_vals)

    return pd.concat([df, hr_feats, st_feats, rr_feats, act_feats], axis=1)


# ---------------------------------------------------------------------------
# Sleep architecture from sleep_events
# ---------------------------------------------------------------------------

def _sleep_architecture(df: pd.DataFrame) -> pd.DataFrame:
    events = _sql("SELECT timestamp, event, duration FROM sleep_events", "garmin")
    if events.empty:
        for col in ["time_to_first_deep_min", "time_to_first_rem_min",
                    "n_awakenings", "longest_uninterrupted_sleep_h"]:
            df[col] = np.nan
        return df

    events["timestamp"] = pd.to_datetime(events["timestamp"])
    events["date"] = events["timestamp"].dt.normalize()
    events["duration_h"] = _time_str_to_hours(events["duration"])

    arch_rows = []
    for date, grp in events.groupby("date"):
        grp = grp.sort_values("timestamp")
        # Find sleep start for that night from df
        night_row = df[df["day"] == date]
        if night_row.empty or pd.isna(night_row["_start"].iloc[0]):
            sleep_start = grp["timestamp"].iloc[0]
        else:
            sleep_start = night_row["_start"].iloc[0]

        def _minutes_from_start(ts):
            return (ts - sleep_start).total_seconds() / 60

        first_deep = grp[grp["event"] == "deep_sleep"]["timestamp"].min()
        first_rem = grp[grp["event"] == "rem_sleep"]["timestamp"].min()
        awakenings = (grp["event"] == "awake").sum()

        # Longest uninterrupted sleep (excluding awake events)
        sleep_events_only = grp[grp["event"] != "awake"]["duration_h"]
        longest = sleep_events_only.max() if len(sleep_events_only) > 0 else np.nan

        arch_rows.append({
            "day": date,
            "time_to_first_deep_min": _minutes_from_start(first_deep) if pd.notna(first_deep) else np.nan,
            "time_to_first_rem_min": _minutes_from_start(first_rem) if pd.notna(first_rem) else np.nan,
            "n_awakenings": int(awakenings),
            "longest_uninterrupted_sleep_h": longest,
        })

    arch_df = pd.DataFrame(arch_rows)
    arch_df["day"] = pd.to_datetime(arch_df["day"])
    df = df.merge(arch_df, on="day", how="left")
    return df


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_sleep_features(verbose: bool = True) -> pd.DataFrame:
    """Build and return the enriched per-night feature DataFrame.

    Parameters
    ----------
    verbose : bool
        Print progress messages while loading monitoring tables.

    Returns
    -------
    pd.DataFrame
        One row per night, indexed 0..N-1, with `day` as a column.
    """
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    from garmin_utils import load_sleep_data, load_activities, _read_sql as _gu_sql
    from customized.data_preproccess_customizers import filter_nighttime_activities

    if verbose:
        print("Loading sleep data...", flush=True)
    sleep = load_sleep_data()

    df = _build_base(sleep)
    df = _temporal_features(df)
    df = _lag_features(df)
    df = _rolling_features(df)

    # Exercise dates for streaks
    if verbose:
        print("Loading activities...", flush=True)
    acts_raw = load_activities(group_rare=False)
    acts = filter_nighttime_activities(acts_raw)
    exercise_dates = set(pd.to_datetime(acts["date"]))

    df = _streak_features(df, exercise_dates)
    df = _bedtime_consistency(df)

    if verbose:
        print("Building exercise features...", flush=True)
    df = _exercise_features(df, acts)

    # Body battery + physiology
    if verbose:
        print("Loading daily summary and days summary...", flush=True)
    daily = _sql("SELECT * FROM daily_summary", "garmin")
    days_sum = _sql("SELECT * FROM days_summary", "summary")
    df = _bb_and_physio_features(df, daily, days_sum)

    # Pre-sleep monitoring windows
    df = _build_pre_sleep_features(df)

    # Sleep architecture
    if verbose:
        print("Building sleep architecture features...", flush=True)
    df = _sleep_architecture(df)

    # Drop internal columns
    df = df.drop(columns=["_start", "_end", "start", "end"], errors="ignore")

    if verbose:
        print(f"Done. Shape: {df.shape}", flush=True)

    return df.reset_index(drop=True)


def report_feature_completeness(df: pd.DataFrame) -> pd.DataFrame:
    """Return a completeness report DataFrame for all columns.

    Columns: feature, non_null, total, pct_complete, partial_coverage, controllability
    """
    rows = []
    total = len(df)
    for col in df.columns:
        non_null = df[col].notna().sum()
        rows.append({
            "feature": col,
            "non_null": non_null,
            "total": total,
            "pct_complete": round(non_null / total * 100, 1),
            "partial_coverage": col in _PARTIAL_COVERAGE,
            "controllability": CONTROLLABILITY.get(col, "—"),
        })
    return pd.DataFrame(rows).sort_values("pct_complete", ascending=True).reset_index(drop=True)
