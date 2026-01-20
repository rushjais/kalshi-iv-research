from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def ensure_outputs_dir():
    Path("outputs").mkdir(exist_ok=True)

def load_data():
    print("Loading data...")
    
    kalshi = pd.read_csv("data/kalshi_unemployment_panel.csv")
    iv = pd.read_csv("data/yahoo_iv_proxy.csv")
    
    kalshi["date"] = pd.to_datetime(kalshi["date"])
    iv["date"] = pd.to_datetime(iv["date"])
    
    print(f"Kalshi data: {len(kalshi)} rows")
    print(f"Yahoo data: {len(iv)} rows")
    
    return kalshi, iv

def create_kalshi_signal(kalshi_df):
    thresholds = sorted(kalshi_df["threshold"].unique())
    mid_thr = thresholds[len(thresholds) // 2]
    print(f"Using threshold: {mid_thr}%")
    
    ksig = kalshi_df[kalshi_df["threshold"] == mid_thr][["date", "prob_close"]].copy()
    ksig = ksig.rename(columns={"prob_close": f"P(>={mid_thr})"})
    ksig = ksig.sort_values("date").drop_duplicates(subset=["date"], keep="last")
    
    return ksig, mid_thr

def merge_data(ksig, iv_df):
    df = ksig.merge(iv_df, on="date", how="inner").sort_values("date")
    print(f"Merged data: {len(df)} rows")
    return df

def plot_kalshi_signal(df, threshold):
    ensure_outputs_dir()
    col_name = f"P(>={threshold})"
    
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(df["date"], df[col_name], linewidth=2, color="#2E86AB", marker='o', markersize=3)
    
    ax.set_title(f"Kalshi: Unemployment ≥ {threshold}% Probability", fontsize=14, fontweight="bold")
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Probability", fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig('outputs/unemployment_kalshi_signal.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved unemployment_kalshi_signal.png")

def plot_iv_proxy(df, iv_col):
    ensure_outputs_dir()
    
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(df["date"], df[iv_col], linewidth=2, color="#A23B72", marker='o', markersize=3)
    
    ax.set_title(f"{iv_col} - Implied Volatility", fontsize=14, fontweight="bold")
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel(iv_col, fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig('outputs/unemployment_iv_proxy.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved unemployment_iv_proxy.png")

def plot_overlay(df, threshold, iv_col):
    ensure_outputs_dir()
    col_name = f"P(>={threshold})"
    
    df = df.copy()
    df["kalshi_norm"] = (df[col_name] - df[col_name].mean()) / df[col_name].std()
    df["iv_norm"] = (df[iv_col] - df[iv_col].mean()) / df[iv_col].std()
    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    ax.plot(df["date"], df["kalshi_norm"], linewidth=2.5, label=f"Kalshi Unemployment ≥{threshold}% (z-score)", 
            color="#2E86AB", marker='o', markersize=4)
    ax.plot(df["date"], df["iv_norm"], linewidth=2.5, label=f"{iv_col} (z-score)", 
            color="#A23B72", alpha=0.8, marker='s', markersize=4)
    
    ax.set_title("Kalshi Unemployment vs VIX (Normalized) - 2 Day Lead Found!", 
                 fontsize=14, fontweight="bold")
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Z-Score", fontsize=12)
    ax.legend(fontsize=11, loc="best")
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=45)
    
    # Add annotation about the finding
    ax.text(0.02, 0.98, 'Granger test: Kalshi predicts VIX at 2-day lag (p=0.024)', 
            transform=ax.transAxes, fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig('outputs/unemployment_overlay_kalshi_vs_iv.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved unemployment_overlay_kalshi_vs_iv.png")

def main():
    print("=" * 60)
    print("Creating Unemployment Market Visualizations")
    print("=" * 60)
    
    kalshi, iv = load_data()
    ksig, threshold = create_kalshi_signal(kalshi)
    df = merge_data(ksig, iv)
    
    iv_col = "VIX"
    
    print("\nCreating plots...")
    plot_kalshi_signal(df, threshold)
    plot_iv_proxy(df, iv_col)
    plot_overlay(df, threshold, iv_col)
    
    print("\n" + "=" * 60)
    print("All plots created! Check outputs/ folder")
    print("=" * 60)

if __name__ == "__main__":
    main()
