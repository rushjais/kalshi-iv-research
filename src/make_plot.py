"""
Plotting and Analysis Script
Creates visualizations comparing Kalshi probabilities with IV proxies
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def ensure_outputs_dir():
    """Create outputs directory if it doesn't exist"""
    Path("outputs").mkdir(exist_ok=True)


def load_data():
    """Load Kalshi and Yahoo data"""
    print("Loading data...")
    
    # Check if data files exist
    kalshi_path = "data/kalshi_threshold_panel.csv"
    yahoo_path = "data/yahoo_iv_proxy.csv"
    
    if not Path(kalshi_path).exists():
        raise FileNotFoundError(f"{kalshi_path} not found. Run kalshi_pull.py first.")
    
    if not Path(yahoo_path).exists():
        raise FileNotFoundError(f"{yahoo_path} not found. Run yahoo_pull.py first.")
    
    kalshi = pd.read_csv(kalshi_path)
    iv = pd.read_csv(yahoo_path)
    
    # Convert dates
    kalshi["date"] = pd.to_datetime(kalshi["date"])
    iv["date"] = pd.to_datetime(iv["date"])
    
    print(f"Kalshi data: {len(kalshi)} rows, {kalshi['date'].min()} to {kalshi['date'].max()}")
    print(f"Yahoo data: {len(iv)} rows, {iv['date'].min()} to {iv['date'].max()}")
    
    return kalshi, iv


def create_kalshi_signal(kalshi_df):
    """
    Create a single Kalshi probability signal
    Strategy: Use median threshold for stability
    """
    thresholds = sorted(kalshi_df["threshold"].unique())
    print(f"\nAvailable thresholds: {thresholds}")
    
    # Use median threshold
    mid_thr = thresholds[len(thresholds) // 2]
    print(f"Using threshold: {mid_thr}")
    
    ksig = kalshi_df[kalshi_df["threshold"] == mid_thr][["date", "prob_close"]].copy()
    ksig = ksig.rename(columns={"prob_close": f"P(>={mid_thr})"})
    
    # Remove duplicates (keep last if multiple per day)
    ksig = ksig.sort_values("date").drop_duplicates(subset=["date"], keep="last")
    
    return ksig, mid_thr


def merge_data(ksig, iv_df):
    """Merge Kalshi signal with IV data"""
    df = ksig.merge(iv_df, on="date", how="inner").sort_values("date")
    print(f"\nMerged data: {len(df)} rows")
    
    if df.empty:
        raise ValueError("No overlapping dates between Kalshi and Yahoo data!")
    
    return df


def plot_kalshi_signal(df, threshold, output_dir="outputs"):
    """Plot Kalshi probability signal over time"""
    col_name = f"P(>={threshold})"
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df["date"], df[col_name], linewidth=2, color="#2E86AB")
    
    ax.set_title(f"Kalshi: Core CPI YoY ≥ {threshold}% Probability", fontsize=14, fontweight="bold")
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Probability", fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/kalshi_signal.png", dpi=300, bbox_inches="tight")
    plt.close()
    
    print(f"✓ Saved kalshi_signal.png")


def plot_iv_proxy(df, iv_col, output_dir="outputs"):
    """Plot implied volatility proxy"""
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df["date"], df[iv_col], linewidth=2, color="#A23B72")
    
    ax.set_title(f"{iv_col} - Implied Volatility Proxy", fontsize=14, fontweight="bold")
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel(iv_col, fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/iv_proxy.png", dpi=300, bbox_inches="tight")
    plt.close()
    
    print(f"✓ Saved iv_proxy.png")


def plot_overlay(df, threshold, iv_col, output_dir="outputs"):
    """Plot normalized overlay of Kalshi vs IV"""
    col_name = f"P(>={threshold})"
    
    # Normalize to z-scores for comparison
    df = df.copy()
    df["kalshi_norm"] = (df[col_name] - df[col_name].mean()) / df[col_name].std()
    df["iv_norm"] = (df[iv_col] - df[iv_col].mean()) / df[iv_col].std()
    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    ax.plot(df["date"], df["kalshi_norm"], linewidth=2, label="Kalshi (z-score)", color="#2E86AB")
    ax.plot(df["date"], df["iv_norm"], linewidth=2, label=f"{iv_col} (z-score)", color="#A23B72", alpha=0.8)
    
    ax.set_title("Kalshi Probability vs Implied Volatility (Normalized)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Z-Score", fontsize=12)
    ax.legend(fontsize=11, loc="best")
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/overlay_kalshi_vs_iv.png", dpi=300, bbox_inches="tight")
    plt.close()
    
    print(f"✓ Saved overlay_kalshi_vs_iv.png")


def compute_correlation(df, threshold, iv_col):
    """Compute correlation statistics"""
    col_name = f"P(>={threshold})"
    
    corr = df[col_name].corr(df[iv_col])
    print(f"\nCorrelation between Kalshi and {iv_col}: {corr:.3f}")
    
    # Lagged correlations
    print("\nLagged correlations (Kalshi leads):")
    for lag in range(1, 6):
        df_lag = df.copy()
        df_lag["kalshi_lag"] = df_lag[col_name].shift(lag)
        lag_corr = df_lag["kalshi_lag"].corr(df_lag[iv_col])
        print(f"  Lag {lag}: {lag_corr:.3f}")
    
    return corr


def main():
    """Main execution function"""
    print("=" * 60)
    print("Plotting and Analysis Script Started")
    print("=" * 60)
    
    ensure_outputs_dir()
    
    # Load data
    kalshi, iv = load_data()
    
    # Create Kalshi signal
    ksig, threshold = create_kalshi_signal(kalshi)
    
    # Merge datasets
    df = merge_data(ksig, iv)
    
    # Determine IV column to use
    iv_cols = [c for c in df.columns if c in ["VIX", "VIX9D", "VIX1D"]]
    if not iv_cols:
        raise ValueError("No VIX columns found in merged data!")
    
    iv_col = "VIX" if "VIX" in iv_cols else iv_cols[0]
    print(f"\nUsing IV column: {iv_col}")
    
    # Create plots
    print("\nCreating visualizations...")
    plot_kalshi_signal(df, threshold)
    plot_iv_proxy(df, iv_col)
    plot_overlay(df, threshold, iv_col)
    
    # Compute statistics
    compute_correlation(df, threshold, iv_col)
    
    print("\n" + "=" * 60)
    print("Analysis complete! Check the outputs/ folder for plots.")
    print("=" * 60)


if __name__ == "__main__":
    main()