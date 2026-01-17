import re
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pandas as pd
import requests

BASE = "https://api.elections.kalshi.com/trade-api/v2"
SERIES_TICKER = "KXCPICOREYOY"
DAYS_BACK = 365
SLEEP = 0.5  # Increased to avoid rate limits
MAX_MARKETS = 100  # Limit to avoid timeout

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
        
        df = pd.DataFrame(candles)
        
        # Handle missing 'ts' field
        if 'ts' not in df.columns:
            return pd.DataFrame()
        
        df["date"] = pd.to_datetime(df["ts"], unit="s", utc=True).dt.date
        df["prob_close"] = df["close"] / 100.0
        
        return df[["date", "prob_close"]].sort_values("date")
    
    except Exception as e:
        return pd.DataFrame()

def main():
    print("=" * 60)
    print("Kalshi Data Pull - Improved")
    print("=" * 60)
    
    ensure_data_dir()
    
    mkts = list_markets(SERIES_TICKER)
    if mkts.empty:
        print("ERROR: No markets found.")
        return
    
    # Filter to finalized markets only (these have historical data)
    finalized = mkts[mkts["status"] == "finalized"].copy()
    print(f"Finalized markets (with historical data): {len(finalized)}")
    
    if finalized.empty:
        print("Using active markets instead...")
        finalized = mkts[mkts["status"] == "active"].copy()
    
    # Extract thresholds
    finalized["threshold"] = finalized["title"].apply(extract_threshold)
    finalized = finalized[finalized["threshold"].notna()].copy()
    
    # Limit to MAX_MARKETS to avoid timeout
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
        print(f"  [{success_count+1}/{len(finalized)}] {tkr}...", end=" ", flush=True)
        
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

if __name__ == "__main__":
    main()
