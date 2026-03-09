---
name: "Analyze: Show Latest Results"
description: Show the story and tree from the most recent autonomous analysis run
category: Analysis
tags: [analysis, autonomous, status]
---

Show results from the most recent `auto_analyst` run.

## Steps

### 1. Find latest output directory

```bash
ls -t analysis/auto_analyst/outputs/ | head -1
```

If no outputs exist, say: "No analysis runs found. Use `/analyze:run` to start one."

### 2. Show story

Read and display `outputs/<latest>/story.md` in full.

### 3. Show analysis tree

Read `outputs/<latest>/tree.json`, then print a compact tree:
```
節點 0 [parent: —  ] 假設: ... → 決策: a深挖
  節點 1 [parent: 0] 假設: ... → 決策: b側探
  節點 2 [parent: 0] 假設: ... → 決策: c回溯
節點 3 [parent: —  ] 假設: ... → 決策: d停止
```

### 4. List charts

```bash
ls analysis/auto_analyst/outputs/<latest>/*.png
```

List each chart filename with its node number.
