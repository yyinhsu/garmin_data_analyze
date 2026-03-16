# Garmin Data Analyze

Personal health data analysis system built on top of [GarminDB](https://github.com/tcgoetz/GarminDB).
Syncs data from Garmin Connect and runs both manual notebook analysis and a **Claude-driven analysis agent**.

## What It Does

- Syncs Garmin Connect data locally (sleep, activities, heart rate, stress, SpO2, etc.)
- Provides a rich feature matrix (150+ columns) for analysis via `build_sleep_features()`
- Includes hand-crafted Jupyter notebooks for sleep quality investigation
- Ships a **Claude-driven analysis agent** — Claude Code directly drives code generation, chart interpretation, and decision-making (no external LLM API required)

---

## Setup

### 1. Clone and install dependencies

```bash
git clone <repo>
cd garmin_data_analyze
uv sync
```

### 2. Configure GarminDB

```bash
cp ~/.GarminDb/GarminConnectConfig.json.example ~/.GarminDb/GarminConnectConfig.json
# Edit with your Garmin Connect credentials
```

### 3. Sync data

```bash
./sync_garmin.sh
```

Data is stored locally in `./HealthData/DBs/` — never uploaded anywhere.

---

## Project Structure

```
garmin_data_analyze/
├── analysis/
│   ├── customized/
│   │   └── sleep_feature_builder.py   # 150-column feature matrix
│   ├── auto_analyst/                  # Claude-driven analysis agent
│   │   ├── executor.py                # Code execution + PNG capture
│   │   ├── tree.py                    # Analysis tree (JSON)
│   │   ├── session.py                 # Session lifecycle + resume
│   │   └── outputs/                   # Per-run results (gitignored)
│   ├── sleep_analysis.ipynb
│   ├── sleep_deep_analysis.ipynb
│   └── sleep_causal_investigation.ipynb
├── tests/                             # Unit tests (pytest)
├── pyproject.toml                     # Project deps + ruff + pytest config
├── uv.lock                           # Locked dependency versions
└── sync_garmin.sh
```

---

## Autonomous Analysis Agent

**Claude Code is the agent** — no external LLM API, no Gemini key required. Claude directly generates analysis code, executes it, reads the charts (multimodal), and decides the next step.

### How it works

```
Exploratory overview → Propose hypothesis → Generate code → Execute
        ↑                                                       ↓
        └──────── You decide direction ←── Claude interprets ──┘
```

Each round Claude pauses and presents findings; you decide to continue, change direction, or end. Sessions persist across conversations via `tree.json` — `/analyze:run` auto-resumes unfinished sessions.

### Start an analysis

Use the Claude Code skill:

```
/analyze:run 什麼因素影響跑步表現
```

### Output

Each session saves to `analysis/auto_analyst/outputs/<timestamp>/`:

| File | Content |
|------|---------|
| `tree.json` | Full analysis tree with all nodes |
| `tree.md` | Human-readable tree |
| `story.md` | Final narrative report with embedded charts |
| `workflow.ipynb` | Jupyter notebook with all code, outputs, and insights |
| `node_N_chart_M.png` | Charts generated per node |

### Decision types

| Decision | Meaning |
|----------|---------|
| a — drill-down | Dig deeper into the current finding |
| b — side-explore | Bring in a new related variable |
| c — backtrack | Dead end — return to a previous node |
| d — conclude | Sufficient conclusion reached |

---

## Manual Notebooks

| Notebook | Topic |
|----------|-------|
| `sleep_analysis.ipynb` | Overview: sleep score distribution, correlations |
| `sleep_deep_analysis.ipynb` | Deep dive: sleep architecture, HRV, stress |
| `sleep_causal_investigation.ipynb` | Six mechanistic hypotheses (bedtime cliff, exercise intensity, etc.) |

Run with:
```bash
cd analysis
../.venv/bin/jupyter notebook
```

---

## Code Quality

```bash
.venv/bin/ruff check analysis/ tests/ --fix   # lint + auto-fix
.venv/bin/ruff format analysis/ tests/         # format
.venv/bin/pytest tests/ -q                     # run unit tests
```

Or use the `/pre-commit:check` Claude Code skill to run all checks before committing.

---

## Claude Code Skills

| Skill | Description |
|-------|-------------|
| `/analyze:run` | Launch autonomous analysis agent |
| `/analyze:status` | View latest run results and story |
| `/pre-commit:check` | Run lint + tests before committing |
