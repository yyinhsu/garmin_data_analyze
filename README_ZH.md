# Garmin 數據分析

基於 [GarminDB](https://github.com/tcgoetz/GarminDB) 的個人健康數據分析系統。
從 Garmin Connect 同步資料到本地端，並提供手動 Notebook 分析與**自主 AI 分析 Agent** 兩種模式。

## 功能概覽

- 將 Garmin Connect 數據同步至本地（睡眠、運動、心率、壓力、血氧等）
- 提供 150+ 欄位的特徵矩陣，透過 `build_sleep_features()` 取得
- 包含手工製作的 Jupyter Notebook 進行睡眠品質探索
- 內建**自主分析 Agent**，給定主題後可全自動探索，無需人工干預

---

## 安裝與設定

### 1. 建立虛擬環境

```bash
git clone <repo>
cd garmin_data_analyze
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 2. 設定 GarminDB

```bash
# 編輯設定檔，填入 Garmin Connect 帳號密碼
~/.GarminDb/GarminConnectConfig.json
```

### 3. 同步數據

```bash
./sync_garmin.sh
```

資料存放於 `./HealthData/DBs/`，完全在本地端，不上傳至任何伺服器。

### 4. 設定 Gemini API Key（自主 Agent 需要）

在專案根目錄建立 `.env`：

```
GEMINI_API_KEY=你的金鑰
```

免費金鑰申請：https://aistudio.google.com/app/apikey

---

## 專案結構

```
garmin_data_analyze/
├── analysis/
│   ├── customized/
│   │   └── sleep_feature_builder.py   # 150 欄特徵矩陣
│   ├── auto_analyst/                  # 自主分析 Agent
│   │   ├── orchestrator.py            # 主迴圈
│   │   ├── agent.py                   # Gemini API 呼叫
│   │   ├── executor.py                # 代碼執行 + PNG 擷取
│   │   ├── tree.py                    # 分析樹（JSON）
│   │   ├── prompts.py                 # Prompt 模板
│   │   ├── run.py                     # CLI 入口
│   │   └── outputs/                   # 每次執行結果
│   ├── sleep_analysis.ipynb
│   ├── sleep_deep_analysis.ipynb
│   └── sleep_causal_investigation.ipynb
├── tests/                             # 單元測試（pytest）
├── pyproject.toml                     # Ruff + pytest 設定
├── requirements.txt
├── sync_garmin.sh
└── .env                               # API 金鑰（已加入 .gitignore）
```

---

## 自主分析 Agent

Agent 接收一個分析主題，然後自動循環執行：

1. **生成**：根據當前假設產生 Python 分析代碼
2. **執行**：執行代碼，擷取數值指標與 PNG 圖表
3. **解讀**：透過 Gemini Vision 分析圖表和數字，得出階段性結論
4. **決策**：選擇下一步方向
5. 所有節點存入 `tree.json`，最終合成 `story.md` 故事線

### 四種決策類型

| 決策 | 說明 |
|------|------|
| a — 深挖 | 對當前發現做更細緻的分層分析 |
| b — 側探 | 引入新的相關變數或角度 |
| c — 回溯 | 此路無顯著發現，退回上一節點換方向 |
| d — 停止 | 已有足夠強的結論，結束分析 |

### CLI 啟動

```bash
cd analysis
../.venv/bin/python auto_analyst/run.py "睡眠品質惡化的原因" --max-iter 12
```

### Python 啟動

```python
import sys; sys.path.insert(0, 'analysis')
from auto_analyst import run
run(topic="睡眠品質惡化的原因", max_iterations=12)
```

### 輸出內容

每次執行結果儲存於 `analysis/auto_analyst/outputs/<timestamp>/`：

| 檔案 | 內容 |
|------|------|
| `tree.json` | 完整分析樹，含所有節點 |
| `tree.md` | 人類可讀的樹狀結構 |
| `story.md` | 最終分析故事線與結論 |
| `node_N_chart_M.png` | 每次迭代產生的圖表 |

---

## 手動 Notebook

| Notebook | 主題 |
|----------|------|
| `sleep_analysis.ipynb` | 總覽：睡眠分數分佈、相關性 |
| `sleep_deep_analysis.ipynb` | 深度分析：睡眠架構、HRV、壓力 |
| `sleep_causal_investigation.ipynb` | 六個因果假設（晚睡閾值、運動強度等） |

啟動方式：
```bash
cd analysis
../.venv/bin/jupyter notebook
```

---

## 代碼品質

```bash
.venv/bin/ruff check analysis/ tests/ --fix   # lint + 自動修復
.venv/bin/ruff format analysis/ tests/         # 格式化
.venv/bin/pytest tests/ -q                     # 單元測試
```

或使用 Claude Code skill `/pre-commit:check` 在 commit 前自動執行所有檢查。

---

## Claude Code Skills

| Skill | 功能 |
|-------|------|
| `/analyze:run` | 啟動自主分析 Agent |
| `/analyze:status` | 查看最近一次分析結果與故事線 |
| `/pre-commit:check` | Commit 前執行 lint + 測試 |
