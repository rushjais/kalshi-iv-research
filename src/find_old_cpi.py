import requests

BASE = "https://api.elections.kalshi.com/trade-api/v2"

# Try to get series ticker from one of the markets
r = requests.get(f"{BASE}/markets/KXCPICOMBO-26JAN-0224", timeout=30)

if r.status_code == 200:
    market = r.json().get("market", {})
    series = market.get("series_ticker")
    print(f"Series ticker: {series}")
    print(f"Market details:")
    print(f"  Title: {market.get('title')}")
    print(f"  Status: {market.get('status')}")
    print(f"  Open time: {market.get('open_time')}")
    
    if series:
        # Now search for all markets in this series
        print(f"\n\nSearching for all markets in series: {series}")
        print("=" * 80)
        
        r2 = requests.get(f"{BASE}/markets", params={"series_ticker": series, "limit": 100}, timeout=30)
        if r2.status_code == 200:
            all_markets = r2.json().get("markets", [])
            print(f"Found {len(all_markets)} markets in this series\n")
            
            for m in all_markets[:20]:
                print(f"Ticker: {m.get('ticker')}")
                print(f"Title: {m.get('title')[:80]}")
                print(f"Status: {m.get('status')}")
                print(f"Close time: {m.get('close_time')}")
                print()
else:
    print(f"Error: {r.status_code} - {r.text}")
