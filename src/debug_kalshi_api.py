"""
Kalshi API Debugging Tool
Helps diagnose API connection and data availability issues
"""

import requests
import json
from datetime import datetime, timezone

BASE = "https://api.elections.kalshi.com/trade-api/v2"


def test_api_connection():
    """Test basic API connectivity"""
    print("=" * 60)
    print("Testing Kalshi API Connection")
    print("=" * 60)
    
    try:
        # Test basic endpoint
        url = f"{BASE}/exchange/status"
        print(f"\nTesting: {url}")
        
        r = requests.get(url, timeout=10)
        print(f"Status code: {r.status_code}")
        
        if r.status_code == 200:
            print("✓ API is accessible")
            data = r.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"✗ API returned error: {r.text}")
            
    except Exception as e:
        print(f"✗ Connection failed: {e}")


def explore_series(series_ticker="kxcpicoreyoy"):
    """Explore available series and markets"""
    print("\n" + "=" * 60)
    print(f"Exploring Series: {series_ticker}")
    print("=" * 60)
    
    # Try to get series info
    url = f"{BASE}/series/{series_ticker}"
    print(f"\nTesting: {url}")
    
    try:
        r = requests.get(url, timeout=10)
        print(f"Status code: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print(f"\nSeries data:")
            print(json.dumps(data, indent=2))
        else:
            print(f"Response: {r.text}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    # Try to list markets
    print(f"\n{'=' * 60}")
    url = f"{BASE}/markets"
    params = {"series_ticker": series_ticker, "limit": 5}
    print(f"Testing: {url}")
    print(f"Params: {params}")
    
    try:
        r = requests.get(url, params=params, timeout=10)
        print(f"Status code: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            
            if "markets" in data:
                markets = data["markets"]
                print(f"\nFound {len(markets)} markets (showing first 5)")
                
                for i, m in enumerate(markets[:5], 1):
                    print(f"\nMarket {i}:")
                    print(f"  Ticker: {m.get('ticker')}")
                    print(f"  Title: {m.get('title')}")
                    print(f"  Event: {m.get('event_ticker')}")
                    print(f"  Status: {m.get('status')}")
            else:
                print(f"Response keys: {data.keys()}")
                print(f"Full response: {json.dumps(data, indent=2)}")
        else:
            print(f"Response: {r.text}")
            
    except Exception as e:
        print(f"Error: {e}")


def search_all_cpi_markets():
    """Search for all CPI-related markets"""
    print("\n" + "=" * 60)
    print("Searching for CPI Markets")
    print("=" * 60)
    
    url = f"{BASE}/markets"
    params = {"limit": 100, "status": "all"}
    
    try:
        r = requests.get(url, params=params, timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            markets = data.get("markets", [])
            
            # Filter for CPI
            cpi_markets = [
                m for m in markets 
                if "cpi" in str(m.get("title", "")).lower() 
                or "cpi" in str(m.get("ticker", "")).lower()
            ]
            
            print(f"\nFound {len(cpi_markets)} CPI-related markets:")
            
            for m in cpi_markets[:20]:  # Show first 20
                print(f"\n  Ticker: {m.get('ticker')}")
                print(f"  Title: {m.get('title')}")
                print(f"  Series: {m.get('series_ticker')}")
                print(f"  Event: {m.get('event_ticker')}")
        else:
            print(f"Error: {r.text}")
            
    except Exception as e:
        print(f"Error: {e}")


def test_candlesticks(series_ticker="kxcpicoreyoy", sample_ticker=None):
    """Test candlestick endpoint"""
    print("\n" + "=" * 60)
    print("Testing Candlestick Endpoint")
    print("=" * 60)
    
    if not sample_ticker:
        print("No sample ticker provided. Fetching one...")
        try:
            r = requests.get(
                f"{BASE}/markets",
                params={"series_ticker": series_ticker, "limit": 1},
                timeout=10
            )
            if r.status_code == 200:
                markets = r.json().get("markets", [])
                if markets:
                    sample_ticker = markets[0]["ticker"]
                    print(f"Using ticker: {sample_ticker}")
        except:
            pass
    
    if not sample_ticker:
        print("Could not find a sample ticker")
        return
    
    # Test candlesticks
    url = f"{BASE}/series/{series_ticker}/markets/{sample_ticker}/candlesticks"
    
    # Last 30 days
    end = datetime.now(timezone.utc)
    start_ts = int((end.timestamp()) - (30 * 24 * 3600))
    end_ts = int(end.timestamp())
    
    params = {
        "start_ts": start_ts,
        "end_ts": end_ts,
        "period_interval": 1440
    }
    
    print(f"\nURL: {url}")
    print(f"Params: {params}")
    
    try:
        r = requests.get(url, params=params, timeout=10)
        print(f"Status code: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            candles = data.get("candlesticks", [])
            print(f"\nFound {len(candles)} candles")
            
            if candles:
                print(f"\nSample candle:")
                print(json.dumps(candles[0], indent=2))
        else:
            print(f"Response: {r.text}")
            
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Run all diagnostic tests"""
    print("\n" + "=" * 70)
    print("KALSHI API DIAGNOSTIC TOOL")
    print("=" * 70)
    
    # Run tests
    test_api_connection()
    explore_series()
    search_all_cpi_markets()
    test_candlesticks()
    
    print("\n" + "=" * 70)
    print("Diagnostic complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
