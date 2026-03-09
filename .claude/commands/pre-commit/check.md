---
name: "Pre-commit: Full Quality Check"
description: Run linter, formatter, and unit tests before committing
category: Quality
tags: [lint, test, quality, pre-commit]
---

Run all quality checks on staged/modified Python files before committing.
Blocks the commit if any check fails.

## Steps

### 1. Identify scope

Get the list of staged + modified Python files:
```bash
git diff --name-only --cached --diff-filter=ACM | grep '\.py$'
git diff --name-only --diff-filter=ACM | grep '\.py$'
```

If no Python files are staged, report "No Python files to check" and stop.

### 2. Ruff — lint

```bash
.venv/bin/ruff check analysis/ tests/ --statistics
```

- If there are **fixable** issues (`[*]`), auto-fix them:
  ```bash
  .venv/bin/ruff check analysis/ tests/ --fix
  ```
  Report: "Auto-fixed N issues."

- If there are **unfixable** issues remaining, list them and **STOP** — do not proceed to commit. Ask the user to fix manually.

### 3. Ruff — format

```bash
.venv/bin/ruff format analysis/ tests/ --check
```

If formatting changes needed, apply them:
```bash
.venv/bin/ruff format analysis/ tests/
```
Report: "Reformatted N files."

### 4. Unit tests

```bash
.venv/bin/pytest tests/ -q --tb=short
```

If any tests **fail**, show the failure output and **STOP** — do not commit.

### 5. Notebook lint (only if .ipynb files are staged)

```bash
git diff --name-only --cached | grep '\.ipynb$'
```

If any notebooks are staged:
```bash
.venv/bin/nbqa ruff <notebook_path> --statistics
```

Notebook issues are **warnings only** — they do not block the commit.

### 6. Summary

If all blocking checks passed, print:
```
✓ ruff lint    — clean
✓ ruff format  — clean  (or: N files reformatted)
✓ pytest       — N passed
⚠ nbqa         — warnings only  (or: skipped)
```
Then invoke the `ccommit` skill to proceed with the commit.

If any blocking check failed, show the errors and say:
> "Fix the above issues and run `/pre-commit:check` again."

## Blocking vs Warning

| Check | Blocks commit? |
|-------|----------------|
| ruff lint (unfixable) | YES |
| ruff format | NO (auto-fixed) |
| pytest failures | YES |
| nbqa notebook lint | NO (warning only) |
