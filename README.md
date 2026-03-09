# Garmin Data Analyze

Personal health data analysis system built on top of [GarminDB](https://github.com/tcgoetz/GarminDB).
Syncs data from Garmin Connect and runs both manual notebook analysis and an **autonomous AI analysis agent**.

## What It Does

- Syncs Garmin Connect data locally (sleep, activities, heart rate, stress, SpO2, etc.)
- Provides a rich feature matrix (150+ columns) for analysis via `build_sleep_features()`
- Includes hand-crafted Jupyter notebooks for sleep quality investigation
- Ships an **autonomous analysis agent** that explores a topic end-to-end without manual intervention

---

## Setup

### 1. Clone and create virtualenv

```bash
git clone <repo>
cd garmin_data_analyze
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
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

### 4. Configure Gemini API key (for autonomous agent)

Create a `.env` file at the project root:

```
GEMINI_API_KEY=your_key_here
```

Get a free key at https://aistudio.google.com/app/apikey

---

## Project Structure

```
garmin_data_analyze/
├── analysis/
│   ├── customized/
│   │   └── sleep_feature_builder.py   # 150-column feature matrix
│   ├── auto_analyst/                  # Autonomous analysis agent
│   │   ├── orchestrator.py            # Main loop
│   │   ├── agent.py                   # Gemini API calls
│   │   ├── executor.py                # Code execution + PNG capture
│   │   ├── tree.py                    # Analysis tree (JSON)
│   │   ├── prompts.py                 # Prompt templates
│   │   ├── run.py                     # CLI entry point
│   │   └── outputs/                   # Per-run results
│   ├── sleep_analysis.ipynb
│   ├── sleep_deep_analysis.ipynb
│   └── sleep_causal_investigation.ipynb
├── tests/                             # Unit tests (pytest)
├── pyproject.toml                     # Ruff + pytest config
├── requirements.txt
├── sync_garmin.sh
└── .env                               # API keys (gitignored)
```

---

## Autonomous Analysis Agent

The agent takes a topic, then autonomously loops:

1. **Generates** Python analysis code based on the current hypothesis
2. **Executes** it — captures stdout metrics + saves PNG charts
3. **Interprets** charts and numbers using Gemini Vision
4. **Decides** next step: drill-down / side-explore / backtrack / stop
5. Saves every node to `tree.json`, synthesises a final `story.md`

### Run via CLI

```bash
cd analysis
../.venv/bin/python auto_analyst/run.py "What causes poor sleep quality?" --max-iter 12
```

### Run via Python

```python
import sys; sys.path.insert(0, 'analysis')
from auto_analyst import run
run(topic="What causes poor sleep quality?", max_iterations=12)
```

### Output

Each run saves to `analysis/auto_analyst/outputs/<timestamp>/`:

| File | Content |
|------|---------|
| `tree.json` | Full analysis tree with all nodes |
| `tree.md` | Human-readable tree |
| `story.md` | Final narrative conclusion |
| `node_N_chart_M.png` | Charts generated per iteration |

### Decision types

| Decision | Meaning |
|----------|---------|
| a — drill-down | Dig deeper into the current finding |
| b — side-explore | Bring in a new related variable |
| c — backtrack | Dead end — return to a previous node |
| d — stop | Sufficient conclusion reached |

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
