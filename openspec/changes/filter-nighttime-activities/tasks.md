## 1. Create Module

- [x] 1.1 Create directory `analysis/customized/` and add empty `__init__.py`
- [x] 1.2 Create `analysis/customized/data_preproccess_customizers.py` with `filter_nighttime_activities(df)` function
- [x] 1.3 Implement midnight-crossing OR logic: remove rows where `start_time.dt.time >= time(22, 30)` OR `start_time.dt.time < time(4, 0)`
- [x] 1.4 Add input validation: raise `KeyError` if `start_time` column missing, raise `TypeError` if not datetime dtype
- [x] 1.5 Add print summary line: `Filtered N nighttime activities (22:30–04:00 window)`
- [x] 1.6 Return filtered copy with `reset_index(drop=True)`; do not mutate input

## 2. Integrate into Notebook

- [x] 2.1 In `analysis/sleep_analysis.ipynb` cell 15, add import: `from analysis.customized.data_preproccess_customizers import filter_nighttime_activities`
- [x] 2.2 In the same cell, add `activities = filter_nighttime_activities(activities)` immediately after `load_activities()` call
- [x] 2.3 Re-run cells 15 onward and verify filtered count is printed and downstream analysis still executes cleanly
