"""
Unit tests for analysis/customized/sleep_feature_builder.py
These are smoke tests — they verify the feature matrix is structurally sound
without requiring any mocked data (the real DBs are present locally).
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

# Make the analysis directory importable
sys.path.insert(0, str(Path(__file__).parent.parent / "analysis"))

from customized.sleep_feature_builder import CONTROLLABILITY, build_sleep_features  # noqa: E402

REQUIRED_COLUMNS = [
    "day",
    "score",
    "total_sleep_hours",
    "deep_sleep_hours",
    "rem_sleep_hours",
    "sleep_start_hour",
    "had_exercise",
    "sport_category",
    "is_late_bedtime",
    "same_day_vigorous_ratio",
    "steps",
    "pre_sleep_stress_avg_4h",
    "time_to_first_deep_min",
]


@pytest.fixture(scope="module")
def df():
    return build_sleep_features()


class TestSchema:
    def test_returns_dataframe(self, df):
        assert isinstance(df, pd.DataFrame)

    def test_minimum_rows(self, df):
        assert len(df) >= 100, f"Expected ≥100 rows, got {len(df)}"

    def test_required_columns_present(self, df):
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        assert not missing, f"Missing columns: {missing}"

    def test_no_duplicate_dates(self, df):
        dupes = df["day"].duplicated().sum()
        assert dupes == 0, f"{dupes} duplicate dates found"

    def test_dates_are_sorted(self, df):
        assert df["day"].is_monotonic_increasing, "Rows are not sorted by date"


class TestScoreColumn:
    def test_score_range(self, df):
        valid = df["score"].dropna()
        assert valid.between(0, 100).all(), "score values outside [0, 100]"

    def test_score_non_empty(self, df):
        assert df["score"].notna().sum() > 50, "Too few non-null scores"


class TestSleepHours:
    def test_total_sleep_non_negative(self, df):
        valid = df["total_sleep_hours"].dropna()
        assert (valid >= 0).all()

    def test_total_sleep_reasonable_max(self, df):
        valid = df["total_sleep_hours"].dropna()
        assert valid.max() <= 18, f"Unrealistic sleep duration: {valid.max():.1f}h"


class TestExerciseFeatures:
    def test_sport_category_valid_values(self, df):
        valid_cats = {"cardio", "strength", "mixed", "other"}
        actual = set(df["sport_category"].dropna().unique())
        assert actual.issubset(valid_cats), f"Unexpected sport categories: {actual - valid_cats}"

    def test_is_late_bedtime_is_bool(self, df):
        non_null = df["is_late_bedtime"].dropna()
        assert non_null.dtype == bool or set(non_null.unique()).issubset({True, False})

    def test_vigorous_ratio_range(self, df):
        valid = df["same_day_vigorous_ratio"].dropna()
        assert valid.between(0, 1).all(), "vigorous_ratio outside [0, 1]"


class TestControllability:
    def test_controllability_is_dict(self):
        assert isinstance(CONTROLLABILITY, dict)

    def test_known_features_tagged(self):
        required_tagged = ["is_late_bedtime", "sport_category", "same_day_vigorous_ratio"]
        for feat in required_tagged:
            assert feat in CONTROLLABILITY, f"{feat} missing from CONTROLLABILITY"

    def test_valid_levels(self):
        valid_levels = {"HIGH", "MEDIUM", "LOW", "NONE"}
        bad = {k: v for k, v in CONTROLLABILITY.items() if v not in valid_levels}
        assert not bad, f"Invalid controllability levels: {bad}"
