
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
_NODE_ID   = 6
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
import seaborn as sns
from scipy.stats import spearmanr, mannwhitneyu, ranksums
import numpy as np

# Helper function to convert HH:MM:SS to total seconds
def hms_to_seconds(time_str):
    if pd.isna(time_str) or not isinstance(time_str, str):
        return 0
    try:
        parts = time_str.split(':')
        if len(parts) == 3:
            h, m, s = map(int, parts)
            return h * 3600 + m * 60 + s
        elif len(parts) == 2: # sometimes only MM:SS
            m, s = map(int, parts)
            return m * 60 + s
    except ValueError:
        return 0
    return 0

# 1. Load Running Activities Data
conn_activities = sqlite3.connect('../HealthData/DBs/garmin_activities.db')
running_df = pd.read_sql_query("SELECT * FROM activities WHERE sport='running'", conn_activities)
conn_activities.close()

# Ensure start_time is datetime and extract date
running_df['start_time'] = pd.to_datetime(running_df['start_time'])
running_df['day'] = running_df['start_time'].dt.strftime('%Y-%m-%d')

# Calculate performance metrics
# pace_min_km = elapsed_time_sec / (distance_km * 60)
running_df['pace_min_km'] = (running_df['elapsed_time'] / 60) / running_df['distance']
running_df['aerobic_efficiency'] = running_df['avg_speed'] / running_df['avg_hr']

# Convert HR zone times to seconds for vigorous ratio
for i in range(1, 6):
    running_df[f'hrz_{i}_sec'] = running_df[f'hrz_{i}_time'].apply(hms_to_seconds)
running_df['elapsed_time_sec'] = running_df['elapsed_time'] # Ensure we have this explicitly
running_df['vigorous_ratio'] = (running_df['hrz_4_sec'] + running_df['hrz_5_sec']) / running_df['elapsed_time_sec']
running_df.replace([np.inf, -np.inf], np.nan, inplace=True) # handle division by zero for ratio

# 2. Load Daily Summary Data
conn_daily = sqlite3.connect('../HealthData/DBs/garmin.db')
daily_summary_df = pd.read_sql_query("SELECT day, rhr, stress_avg, steps, vigorous_activity_time, spo2_avg, rr_waking_avg FROM daily_summary", conn_daily)
conn_daily.close()

daily_summary_df['day'] = pd.to_datetime(daily_summary_df['day']).dt.strftime('%Y-%m-%d')

# 3. Load Sleep Features Data
df_sleep = build_sleep_features()
df_sleep['day'] = pd.to_datetime(df_sleep['day']).dt.strftime('%Y-%m-%d')

# Derive 'is_deprived'
df_sleep['is_deprived'] = (df_sleep['score'] < 50) | (df_sleep['total_sleep_hours'] < 4.5)

# 4. Merge Datasets
# Merge running_df with daily_summary_df
merged_df = pd.merge(running_df, daily_summary_df, on='day', how='left')

# Merge with sleep features
final_df = pd.merge(merged_df, df_sleep, on='day', how='left')

# Drop rows where pace_min_km is NaN or infinite (e.g., if distance was 0)
final_df.dropna(subset=['pace_min_km'], inplace=True)

print(f"Total running activities for analysis: {len(final_df)}")

# 5. Explore factors affecting pace_min_km (lower is better)
# Variables to investigate:
# - avg_cadence (from activity)
# - training_load (from activity)
# - rhr (from daily_summary)
# - stress_avg (from daily_summary)
# - total_sleep_hours (from sleep_features)
# - rolling_7d_sleep_avg (from sleep_features)
# - is_deprived (derived from sleep_features)

print("\n--- Correlation Analysis with Running Pace (pace_min_km) ---")

analysis_variables = [
    'avg_cadence', 'training_load', 'rhr', 'stress_avg',
    'total_sleep_hours', 'rolling_7d_sleep_avg', 'aerobic_efficiency'
]

results = {}
for var in analysis_variables:
    temp_df = final_df.dropna(subset=['pace_min_km', var])
    if len(temp_df) > 1:
        r, p = spearmanr(temp_df['pace_min_km'], temp_df[var])
        n = len(temp_df)
        results[var] = {'r': r, 'p': p, 'n': n}
        print(f"Pace vs. {var}: Spearman r = {r:.3f}, p = {p:.4f}, n = {n}")
    else:
        print(f"Not enough data to correlate Pace vs. {var}")

# 6. Group Comparison for is_deprived
print("\n--- Group Comparison: Pace vs. Sleep Deprivation (is_deprived) ---")
group_deprived = final_df[final_df['is_deprived'] == True]['pace_min_km'].dropna()
group_not_deprived = final_df[final_df['is_deprived'] == False]['pace_min_km'].dropna()

if len(group_deprived) > 1 and len(group_not_deprived) > 1:
    mean_deprived = group_deprived.mean()
    mean_not_deprived = group_not_deprived.mean()
    
    # Mann-Whitney U test for non-normal distributions
    stat, p_mw = mannwhitneyu(group_deprived, group_not_deprived, alternative='two-sided')
    
    # Calculate effect size (rank-biserial correlation)
    # r = 1 - (2 * U) / (n1 * n2)
    # For independent samples: r = 1 - (2 * U_min) / (n1 * n2) or use direct formula for r_biserial
    # Using scipy.stats.ranksums to get Z-score, then convert to r (r = Z / sqrt(N)) or use a dedicated formula.
    # A simpler rank-biserial r can be calculated as: 2 * (mean_rank_group1 - mean_rank_total) / N
    # Or based on Z score from ranksums: r = Z / sqrt(N) where N = n1+n2
    
    n1 = len(group_deprived)
    n2 = len(group_not_deprived)
    
    # Using a common approximation for rank-biserial correlation from Mann-Whitney U
    # r = 1 - 2*U_min / (n1*n2) - this is for U, not for the effect size directly.
    # Let's use simpler interpretation: Cohen's d or common language effect size for now if direct r_biserial is complex.
    # For now, let's report means and p-value.
    
    # Rank-biserial correlation using common formula
    all_paces = pd.concat([group_deprived, group_not_deprived])
    ranks = all_paces.rank()
    mean_rank_deprived = ranks.loc[group_deprived.index].mean()
    mean_rank_not_deprived = ranks.loc[group_not_deprived.index].mean()

    # r_biserial = (mean_rank_deprived - mean_rank_not_deprived) / (len(all_paces)/2) approximately
    # More precisely: r = 2 * (mean_rank_group1 - (N+1)/2) / (N-1) - This is for one group vs total mean rank
    # Alternative: r = (U_statistic - (n1*n2)/2) / ((n1*n2)/2) for non-directionality or use Z from Wilcoxon.
    # Or, the common r = Z / sqrt(N) approach, where Z is from Wilcoxon/Ranksums
    
    stat_ranksums, p_ranksums = ranksums(group_deprived, group_not_deprived)
    eff_size = stat_ranksums / np.sqrt(n1 + n2) # Approximation for effect size based on Z-score from ranksums

    print(f"Mean pace (Sleep Deprived) = {mean_deprived:.2f} min/km (n={n1})")
    print(f"Mean pace (Not Sleep Deprived) = {mean_not_deprived:.2f} min/km (n={n2})")
    print(f"Mann-Whitney U p-value = {p_mw:.4f}")
    print(f"Effect size (Z-based r) = {eff_size:.3f}")
else:
    print("Not enough data to compare pace between sleep deprived and not sleep deprived groups.")


# 7. Plotting
# Plot 1: Scatter plot for strongest correlation (e.g., Pace vs. avg_cadence or aerobic_efficiency)
# Assuming avg_cadence has a meaningful correlation
if 'avg_cadence' in results and results['avg_cadence']['n'] > 0:
    plt.figure(figsize=(10, 6))
    sns.regplot(x='avg_cadence', y='pace_min_km', data=final_df.dropna(subset=['avg_cadence', 'pace_min_km']), scatter_kws={'alpha':0.6}, line_kws={'color': 'red'})
    plt.title(f'Running Pace vs. Average Cadence (Spearman r = {results["avg_cadence"]["r"]:.3f})')
    plt.xlabel('Average Cadence (steps/min)')
    plt.ylabel('Pace (min/km, lower is faster)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.show()

# Plot 2: Box plot for Pace vs. is_deprived
if len(group_deprived) > 1 and len(group_not_deprived) > 1