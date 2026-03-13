
import sys, os
sys.path.insert(0, '/Users/yinhsu/Documents/side_project/garmin_data_analyze/analysis')
os.chdir('/Users/yinhsu/Documents/side_project/garmin_data_analyze/analysis')

import warnings
warnings.filterwarnings("ignore")

import sqlite3
import matplotlib
matplotlib.use("Agg")   # non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from scipy.stats import spearmanr, pearsonr, mannwhitneyu, ttest_ind
from statsmodels.nonparametric.smoothers_lowess import lowess

from customized.sleep_feature_builder import build_sleep_features

# ── Pre-loaded running fixtures (always available, correct schema) ──
_conn_act = sqlite3.connect("../HealthData/DBs/garmin_activities.db")
runs = pd.read_sql_query(
    "SELECT * FROM activities WHERE sport='running' ORDER BY start_time",
    _conn_act,
)
_conn_act.close()

def _hms_to_sec(s):
    if pd.isna(s): return float("nan")
    p = str(s).split(":")
    return int(p[0])*3600 + int(p[1])*60 + float(p[2])

runs["elapsed_sec"]  = runs["elapsed_time"].apply(_hms_to_sec)
runs["distance_km"]  = runs["distance"]
runs["date"]         = pd.to_datetime(runs["start_time"]).dt.normalize()
runs["hour"]         = pd.to_datetime(runs["start_time"]).dt.hour
runs = runs[runs["distance_km"] >= 0.5].copy()   # filter GPS noise
runs["pace_min_km"]  = runs["elapsed_sec"] / runs["distance_km"] / 60
runs["aerobic_eff"]  = runs["avg_speed"] / runs["avg_hr"]
for col in ["hrz_1_time","hrz_2_time","hrz_3_time","hrz_4_time","hrz_5_time"]:
    runs[col+"_sec"] = runs[col].apply(_hms_to_sec)
runs["vigorous_sec"] = runs["hrz_4_time_sec"] + runs["hrz_5_time_sec"]
runs["vigorous_ratio"] = runs["vigorous_sec"] / runs["elapsed_sec"].replace(0, float("nan"))

_conn_g = sqlite3.connect("../HealthData/DBs/garmin.db")
daily = pd.read_sql_query(
    "SELECT day, rhr, stress_avg, steps, spo2_avg FROM daily_summary",
    _conn_g,
)
_conn_g.close()
daily["day"] = pd.to_datetime(daily["day"])

df_sleep = build_sleep_features()
df_sleep["day"] = pd.to_datetime(df_sleep["day"])

# Merge: runs + daily summary (same day)
runs_daily = runs.merge(daily, left_on="date", right_on="day", how="left")
# Merge: runs + sleep quality (night BEFORE the run)
df_sleep_lag = df_sleep[["day", "score", "total_sleep_hours", "deep_sleep_hours"]].copy()
df_sleep_lag["run_date"] = df_sleep_lag["day"] + pd.Timedelta(days=1)
runs_sleep = runs.merge(df_sleep_lag, left_on="date", right_on="run_date", how="left")

print(f"Running sessions available: {len(runs)}")
print(f"Columns: {list(runs.columns)}")

# --- Chart save helper ---
_CHART_DIR = '/Users/yinhsu/Documents/side_project/garmin_data_analyze/analysis/auto_analyst/outputs/20260312_145329'
_NODE_ID   = 0
_chart_counter = [0]

def save_chart(title=""):
    idx = _chart_counter[0]
    _chart_counter[0] += 1
    fname = f"node_{_NODE_ID}_chart_{idx}.png"
    path  = os.path.join(_CHART_DIR, fname)
    plt.tight_layout()
    plt.savefig(path, dpi=110, bbox_inches="tight")
    plt.close("all")
    print(f"CHART_SAVED: {path}")
    return path

# Monkey-patch plt.show → save_chart so agent code works unchanged
plt.show = save_chart


from scipy.stats import spearmanr
import matplotlib.pyplot as plt

# 核心表現指標: pace_min_km (分/公里，數值越小代表配速越快，表現越好)

# 1. 檢視跑步表現與跑步時生理指標的關係

# 假設1a: 跑步時平均心率越高，配速越快 (pace_min_km 越低) -> 預期負相關
data_hr_pace = runs[["avg_hr", "pace_min_km"]].dropna()
if len(data_hr_pace) > 1:
    r_hr, p_hr = spearmanr(data_hr_pace["avg_hr"], data_hr_pace["pace_min_km"])
    print(f"跑步表現 (pace_min_km) vs. 平均心率 (avg_hr): Spearman r={r_hr:.3f}, p={p_hr:.4f}, n={len(data_hr_pace)}")
else:
    print("數據量不足以分析跑步表現 vs. 平均心率")

# 假設1b: 跑步時平均步頻越高，配速越快 (pace_min_km 越低) -> 預期負相關
data_cadence_pace = runs[["avg_cadence", "pace_min_km"]].dropna()
if len(data_cadence_pace) > 1:
    r_cad, p_cad = spearmanr(data_cadence_pace["avg_cadence"], data_cadence_pace["pace_min_km"])
    print(f"跑步表現 (pace_min_km) vs. 平均步頻 (avg_cadence): Spearman r={r_cad:.3f}, p={p_cad:.4f}, n={len(data_cadence_pace)}")
else:
    print("數據量不足以分析跑步表現 vs. 平均步頻")

# 假設1c: 跑步時總爬升越高，配速越慢 (pace_min_km 越高) -> 預期正相關
data_ascent_pace = runs[["ascent", "pace_min_km"]].dropna()
if len(data_ascent_pace) > 1:
    r_asc, p_asc = spearmanr(data_ascent_pace["ascent"], data_ascent_pace["pace_min_km"])
    print(f"跑步表現 (pace_min_km) vs. 總爬升 (ascent): Spearman r={r_asc:.3f}, p={p_asc:.4f}, n={len(data_ascent_pace)}")
else:
    print("數據量不足以分析跑步表現 vs. 總爬升")


# 2. 檢視跑步表現與前一晚睡眠品質的關係 (使用 runs_sleep)

# 假設2a: 前一晚總睡眠時數越長，跑步表現越好 (pace_min_km 越低) -> 預期負相關
data_sleep_pace = runs_sleep[["total_sleep_hours", "pace_min_km"]].dropna()
if len(data_sleep_pace) > 1:
    r_sleep, p_sleep = spearmanr(data_sleep_pace["total_sleep_hours"], data_sleep_pace["pace_min_km"])
    print(f"跑步表現 (pace_min_km) vs. 前一晚總睡眠時數 (total_sleep_hours): Spearman r={r_sleep:.3f}, p={p_sleep:.4f}, n={len(data_sleep_pace)}")
else:
    print("數據量不足以分析跑步表現 vs. 前一晚總睡眠時數")

# 假設2b: 前一晚睡眠分數越高，跑步表現越好 (pace_min_km 越低) -> 預期負相關
data_score_pace = runs_sleep[["score", "pace_min_km"]].dropna()
if len(data_score_pace) > 1:
    r_score, p_score = spearmanr(data_score_pace["score"], data_score_pace["pace_min_km"])
    print(f"跑步表現 (pace_min_km) vs. 前一晚睡眠分數 (score): Spearman r={r_score:.3f}, p={p_score:.4f}, n={len(data_score_pace)}")
else:
    print("數據量不足以分析跑步表現 vs. 前一晚睡眠分數")


# 3. 檢視跑步表現與當日身體狀況的關係 (使用 runs_daily)

# 假設3a: 當日靜息心率 (RHR) 越低，跑步表現越好 (pace_min_km 越低) -> 預期正相關 (RHR高->pace慢)
data_rhr_pace = runs_daily[["rhr", "pace_min_km"]].dropna()
if len(data_rhr_pace) > 1:
    r_rhr, p_rhr = spearmanr(data_rhr_pace["rhr"], data_rhr_pace["pace_min_km"])
    print(f"跑步表現 (pace_min_km) vs. 當日靜息心率 (rhr): Spearman r={r_rhr:.3f}, p={p_rhr:.4f}, n={len(data_rhr_pace)}")
else:
    print("數據量不足以分析跑步表現 vs. 當日靜息心率")

# 假設3b: 當日平均壓力值越低，跑步表現越好 (pace_min_km 越低) -> 預期正相關 (壓力高->pace慢)
data_stress_pace = runs_daily[["stress_avg", "pace_min_km"]].dropna()
if len(data_stress_pace) > 1:
    r_stress, p_stress = spearmanr(data_stress_pace["stress_avg"], data_stress_pace["pace_min_km"])
    print(f"跑步表現 (pace_min_km) vs. 當日平均壓力 (stress_avg): Spearman r={r_stress:.3f}, p={p_stress:.4f}, n={len(data_stress_pace)}")
else:
    print("數據量不足以分析跑步表現 vs. 當日平均壓力")


# 繪圖展示兩個最相關或最具代表性的關係：平均心率 (直接生理反應) 和 總睡眠時數 (恢復因素)

# 圖1: 跑步表現 (配速) vs. 平均心率
if len(data_hr_pace) > 1:
    fig1, ax1 = plt.subplots(figsize=(8, 6))
    ax1.scatter(data_hr_pace["avg_hr"], data_hr_pace["pace_min_km"], alpha=0.7)
    ax1.set_xlabel("平均心率 (avg_hr)")
    ax1.set_ylabel("配速 (分/公里, 越小越快)")
    ax1.set_title(f"跑步表現 vs. 平均心率 (Spearman r={r_hr:.3f})")
    ax1.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()
else:
    print("數據量不足，無法繪製 跑步表現 vs. 平均心率 圖")

# 圖2: 跑步表現 (配速) vs. 前一晚總睡眠時數
if len(data_sleep_pace) > 1:
    fig2, ax2 = plt.subplots(figsize=(8, 6))
    ax2.scatter(data_sleep_pace["total_sleep_hours"], data_sleep_pace["pace_min_km"], alpha=0.7)
    ax2.set_xlabel("前一晚總睡眠時數 (total_sleep_hours)")
    ax2.set_ylabel("配速 (分/公里, 越小越快)")
    ax2.set_title(f"跑步表現 vs. 前一晚總睡眠時數 (Spearman r={r_sleep:.3f})")
    ax2.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()
else:
    print("數據量不足，無法繪製 跑步表現 vs. 前一晚總睡眠時數 圖")