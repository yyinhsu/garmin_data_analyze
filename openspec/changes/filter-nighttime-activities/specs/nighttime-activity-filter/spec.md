## ADDED Requirements

### Requirement: Nighttime activity filter function

The `analysis/customized/data_preproccess_customizers.py` module SHALL provide a `filter_nighttime_activities(df)` function that removes activity records whose start time falls within the 22:30–04:00 window (crossing midnight).

#### Scenario: Records in nighttime window are removed

- **WHEN** `filter_nighttime_activities(df)` is called with a DataFrame containing activities
- **THEN** it SHALL remove all rows where `start_time` is >= 22:30 OR < 04:00
- **AND** it SHALL return a new DataFrame with the remaining rows (index reset)
- **AND** the original DataFrame SHALL not be mutated

#### Scenario: Records outside nighttime window are retained

- **WHEN** `filter_nighttime_activities(df)` is called
- **THEN** all rows with `start_time` between 04:00 (inclusive) and 22:30 (exclusive) SHALL be retained unchanged

#### Scenario: Minute-level precision is enforced

- **WHEN** an activity starts at exactly 22:29
- **THEN** it SHALL be retained (not filtered)
- **WHEN** an activity starts at exactly 22:30
- **THEN** it SHALL be removed

#### Scenario: Filter logs dropped record count

- **WHEN** `filter_nighttime_activities(df)` is called
- **THEN** it SHALL print a summary line indicating how many records were removed and the window applied (e.g., `Filtered 12 nighttime activities (22:30–04:00 window)`)

#### Scenario: Missing or wrong-type start_time raises a clear error

- **WHEN** the input DataFrame does not have a `start_time` column
- **THEN** the function SHALL raise a `KeyError` with a message indicating `start_time` is required
- **WHEN** the `start_time` column is not of datetime dtype
- **THEN** the function SHALL raise a `TypeError` with a message indicating `start_time` must be datetime (use `load_activities()` as the source)

### Requirement: Module location and import path

The filter function SHALL reside in `analysis/customized/data_preproccess_customizers.py` and SHALL be importable as:

```python
from analysis.customized.data_preproccess_customizers import filter_nighttime_activities
```

#### Scenario: Module is importable from project root

- **WHEN** a notebook or script at the project root (or with project root on `sys.path`) imports from `analysis.customized.data_preproccess_customizers`
- **THEN** the import SHALL succeed without modifying `garmin_utils.py` or any existing module

### Requirement: Notebook integration in sleep_analysis.ipynb

The `sleep_analysis.ipynb` notebook SHALL apply `filter_nighttime_activities` immediately after `load_activities()` is called, before any activity grouping or analysis cell.

#### Scenario: Filter applied before activity analysis

- **WHEN** cell 15 of `sleep_analysis.ipynb` calls `load_activities()`
- **THEN** the very next statement SHALL call `filter_nighttime_activities(activities)` and reassign the result to `activities`
- **AND** all subsequent cells that use `activities` SHALL operate on the filtered DataFrame
