
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
_CHART_DIR = '/Users/yinhsu/Documents/side_project/garmin_data_analyze/analysis/auto_analyst/outputs/20260312_123341'
_NODE_ID   = 2
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
import sqlite3
import matplotlib.pyplot as plt
from scipy.stats import spearmanr, mannwhitneyu, rankdata
import numpy as np
from customized.sleep_feature_builder import build_sleep_features

# --- 1. Load Data ---
# Connect to databases
conn_activities = sqlite3.connect('../HealthData/DBs/garmin_activities.db')
conn_daily = sqlite3.connect('../HealthData/DBs/garmin.db')

# Load running activities
activities_df = pd.read_sql_query("SELECT * FROM activities WHERE sport='running'", conn_activities)
conn_activities.close()

# Load daily summary
daily_summary_df = pd.read_sql_query("SELECT day, rhr, stress_avg, steps FROM daily_summary", conn_daily)
conn_daily.close()

# Load sleep features
sleep_features_df = build_sleep_features()

# --- 2. Data Preprocessing and Merging ---

# Convert start_time to date string for merging activities
activities_df['run_date'] = pd.to_datetime(activities_df['start_time']).dt.strftime('%Y-%m-%d')

# Ensure daily_summary 'day' is date string
daily_summary_df['day'] = pd.to_datetime(daily_summary_df['day']).dt.strftime('%Y-%m-%d')

# Ensure sleep_features 'day' is date string
sleep_features_df['day'] = pd.to_datetime(sleep_features_df['day']).dt.strftime('%Y-%m-%d')

# Merge running data with daily summary
merged_df = activities_df.merge(daily_summary_df, how='left', left_on='run_date', right_on='day', suffixes=('_run', '_daily'))

# Merge with sleep features
merged_df = merged_df.merge(sleep_features_df, how='left', left_on='run_date', right_on='day', suffixes=('_merged', '_sleep'))

# Drop redundant 'day' columns from merges
merged_df = merged_df.drop(columns=['day_daily', 'day_sleep'])

# Calculate derived performance metric: pace_min_km (lower is better)
# Handle cases where distance might be zero or very small to avoid division by zero
merged_df['pace_min_km'] = merged_df.apply(lambda row: (row['elapsed_time'] / 60) / row['distance'] if row['distance'] > 0 else np.nan, axis=1)

# Calculate derived sleep metric: is_deprived
merged_df['is_deprived'] = (merged_df['score'] < 50) | (merged_df['total_sleep_hours'] < 4.5)

# --- 3. Analysis ---

print("--- Analysis of factors influencing running pace (pace_min_km) ---")

# Factors to explore via correlation
correlation_factors = ['total_sleep_hours', 'rhr', 'stress_avg_daily', 'distance']
print("\n[Spearman Correlation with pace_min_km (lower is better)]")

for factor in correlation_factors:
    temp_df = merged_df[[factor, 'pace_min_km']].dropna()
    if len(temp_df) > 1:
        r, p = spearmanr(temp_df[factor], temp_df['pace_min_km'])
        n = len(temp_df)
        print(f"Factor: {factor}")
        print(f"  Spearman r = {r:.3f}, p = {p:.4f}, n = {n}")
        if factor == 'total_sleep_hours':
             print(f"  Interpretation: {'Longer sleep tends to lead to faster pace' if r < 0 else 'Longer sleep tends to lead to slower pace' if r > 0 else 'No clear linear relationship'}.")
        elif factor == 'rhr':
             print(f"  Interpretation: {'Lower RHR tends to lead to faster pace' if r < 0 else 'Higher RHR tends to lead to faster pace' if r > 0 else 'No clear linear relationship'}.")
        elif factor == 'stress_avg_daily':
             print(f"  Interpretation: {'Lower daily stress tends to lead to faster pace' if r < 0 else 'Higher daily stress tends to lead to faster pace' if r > 0 else 'No clear linear relationship'}.")
        elif factor == 'distance':
             print(f"  Interpretation: {'Longer runs tend to be faster' if r < 0 else 'Longer runs tend to be slower' if r > 0 else 'No clear linear relationship'}.")
    else:
        print(f"Not enough data to calculate correlation for {factor}.")

# Factor to explore via group comparison: is_deprived
print("\n[Comparison of pace_min_km based on Sleep Deprivation]")
group_a = merged_df[merged_df['is_deprived'] == False]['pace_min_km'].dropna()
group_b = merged_df[merged_df['is_deprived'] == True]['pace_min_km'].dropna()

if len(group_a) > 1 and len(group_b) > 1:
    stat, p = mannwhitneyu(group_a, group_b, alternative='two-sided')
    mean_a = group_a.mean()
    mean_b = group_b.mean()
    n_a = len(group_a)
    n_b = len(group_b)

    # Calculate rank-biserial correlation as effect size
    # Based on: https://www.statisticshowto.com/williams-t-statistic/
    # Or common formula: r_rb = 1 - (2 * U) / (n1 * n2)
    # where U is the Mann-Whitney U statistic (min(U1, U2))
    # Using scipy's U value directly, and N1*N2
    U1 = mannwhitneyu(group_a, group_b, alternative='less').statistic # U for group A ranks being less than group B
    U2 = mannwhitneyu(group_a, group_b, alternative='greater').statistic # U for group B ranks being less than group A
    # The Mann-Whitney U test reports min(U1, U2) or a U that implicitly considers the 'direction'
    # To get effect size, we need to consider the sum of ranks.
    # A simpler way: r = (mean rank of group A - mean rank of group B) / (N / 2)
    # Or simpler still, use common formula r_rb = 1 - (2 * U_min) / (n1 * n2) when U is the smaller U
    # or r_rb = (U_large - U_small) / (n1 * n2) for difference in U.
    # Or, as effect size for Mann-Whitney is often reported as r = Z / sqrt(N_total)
    # Let's compute rank-biserial r using a common formula:
    # r_rb = 2 * (U_statistic / (n_a * n_b)) - 1
    # Note: scipy's mannwhitneyu returns U_min by default.
    # If the alternative is 'two-sided', the U returned is often U_smaller.
    # A more robust calculation for rank-biserial correlation from a U statistic:
    # r_rb = 1 - (2 * U_statistic) / (n_a * n_b) -- if U_statistic is min(U1, U2)
    # We want to know if Pace_A is different from Pace_B.
    # U = stat from mannwhitneyu. If stat is U_smaller, we need U_larger.
    # U_larger = n_a * n_b - U_smaller
    # rank-biserial r = (U_larger - U_smaller) / (n_a * n_b)
    # Or simpler: compute r_rb = 2 * (U / (n_a * n_b)) - 1 if U is the *sum of ranks* for one group.
    # Let's use rankdata to calculate directly.
    all_paces = pd.concat([group_a, group_