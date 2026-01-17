import requests

BASE = "https://api.elections.kalshi.com/trade-api/v2"

# CPI-related series we found
series_list = [
    "KXCPIYOY",      # Inflation
    "KXCPICOREYOY",  # Core inflation  
    "KXCPI",         # CPI
    "CPIYOY",        # Inflation
    "CPICORE",       # CPI core
    "CPICOREYOY",    # Core inflation
]

for series in series_list:
    print(f"\n{'='*80}")
    print(f"Series: {series}")
    print(f"{'='*80}")
    
    r = requests.get(f"{BASE}/markets", 
                     params={"series_ticker": series, "limit": 50}, 
                     timeout=30)
    
    if r.status_code == 200:
        markets = r.json().get("markets", [])
        print(f"Markets found: {len(markets)}")
        
        if markets:
            # Group by status
            statuses = {}
            for m in markets:
                status = m.get('status', 'unknown')
                statuses[status] = statuses.get(status, 0) + 1
            
            print(f"Status breakdown: {statuses}")
            
            # Show sample markets
            print(f"\nSample markets:")
            for m in markets[:5]:
                print(f"  {m.get('ticker')}")
                print(f"    Title: {m.get('title')[:70]}")
                print(f"    Status: {m.get('status')}")
                print(f"    Close: {m.get('close_time')}")
    else:
        print(f"Error: {r.status_code}")
