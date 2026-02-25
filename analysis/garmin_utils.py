"""Reusable utilities for loading Garmin SQLite data into pandas DataFrames,
common transformations, statistical helpers, and shared plotting functions."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_DIR = _PROJECT_ROOT / "HealthData" / "DBs"

DB_PATHS = {
    "garmin": DB_DIR / "garmin.db",
    "activities": DB_DIR / "garmin_activities.db",
    "monitoring": DB_DIR / "garmin_monitoring.db",
    "summary": DB_DIR / "garmin_summary.db",
}


def get_db_path(name: str) -> Path:
    """Return the path to a Garmin database by short name.

    Parameters
    ----------
    name : str
        One of 'garmin', 'activities', 'monitoring', 'summary'.

    Raises
    ------
    FileNotFoundError
        If the database file does not exist.
    """
    path = DB_PATHS.get(name)
    if path is None:
        raise ValueError(f"Unknown database name '{name}'. Choose from: {list(DB_PATHS)}")
    if not path.exists():
        raise FileNotFoundError(f"Database not found: {path}")
    return path


def _read_sql(query: str, db_name: str, **kwargs) -> pd.DataFrame:
    """Execute *query* against the named database and return a DataFrame."""
    import sqlite3

    path = get_db_path(db_name)
    with sqlite3.connect(str(path)) as conn:
        return pd.read_sql_query(query, conn, **kwargs)


# ---------------------------------------------------------------------------
# Time parsing helpers
# ---------------------------------------------------------------------------

def _time_str_to_hours(series: pd.Series) -> pd.Series:
    """Convert a column of 'HH:MM:SS.ffffff' strings to float hours."""
    return pd.to_timedelta(series, errors="coerce").dt.total_seconds() / 3600


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_sleep_data() -> pd.DataFrame:
    """Load sleep records joined with daily_summary and resting_hr.

    Returns a DataFrame with one row per sleep day, columns prefixed where
    needed to avoid ambiguity.  Duration columns are converted to float hours.
    """
    sleep = _read_sql("SELECT * FROM sleep", "garmin")
    daily = _read_sql("SELECT * FROM daily_summary", "garmin")
    rhr = _read_sql("SELECT * FROM resting_hr", "garmin")

    # Parse dates
    sleep["day"] = pd.to_datetime(sleep["day"])
    daily["day"] = pd.to_datetime(daily["day"])
    rhr["day"] = pd.to_datetime(rhr["day"])

    # Convert sleep duration columns to hours
    for col in ["total_sleep", "deep_sleep", "light_sleep", "rem_sleep", "awake"]:
        sleep[f"{col}_hours"] = _time_str_to_hours(sleep[col])

    # Convert daily time columns to hours
    for col in ["moderate_activity_time", "vigorous_activity_time", "intensity_time_goal"]:
        if col in daily.columns:
            daily[f"{col}_hours"] = _time_str_to_hours(daily[col])

    # Rename resting_hr column before merge
    rhr = rhr.rename(columns={"resting_heart_rate": "rhr_daily"})

    # Merge: sleep LEFT JOIN daily_summary ON day
    df = sleep.merge(daily, on="day", how="left", suffixes=("", "_daily"))
    # Merge with resting_hr
    df = df.merge(rhr, on="day", how="left")

    # Sort by date
    df = df.sort_values("day").reset_index(drop=True)

    return df


def load_activities(group_rare: bool = False, min_count: int = 10) -> pd.DataFrame:
    """Load activities with a time_bucket column and date for joining with sleep.

    Parameters
    ----------
    group_rare : bool
        If True, sport types with fewer than *min_count* sessions are relabeled 'Other'.
    min_count : int
        Minimum sessions to keep a sport label (default 10).
    """
    df = _read_sql("SELECT * FROM activities", "activities")

    # Parse start_time
    df["start_time"] = pd.to_datetime(df["start_time"])
    df["date"] = df["start_time"].dt.date
    df["date"] = pd.to_datetime(df["date"])
    df["hour"] = df["start_time"].dt.hour

    # Time bucket classification
    conditions = [
        df["hour"] < 12,
        (df["hour"] >= 12) & (df["hour"] < 17),
        (df["hour"] >= 17) & (df["hour"] < 20),
        df["hour"] >= 20,
    ]
    labels = ["Morning", "Afternoon", "Evening", "Late Night"]
    df["time_bucket"] = np.select(conditions, labels, default="Unknown")

    # Convert elapsed_time to hours
    df["elapsed_time_hours"] = _time_str_to_hours(df["elapsed_time"])

    # Group rare sport types
    if group_rare:
        counts = df["sport"].value_counts()
        rare = counts[counts < min_count].index
        df["sport_grouped"] = df["sport"].where(~df["sport"].isin(rare), "Other")
    else:
        df["sport_grouped"] = df["sport"]

    return df


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def classify_sleep(df: pd.DataFrame) -> pd.DataFrame:
    """Add sleep deprivation classification columns to a sleep DataFrame.

    Adds:
    - ``is_deprived`` (bool): True if sleep score < 50 or total_sleep_hours < 4.5.
    - ``sleep_quality`` (str): 'Deprived' or 'Adequate'.
    """
    df = df.copy()
    df["is_deprived"] = (
        (df["score"] < 50)
        | (df["total_sleep_hours"] < 4.5)
    )
    df["sleep_quality"] = df["is_deprived"].map({True: "Deprived", False: "Adequate"})
    return df


# ---------------------------------------------------------------------------
# Data quality
# ---------------------------------------------------------------------------

def report_completeness(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    """Return a summary of data completeness for each column.

    Parameters
    ----------
    columns : list[str] or None
        Columns to check. If None, checks all columns.

    Returns
    -------
    DataFrame with columns: total, non_null, null, pct_complete, reliable
    """
    if columns is None:
        columns = list(df.columns)
    records = []
    for col in columns:
        total = len(df)
        non_null = df[col].notna().sum()
        records.append({
            "column": col,
            "total": total,
            "non_null": int(non_null),
            "null": int(total - non_null),
            "pct_complete": round(non_null / total * 100, 1) if total else 0,
        })
    result = pd.DataFrame(records)
    result["reliable"] = result["pct_complete"] >= 80
    return result


# ---------------------------------------------------------------------------
# Statistical helpers
# ---------------------------------------------------------------------------

def compute_correlations(
    df: pd.DataFrame,
    target_col: str,
    feature_cols: list[str],
) -> pd.DataFrame:
    """Compute Spearman correlations between *target_col* and each feature.

    Returns a DataFrame sorted by absolute correlation, with columns:
    feature, correlation, p_value, significant (p < 0.05).
    """
    records = []
    for col in feature_cols:
        mask = df[[target_col, col]].dropna()
        if len(mask) < 3:
            continue
        corr, pval = stats.spearmanr(mask[target_col], mask[col])
        records.append({
            "feature": col,
            "correlation": round(corr, 4),
            "p_value": round(pval, 6),
            "significant": pval < 0.05,
        })
    result = pd.DataFrame(records)
    if not result.empty:
        result = result.sort_values("correlation", key=abs, ascending=False).reset_index(drop=True)
    return result


def compare_groups(
    df: pd.DataFrame,
    group_col: str,
    metric_col: str,
) -> dict:
    """Run Mann-Whitney U test comparing two groups on a metric.

    Returns dict with keys: statistic, p_value, effect_size (rank-biserial),
    group_stats (mean/median per group), n_per_group.
    """
    groups = df[group_col].dropna().unique()
    if len(groups) != 2:
        raise ValueError(f"Expected 2 groups in '{group_col}', got {len(groups)}: {groups}")

    a = df.loc[df[group_col] == groups[0], metric_col].dropna()
    b = df.loc[df[group_col] == groups[1], metric_col].dropna()

    if len(a) < 2 or len(b) < 2:
        return {"error": "Insufficient data for comparison"}

    stat, pval = stats.mannwhitneyu(a, b, alternative="two-sided")
    # Rank-biserial correlation as effect size
    n1, n2 = len(a), len(b)
    effect_size = 1 - (2 * stat) / (n1 * n2)

    return {
        "statistic": round(stat, 2),
        "p_value": round(pval, 6),
        "effect_size": round(effect_size, 4),
        "group_stats": {
            str(groups[0]): {"mean": round(a.mean(), 2), "median": round(a.median(), 2), "n": n1},
            str(groups[1]): {"mean": round(b.mean(), 2), "median": round(b.median(), 2), "n": n2},
        },
    }


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def setup_style():
    """Apply consistent seaborn theme for all plots."""
    sns.set_theme(style="whitegrid", font_scale=1.1)
    plt.rcParams.update({
        "figure.figsize": (12, 6),
        "axes.titlesize": 16,
        "axes.labelsize": 13,
        "xtick.labelsize": 11,
        "ytick.labelsize": 11,
    })


def plot_correlation_heatmap(
    df: pd.DataFrame,
    columns: list[str],
    title: str = "Spearman Correlation Heatmap",
    figsize: tuple = (12, 10),
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Plot an annotated Spearman correlation heatmap.

    Returns (corr_matrix, p_value_matrix).
    """
    subset = df[columns].dropna()
    n = len(columns)
    corr_matrix = pd.DataFrame(np.zeros((n, n)), index=columns, columns=columns)
    p_matrix = pd.DataFrame(np.ones((n, n)), index=columns, columns=columns)

    for i, c1 in enumerate(columns):
        for j, c2 in enumerate(columns):
            if i == j:
                corr_matrix.iloc[i, j] = 1.0
                p_matrix.iloc[i, j] = 0.0
            elif i < j:
                mask = subset[[c1, c2]].dropna()
                if len(mask) >= 3:
                    c, p = stats.spearmanr(mask[c1], mask[c2])
                    corr_matrix.iloc[i, j] = c
                    corr_matrix.iloc[j, i] = c
                    p_matrix.iloc[i, j] = p
                    p_matrix.iloc[j, i] = p

    fig, ax = plt.subplots(figsize=figsize)
    mask_upper = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
    sns.heatmap(
        corr_matrix,
        mask=mask_upper,
        annot=True,
        fmt=".2f",
        cmap="RdBu_r",
        center=0,
        vmin=-1,
        vmax=1,
        square=True,
        ax=ax,
    )
    ax.set_title(title)
    plt.tight_layout()
    plt.show()

    return corr_matrix, p_matrix


def plot_group_comparison(
    df: pd.DataFrame,
    group_col: str,
    metric_cols: list[str],
    title_prefix: str = "",
    figsize_per_plot: tuple = (6, 4),
):
    """Produce violin plots comparing metric distributions across groups,
    annotated with Mann-Whitney U p-values."""
    n = len(metric_cols)
    cols = min(n, 3)
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(figsize_per_plot[0] * cols, figsize_per_plot[1] * rows))
    if n == 1:
        axes = np.array([axes])
    axes = axes.flatten()

    for i, col in enumerate(metric_cols):
        ax = axes[i]
        data = df[[group_col, col]].dropna()
        sns.violinplot(data=data, x=group_col, y=col, ax=ax, inner="box")

        # Compute p-value
        try:
            result = compare_groups(data, group_col, col)
            p = result["p_value"]
            sig = "*" if p < 0.05 else ""
            ax.set_title(f"{title_prefix}{col}\n(p={p:.4f}{sig})")
        except (ValueError, KeyError):
            ax.set_title(f"{title_prefix}{col}")
        ax.set_xlabel("")

    # Hide unused axes
    for j in range(i + 1, len(axes)):
        axes[j].set_visible(False)

    plt.tight_layout()
    plt.show()


def plot_time_series(
    df: pd.DataFrame,
    date_col: str,
    value_col: str,
    rolling_windows: list[int] | None = None,
    title: str = "",
    ylabel: str = "",
    figsize: tuple = (14, 5),
):
    """Plot raw values with optional rolling average overlays."""
    if rolling_windows is None:
        rolling_windows = [7, 30]

    fig, ax = plt.subplots(figsize=figsize)
    data = df[[date_col, value_col]].dropna().sort_values(date_col)

    ax.plot(data[date_col], data[value_col], alpha=0.3, linewidth=0.8, label="Daily")

    for w in rolling_windows:
        rolled = data[value_col].rolling(w, min_periods=1).mean()
        ax.plot(data[date_col], rolled, linewidth=2, label=f"{w}-day avg")

    ax.set_title(title or f"{value_col} Over Time")
    ax.set_ylabel(ylabel or value_col)
    ax.set_xlabel("Date")
    ax.legend()
    plt.tight_layout()
    plt.show()
