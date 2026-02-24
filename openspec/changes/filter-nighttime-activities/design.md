## Context

`garmin_utils.load_activities()` returns a DataFrame with a `start_time` column (datetime) and an `hour` column (int). The existing `time_bucket` classification groups anything after 20:00 as "Late Night", which includes legitimate evening workouts as well as phantom recordings during sleep hours (22:30–04:00). No filtering layer currently exists between data loading and analysis.

The new `analysis/customized/data_preproccess_customizers.py` module adds a postprocessing step that callers apply themselves after `load_activities()` — `garmin_utils.py` is not touched.

## Goals / Non-Goals

**Goals:**
- Provide `filter_nighttime_activities(df)` that removes rows where `start_time` falls in 22:30–04:00 (inclusive of both endpoints)
- Filter operates on the DataFrame returned by `load_activities()` — pure transformation, no I/O
- Minute-level precision (22:30 not just 23:00) to avoid over-filtering legitimate late evening sessions
- `sleep_analysis.ipynb` applies the filter in cell 15, immediately after `load_activities()`

**Non-Goals:**
- Not modifying `garmin_utils.py` or `load_activities()` in any way
- Not filtering based on activity type, duration, or sport
- Not persisting filtered data — caller always filters at runtime
- Not adding the filter to any other notebooks automatically (convention only, not enforced)

## Decisions

### D1: Filter by `start_time` (minute precision), not `hour` column

**Decision**: Use `df["start_time"].dt.time` to check against `time(22, 30)` and `time(4, 0)`.

**Rationale**: The `hour` column already in the DataFrame only gives hour-level precision. A session starting at 22:15 is a legitimate late-evening workout; the cutoff is specifically 22:30. Using `start_time` avoids re-querying the DB and is already present in the DataFrame.

**Alternative considered**: Add a new column in `load_activities()` — rejected because it would require touching `garmin_utils.py`.

---

### D2: Midnight-crossing window handled with OR logic

**Decision**: A row is filtered if `start_time.time() >= time(22, 30)` **OR** `start_time.time() < time(4, 0)`.

**Rationale**: The window crosses midnight so a simple range check would fail. OR correctly captures both the late-night side (≥ 22:30) and the early-morning side (< 04:00).

---

### D3: Separate `analysis/customized/` directory, not added to `garmin_utils.py`

**Decision**: New file `analysis/customized/data_preproccess_customizers.py`; callers import and apply explicitly.

**Rationale**: Keeps `garmin_utils.py` as a stable, generic loading layer. The customizer is an opinionated, project-specific filter that not all use cases will want. Explicit import in the notebook also makes the filtering step visible and easy to toggle during exploration.

---

### D4: Function returns a filtered copy, logs dropped count

**Decision**: Return `df[mask].reset_index(drop=True)` and print a one-line summary (`Filtered N nighttime activities (HH:MM–HH:MM window)`).

**Rationale**: Non-destructive (caller's original `df` is unchanged). The print gives immediate feedback so the analyst knows how many records were dropped.

## Risks / Trade-offs

- **Risk**: Analyst forgets to apply the filter in a new notebook → Mitigation: document in proposal that it's a convention; future analysis template can include the import as boilerplate
- **Risk**: `start_time` column missing or not datetime type → Mitigation: function raises `KeyError`/`TypeError` with a clear message pointing to `load_activities()` as the expected source
- **Trade-off**: Filter window (22:30–04:00) is hardcoded — if the threshold changes, one place to update; acceptable for now given this is a personal analysis project
