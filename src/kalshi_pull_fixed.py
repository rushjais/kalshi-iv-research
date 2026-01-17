import re
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pandas as pd
import requests

BASE = "https://api.elections.kalshi.com/trade-api/v2"
SERIES_TICKER = "KXCPICOREYOY"
DAYS_BACK = 365
SLEEP = 0.3
MAX_MARKETS = 50

THRESH_RE = re.compile(r"above\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)

def ensure_data_dir():
    Path("data").mkdir(exist_ok=True)

def list_markets(series_ticker: str, limit: int = 1000):
    url = f"{BASE}/markets"
    params = {"series_ticker": series_ticker, "limit": limit}
    
    print(f"Fetching markets...")
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    
    markets = r.json().get("markets", [])
    print(f"Found {len(markets)} markets")
    return pd.DataFrame(markets)

def extract_threshold(title: str):
    if not isinstance(title, str):
        return None
    m = THRESH_RE.search(title)
    return float(m.group(1)) if m else None

def pull_candles(series_ticker: str, market_ticker: str, start_ts: int, end_ts: int):
    url = f"{BASE}/series/{series_ticker}/markets/{market_ticker}/candlesticks"
    params = {"start_ts": start_ts, "end_ts": end_ts, "period_interval": 1440}
    
    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        
        candles = data.get("candlesticks", [])
        if not candles:
            return pd.DataFrame()
        
        # Process candles with correct structure
        rows = []
        for c in candles:
            # Use end_period_ts instead of ts
            ts = c.get("end_period_ts")
            if not ts:
                continue
            
            # Get price from nested structure
            price_data = c.get("price", {})
            close_price = price_data.get("close")
            
            # Skip if no price data
            if close_price is None:
                continue
            
            rows.append({
                "date": datetime.fromtimestamp(ts, tz=timezone.utc).date(),
                "prob_close": close_price / 100.0
            })
        
        if not rows:
            return pd.DataFrame()
        
        df = pd.DataFrame(rows)
        return df.sort_values("date")
    
    except Exception as e:
        return pd.DataFrame()

def main():
    print("=" * 60)
    print("Kalshi Data Pull - FIXED")
    print("=" * 60)
    
    ensure_data_dir()
    
    mkts = list_markets(SERIES_TICKER)
    if mkts.empty:
        print("ERROR: No markets found.")
        return
    
    # Filter to finalized markets
    finalized = mkts[mkts["status"] == "finalized"].copy()
    print(f"Finalized markets: {len(finalized)}")
    
    # Extract thresholds
    finalized["threshold"] = finalized["title"].apply(extract_threshold)
    finalized = finalized[finalized["threshold"].notna()].copy()
    
    # Limit markets
    finalized = finalized.head(MAX_MARKETS)
    
    print(f"Fetching {len(finalized)} markets...")
    
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=DAYS_BACK)
    start_ts = int(start.timestamp())
    end_ts = int(end.timestamp())
    
    rows = []
    success_count = 0
    
    for idx, r in finalized.iterrows():
        tkr = r["ticker"]
        print(f"  [{success_count+1}] {tkr}...", end=" ", flush=True)
        
        c = pull_candles(SERIES_TICKER, tkr, start_ts, end_ts)
        
        if c.empty:
            print("no data")
        else:
            c["ticker"] = tkr
            c["threshold"] = r["threshold"]
            c["title"] = r["title"]
            rows.append(c)
            success_count += 1
            print(f"✓ {len(c)} days")
        
        time.sleep(SLEEP)
        
        if success_count >= 100:  # Stop after 100 successful markets for now
            print(f"\nStopping after {success_count} successful markets (for testing)")
            break
    
    if not rows:
        print("\nERROR: No data retrieved.")
        return
    
    panel = pd.concat(rows, ignore_index=True)
    
    print(f"\n✓ Successfully fetched {success_count} markets")
    print(f"Total data points: {len(panel)}")
    print(f"Date range: {panel['date'].min()} to {panel['date'].max()}")
    print(f"Thresholds: {sorted(panel['threshold'].unique())}")
    
    out_path = "data/kalshi_threshold_panel.csv"
    panel.to_csv(out_path, index=False)
    
    print(f"\n✓ Saved to {out_path}")
    print("\nSample data:")
    print(panel.head(10))

if __name__ == "__main__":
    main()
