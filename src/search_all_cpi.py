import requests
from collections import defaultdict

BASE = "https://api.elections.kalshi.com/trade-api/v2"

print("Searching ALL markets for CPI-related data...")
print("=" * 80)

# Get as many markets as possible
r = requests.get(f"{BASE}/markets", params={"limit": 1000}, timeout=30)

if r.status_code == 200:
    markets = r.json().get("markets", [])
    
    # Find CPI markets
    cpi_markets = [m for m in markets if 'cpi' in m.get('title', '').lower() 
                   or 'cpi' in m.get('ticker', '').lower()]
    
    print(f"Total markets: {len(markets)}")
    print(f"CPI markets: {len(cpi_markets)}\n")
    
    # Group by status
    by_status = defaultdict(list)
    for m in cpi_markets:
        status = m.get('status', 'unknown')
        by_status[status].append(m)
    
    print("CPI Markets by status:")
    for status, mkts in by_status.items():
        print(f"  {status}: {len(mkts)} markets")
    
    # Show settled/closed markets (these have historical data!)
    print("\n\nSETTLED/CLOSED CPI Markets (with historical data):")
    print("=" * 80)
    
    historical = [m for m in cpi_markets if m.get('status') in ['settled', 'closed', 'finalized']]
    
    if historical:
        for m in historical[:20]:
            print(f"Ticker: {m.get('ticker')}")
            print(f"Title: {m.get('title')}")
            print(f"Series: {m.get('series_ticker')}")
            print(f"Status: {m.get('status')}")
            print(f"Close: {m.get('close_time')}")
            print()
    else:
        print("No settled CPI markets found in current page.")
        print("\nShowing all CPI markets found:")
        for m in cpi_markets[:15]:
            print(f"Ticker: {m.get('ticker')}")
            print(f"Title: {m.get('title')[:70]}")
            print(f"Series: {m.get('series_ticker')}")
            print(f"Status: {m.get('status')}")
            print()
    
    # Also search for inflation/economic indicators
    print("\n\nOTHER ECONOMIC MARKETS (alternatives to use):")
    print("=" * 80)
    
    keywords = ['inflation', 'fed', 'rate', 'unemployment', 'jobs']
    for keyword in keywords:
        matches = [m for m in markets if keyword in m.get('title', '').lower()]
        if matches:
            settled = [m for m in matches if m.get('status') in ['settled', 'closed', 'finalized']]
            print(f"\n{keyword.upper()}: {len(matches)} total, {len(settled)} settled")
            if settled:
                print(f"  Example: {settled[0].get('title')[:70]}")
                print(f"  Series: {settled[0].get('series_ticker')}")
else:
    print(f"Error: {r.text}")
