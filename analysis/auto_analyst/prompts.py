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

## 代碼規範
1. 呼叫 `df = build_sleep_features()` 取得資料（已由環境自動 import）
2. 衍生欄位 `is_deprived = (df["score"] < 50) | (df["total_sleep_hours"] < 4.5)`
3. 必須 print 出關鍵指標，格式範例：
   ```
   print(f"Spearman r = {{r:.3f}}, p = {{p:.4f}}, n = {{n}}")
   print(f"Mean score (A) = {{a:.1f}}, Mean score (B) = {{b:.1f}}")
   print(f"Effect size (rank-biserial r) = {{eff:.3f}}")
   ```
4. 繪製 1-2 張圖後呼叫 `plt.show()` — 系統會自動儲存為 PNG
5. 只輸出純 Python 代碼，不要加任何說明文字或 markdown fence
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

**必須**以下列 JSON 格式輸出（不要加任何其他文字）：
{{
  "insight": "...",
  "decision": "a|b|c|d",
  "rationale": "為什麼這樣決定（1句）",
  "next_hypothesis": "下一個假設（選a/b時填寫，否則留空字串）"
}}
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
