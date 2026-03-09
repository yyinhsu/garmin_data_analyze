# Project Instructions

## Database Schema

資料庫架構請看 `DATABASE_SCHEMA_ZH.md`（中文）或 `DATABASE_SCHEMA.md`（英文）。
若架構有變動，請同時更新兩份文件。

## Python Environment

Always use `./.venv` as the Python environment for this project.

```bash
.venv/bin/python script.py
# or
.venv/bin/python -c "..."
```

Do NOT use the system `python3`.

## Autonomous Analysis Agent

`analysis/auto_analyst/` 是一個自主數據分析系統，讓 AI 自動決定要繪製什麼圖表、計算哪些指標，並根據結果決定下一步探索方向，最終輸出分析故事線。

### 架構
```
analysis/auto_analyst/
├── orchestrator.py   # 主迴圈
├── agent.py          # Gemini API 呼叫（代碼生成 + 結果解讀）
├── executor.py       # subprocess 執行代碼，擷取 stdout + PNG
├── tree.py           # 分析樹（JSON 儲存、摘要生成）
├── prompts.py        # Prompt templates
├── run.py            # CLI 入口
└── outputs/          # 每次執行結果（PNG + tree.json + story.md）
```

### 設定
API Key 存放在專案根目錄 `.env`（已加入 `.gitignore`）：
```
GEMINI_API_KEY=sk-...
```

### 啟動方式
```bash
# CLI
cd analysis
../.venv/bin/python auto_analyst/run.py "分析主題" --max-iter 12

# Python
from auto_analyst import run
run(topic="睡眠品質惡化的原因", max_iterations=12)
```

### 分析迴圈邏輯
每次迭代 Agent 會：
1. 根據假設生成 Python 分析代碼
2. 執行代碼，儲存 PNG + 擷取數值指標
3. 看圖 + 看數字 → 解讀發現
4. 選擇決策：**a 深挖 / b 側探 / c 回溯 / d 停止**
5. 所有節點存入 `tree.json`，最後合成 `story.md`

使用 `/analyze:run` skill 可快速啟動，`/analyze:status` 可查看最近一次結果。

## Code Quality

### Tools
| Tool | 用途 |
|------|------|
| `ruff` | Linter + formatter（取代 flake8 / black / isort） |
| `pytest` | Unit tests（位於 `tests/`） |
| `nbqa` | 在 notebook 上執行 ruff |

### Config
- `pyproject.toml` — ruff 和 pytest 設定
- Line length: 100，target: Python 3.12

### 手動執行
```bash
.venv/bin/ruff check analysis/ tests/ --fix   # lint + auto-fix
.venv/bin/ruff format analysis/ tests/         # format
.venv/bin/pytest tests/ -q                     # unit tests
```

### Pre-commit skill
使用 `/pre-commit:check` 在 commit 前自動執行所有檢查。
- ruff unfixable errors → 阻擋 commit
- pytest failures → 阻擋 commit
- notebook lint → 僅警告
