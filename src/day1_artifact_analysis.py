"""
Aadhaar Day-1 Artifact Analysis
-------------------------------
Generates the polished charts for UIDAI Hackathon submission.

Author: Dhananjay
Date: Jan 2025
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Create outputs folder
if not os.path.exists('outputs'):
    os.makedirs('outputs')

print("=" * 60)
print("UIDAI Day 1 Artifact Analysis")
print("=" * 60)

# --- Load Data ---
print("\nLoading biometric data...")
data_path = 'data/biometric/api_data_aadhar_biometric/api_data_aadhar_biometric_0_500000.csv'
df = pd.read_csv(data_path)
df.columns = df.columns.str.strip()

# Parse dates
df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')
df = df.dropna(subset=['date'])
df['day'] = df['date'].dt.day
df['month'] = df['date'].dt.month
df['year_month'] = df['date'].dt.to_period('M')

print(f"Loaded {len(df):,} records")
print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")

# --- Calculate Key Metrics ---
day1_records = len(df[df['day'] == 1])
total_records = len(df)
day1_pct = day1_records / total_records * 100

day1_volume = df[df['day'] == 1]['bio_age_17_'].sum()
other_avg = df[df['day'] != 1].groupby('day')['bio_age_17_'].sum().mean()
volume_ratio = day1_volume / other_avg

print(f"\nKey Finding: {day1_pct:.1f}% of records on Day 1")
print(f"Volume concentration: {volume_ratio:.0f}x")

# ============================================================
# CHART 1: Administrative Heartbeat (Time Series)
# ============================================================
print("\n--- Generating Chart 1: Administrative Heartbeat ---")

monthly_day1 = df[df['day'] == 1].groupby('year_month')['bio_age_17_'].sum() / 1e6
months = [str(m) for m in monthly_day1.index]

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(months, monthly_day1.values, 'k-', linewidth=2, label='Daily Volume')
ax.scatter(months, monthly_day1.values, c='red', s=100, zorder=5, label='1st of Month (Batch Upload)')

for i, (m, v) in enumerate(zip(months, monthly_day1.values)):
    ax.annotate(f'{v:.1f}M', (i, v), textcoords="offset points", 
                xytext=(0,10), ha='center', fontsize=10, color='red', fontweight='bold')

ax.set_xlabel('Date (2025)', fontsize=12)
ax.set_ylabel('Biometric Updates (Millions)', fontsize=12)
ax.set_title('The Administrative Heartbeat: Why Real-Time Analysis Fails', fontsize=14, fontweight='bold')
ax.legend(loc='upper right')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('outputs/chart1_heartbeat.png', dpi=200, bbox_inches='tight')
print("  Saved: outputs/chart1_heartbeat.png")

# ============================================================
# CHART 2: State Artifact Index (Batch Processing Intensity)
# ============================================================
print("\n--- Generating Chart 2: State Artifact Index ---")

state_day1 = df[df['day'] == 1].groupby('state')['bio_age_17_'].sum()
state_other = df[df['day'] != 1].groupby('state')['bio_age_17_'].sum() / 30
state_ratio = (state_day1 / state_other).dropna().sort_values(ascending=True)

# Filter significant states and top 15
state_counts = df.groupby('state').size()
state_ratio = state_ratio[state_ratio.index.isin(state_counts[state_counts > 1000].index)]
state_ratio = state_ratio.tail(15)

fig, ax = plt.subplots(figsize=(10, 8))
bars = ax.barh(range(len(state_ratio)), state_ratio.values, color='steelblue')
ax.set_yticks(range(len(state_ratio)))
ax.set_yticklabels(state_ratio.index, fontsize=10)
ax.axvline(1.0, color='red', linestyle='--', linewidth=2, label='1.0 (Day 1 > Total of Rest!)')
ax.set_xlabel('Batch Processing Intensity (Ratio of Day 1 vs All Other Days)', fontsize=11)
ax.set_title('The "Artificial" States: Where Data is Batched, Not Streamed', 
             fontsize=14, fontweight='bold', color='darkred')

# Add value labels
for i, v in enumerate(state_ratio.values):
    ax.text(v + 0.2, i, f'{v:.1f}x', va='center', fontweight='bold')

ax.legend(loc='lower right')
plt.tight_layout()
plt.savefig('outputs/chart2_artifact_index.png', dpi=200, bbox_inches='tight')
print("  Saved: outputs/chart2_artifact_index.png")

# ============================================================
# CHART 3: Monthly Consistency (100% bars)
# ============================================================
print("\n--- Generating Chart 3: Monthly Consistency ---")

monthly_pct = []
for m in sorted(df['year_month'].unique()):
    mdata = df[df['year_month'] == m]
    day1_vol = mdata[mdata['day'] == 1]['bio_age_17_'].sum()
    total_vol = mdata['bio_age_17_'].sum()
    pct = (day1_vol / total_vol * 100) if total_vol > 0 else 0
    monthly_pct.append({'month': str(m), 'pct': pct})

monthly_df = pd.DataFrame(monthly_pct)
avg_pct = monthly_df['pct'].mean()

fig, ax = plt.subplots(figsize=(12, 6))
bars = ax.bar(range(len(monthly_df)), monthly_df['pct'], color='darkred', edgecolor='black')
ax.axhline(50, color='orange', linestyle='--', linewidth=2, label='50% threshold (already problematic)')
ax.axhline(avg_pct, color='blue', linestyle='--', linewidth=2, label=f'Average = {avg_pct:.1f}%')

# Add percentage labels
for i, pct in enumerate(monthly_df['pct']):
    ax.text(i, pct + 2, f'{pct:.0f}%', ha='center', fontweight='bold', fontsize=11)

ax.set_xticks(range(len(monthly_df)))
ax.set_xticklabels(monthly_df['month'], fontsize=10)
ax.set_ylabel('% of Monthly Data on Day 1', fontsize=12)
ax.set_ylim(0, 110)
ax.legend(loc='upper right')

# Title with key message
ax.set_title(f'AADHAAR TEMPORAL CORRUPTION: {avg_pct:.0f}% of Monthly Data Compressed Into Day 1\n'
             'This is NOT citizen behavior - this is upload artifact', 
             fontsize=13, fontweight='bold', color='darkred')

plt.tight_layout()
plt.savefig('outputs/chart3_monthly.png', dpi=200, bbox_inches='tight')
print("  Saved: outputs/chart3_monthly.png")

# ============================================================
# CHART 4: State-by-State Analysis (Color-coded)
# ============================================================
print("\n--- Generating Chart 4: Universal System Failure ---")

state_day1_pct = []
for state in df['state'].unique():
    sdata = df[df['state'] == state]
    if len(sdata) < 100:  # Lower threshold to include more states
        continue
    day1_vol = sdata[sdata['day'] == 1]['bio_age_17_'].sum()
    total_vol = sdata['bio_age_17_'].sum()
    pct = (day1_vol / total_vol * 100) if total_vol > 0 else 0
    state_day1_pct.append({'state': state, 'pct': pct})

state_df = pd.DataFrame(state_day1_pct).sort_values('pct', ascending=True)

# Color coding
colors = []
for pct in state_df['pct']:
    if pct > 80:
        colors.append('darkred')
    elif pct > 50:
        colors.append('orange')
    else:
        colors.append('gold')

severe = len(state_df[state_df['pct'] > 80])
moderate = len(state_df[(state_df['pct'] > 50) & (state_df['pct'] <= 80)])
mild = len(state_df[state_df['pct'] <= 50])

fig, ax = plt.subplots(figsize=(12, 10))
bars = ax.barh(range(len(state_df)), state_df['pct'].values, color=colors)
ax.set_yticks(range(len(state_df)))
ax.set_yticklabels(state_df['state'].values, fontsize=8)
ax.axvline(50, color='gray', linestyle='--', linewidth=1.5)
ax.axvline(80, color='gray', linestyle='--', linewidth=1.5)
ax.set_xlabel('% of Monthly Data on Day 1', fontsize=12)
ax.set_xlim(0, 100)

# Legend
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor='darkred', label=f'SEVERE (>80%): {severe} states'),
    Patch(facecolor='orange', label=f'MODERATE (50-80%): {moderate} states'),
    Patch(facecolor='gold', label=f'MILD (<50%): {mild} states')
]
ax.legend(handles=legend_elements, loc='lower right', fontsize=10)

ax.set_title(f'State-by-State Analysis: UNIVERSAL System Failure\n'
             f'(Red = >80% on day 1 | Orange = 50-80% | Yellow = <50%)', 
             fontsize=13, fontweight='bold')

plt.tight_layout()
plt.savefig('outputs/chart4_states.png', dpi=200, bbox_inches='tight')
print("  Saved: outputs/chart4_states.png")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)
print(f"""
Summary:
  - {day1_pct:.1f}% of records on Day 1 (expected: 3.2%)
  - Volume concentration: {volume_ratio:.0f}x
  - Monthly average: {avg_pct:.0f}% on Day 1
  - {severe} states SEVERE, {moderate} states MODERATE
  
Charts saved to outputs/ folder:
  - chart1_heartbeat.png
  - chart2_artifact_index.png
  - chart3_monthly.png
  - chart4_states.png
  
Conclusion: This is batch processing, not citizen behavior.
""")
