"""
Kalshi Data Pull Script - Fixed Version
Pulls CPI prediction market data from Kalshi API
"""

import re
import time
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd
import requests

# Configuration
BASE = "https://api.elections.kalshi.com/trade-api/v2"
SERIES_TICKER = "KXCPICOREYOY"
EVENT_HINT = ""
DAYS_BACK = 240
SLEEP = 0.1

THRESH_RE = re.compile(r"above\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)


def ensure_data_dir():
    Path("data").mkdir(exist_ok=True)


def list_markets(series_ticker: str, limit: int = 1000):
    url = f"{BASE}/markets"
    params = {"series_ticker": series_ticker, "limit": limit}
    
    print(f"Fetching markets from: {url}")
    print(f"Params: {params}")
    
    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        
        if "markets" not in data:
            print(f"Response keys: {data.keys()}")
            return pd.DataFrame()
        
        markets = data["markets"]
        print(f"Found {len(markets)} markets")
        return pd.DataFrame(markets)
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching markets: {e}")
        return pd.DataFrame()


def extract_threshold(title: str):
    if not isinstance(title, str):
        return None
    m = THRESH_RE.search(title)
    if not m:
        return None
    return float(m.group(1))


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
        df["date"] = pd.to_datetime(df["ts"], unit="s", utc=True).dt.date
        df["prob_close"] = df["close"] / 100.0
        
        return df[["date", "prob_close"]].sort_values("date")
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching candles for {market_ticker}: {e}")
        return pd.DataFrame()


def main():
    print("=" * 60)
    print("Kalshi Data Pull Script Started")
    print("=" * 60)
    
    ensure_data_dir()
    
    print("\nStep 1: Fetching markets...")
    mkts = list_markets(SERIES_TICKER)
    
    if mkts.empty:
        print("ERROR: No markets found.")
        return
    
    print(f"Total markets found: {len(mkts)}")
    print("\nSample markets:")
    print(mkts[["ticker", "title"]].head(10).to_string(index=False))
    
    evt = mkts.copy()
    
    print("\nStep 2: Extracting thresholds...")
    evt["threshold"] = evt["title"].apply(extract_threshold)
    evt = evt[evt["threshold"].notna()].copy()
    
    if evt.empty:
        print("ERROR: No threshold markets found.")
        return
    
    print(f"Threshold markets found: {len(evt)}")
    
    tickers = evt[["ticker", "title", "threshold"]].sort_values("threshold")
    print("\nThreshold markets to fetch:")
    print(tickers.head(20).to_string(index=False))
    
    print("\nStep 3: Pulling historical candlestick data...")
    
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=DAYS_BACK)
    start_ts = int(start.timestamp())
    end_ts = int(end.timestamp())
    
    print(f"Date range: {start.date()} to {end.date()}")
    
    rows = []
    for idx, r in tickers.iterrows():
        tkr = r["ticker"]
        print(f"  Fetching {tkr} (threshold={r['threshold']})...", end=" ")
        
        try:
            c = pull_candles(SERIES_TICKER, tkr, start_ts, end_ts)
            
            if c.empty:
                print("No data")
                continue
            
            c["ticker"] = tkr
            c["threshold"] = r["threshold"]
            c["title"] = r["title"]
            rows.append(c)
            
            print(f"✓ {len(c)} days")
            time.sleep(SLEEP)
            
        except Exception as e:
            print(f"✗ Error: {e}")
            continue
    
    if not rows:
        print("\nERROR: No candlestick data retrieved.")
        return
    
    print(f"\nStep 4: Combining data from {len(rows)} markets...")
    panel = pd.concat(rows, ignore_index=True)
    
    print(f"Total rows: {len(panel)}")
    print(f"Date range in data: {panel['date'].min()} to {panel['date'].max()}")
    print(f"Thresholds: {sorted(panel['threshold'].unique())}")
    
    out_path = "data/kalshi_threshold_panel.csv"
    panel.to_csv(out_path, index=False)
    
    print(f"\n✓ Saved to {out_path}")
    print("\n" + "=" * 60)
    print("Kalshi data pull complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
