## Why

Activities recorded between 22:30 and 04:00 are likely erroneous entries — the watch may misclassify sleep movements or auto-record phantom sessions during rest hours — and including them distorts activity timing analysis (e.g., inflating "Late Night" exercise counts and skewing sleep-activity correlations). A dedicated preprocessing filter ensures all downstream analyses operate on clean, credible activity data.

## What Changes

- **New file**: `analysis/customized/data_preproccess_customizers.py` containing a reusable filter function
- New function `filter_nighttime_activities(df)` that removes activity records whose start time falls in the 22:30–04:00 window (crosses midnight)
- `sleep_analysis.ipynb` (and any future notebooks) must apply this filter immediately after calling `load_activities()`, before any grouping or analysis

## Capabilities

### New Capabilities
- `nighttime-activity-filter`: A preprocessing utility that filters out activity records starting between 22:30 and 04:00, stored in a dedicated `analysis/customized/` module separate from `garmin_utils.py`

### Modified Capabilities

_(none — `analysis-utils` spec requirements are unchanged; the new filter is an additive preprocessing step, not a change to existing loading behavior)_

## Impact

- **New**: `analysis/customized/data_preproccess_customizers.py` (new script + new directory)
- **Notebooks**: `analysis/sleep_analysis.ipynb` — must import and apply the filter before activity-related analysis cells
- **No changes** to `analysis/garmin_utils.py` or existing specs
- Any future notebook that calls `load_activities()` should also apply this filter as a convention
