
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
_NODE_ID   = 4
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


# 步驟1：計算相關係數
# 驗證假設：跑步當天的靜息心率 (rhr) 是否影響跑步表現 (pace_min_km)
# 預期：更低的靜息心率通常與更好的跑步體能相關，因此預期靜息心率越高，配速越慢 (pace_min_km 越高)
# 這表示我們期望看到一個正相關。
from scipy.stats import spearmanr

# 準備數據：從 runs_daily 中選取 'pace_min_km' 和 'rhr'，並移除任何包含缺失值的行。
# 靜息心率 (rhr) 來自 daily_summary 表，如果跑步當天沒有對應的 daily_summary 記錄，則 rhr 可能為 NaN。
df_for_analysis = runs_daily[["pace_min_km", "rhr"]].dropna()

# 確保有足夠的數據點進行相關性分析
if len(df_for_analysis) > 1:
    r, p = spearmanr(df_for_analysis["rhr"], df_for_analysis["pace_min_km"])
    n = len(df_for_analysis)
    print(f"跑步配速 (pace_min_km) vs 當天靜息心率 (rhr): Spearman r={r:.3f}, p={p:.4f}, n={n}")

    # 步驟2：繪製散點圖以視覺化關係
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(df_for_analysis["rhr"], df_for_analysis["pace_min_km"], alpha=0.7)
    
    # 添加趨勢線
    # 使用 numpy.polyfit 進行線性擬合
    z = np.polyfit(df_for_analysis["rhr"], df_for_analysis["pace_min_km"], 1)
    p_fit = np.poly1d(z)
    ax.plot(df_for_analysis["rhr"], p_fit(df_for_analysis["rhr"]), 
            color='red', linestyle='--', label=f'趨勢線 (y={z[0]:.2f}x + {z[1]:.2f})')

    ax.set_xlabel("當天靜息心率 (bpm)")
    ax.set_ylabel("跑步配速 (分/公里, 越低越快)")
    ax.set_title("跑步配速與當天靜息心率的關係")
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend()
    plt.show()
else:
    print("沒有足夠的數據點來分析跑步配速與當天靜息心率的關係。請檢查 'runs_daily' 和 'rhr' 欄位。")