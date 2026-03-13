# Project Instructions

## Documentation Sync Rule

**When any operational content in this file changes** (setup steps, usage commands, system architecture, skills, or code quality workflows), you **must** also update both:
- `README.md` (English)
- `README_ZH.md` (Traditional Chinese)

Keep all three files in sync. `CLAUDE.md` is a symlink to this file and does not need separate edits.

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

`analysis/auto_analyst/` 是 Claude Code 直接驅動的自主數據分析系統。**不使用任何外部 LLM API**（無 Gemini、無 Anthropic key）。Claude 本身就是 agent，負責：生成分析代碼、執行、看圖解讀、決定下一步。

### 架構
```
analysis/auto_analyst/
├── executor.py   # subprocess 執行代碼，prepend 資料載入 preamble，擷取 stdout + PNG
├── tree.py       # AnalysisTree：節點資料結構、JSON 儲存、Markdown 輸出
├── session.py    # Session：找/建 session、跨對話斷點續傳
└── outputs/      # 每次執行結果（PNG + tree.json + story.md）[gitignored]
```

> **舊的 Gemini 方案**（agent.py / orchestrator.py）保存於 git branch `archive/gemini-auto-analyst`。

### 啟動方式

使用 `/analyze:run <主題>` skill 啟動分析。Claude 會：
1. 找是否有未完成的 session（斷點續傳）
2. 先跑探索性總覽（correlation matrix）
3. 每輪暫停，等你決定繼續方向
4. 最後輸出 `story.md`（核心結論 + 因果鏈 + 分析路徑）

使用 `/analyze:status` 查看最近一次 session 的結果。

### 分析迴圈邏輯
```
探索性總覽 → 提出假設 → 生成代碼 → 執行 → 看圖 + 數值
     ↑                                              ↓
     └──────── 你決定方向 ←── Claude 解讀 + 暫停 ──┘
```
決策：**a 深挖 / b 側探 / c 回溯 / d 結論**，所有節點存入 `tree.json`。

### 跨對話續傳

Session 狀態存在 `outputs/<timestamp>/tree.json`。有 `tree.json` 但無 `story.md` 的 session 視為未完成，下次 `/analyze:run` 會自動繼續。

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
