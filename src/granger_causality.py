"""
Granger Causality Analysis
Tests whether Kalshi probabilities predict future VIX movements
"""

import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import grangercausalitytests
from statsmodels.tsa.stattools import adfuller
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')


def load_and_merge_data():
    """Load and merge Kalshi and Yahoo data"""
    print("Loading data...")
    
    kalshi = pd.read_csv("data/kalshi_threshold_panel.csv")
    iv = pd.read_csv("data/yahoo_iv_proxy.csv")
    
    kalshi["date"] = pd.to_datetime(kalshi["date"])
    iv["date"] = pd.to_datetime(iv["date"])
    
    # Use median threshold
    thresholds = sorted(kalshi["threshold"].unique())
    mid_thr = thresholds[len(thresholds) // 2]
    
    ksig = kalshi[kalshi["threshold"] == mid_thr][["date", "prob_close"]].copy()
    ksig = ksig.sort_values("date").drop_duplicates(subset=["date"], keep="last")
    ksig = ksig.rename(columns={"prob_close": "kalshi_prob"})
    
    # Merge
    df = ksig.merge(iv, on="date", how="inner").sort_values("date")
    
    print(f"Merged dataset: {len(df)} observations")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    
    return df, mid_thr


def check_stationarity(series, name):
    """
    Test for stationarity using Augmented Dickey-Fuller test
    Stationarity is required for Granger causality
    """
    print(f"\n{'='*60}")
    print(f"Stationarity Test: {name}")
    print(f"{'='*60}")
    
    result = adfuller(series.dropna(), autolag='AIC')
    
    print(f"ADF Statistic: {result[0]:.4f}")
    print(f"p-value: {result[1]:.4f}")
    print(f"Critical values:")
    for key, value in result[4].items():
        print(f"  {key}: {value:.4f}")
    
    if result[1] < 0.05:
        print(f"✓ {name} is stationary (p < 0.05)")
        return True
    else:
        print(f"✗ {name} is NOT stationary (p >= 0.05)")
        print(f"  Recommendation: Use first differences")
        return False


def make_stationary(df):
    """
    Convert non-stationary series to stationary by taking first differences
    """
    print("\nConverting to first differences (changes)...")
    
    df = df.copy()
    df["kalshi_change"] = df["kalshi_prob"].diff()
    df["vix_change"] = df["VIX"].diff()
    
    # Drop first row (NaN after diff)
    df = df.dropna()
    
    print(f"Observations after differencing: {len(df)}")
    
    return df


def run_granger_test(data, var1, var2, maxlag=5):
    """
    Run Granger causality test
    Tests if var1 Granger-causes var2
    """
    print(f"\n{'='*60}")
    print(f"Granger Causality Test: Does {var1} → {var2}?")
    print(f"{'='*60}")
    
    # Prepare data
    test_data = data[[var2, var1]].dropna()
    
    if len(test_data) < maxlag * 3:
        print(f"✗ Not enough observations ({len(test_data)}) for lag {maxlag}")
        return None
    
    print(f"Testing with max lag: {maxlag}")
    print(f"Sample size: {len(test_data)}")
    
    try:
        results = grangercausalitytests(test_data, maxlag=maxlag, verbose=False)
        
        print(f"\n{'Lag':<6} {'F-stat':<12} {'p-value':<12} {'Result'}")
        print("-" * 50)
        
        for lag in range(1, maxlag + 1):
            # Extract F-test results (ssr_ftest)
            f_stat = results[lag][0]['ssr_ftest'][0]
            p_value = results[lag][0]['ssr_ftest'][1]
            
            result = "✓ Significant" if p_value < 0.05 else "✗ Not significant"
            print(f"{lag:<6} {f_stat:<12.4f} {p_value:<12.4f} {result}")
        
        # Overall interpretation
        print("\n" + "="*60)
        min_pval = min(results[lag][0]['ssr_ftest'][1] for lag in range(1, maxlag + 1))
        
        if min_pval < 0.05:
            print(f"✓ CONCLUSION: {var1} DOES Granger-cause {var2}")
            print(f"  (Minimum p-value: {min_pval:.4f} < 0.05)")
        else:
            print(f"✗ CONCLUSION: {var1} does NOT Granger-cause {var2}")
            print(f"  (Minimum p-value: {min_pval:.4f} >= 0.05)")
        
        return results
        
    except Exception as e:
        print(f"✗ Error running test: {e}")
        return None


def compute_lead_lag_correlation(df, var1, var2, max_lag=10):
    """
    Compute lead-lag correlation
    Helps identify if one series leads the other
    """
    print(f"\n{'='*60}")
    print(f"Lead-Lag Correlation: {var1} vs {var2}")
    print(f"{'='*60}")
    
    correlations = []
    
    print(f"\n{'Lag':<6} {'Correlation':<15} {'Interpretation'}")
    print("-" * 60)
    
    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            # var1 lags var2 (var2 leads)
            corr = df[var1].corr(df[var2].shift(-lag))
        else:
            # var1 leads var2
            corr = df[var1].shift(lag).corr(df[var2])
        
        correlations.append((lag, corr))
        
        if abs(lag) <= 5:  # Print nearby lags
            if lag < 0:
                interp = f"{var2} leads by {abs(lag)}"
            elif lag > 0:
                interp = f"{var1} leads by {lag}"
            else:
                interp = "Contemporaneous"
            
            print(f"{lag:<6} {corr:<15.4f} {interp}")
    
    # Find max correlation
    max_corr_lag, max_corr = max(correlations, key=lambda x: abs(x[1]))
    
    print(f"\n{'='*60}")
    print(f"Maximum correlation: {max_corr:.4f} at lag {max_corr_lag}")
    
    if max_corr_lag > 0:
        print(f"✓ {var1} LEADS {var2} by {max_corr_lag} days")
    elif max_corr_lag < 0:
        print(f"✓ {var2} LEADS {var1} by {abs(max_corr_lag)} days")
    else:
        print(f"✓ Contemporaneous relationship (no clear leader)")
    
    return correlations


def plot_lead_lag(correlations, var1, var2):
    """Plot lead-lag correlation"""
    lags = [x[0] for x in correlations]
    corrs = [x[1] for x in correlations]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(lags, corrs, color=['#2E86AB' if x >= 0 else '#A23B72' for x in lags])
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax.axvline(x=0, color='gray', linestyle='--', linewidth=1)
    
    ax.set_xlabel('Lag (days)', fontsize=12)
    ax.set_ylabel('Correlation', fontsize=12)
    ax.set_title(f'Lead-Lag Correlation: {var1} vs {var2}', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # Add annotations
    ax.text(0.02, 0.98, f'Positive lag: {var1} leads {var2}', 
            transform=ax.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='#2E86AB', alpha=0.3))
    ax.text(0.02, 0.90, f'Negative lag: {var2} leads {var1}', 
            transform=ax.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='#A23B72', alpha=0.3))
    
    plt.tight_layout()
    plt.savefig('outputs/lead_lag_correlation.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\n✓ Saved lead_lag_correlation.png")


def main():
    """Main analysis"""
    print("="*70)
    print("GRANGER CAUSALITY ANALYSIS")
    print("="*70)
    
    # Load data
    df, threshold = load_and_merge_data()
    
    if "VIX" not in df.columns:
        print("Error: VIX column not found")
        return
    
    # Check stationarity
    kalshi_stationary = check_stationarity(df["kalshi_prob"], "Kalshi Probability")
    vix_stationary = check_stationarity(df["VIX"], "VIX")
    
    # If not stationary, use first differences
    if not kalshi_stationary or not vix_stationary:
        df = make_stationary(df)
        var1 = "kalshi_change"
        var2 = "vix_change"
        
        # Re-check stationarity
        check_stationarity(df[var1], "Kalshi Changes")
        check_stationarity(df[var2], "VIX Changes")
    else:
        var1 = "kalshi_prob"
        var2 = "VIX"
    
    # Run Granger causality tests in both directions
    print("\n" + "="*70)
    print("MAIN HYPOTHESIS TEST")
    print("="*70)
    
    # Test 1: Does Kalshi → VIX?
    results_k2v = run_granger_test(df, var1, var2, maxlag=5)
    
    # Test 2: Does VIX → Kalshi? (reverse causality check)
    results_v2k = run_granger_test(df, var2, var1, maxlag=5)
    
    # Lead-lag correlation analysis
    correlations = compute_lead_lag_correlation(df, var1, var2, max_lag=10)
    plot_lead_lag(correlations, var1, var2)
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"\nDataset: {len(df)} observations")
    print(f"Variables: {var1}, {var2}")
    print("\nKey Questions:")
    print("1. Does Kalshi predict future VIX moves? (Granger test)")
    print("2. Who leads whom? (Lead-lag correlation)")
    print("\nNext steps:")
    print("- Review outputs/lead_lag_correlation.png")
    print("- If significant: Kalshi provides predictive signal")
    print("- Calculate arb coefficient (ε) for trading opportunities")


if __name__ == "__main__":
    main()