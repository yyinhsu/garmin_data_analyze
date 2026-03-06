## Why

The existing sleep analyses reveal strong correlations but don't explain the mechanisms. Five causal hypotheses have emerged from the data that are worth testing directly: (1) a bedtime cliff-edge around 3 AM, (2) exercise intensity (not sport label) as the true driver of sleep benefit, (3) pre-sleep stress propagating into late bedtimes, (4) time-to-first-deep-sleep cascading into next-night quality, and (5) cardio vs strength workout type as a sleep differentiator. Additionally, two lifestyle signals — calories consumed and daily walking steps — are untested against sleep outcomes.

## What Changes

- **New notebook** `analysis/sleep_causal_investigation.ipynb` with 6 targeted investigation sections
- **New features in `sleep_feature_builder.py`**: `calories_consumed` and `steps` (daily walking, from daily_summary) added to the feature matrix
- **New helper column** `sport_category` on activity features: classifies sport into `cardio`, `strength`, `mixed`, `other` for the cardio vs strength investigation
- **New helper column** `is_late_bedtime` (bool): `sleep_start_hour >= 3.0` for bedtime threshold analysis

## Capabilities

### New Capabilities
- `sleep-causal-investigation`: Six-section notebook investigating causal hypotheses: bedtime threshold, intensity vs sport label, stress→bedtime feedback, deep-sleep cascading, cardio vs strength, and calories/steps effects

### Modified Capabilities
- `sleep-feature-engineering`: Add `calories_consumed`, `steps` (daily walking), `sport_category`, `is_late_bedtime` features to `build_sleep_features()`

## Impact

- `analysis/customized/sleep_feature_builder.py` — add 4 new feature columns
- `analysis/sleep_causal_investigation.ipynb` — new notebook (create)
- `analysis/customized/data_preproccess_customizers.py` — no changes needed
