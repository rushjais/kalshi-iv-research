import requests
import pandas as pd
from datetime import datetime

BASE = "https://api.elections.kalshi.com/trade-api/v2"

print("="*70)
print("SEARCHING FOR MARKETS WITH HISTORICAL DATA")
print("="*70)

# Target series with likely historical data
target_series = ["KXFED", "FED", "FEDFUNDS", "KXU3", "U3", "KXPAYROLLS", "PAYROLLS"]

for series_ticker in target_series:
    print(f"\n{'='*70}")
    print(f"Checking: {series_ticker}")
    print(f"{'='*70}")
    
    r = requests.get(f"{BASE}/markets", 
                     params={"series_ticker": series_ticker, "limit": 100},
                     timeout=30)
    
    if r.status_code != 200:
        print(f"  Not found or error")
        continue
    
    markets = r.json().get("markets", [])
    if not markets:
        print(f"  No markets")
        continue
    
    df = pd.DataFrame(markets)
    
    # Check finalized markets
    finalized = df[df["status"] == "finalized"]
    active = df[df["status"] == "active"]
    
    print(f"  Total markets: {len(df)}")
    print(f"  Finalized (historical data): {len(finalized)}")
    print(f"  Active: {len(active)}")
    
    if len(finalized) > 0:
        # Get date range
        df["open_time"] = pd.to_datetime(df["open_time"])
        df["close_time"] = pd.to_datetime(df["close_time"])
        
        earliest = df["open_time"].min()
        latest = df["close_time"].max()
        
        print(f"  Date range: {earliest.date()} to {latest.date()}")
        print(f"  ✓ GOOD CANDIDATE - Has historical data!")
        
        print(f"\n  Sample markets:")
        for _, m in finalized.head(5).iterrows():
            print(f"    {m['ticker']}: {m['title'][:60]}")

print("\n" + "="*70)
print("RECOMMENDATION")
print("="*70)
print("\nBest series for historical analysis:")
print("  1. Check which series above has most finalized markets")
print("  2. Use that series in a new version of kalshi_pull_fixed.py")
print("  3. Rerun the full pipeline with more historical data")
