
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
_NODE_ID   = 1
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

# 1. 驗證已知路徑：跑步表現 (配速) 與平均步頻、平均心率的關聯

# 跑步表現 (pace_min_km, 越小越好) vs. 平均步頻 (avg_cadence, 越高越好)
# 預期：負相關 (步頻越高，配速越快)
common_indices_cadence = runs[["pace_min_km", "avg_cadence"]].dropna().index
pace_cadence_r, pace_cadence_p = spearmanr(runs.loc[common_indices_cadence, "pace_min_km"], runs.loc[common_indices_cadence, "avg_cadence"])
print(f"跑步表現 (pace_min_km) vs. 平均步頻 (avg_cadence): Spearman r={pace_cadence_r:.3f}, p={pace_cadence_p:.4f}, n={len(common_indices_cadence)}")

# 跑步表現 (pace_min_km, 越小越好) vs. 平均心率 (avg_hr, 通常越快心率越高)
# 預期：負相關 (心率越高，配速越快，因為更努力)
common_indices_hr = runs[["pace_min_km", "avg_hr"]].dropna().index
pace_hr_r, pace_hr_p = spearmanr(runs.loc[common_indices_hr, "pace_min_km"], runs.loc[common_indices_hr, "avg_hr"])
print(f"跑步表現 (pace_min_km) vs. 平均心率 (avg_hr): Spearman r={pace_hr_r:.3f}, p={pace_hr_p:.4f}, n={len(common_indices_hr)}")

# 2. 探索相關變數：有氧效率、靜息心率、總睡眠時數對跑步表現的影響

# 跑步表現 (pace_min_km, 越小越好) vs. 有氧效率 (aerobic_eff, 越大越省力)
# 預期：負相關 (有氧效率越高，配速越快)
common_indices_aerobic_eff = runs[["pace_min_km", "aerobic_eff"]].dropna().index
pace_aerobic_eff_r, pace_aerobic_eff_p = spearmanr(runs.loc[common_indices_aerobic_eff, "pace_min_km"], runs.loc[common_indices_aerobic_eff, "aerobic_eff"])
print(f"跑步表現 (pace_min_km) vs. 有氧效率 (aerobic_eff): Spearman r={pace_aerobic_eff_r:.3f}, p={pace_aerobic_eff_p:.4f}, n={len(common_indices_aerobic_eff)}")

# 跑步表現 (pace_min_km, 越小越好) vs. 靜息心率 (rhr, 越低體能越好)
# 預期：正相關 (靜息心率越高，體能越差，配速越慢)
common_indices_rhr = runs_daily[["pace_min_km", "rhr"]].dropna().index
pace_rhr_r, pace_rhr_p = spearmanr(runs_daily.loc[common_indices_rhr, "pace_min_km"], runs_daily.loc[common_indices_rhr, "rhr"])
print(f"跑步表現 (pace_min_km) vs. 靜息心率 (rhr, 當天): Spearman r={pace_rhr_r:.3f}, p={pace_rhr_p:.4f}, n={len(common_indices_rhr)}")

# 跑步表現 (pace_min_km, 越小越好) vs. 總睡眠時數 (total_sleep_hours, 越多恢復越好)
# 預期：負相關 (總睡眠時數越多，恢復越好，配速越快)
common_indices_sleep = runs_sleep[["pace_min_km", "total_sleep_hours"]].dropna().index
pace_sleep_r, pace_sleep_p = spearmanr(runs_sleep.loc[common_indices_sleep, "pace_min_km"], runs_sleep.loc[common_indices_sleep, "total_sleep_hours"])
print(f"跑步表現 (pace_min_km) vs. 總睡眠時數 (total_sleep_hours, 前一晚): Spearman r={pace_sleep_r:.3f}, p={pace_sleep_p:.4f}, n={len(common_indices_sleep)}")

# 繪製圖表以視覺化關鍵關係
# 圖1：跑步表現 (配速) 與平均步頻的關係 (核心發現之一)
plt.figure(figsize=(8, 6))
plt.scatter(runs["avg_cadence"], runs["pace_min_km"], alpha=0.7)
plt.title("跑步表現 (配速) vs. 平均步頻")
plt.xlabel("平均步頻 (steps/min)")
plt.ylabel("配速 (min/km, 越小越快)")
plt.grid(True, linestyle='--', alpha=0.6)
plt.show()

# 圖2：跑步表現 (配速) 與有氧效率的關係 (探索新的衍生指標)
plt.figure(figsize=(8, 6))
plt.scatter(runs["aerobic_eff"], runs["pace_min_km"], alpha=0.7)
plt.title("跑步表現 (配速) vs. 有氧效率")
plt.xlabel("有氧效率 (avg_speed / avg_hr, 越大越省力)")
plt.ylabel("配速 (min/km, 越小越快)")
plt.grid(True, linestyle='--', alpha=0.6)
plt.show()