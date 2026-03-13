---
name: "Analyze: Status"
description: Show the story and tree from the most recent analysis session
---

Show results from the most recent analysis session.

## Steps

### 1. Find latest session

```bash
cd /Users/yinhsu/Documents/side_project/garmin_data_analyze
.venv/bin/python -c "
import sys; sys.path.insert(0, 'analysis')
from auto_analyst.session import Session

session = Session.load_latest()
if not session:
    print('NO_SESSION')
else:
    print('DIR:', session.session_dir)
    print('TOPIC:', session.topic)
    print('NODES:', session.node_count)
    print('FINISHED:', session.is_finished())
    print(session.summary())
"
```

If no session, say: "尚無分析記錄。使用 `/analyze:run <主題>` 開始分析。"

### 2. Show story (if finished)

Read `story.md` from the session directory and display it in full.

### 3. Show tree summary

Display the tree summary from the Python output above.

### 4. List charts

```bash
ls analysis/auto_analyst/outputs/<session_dir>/*.png 2>/dev/null
```

List each chart with its node number. Offer to show any specific chart with the Read tool if the user wants to see it.
