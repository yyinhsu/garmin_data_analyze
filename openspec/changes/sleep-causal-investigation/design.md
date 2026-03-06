## Context

The sleep_feature_builder.py already provides a 601×146 feature matrix. The sleep_deep_analysis.ipynb identified five mechanistic hypotheses but did not test them directly. This change builds a dedicated investigation notebook and extends the feature matrix with two new lifestyle signals (calories_consumed, steps) and two classifier columns (sport_category, is_late_bedtime).

Current state:
- `sleep_feature_builder.py` builds features from daily_summary, activities, monitoring tables
- `sleep_analysis.ipynb` covers correlation and group comparison
- `sleep_deep_analysis.ipynb` covers interventional effect sizes and pre-sleep window analysis
- No notebook yet tests bedtime thresholds, intensity vs sport label, or stress propagation

## Goals / Non-Goals

**Goals:**
- Test bedtime cliff-edge hypothesis (is there a score drop-off at/after 3 AM bedtime?)
- Disentangle exercise intensity from sport label as the sleep benefit driver
- Test stress→late bedtime feedback loop (does evening stress predict going to bed later?)
- Test time-to-first-deep-sleep cascading to next-night quality (144-night window)
- Compare cardio vs strength workouts on sleep score and total sleep hours
- Add calories_consumed and steps to the feature matrix and assess their relationship with sleep

**Non-Goals:**
- Causal inference / DAG modelling (observational data only)
- Adding new data sources beyond what's already in the Garmin DBs
- Modifying sleep_analysis.ipynb or sleep_deep_analysis.ipynb

## Decisions

**D1 — `sport_category` classification**
Map `sport` column to: `cardio` (running, cycling, swimming, walking, hiking), `strength` (fitness_equipment when sub_sport indicates weight training), `mixed` (basketball, other team sports), `other` (fallback). Rationale: `sport_grouped` is too coarse; this lets us directly test cardio vs strength.

Alternatives considered: using `sub_sport` column directly — too sparse, many nulls.

**D2 — `is_late_bedtime` threshold**
Set at `sleep_start_hour >= 3.0` (i.e., going to sleep at or after 3:00 AM). Rationale: deprived mean bedtime is 4.38h, adequate is 2.63h — the 3h mark sits between them.

**D3 — calories_consumed and steps from daily_summary**
`calories_consumed` and `steps` are already in the `daily_summary` table joined by `load_sleep_data()`. They're available in the raw sleep DataFrame; just expose them explicitly in the feature matrix and add to CONTROLLABILITY dict.

**D4 — Intensity metric**
Use `vigorous_ratio` (hrz4+hrz5 min / total min) as the intensity proxy per workout, then create `same_day_vigorous_ratio` and `same_day_total_vigorous_min` merged onto the per-night df. Rationale: duration-normalized metric avoids length confound.

## Risks / Trade-offs

- [Risk] 144-night sleep architecture window is small for regression → Mitigation: report confidence intervals and flag n explicitly in all plots
- [Risk] `sub_sport` is often NULL for fitness_equipment, making strength/cardio split unreliable → Mitigation: use `sport` + duration heuristic; note limitation in notebook
- [Risk] stress→bedtime test is confounded (nights with both high stress AND lots of activities will have later bedtimes for other reasons) → Mitigation: partial correlation controlling for `had_exercise`
