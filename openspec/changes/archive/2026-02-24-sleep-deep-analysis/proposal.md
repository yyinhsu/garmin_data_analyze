## Why

The existing `sleep_analysis.ipynb` identified broad correlations (REM, stress, body battery) but used only a small set of same-day summary metrics. A deeper interventional analysis requires richer feature engineering — including pre-sleep physiological windows, lagged sleep history, exercise timing precision, and sleep architecture — to identify which **actionable behaviors** most predictably improve sleep quality.

## What Changes

- **New notebook**: `analysis/sleep_deep_analysis.ipynb` — full feature-engineered dataset with ~80+ features, dual-target analysis (sleep score + bb_charged), and interventional framing
- **New feature builder**: `analysis/customized/sleep_feature_builder.py` — reusable module that constructs the enriched feature DataFrame from all Garmin tables
- No changes to existing `sleep_analysis.ipynb` or `garmin_utils.py`

## Capabilities

### New Capabilities
- `sleep-feature-engineering`: Builds enriched per-night feature set from all Garmin SQLite tables, including temporal features, lag/rolling features, streak counters, exercise features, pre-sleep monitoring windows (1/2/4/6/8h for HR, stress, HRV proxy, activity), body battery features, and sleep architecture from sleep_events
- `sleep-interventional-analysis`: Jupyter notebook that loads the engineered features, runs dual-target analysis (sleep score + bb_charged), and ranks actionable (controllable) variables by effect size

### Modified Capabilities

_(none)_

## Impact

- **New**: `analysis/sleep_deep_analysis.ipynb`
- **New**: `analysis/customized/sleep_feature_builder.py`
- **New directory dependency**: reads from garmin.db, garmin_activities.db, garmin_monitoring.db, garmin_summary.db — all via existing DB_PATHS
- **Filter dependency**: `filter_nighttime_activities` from `data_preproccess_customizers.py` applied before exercise features are built
- No breaking changes to existing files
