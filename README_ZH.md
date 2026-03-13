# Garmin 數據分析

基於 [GarminDB](https://github.com/tcgoetz/GarminDB) 的個人健康數據分析系統。
從 Garmin Connect 同步資料到本地端，並提供手動 Notebook 分析與 **Claude 驅動的分析 Agent** 兩種模式。

## 功能概覽

- 將 Garmin Connect 數據同步至本地（睡眠、運動、心率、壓力、血氧等）
- 提供 150+ 欄位的特徵矩陣，透過 `build_sleep_features()` 取得
- 包含手工製作的 Jupyter Notebook 進行睡眠品質探索
- 內建 **Claude 驅動的分析 Agent**：Claude Code 直接負責代碼生成、圖表解讀與決策，無需外部 LLM API

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

---

## 專案結構

```
garmin_data_analyze/
├── analysis/
│   ├── customized/
│   │   └── sleep_feature_builder.py   # 150 欄特徵矩陣
│   ├── auto_analyst/                  # Claude 驅動的分析 Agent
│   │   ├── executor.py                # 代碼執行 + PNG 擷取
│   │   ├── tree.py                    # 分析樹（JSON）
│   │   ├── session.py                 # Session 生命週期 + 斷點續傳
│   │   └── outputs/                   # 每次執行結果（已加入 .gitignore）
│   ├── sleep_analysis.ipynb
│   ├── sleep_deep_analysis.ipynb
│   └── sleep_causal_investigation.ipynb
├── tests/                             # 單元測試（pytest）
├── pyproject.toml                     # Ruff + pytest 設定
├── requirements.txt
└── sync_garmin.sh
```

---

## 自主分析 Agent

**Claude Code 即是 Agent** — 無需外部 LLM API，無需 Gemini 金鑰。Claude 直接生成分析代碼、執行、解讀圖表（多模態），並決定下一步。

### 分析迴圈

```
探索性總覽 → 提出假設 → 生成代碼 → 執行
     ↑                                  ↓
     └── 你決定方向 ←── Claude 解讀並暫停 ┘
```

每輪結束後 Claude 暫停並呈現發現，由你決定繼續、換方向或結束。Session 透過 `tree.json` 跨對話保存，`/analyze:run` 會自動續傳未完成的 session。

### 啟動分析

使用 Claude Code skill：

```
/analyze:run 什麼因素影響跑步表現
```

### 輸出內容

每次 Session 結果儲存於 `analysis/auto_analyst/outputs/<timestamp>/`：

| 檔案 | 內容 |
|------|------|
| `tree.json` | 完整分析樹，含所有節點 |
| `tree.md` | 人類可讀的樹狀結構 |
| `story.md` | 最終分析報告，附嵌入圖表 |
| `workflow.ipynb` | Jupyter Notebook，記錄所有代碼、輸出與解讀 |
| `node_N_chart_M.png` | 每個節點產生的圖表 |

### 四種決策類型

| 決策 | 說明 |
|------|------|
| a — 深挖 | 對當前發現做更細緻的分層分析 |
| b — 側探 | 引入新的相關變數或角度 |
| c — 回溯 | 此路無顯著發現，退回上一節點換方向 |
| d — 結論 | 已有足夠強的結論，結束分析 |

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
