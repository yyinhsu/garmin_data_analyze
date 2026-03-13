
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
from scipy import stats
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
_CHART_DIR = '/Users/yinhsu/Documents/side_project/garmin_data_analyze/analysis/auto_analyst/outputs/20260312_130451'
_NODE_ID   = 3
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


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr

# 設置中文字體以防圖表中文亂碼
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS'] # For macOS
plt.rcParams['axes.unicode_minus'] = False # 解決負號顯示問題

# 假設 runs_sleep 和 runs_daily 已經預載
# runs_sleep: 跑步活動數據 LEFT JOIN 前一晚睡眠特徵
# runs_daily: 跑步活動數據 LEFT JOIN 當天每日彙總數據

# --- 1. 準備綜合分析 DataFrame ---
# 以 runs_sleep 為基礎，它包含了跑步活動和前