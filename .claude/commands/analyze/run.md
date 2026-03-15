---
name: "Analyze: Run"
description: Launch or continue a Claude-driven analysis session
---

You are the analysis agent. No external LLM API is used — YOU drive the entire loop.

**Input**: The argument after `/analyze:run` is the topic. If none given, ask the user.

---

## Data available (pre-loaded by executor preamble)

### Pre-joined DataFrames

| Variable | Content |
|----------|---------|
| `runs` | 跑步活動（距離≥0.5km），含 `pace_min_km`, `aerobic_eff`, `avg_hr`, `avg_cadence`, `vigorous_ratio`, `distance_km`, `elapsed_sec`, `hour`, `date`, `ascent`, `start_time`, `stop_time` |
| `daily` | 每日彙總：`rhr`, `stress_avg`, `steps`, `spo2_avg`, `bb_charged`, `bb_max`, `bb_min` |
| `df_sleep` | 睡眠特徵矩陣（150欄）：`score`, `total_sleep_hours`, `deep_sleep_hours`, `rem_sleep_hours`, `is_deprived`, `rolling_7d_sleep_avg`, `pre_sleep_hr_avg_Xh`, `pre_sleep_stress_avg_Xh` … |
| `runs_daily` | runs LEFT JOIN daily（同一天） |
| `runs_sleep` | runs LEFT JOIN 前一晚睡眠（score, total_sleep_hours, deep_sleep_hours） |

### Raw time-series (for feature engineering)

| Variable | Content |
|----------|---------|
| `mon_hr` | `timestamp`, `heart_rate`（每 ~3 分鐘）|
| `mon_stress` | `timestamp`, `stress`（已濾掉未測量/睡眠的負值）|

### Helper function

```python
pre_run_window(run_row, hours_before=3, source="hr")
# → Series of HR or stress values in [start_time - N hours, start_time)
# source: "hr" or "stress"
```

Pre-loaded imports: `pd`, `np`, `plt`, `sns`, `stats`, `spearmanr`, `pearsonr`, `mannwhitneyu`, `ttest_ind`, `lowess`

---

## Feature engineering — 積極自己做！

**不要只用現有欄位。** 根據假設在分析代碼開頭加工衍生特徵。常見範例：

```python
# 跑前 3h HR 均值 & 趨勢斜率
runs["pre_hr_mean_3h"] = runs.apply(
    lambda r: pre_run_window(r, 3, "hr").mean(), axis=1)
runs["pre_hr_slope_3h"] = runs.apply(
    lambda r: (lambda s: np.polyfit(range(len(s)), s, 1)[0] if len(s) > 2 else np.nan)(
        pre_run_window(r, 3, "hr").values), axis=1)

# 跑前 2h 壓力均值
runs["pre_stress_2h"] = runs.apply(
    lambda r: pre_run_window(r, 2, "stress").mean(), axis=1)

# 當天 Body Battery 下降幅度（日內最高 - 最低）
runs_bb = runs.merge(daily[["day","bb_charged","bb_max","bb_min"]], left_on="date", right_on="day", how="left")
runs_bb["bb_drop"] = runs_bb["bb_max"] - runs_bb["bb_min"]

# 跑步當天的睡眠（同一晚，非前一晚）
runs_sleep_same = runs.merge(df_sleep[["day","score","total_sleep_hours"]], left_on="date", right_on="day", how="left")
```

其他可以考慮的衍生特徵：
- 跑前 1h / 2h / 3h 心率與靜息心率的差值（`pre_hr_mean - rhr`）
- 跑前壓力趨勢（上升 or 下降）
- 前 7 天累積跑量（疲勞指標）
- 跑步距離 / 最近一次跑步的間隔天數

---

## Step 0 — Sync latest Garmin data

Before starting analysis, run an incremental sync to pull the latest data from Garmin Connect:

```bash
cd /Users/yinhsu/Documents/side_project/garmin_data_analyze
./sync_garmin.sh 2>&1 | tail -20
```

- If the sync **succeeds**, proceed to Step 1.
- If it **fails** (network error, credentials expired, etc.), tell the user and ask whether to continue with existing data or abort.

---

## Step 1 — Session setup

```bash
cd /Users/yinhsu/Documents/side_project/garmin_data_analyze
.venv/bin/python << 'PYEOF'
import sys; sys.path.insert(0, 'analysis')
from auto_analyst.session import Session

topic = 'TOPIC_PLACEHOLDER'
session = Session.latest_unfinished()
if session:
    print('RESUME')
    print('DIR:', session.session_dir)
    print('TOPIC:', session.topic)
    print('NODES:', session.node_count)
    print(session.summary())
else:
    session = Session.new(topic)
    print('NEW')
    print('DIR:', session.session_dir)
    print('NEXT_ID:', session.next_node_id)
PYEOF
```

- **RESUME**: Read the tree summary. Identify all open leaves — these are the branches to continue.
- **NEW**: Proceed to the exploratory overview.

---

## Step 2 — Exploratory overview (new sessions only)

Compute a correlation matrix between the target variable and all candidate predictors. Plot a heatmap.

After reading the chart, **propose 2–4 first-level branches** to explore (the most promising hypotheses). Record as node 0 with `next_hypotheses`.

---

## Step 3 — Record each node

After every analysis round:

```bash
.venv/bin/python << 'PYEOF'
import sys; sys.path.insert(0, 'analysis')
from auto_analyst.session import Session

session = Session.latest_unfinished()
session.add_node(
    hypothesis='THIS_HYPOTHESIS',
    parent_id=PARENT_ID,          # None for root; int for child nodes
    code='''CODE''',
    stdout='''STDOUT''',
    png_paths=['PATH1'],
    insight='KEY_FINDING_WITH_NUMBERS',
    mini_summary='ONE_SENTENCE_CONCLUSION_EVEN_IF_NEGATIVE',  # always fill this
    status='open',                # 'open' = has children to explore; 'closed' = dead end
    next_hypotheses=[             # list the child branches you plan to explore next
        'Child hypothesis A',
        'Child hypothesis B',
    ],
)
print('Node recorded. Next ID:', session.next_node_id)
print(session.summary())
PYEOF
```

**Rules:**
- `mini_summary` is **always required** — write a one-sentence conclusion whether the hypothesis is confirmed or rejected.
- `status='closed'` when this branch has no further exploration value.
- `status='open'` when you have child hypotheses to explore.
- `next_hypotheses` can list **multiple** children — explore them one by one.

---

## Step 4 — Analysis loop (tree traversal)

The analysis proceeds as a **depth-first tree exploration**:

1. Pick the most promising open leaf from the tree summary.
2. Write focused analysis code for that hypothesis.
3. Run via executor with current `node_id`.
4. Read the PNG(s).
5. Interpret findings.
6. Record the node (with `mini_summary` + `next_hypotheses` if branching further).
7. **Pause and present findings.**

**Branching**: After any node, you may propose 1–3 child hypotheses. List them all in `next_hypotheses`. Explore one immediately; return to the others later.

**Deep exploration mindset**: Don't give up easily. When a result is ambiguous or marginal:
- Try **alternative operationalizations** (e.g., continuous → categorical, different window sizes, log transform)
- Try **subgroup analysis** (e.g., only flat routes, only morning runs, only weekdays)
- Try **non-linear models** (e.g., quadratic terms, LOWESS visual inspection for U-shaped patterns)
- Try **different control strategies** (e.g., stratification instead of regression, propensity matching)
- Ask: "What would I need to see to change my conclusion?" — then test that specific scenario

**Closing a branch**: Only close when **all** of the following are true:
1. p > 0.2 after controlling for known confounders, **AND**
2. No subgroup or non-linear pattern visible in the chart, **AND**
3. No alternative operationalization or feature engineering could rescue the hypothesis.

If **any** of these hold, keep exploring instead of closing:
- p < 0.1 (even marginal) → try subgroup analysis, non-linear models, or alternative metrics
- Effect is confounded → don't just close; test if the effect survives a different control strategy (e.g., stratified analysis, matching, residualization)
- Significant in raw but not after control → propose **why** and test the mechanism (mediation analysis, instrumental variable, or natural experiment within the data)
- Small sample per group → try bootstrapping confidence intervals or different grouping thresholds before giving up
- A "definitional" or "tautological" correlation → reframe the hypothesis to test the causal direction (e.g., does deliberately higher intensity on same route → faster pace?)

Write a clear `mini_summary` regardless (e.g., "睡眠時長與跑步表現無顯著關聯 (p=0.42)")

**Depth target**: Aim for at least **3 levels deep** on promising branches before closing. A single null result is not sufficient — try at least one alternative approach before closing.

**Session ends** when all branches are closed OR the user says "結束分析".

---

## Pause format (after every round)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 節點 N — [假設]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 發現：[2-3 句，引用具體數值]
📝 小結：[一句話結論，不管假設是否成立]

🌿 目前樹狀態：
  [貼上 session.summary() 輸出]

⬇ 下一步探索（選擇以下其中一個分支）：
  A. [子假設 A]
  B. [子假設 B]
  C. [子假設 C（若有）]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
回覆：「A」/ 「B」/ 「全部」/ 新方向 / 「結束分析」
```

---

## Ending the session

When all branches closed or user says "結束分析":
1. Write a Markdown story: 核心結論（附數值）、探索樹結構、無顯著發現的路徑及原因、後續建議
2. Save:

```bash
.venv/bin/python << 'PYEOF'
import sys; sys.path.insert(0, 'analysis')
from auto_analyst.session import Session

session = Session.latest_unfinished()
story = '''STORY_MARKDOWN'''
session.save_story(story)
print('Saved:', session.session_dir)
PYEOF
```

`save_story()` automatically produces:
- `story.md` — narrative report with embedded charts
- `workflow.ipynb` — Jupyter notebook with all code, outputs, and insights per node
- `tree.md` — full analysis tree in Markdown
