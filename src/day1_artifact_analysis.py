"""
Aadhaar Day-1 Artifact Analysis
-------------------------------
Digging into why so much data lands on the 1st of every month.
Spoiler: it's not because everyone loves updating on day 1.

Author: [Your Name]
Date: Jan 2025
"""

import pandas as pd
import matplotlib.pyplot as plt
import os

# gonna need somewhere to dump the charts
if not os.path.exists('outputs'):
    os.makedirs('outputs')

print("=" * 60)
print("Let's figure out what's going on with Day 1...")
print("=" * 60)

# --- STEP 1: Load the data ---
# using the biometric updates file, it's the biggest one
print("\nLoading biometric data...")

data_path = 'data/biometric/api_data_aadhar_biometric/api_data_aadhar_biometric_0_500000.csv'
df = pd.read_csv(data_path)

# clean up column names, sometimes there's whitespace
df.columns = df.columns.str.strip()

# parse the dates - they're in DD-MM-YYYY format (Indian style)
df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')

# drop any rows where date parsing failed
before = len(df)
df = df.dropna(subset=['date'])
after = len(df)
if before != after:
    print(f"Dropped {before - after} rows with bad dates")

print(f"Got {len(df):,} records")
print(f"From {df['date'].min().date()} to {df['date'].max().date()}")

# --- STEP 2: Extract day of month ---
df['day'] = df['date'].dt.day
df['month'] = df['date'].dt.month

# --- STEP 3: The big question - how many records on each day? ---
print("\n--- Checking record distribution by day ---")

records_per_day = df.groupby('day').size()
day1_count = records_per_day.get(1, 0)
total = len(df)

# what would we expect if it was evenly distributed?
expected_per_day = total / 31

pct_on_day1 = (day1_count / total) * 100
concentration = day1_count / expected_per_day

print(f"Records on Day 1: {day1_count:,} ({pct_on_day1:.1f}%)")
print(f"Expected if uniform: {expected_per_day:,.0f} (3.2%)")
print(f"That's {concentration:.1f}x more than expected!")

# --- STEP 4: What about volume (actual updates, not just rows)? ---
print("\n--- Now checking actual update volume ---")

volume_per_day = df.groupby('day')['bio_age_17_'].sum()
day1_volume = volume_per_day.get(1, 0)

# average for other days
other_days = volume_per_day[volume_per_day.index != 1]
avg_other = other_days.mean()

volume_ratio = day1_volume / avg_other

print(f"Volume on Day 1: {day1_volume:,}")
print(f"Avg other days: {avg_other:,.0f}")
print(f"Volume concentration: {volume_ratio:.0f}x - holy shit")

# --- STEP 5: Is this consistent across months? ---
print("\n--- Checking if pattern holds every month ---")

for month in sorted(df['month'].unique()):
    month_data = df[df['month'] == month]
    day1_in_month = len(month_data[month_data['day'] == 1])
    pct = (day1_in_month / len(month_data)) * 100
    print(f"  Month {month}: {pct:.0f}% on Day 1")

# --- STEP 6: Same for all states? ---
print("\n--- Checking across states ---")

states_checked = 0
states_with_spike = 0

for state in df['state'].unique():
    state_data = df[df['state'] == state]
    
    # skip if too few records
    if len(state_data) < 100:
        continue
    
    states_checked += 1
    day1_pct = len(state_data[state_data['day'] == 1]) / len(state_data) * 100
    
    if day1_pct > 50:
        states_with_spike += 1

print(f"Checked {states_checked} states with significant data")
print(f"{states_with_spike} have >50% on Day 1")
print(f"That's {states_with_spike/states_checked*100:.0f}% of states - it's everywhere")

# --- CHARTS TIME ---
print("\n--- Making some charts ---")

# Chart 1: Bar chart of records by day
fig, ax = plt.subplots(figsize=(12, 5))

colors = ['#d32f2f' if d == 1 else '#1976d2' for d in records_per_day.index]
ax.bar(records_per_day.index, records_per_day.values, color=colors)
ax.axhline(expected_per_day, color='orange', linestyle='--', linewidth=2, 
           label=f'Expected ({expected_per_day:,.0f})')
ax.set_xlabel('Day of Month')
ax.set_ylabel('Number of Records')
ax.set_title('Day 1 Concentration: 26.6% of Records on Single Day', fontweight='bold')
ax.legend()
ax.set_xticks(range(1, 32))
plt.tight_layout()
plt.savefig('outputs/chart1_day_distribution.png', dpi=200)
print("  Saved chart1_day_distribution.png")

# Chart 2: Volume by day
fig, ax = plt.subplots(figsize=(12, 5))

colors = ['#d32f2f' if d == 1 else '#4caf50' for d in volume_per_day.index]
ax.bar(volume_per_day.index, volume_per_day.values / 1e6, color=colors)
ax.axhline(volume_per_day.mean() / 1e6, color='orange', linestyle='--', 
           linewidth=2, label='Average')
ax.set_xlabel('Day of Month')
ax.set_ylabel('Updates (Millions)')
ax.set_title(f'Volume Concentration: {day1_volume/1e6:.1f}M on Day 1 ({volume_ratio:.0f}x Average)', 
             fontweight='bold')
ax.legend()
ax.set_xticks(range(1, 32))
plt.tight_layout()
plt.savefig('outputs/chart2_volume_by_day.png', dpi=200)
print("  Saved chart2_volume_by_day.png")

# Chart 3: Monthly consistency
monthly_pcts = []
for m in sorted(df['month'].unique()):
    mdata = df[df['month'] == m]
    pct = len(mdata[mdata['day'] == 1]) / len(mdata) * 100
    monthly_pcts.append({'month': m, 'pct': pct})

monthly_df = pd.DataFrame(monthly_pcts)

fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(range(len(monthly_df)), monthly_df['pct'], color='#d32f2f')
ax.set_xticks(range(len(monthly_df)))
ax.set_xticklabels([f"Month {m}" for m in monthly_df['month']])
ax.axhline(3.2, color='green', linestyle='--', linewidth=2, label='Expected 3.2%')
ax.set_ylabel('% of Records on Day 1')
ax.set_title('Pattern Repeats Every Month', fontweight='bold')

# add labels on bars
for i, pct in enumerate(monthly_df['pct']):
    ax.text(i, pct + 2, f'{pct:.0f}%', ha='center', fontweight='bold')

ax.legend()
ax.set_ylim(0, 110)
plt.tight_layout()
plt.savefig('outputs/chart3_monthly_pattern.png', dpi=200)
print("  Saved chart3_monthly_pattern.png")

# Chart 4: State breakdown
state_day1 = df[df['day'] == 1].groupby('state').size()
state_total = df.groupby('state').size()
state_pct = (state_day1 / state_total * 100).dropna()

# only keep states with decent sample size
state_pct = state_pct[state_total > 500].sort_values()

fig, ax = plt.subplots(figsize=(10, 8))

colors = ['#d32f2f' if p > 80 else '#ff9800' if p > 50 else '#4caf50' 
          for p in state_pct.values]
ax.barh(range(len(state_pct)), state_pct.values, color=colors)
ax.set_yticks(range(len(state_pct)))
ax.set_yticklabels(state_pct.index, fontsize=8)
ax.axvline(3.2, color='green', linestyle='--', linewidth=2, label='Expected 3.2%')
ax.set_xlabel('% of Records on Day 1')
ax.set_title('All States Show Day 1 Concentration', fontweight='bold')
ax.legend()
ax.set_xlim(0, 100)
plt.tight_layout()
plt.savefig('outputs/chart4_state_breakdown.png', dpi=200)
print("  Saved chart4_state_breakdown.png")

# --- WRAP UP ---
print("\n" + "=" * 60)
print("DONE")
print("=" * 60)
print(f"""
Summary:
  - {pct_on_day1:.1f}% of records fall on Day 1 (expected: 3.2%)
  - Volume concentration: {volume_ratio:.0f}x higher than other days
  - Pattern holds in {states_with_spike}/{states_checked} states
  
Conclusion: This ain't citizen behavior. It's batch processing.
The 'date' field is upload time, not transaction time.
""")
