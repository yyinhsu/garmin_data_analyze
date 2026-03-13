
import sys, os
sys.path.insert(0, '/Users/yinhsu/Documents/side_project/garmin_data_analyze/analysis')
os.chdir('/Users/yinhsu/Documents/side_project/garmin_data_analyze/analysis')

import warnings
warnings.filterwarnings("ignore")

import matplotlib
matplotlib.use("Agg")   # non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.nonparametric.smoothers_lowess import lowess

from customized.sleep_feature_builder import build_sleep_features

# --- Chart save helper ---
_CHART_DIR = '/Users/yinhsu/Documents/side_project/garmin_data_analyze/analysis/auto_analyst/outputs/20260312_124611'
_NODE_ID   = 7
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


import sqlite3
import pandas as pd
import re
from customized.sleep_feature_builder import build_sleep_features
from scipy.stats import spearmanr
import matplotlib.pyplot as plt
import seaborn as sns

# 資料庫存取範本
conn_act = sqlite3.connect("../HealthData/DBs/garmin_activities.db")
runs = pd.read_sql_query(
    "SELECT * FROM activities WHERE sport='running' ORDER BY start_time",
    conn_act,
)
conn_act.close()

conn_g = sqlite3.connect("../HealthData/DBs/garmin.db")
daily = pd.read_sql_query(
    "SELECT * FROM daily",
    conn_g,
)