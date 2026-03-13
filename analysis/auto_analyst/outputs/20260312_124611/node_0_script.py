
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


import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr

# Assume customized.sleep_feature_builder is available in the environment
try:
    from customized.sleep_feature_builder import build_sleep_features
except ImportError:
    # Placeholder for environments where custom module isn't directly available.
    # In the actual analysis environment, this block should not be triggered.
    def build_sleep_features():
        print("Warning: customized.sleep_feature_builder not found. Returning empty DataFrame.")
        return pd.DataFrame({'day': [], 'score': [], 'total_sleep_hours': [], 'deep_sleep_hours': []})