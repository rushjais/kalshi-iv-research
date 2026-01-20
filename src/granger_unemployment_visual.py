import pandas as pd
from statsmodels.tsa.stattools import grangercausalitytests, adfuller
import matplotlib.pyplot as plt
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def ensure_outputs_dir():
    Path("outputs").mkdir(exist_ok=True)

print("="*70)
print("GRANGER CAUSALITY - UNEMPLOYMENT (with visualizations)")
print("="*70)

# Load data
kalshi = pd.read_csv("data/kalshi_unemployment_panel.csv")
iv = pd.read_csv("data/yahoo_iv_proxy.csv")

kalshi["date"] = pd.to_datetime(kalshi["date"])
iv["date"] = pd.to_datetime(iv["date"])

# Use median threshold
thresholds = sorted(kalshi["threshold"].unique())
mid_thr = thresholds[len(thresholds) // 2]

ksig = kalshi[kalshi["threshold"] == mid_thr][["date", "prob_close"]].copy()
ksig = ksig.rename(columns={"prob_close": "kalshi_prob"})
ksig = ksig.sort_values("date").drop_duplicates(subset=["date"], keep="last")

df = ksig.merge(iv, on="date", how="inner").sort_values("date")

print(f"\nDataset: {len(df)} observations")
print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")

# Make stationary
df["kalshi_change"] = df["kalshi_prob"].diff()
df["vix_change"] = df["VIX"].diff()
df = df.dropna()

print(f"After differencing: {len(df)} observations")

# Granger test
test_data = df[["vix_change", "kalshi_change"]].dropna()

print(f"\n{'='*70}")
print("GRANGER TEST: Does Kalshi → VIX?")
print(f"{'='*70}\n")

results = grangercausalitytests(test_data, maxlag=5, verbose=False)

# Extract results
lags = []
f_stats = []
p_values = []

print(f"{'Lag':<6} {'F-stat':<12} {'p-value':<12} {'Result'}")
print("-" * 50)

for lag in range(1, 6):
    f_stat = results[lag][0]['ssr_ftest'][0]
    p_value = results[lag][0]['ssr_ftest'][1]
    result = "✓ Significant" if p_value < 0.05 else "✗ Not significant"
    
    lags.append(lag)
    f_stats.append(f_stat)
    p_values.append(p_value)
    
    print(f"{lag:<6} {f_stat:<12.4f} {p_value:<12.4f} {result}")

min_p = min(p_values)
min_lag = lags[p_values.index(min_p)]

print(f"\n{'='*70}")
if min_p < 0.05:
    print(f"✓ Kalshi DOES predict VIX")
    print(f"  Strongest at lag {min_lag} days (p={min_p:.4f})")
else:
    print(f"✗ No significant relationship (min p={min_p:.4f})")
print(f"{'='*70}")

# Create visualizations
ensure_outputs_dir()

# 1. P-values plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# P-values by lag
colors = ['green' if p < 0.05 else 'red' for p in p_values]
ax1.bar(lags, p_values, color=colors, alpha=0.7, edgecolor='black')
ax1.axhline(y=0.05, color='blue', linestyle='--', linewidth=2, label='p=0.05 threshold')
ax1.set_xlabel('Lag (days)', fontsize=12)
ax1.set_ylabel('p-value', fontsize=12)
ax1.set_title('Granger Causality p-values\n(Kalshi → VIX)', fontsize=13, fontweight='bold')
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.set_ylim(0, max(p_values) * 1.1)

# Add annotation for significant lag
if min_p < 0.05:
    ax1.annotate(f'Significant!\np={min_p:.4f}', 
                xy=(min_lag, p_values[min_lag-1]), 
                xytext=(min_lag, p_values[min_lag-1] + 0.02),
                arrowprops=dict(arrowstyle='->', color='green', lw=2),
                fontsize=10, ha='center', color='green', fontweight='bold')

# F-statistics by lag
ax2.bar(lags, f_stats, color='steelblue', alpha=0.7, edgecolor='black')
ax2.set_xlabel('Lag (days)', fontsize=12)
ax2.set_ylabel('F-statistic', fontsize=12)
ax2.set_title('Granger Causality F-statistics\n(Kalshi → VIX)', fontsize=13, fontweight='bold')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('outputs/granger_unemployment_pvalues.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"\n✓ Saved granger_unemployment_pvalues.png")

# 2. Lead-lag correlation plot
correlations = []
lag_range = range(-10, 11)

for lag in lag_range:
    if lag < 0:
        corr = df["kalshi_change"].corr(df["vix_change"].shift(-lag))
    else:
        corr = df["kalshi_change"].shift(lag).corr(df["vix_change"])
    correlations.append(corr)

fig, ax = plt.subplots(figsize=(12, 6))
colors = ['#2E86AB' if x >= 0 else '#A23B72' for x in lag_range]
ax.bar(lag_range, correlations, color=colors, alpha=0.7, edgecolor='black')
ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax.axvline(x=0, color='gray', linestyle='--', linewidth=1)

# Highlight the significant lag from Granger test
if min_p < 0.05:
    ax.axvline(x=min_lag, color='green', linestyle='--', linewidth=2, 
               label=f'Granger significant at lag {min_lag}')

ax.set_xlabel('Lag (days)', fontsize=12)
ax.set_ylabel('Correlation', fontsize=12)
ax.set_title('Lead-Lag Correlation: Kalshi Unemployment vs VIX Changes', 
             fontsize=14, fontweight='bold')
ax.legend(loc='best')
ax.grid(True, alpha=0.3)

# Add text boxes
ax.text(0.02, 0.98, f'Positive lag: Kalshi leads VIX', 
        transform=ax.transAxes, verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='#2E86AB', alpha=0.3))
ax.text(0.02, 0.90, f'Negative lag: VIX leads Kalshi', 
        transform=ax.transAxes, verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='#A23B72', alpha=0.3))

plt.tight_layout()
plt.savefig('outputs/granger_unemployment_leadlag.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"✓ Saved granger_unemployment_leadlag.png")

print("\n" + "="*70)
print("VISUALIZATION COMPLETE")
print("="*70)
print("\nGenerated plots:")
print("  1. granger_unemployment_pvalues.png - Statistical significance by lag")
print("  2. granger_unemployment_leadlag.png - Lead-lag correlation pattern")
