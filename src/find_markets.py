import requests
import json

BASE = "https://api.elections.kalshi.com/trade-api/v2"

print("Searching for CPI markets (including closed/historical)...")
print("=" * 80)

# Search WITHOUT status filter to get ALL markets
r = requests.get(f"{BASE}/markets", params={"limit": 1000}, timeout=30)

if r.status_code == 200:
    markets = r.json().get("markets", [])
    print(f"Total markets retrieved: {len(markets)}\n")
    
    # Search for CPI in title or ticker
    cpi_markets = [m for m in markets if 
                   'cpi' in m.get('title', '').lower() or 
                   'cpi' in m.get('ticker', '').lower()]
    
    print(f"CPI-related markets found: {len(cpi_markets)}\n")
    
    if cpi_markets:
        # Group by series
        series_groups = {}
        for m in cpi_markets:
            series = m.get('series_ticker', 'unknown')
            if series not in series_groups:
                series_groups[series] = []
            series_groups[series].append(m)
        
        print(f"CPI Series found: {list(series_groups.keys())}\n")
        
        # Show details
        for series, markets_list in series_groups.items():
            print(f"\nSeries: {series}")
            print(f"Markets in series: {len(markets_list)}")
            print("-" * 80)
            
            for m in markets_list[:10]:
                print(f"  Ticker: {m.get('ticker')}")
                print(f"  Title: {m.get('title')}")
                print(f"  Status: {m.get('status')}")
                print(f"  Close time: {m.get('close_time')}")
                print()
    else:
        print("No CPI markets found. Showing sample of what's available:")
        print("-" * 80)
        for m in markets[:10]:
            print(f"Title: {m.get('title')}")
            print(f"Ticker: {m.get('ticker')}")
            print(f"Series: {m.get('series_ticker')}")
            print()
else:
    print(f"Error: {r.status_code}")
    print(r.text)
