import pandas as pd
from statsmodels.tsa.stattools import grangercausalitytests, adfuller
import warnings
warnings.filterwarnings('ignore')

print("="*70)
print("GRANGER CAUSALITY - UNEMPLOYMENT MARKETS")
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
print(f"Threshold: Unemployment ≥ {mid_thr}%")
print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")

# Make stationary
df["kalshi_change"] = df["kalshi_prob"].diff()
df["vix_change"] = df["VIX"].diff()
df = df.dropna()

print(f"\nAfter differencing: {len(df)} observations")

# Granger test
test_data = df[["vix_change", "kalshi_change"]].dropna()

print(f"\n{'='*70}")
print("GRANGER TEST: Does Kalshi → VIX?")
print(f"{'='*70}")

results = grangercausalitytests(test_data, maxlag=5, verbose=False)

print(f"\n{'Lag':<6} {'F-stat':<12} {'p-value':<12} {'Result'}")
print("-" * 50)

for lag in range(1, 6):
    f_stat = results[lag][0]['ssr_ftest'][0]
    p_value = results[lag][0]['ssr_ftest'][1]
    result = "✓ Significant" if p_value < 0.05 else "✗ Not significant"
    print(f"{lag:<6} {f_stat:<12.4f} {p_value:<12.4f} {result}")

min_p = min(results[lag][0]['ssr_ftest'][1] for lag in range(1, 6))

print(f"\n{'='*70}")
if min_p < 0.05:
    print(f"✓ Kalshi DOES predict VIX (p={min_p:.4f})")
else:
    print(f"✗ No significant relationship (p={min_p:.4f})")
print(f"{'='*70}")
