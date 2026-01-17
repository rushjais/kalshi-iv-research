"""
Master Run Script
Executes the entire data pipeline: pull data, analyze, and plot
"""

import sys
import subprocess
from pathlib import Path


def run_script(script_name, description):
    """Run a Python script and handle errors"""
    print("\n" + "=" * 70)
    print(f"Running: {description}")
    print("=" * 70)
    
    try:
        result = subprocess.run(
            [sys.executable, f"src/{script_name}"],
            check=True,
            capture_output=False,
            text=True
        )
        print(f"✓ {description} completed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed with error code {e.returncode}")
        return False
    
    except Exception as e:
        print(f"✗ {description} failed: {e}")
        return False


def main():
    """Run the complete pipeline"""
    print("=" * 70)
    print("KALSHI vs OPTIONS IV - COMPLETE PIPELINE")
    print("=" * 70)
    
    # Ensure directories exist
    Path("data").mkdir(exist_ok=True)
    Path("outputs").mkdir(exist_ok=True)
    
    # Step 1: Pull Kalshi data
    if not run_script("kalshi_pull.py", "Step 1: Pulling Kalshi data"):
        print("\n⚠️  Kalshi data pull failed. Check API endpoint and credentials.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Step 2: Pull Yahoo Finance data
    if not run_script("yahoo_pull.py", "Step 2: Pulling Yahoo Finance data"):
        print("\n⚠️  Yahoo Finance pull failed.")
        return
    
    # Step 3: Create plots and analysis
    if not run_script("make_plot.py", "Step 3: Creating visualizations and analysis"):
        print("\n⚠️  Plotting failed. Check if data files exist.")
        return
    
    print("\n" + "=" * 70)
    print("✓ PIPELINE COMPLETE!")
    print("=" * 70)
    print("\nGenerated files:")
    print("  Data:")
    print("    - data/kalshi_threshold_panel.csv")
    print("    - data/yahoo_iv_proxy.csv")
    print("  Plots:")
    print("    - outputs/kalshi_signal.png")
    print("    - outputs/iv_proxy.png")
    print("    - outputs/overlay_kalshi_vs_iv.png")
    print("\nNext steps:")
    print("  1. Review the plots in outputs/")
    print("  2. Implement Granger causality tests")
    print("  3. Calculate arb coefficient (ε)")


if __name__ == "__main__":
    main()