---
name: "Analyze: Run"
description: Launch or continue a Claude-driven analysis session
---

You are the analysis agent. No external LLM API is used — YOU drive the entire loop.

**Input**: The argument after `/analyze:run` is the topic. If none given, ask the user.

---

## Data available (pre-loaded by executor preamble)

| Variable | Content |
|----------|---------|
| `runs` | 跑步活動（距離≥0.5km），含 `pace_min_km`, `aerobic_eff`, `avg_hr`, `avg_cadence`, `vigorous_ratio`, `distance_km`, `elapsed_sec`, `hour`, `date`, `ascent` |
| `daily` | 每日彙總：`rhr`, `stress_avg`, `steps`, `spo2_avg` |
| `df_sleep` | 睡眠特徵矩陣（150欄）：`score`, `total_sleep_hours`, `deep_sleep_hours`, `rem_sleep_hours`, `is_deprived`, `rolling_7d_sleep_avg`, `pre_sleep_hr_avg_Xh`, `pre_sleep_stress_avg_Xh` … |
| `runs_daily` | runs LEFT JOIN daily（同一天） |
| `runs_sleep` | runs LEFT JOIN 前一晚睡眠（score, total_sleep_hours, deep_sleep_hours） |

Pre-loaded imports: `pd`, `np`, `plt`, `sns`, `stats`, `spearmanr`, `pearsonr`, `mannwhitneyu`, `ttest_ind`, `lowess`

---

## Step 1 — Session setup

Run this to find or create a session:

```bash
cd /Users/yinhsu/Documents/side_project/garmin_data_analyze
.venv/bin/python -c "
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
"
```

- **RESUME**: Read the tree summary. Understand what has already been explored.
- **NEW**: Proceed to the exploratory overview.

---

## Step 2 — Exploratory overview (new sessions only)

Write analysis code that computes a **correlation matrix** between `pace_min_km` (or the relevant target variable) and all candidate predictors. Plot a heatmap + top-5 scatter plots.

Run it using the executor:

```bash
cd /Users/yinhsu/Documents/side_project/garmin_data_analyze
.venv/bin/python -c "
import sys; sys.path.insert(0, 'analysis')
from auto_analyst.session import Session
from auto_analyst.executor import run
from pathlib import Path

session = Session.latest_unfinished()
node_id = session.next_node_id

code = '''
# YOUR ANALYSIS CODE HERE — do NOT import or load data, it's already done
# Available: runs, daily, df_sleep, runs_daily, runs_sleep
# Call plt.show() after each figure to save it

cols = ['pace_min_km', 'avg_hr', 'avg_cadence', 'aerobic_eff',
        'vigorous_ratio', 'distance_km', 'ascent', 'hour']
corr = runs[cols].corr(method='spearman')
print(corr['pace_min_km'].sort_values())

import seaborn as sns
fig, ax = plt.subplots(figsize=(8, 6))
sns.heatmap(corr, annot=True, fmt='.2f', center=0, ax=ax, cmap='RdBu_r')
ax.set_title('Spearman 相關矩陣 — 跑步指標')
plt.show()
'''

result = run(code, output_dir=session.session_dir, node_id=node_id)
print(result.stdout)
print('SUCCESS:', result.success)
if not result.success:
    print('STDERR:', result.stderr[:500])
print('PNGS:', [str(p) for p in result.png_paths])
"
```

After running, **read each PNG** using the Read tool to see the charts:
```
Read: analysis/auto_analyst/outputs/<session_dir>/node_0_chart_0.png
```

---

## Step 3 — Record the node

After each analysis round, record it:

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'analysis')
from auto_analyst.session import Session

session = Session.latest_unfinished()
session.add_node(
    hypothesis='HYPOTHESIS',
    parent_id=PARENT_ID,   # None for root nodes
    code='''CODE''',
    stdout='''STDOUT''',
    png_paths=['PATH1', 'PATH2'],
    insight='INSIGHT',
    decision='DECISION',   # a=深挖 b=側探 c=回溯 d=結論
    next_hypothesis='NEXT_HYPOTHESIS',
)
print('Node recorded. Next ID:', session.next_node_id)
"
```

---

## Step 4 — Analysis loop (repeat from Step 2 code pattern)

For each subsequent hypothesis:
1. Write focused analysis code (correlations, group comparisons, scatter plots)
2. Run via executor with the current `node_id`
3. Read the PNG(s)
4. Interpret the numbers + chart pattern
5. Record the node
6. **Pause and present findings** (see format below)

The code you write should be direct analysis — no setup, no data loading.

---

## Pause format (after every round)

End your response with this block:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 節點 N — [假設]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 發現：[2-3 句，引用具體數值]

⬇ 建議下一步（決策 X）：
  [具體的下一個假設]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
回覆：「繼續」/ 新方向 / 「結束分析」
```

---

## Ending the session

When the user says "結束分析" (or you have sufficient conclusions):
1. Write a Markdown story with: 核心結論（附數值）、因果鏈、無顯著發現的路徑、後續建議
2. Save it:

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'analysis')
from auto_analyst.session import Session

session = Session.latest_unfinished()
story = '''STORY_MARKDOWN'''
session.save_story(story)
print('Story saved to:', session.session_dir / 'story.md')
"
```
