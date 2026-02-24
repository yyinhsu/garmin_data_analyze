## Context

Four Garmin SQLite databases provide the raw data. The existing `garmin_utils.py` only surfaces daily summaries and activity lists. The new feature set requires:
1. Per-minute monitoring data (monitoring_hr: 658K rows, stress: 817K rows, monitoring_rr: 558K rows) queried via time windows anchored to each night's `sleep.start`
2. Activity-level data including HR zones and training load (garmin_activities.db)
3. Days-level summary with `inactive_hr_avg` (garmin_summary.db)
4. Sleep stage timeline (garmin.db sleep_events, 144/601 nights)

Sleep start time (`sleep.start`) is populated for 568/601 nights and anchors all pre-sleep window computations.

## Goals / Non-Goals

**Goals:**
- Build a 601-row × 80+ column feature DataFrame, one row per night
- Compute pre-sleep monitoring features for windows N = 1, 2, 4, 6, 8 hours before sleep start
- Two analysis targets: `score` (sleep quality) and `bb_charged` (sleep recovery)
- Interventional framing: rank controllable features by effect size
- Encapsulate all feature engineering in `sleep_feature_builder.py` (importable, not notebook-only)

**Non-Goals:**
- Predictive model / ML pipeline (this is exploratory correlation + effect size analysis)
- Menstrual cycle features (deferred)
- Modifying `garmin_utils.py` or `sleep_analysis.ipynb`
- Real-time or streaming data

## Decisions

### D1: Pre-sleep monitoring — load-all + searchsorted, not per-query SQL

**Decision**: Load each monitoring table once into memory as a sorted DataFrame. For each of 601 nights, use `numpy.searchsorted` to slice the time window. Compute aggregates on the slice.

**Rationale**: 601 × 8 windows × 3 tables = 14,424 slices. Each slice is ~300 rows (for 2h window). searchsorted is O(log N) per lookup → total ~30ms. Alternative (SQL per-row `BETWEEN` queries) would require 14K round-trips and be 10-100× slower in SQLite.

**Alternative**: Pre-aggregate into 15-min buckets, then join — rejected because window boundaries (anchored to exact sleep.start) would be imprecise.

---

### D2: Feature engineering in `sleep_feature_builder.py`, not inline in notebook

**Decision**: All feature construction logic lives in `analysis/customized/sleep_feature_builder.py`. The notebook calls `build_sleep_features()` → gets a ready DataFrame.

**Rationale**: Keeps the notebook focused on analysis. Feature builder can be reused, tested independently, and iterated without re-running all notebook cells. Consistent with the existing `data_preproccess_customizers.py` pattern.

---

### D3: Pre-sleep windows are cumulative (0 → N hours before sleep), not segmented

**Decision**: `pre_sleep_hr_avg_2h` = avg HR in the 2 hours immediately before sleep. `pre_sleep_hr_avg_4h` = avg HR in the 4 hours immediately before sleep. Windows overlap and nest.

**Rationale**: Cumulative windows capture the "recent state" at bedtime. Segmented windows (e.g., 2h-4h ago vs 0h-2h) would require twice as many features and complicate interpretation. Effect size differences across N will reveal the relevant time horizon naturally.

---

### D4: sleep_events features included with NaN for uncovered nights

**Decision**: Build `time_to_first_deep_min`, `time_to_first_rem_min`, `n_awakenings` for all 601 rows; rows before 2025-10-01 will be NaN.

**Rationale**: 144 non-null samples is sufficient for correlation analysis. Features are flagged as `partial_coverage` in the completeness report. Alternative (drop entirely) loses potentially informative signals for the post-Oct 2025 period.

---

### D5: `hours_workout_to_sleep` = NaN on rest days, not 0

**Decision**: On days with no exercise, `hours_workout_to_sleep` is NaN, not 0. A boolean `had_exercise` flag is separate.

**Rationale**: 0 would incorrectly imply "worked out right before sleep". NaN + had_exercise=False is semantically correct and avoids corrupting correlations.

---

### D6: Controllability tags on features (metadata, not columns)

**Decision**: Feature controllability (HIGH/MEDIUM/LOW) is documented in a dict in the feature builder, not added as extra columns. The notebook uses this dict to filter for the interventional analysis section.

**Rationale**: Keeps the DataFrame clean for correlation analysis; controllability is an analytical lens, not a data property.

## Risks / Trade-offs

- **Risk**: `sleep.start` is NULL for 33/601 nights → pre-sleep features will be NaN for those nights. Mitigation: document in completeness report; 568 valid nights is sufficient.
- **Risk**: monitoring_hr has gaps (watch removed, charging) → some windows will have sparse data. Mitigation: record `pre_sleep_hr_n_readings_Nh` as a coverage indicator alongside each aggregate.
- **Risk**: `bb_charged` is partially derived from sleep quality (circular) → use as secondary target, interpret with caution. Mitigation: note clearly in notebook.
- **Trade-off**: ~80 features on 601 rows → some correlations will be spurious. Mitigation: use Spearman (rank-based, robust to outliers); report effect sizes alongside p-values; Bonferroni or FDR correction in analysis.
