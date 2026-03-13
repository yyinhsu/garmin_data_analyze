"""
Prompt templates for the two agent calls:
  1. generate_code  — given hypothesis + tree summary → Python code
  2. interpret      — given stdout + PNGs + tree summary → insight + decision
  3. story          — final synthesis → Markdown story line
"""

# ─────────────────────────────────────────────────────────────────────────────
# Column catalogue shown to the code-generation agent
# ─────────────────────────────────────────────────────────────────────────────
COLUMN_CATALOGUE = """
### 資料來源說明
分析時可直接查詢 SQLite 資料庫：
- 跑步/運動資料：`sqlite3.connect('../HealthData/DBs/garmin_activities.db')`
  - 主表 `activities`：每一筆為一次活動
  - 睡眠特徵矩陣：`from customized.sleep_feature_builder import build_sleep_features`（每晚一列）
- 每日彙總：`sqlite3.connect('../HealthData/DBs/garmin.db')` → 表 `daily_summary`

### 跑步活動欄位（activities 表，WHERE sport='running'，共 26 筆）
- **時間地點**：start_time, elapsed_time, moving_time
- **表現指標**：avg_speed (m/s), max_speed, avg_cadence, max_cadence
- **生理指標**：avg_hr, max_hr, calories
- **地形**：ascent (m), descent (m), distance (km)
- **心率區間時長**：hrz_1_time ~ hrz_5_time（字串格式 HH:MM:SS）
- **主觀評分**：self_eval_feel, self_eval_effort, training_load, training_effect
- 衍生欄位建議：
  - `pace_min_km = elapsed_time_sec / (distance_km * 60)`（越小越快）
  - `aerobic_efficiency = avg_speed / avg_hr`（越大越省力）
  - `vigorous_ratio = (hrz4_sec + hrz5_sec) / elapsed_sec`

### 每日彙總欄位（daily_summary 表）
day, rhr, stress_avg, steps, vigorous_activity_time, spo2_avg, rr_waking_avg

### 睡眠特徵矩陣（build_sleep_features() 回傳，可與跑步資料 JOIN 當天日期）
### 睡眠基本指標
day, score, total_sleep_hours, deep_sleep_hours, light_sleep_hours, rem_sleep_hours,
sleep_start_hour, sleep_start_minute, n_awakenings, time_to_first_deep_min,
time_to_first_rem_min, longest_uninterrupted_sleep_h, avg_spo2, avg_rr, avg_stress

### 睡眠衍生 / 歷史
is_deprived (score<50 or total_sleep_hours<4.5),
rolling_3d_sleep_avg, rolling_7d_sleep_avg, sleep_debt_7d,
consecutive_poor_sleep, consecutive_good_sleep, days_since_last_good_sleep,
is_late_bedtime (sleep_start_hour>=3.0)

### 運動特徵
had_exercise, sport_category (cardio/strength/mixed/other/NaN),
same_day_vigorous_ratio, same_day_vigorous_min, hours_workout_to_sleep,
consecutive_exercise_days, consecutive_rest_days

### 睡前生理訊號（1h/2h/4h/6h/8h 視窗）
pre_sleep_hr_avg_Xh, pre_sleep_hr_min_Xh, pre_sleep_hr_std_Xh, pre_sleep_hr_trend_Xh
pre_sleep_stress_avg_Xh, pre_sleep_stress_max_Xh, pre_sleep_high_stress_min_Xh
pre_sleep_rr_avg_Xh, pre_sleep_rr_std_Xh
pre_sleep_steps_Xh, pre_sleep_active_cal_Xh

### 每日彙總
steps, calories_consumed (全NULL), resting_hr, weekday
"""

# ─────────────────────────────────────────────────────────────────────────────
# 1. Code generation
# ─────────────────────────────────────────────────────────────────────────────
CODE_GENERATION_SYSTEM = """\
你是一個自主數據分析 Agent，專門分析 Garmin 個人健康數據。
你的目標是驗證或否定一個分析假設，並輸出可量化的指標供後續決策使用。

【關鍵限制】
- 所有 DataFrame 已預載，絕對不要重複 import 或讀取資料庫
- 代碼必須從統計計算開始，第一行就是分析邏輯
"""

CODE_GENERATION_USER = """\
## 任務
根據以下假設，生成一段 Python 分析代碼。

## 分析主題
{topic}

## 當前假設
{hypothesis}

## 已探索路徑摘要
{tree_summary}

## 可用欄位
{column_catalogue}

## ⚠️ 重要：以下變數已在執行環境中預載，可直接使用

| 變數 | 說明 |
|------|------|
| `runs` | 跑步活動（21筆），距離 >= 0.5 km，含衍生欄位 |
| `daily` | 每日彙總（rhr, stress_avg, steps, spo2_avg） |
| `df_sleep` | 睡眠特徵矩陣（150 欄） |
| `runs_daily` | runs LEFT JOIN daily（同一天） |
| `runs_sleep` | runs LEFT JOIN 前一晚睡眠（score, total_sleep_hours, deep_sleep_hours） |

已預載的 library（直接使用，**不要重複 import**）：
`pandas as pd`, `numpy as np`, `matplotlib.pyplot as plt`, `scipy.stats`

### `runs` 的重要欄位
- `pace_min_km` — 配速（分/公里），越小越快
- `aerobic_eff` — 有氧效率 avg_speed / avg_hr，越大越省力
- `avg_hr`, `max_hr` — 平均/最高心率
- `avg_cadence` — 步頻（步/分）
- `vigorous_ratio` — 高強度心率區間佔比
- `distance_km`, `elapsed_sec`, `hour`, `date`
- `ascent` — 爬升高度 (m)

## 代碼規範（嚴格遵守）
1. **絕對不要** import pandas, numpy, matplotlib, scipy, sqlite3 或讀取資料庫 — 已預載
2. **第一行必須是統計計算或分析邏輯**（不是 import，不是數據載入）
3. 必須 print 出關鍵指標，例如：
   `print(f"Spearman r = {{r:.3f}}, p = {{p:.4f}}, n = {{n}}")`
4. 繪製 1-2 張圖後呼叫 `plt.show()` — 系統會自動儲存 PNG
5. 只輸出純 Python 代碼，不加說明文字，不加 markdown fence
6. 確保所有字串、括號、引號正確閉合

## 代碼模板（參考結構）
```python
# 步驟1：計算相關係數
from scipy.stats import spearmanr
r, p = spearmanr(runs["pace_min_km"].dropna(), runs["avg_hr"].dropna())
print(f"配速 vs 心率: Spearman r={{r:.3f}}, p={{p:.4f}}, n={{len(runs)}}")

# 步驟2：繪圖
fig, ax = plt.subplots()
ax.scatter(runs["avg_hr"], runs["pace_min_km"])
ax.set_xlabel("avg_hr"); ax.set_ylabel("pace_min_km")
ax.set_title("心率 vs 配速")
plt.show()
```
"""

# ─────────────────────────────────────────────────────────────────────────────
# 2. Interpretation + next-step decision
# ─────────────────────────────────────────────────────────────────────────────
INTERPRET_SYSTEM = """\
你是一個自主數據分析 Agent，負責解讀分析結果並決定下一步探索方向。
"""

INTERPRET_USER = """\
## 分析主題
{topic}

## 剛才驗證的假設
{hypothesis}

## 代碼執行結果（指標與文字輸出）
```
{stdout}
```

## 圖表
（已附上，請從中觀察趨勢、分佈、異常點）

## 已探索路徑摘要
{tree_summary}

## 任務
1. 用 2-4 句話描述這次分析的**核心發現**（請具體引用數值）
2. 選擇下一步決策：
   - a) 深挖 — 對當前發現做更細緻的分層/子群分析
   - b) 側探 — 引入一個新的相關變數或角度
   - c) 回溯 — 此假設無顯著發現，退回上一個節點換方向
   - d) 停止 — 已有足夠強的結論，不需要繼續
3. 如果選 a 或 b，提出下一個具體假設（一句話）

**必須**以下列格式輸出，**JSON 必須在一行內**（insight 中不得有換行符）：
{{"insight": "...", "decision": "a|b|c|d", "rationale": "1句", "next_hypothesis": "..."}}
"""

# ─────────────────────────────────────────────────────────────────────────────
# 3. Final story synthesis
# ─────────────────────────────────────────────────────────────────────────────
STORY_SYSTEM = """\
你是一個資深數據分析師，擅長把複雜的統計發現整理成清晰的故事線。
"""

STORY_USER = """\
## 分析主題
{topic}

## 完整分析樹
{tree_summary}

## 任務
根據上方的分析歷程，撰寫一份**數據分析故事線報告**，包含：

1. **核心結論**（3-5 條，每條附上最強的支持數值）
2. **因果鏈推斷**（用箭頭圖文說明，e.g. A → B → C）
3. **無顯著發現的路徑**（哪些假設被否定）
4. **後續建議**（下一步可以做哪些分析或行為改變）

用 Markdown 格式輸出，繁體中文。
"""
