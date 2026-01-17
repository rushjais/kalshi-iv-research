import requests

BASE = "https://api.elections.kalshi.com/trade-api/v2"

# Try different search strategies
print("Strategy 1: Search by ticker prefix 'KXCPI'")
print("=" * 80)

r = requests.get(f"{BASE}/markets", params={"ticker": "KXCPI", "limit": 100}, timeout=30)
print(f"Status: {r.status_code}")

if r.status_code == 200:
    markets = r.json().get("markets", [])
    print(f"Found {len(markets)} markets\n")
    for m in markets[:10]:
        print(f"{m.get('ticker')} - {m.get('title')[:60]}")
        print(f"  Series: {m.get('series_ticker')}, Status: {m.get('status')}")
        print()

# Strategy 2: Try searching with cursor for more pages
print("\n\nStrategy 2: Let's look at what series ARE available")
print("=" * 80)

r = requests.get(f"{BASE}/series", timeout=30)
if r.status_code == 200:
    series = r.json().get("series", [])
    print(f"Total series: {len(series)}\n")
    
    # Look for economic/macro series
    for s in series:
        ticker = s.get('ticker', '')
        title = s.get('title', '')
        category = s.get('category', '')
        
        if any(word in ticker.lower() or word in title.lower() 
               for word in ['cpi', 'inflation', 'fed', 'rate', 'jobs', 'unemployment', 'economic']):
            print(f"Series: {ticker}")
            print(f"Title: {title}")
            print(f"Category: {category}")
            print()
else:
    print(f"Error: {r.text}")

# Strategy 3: Try the combo tickers we found
print("\n\nStrategy 3: Check the KXCPICOMBO markets directly")
print("=" * 80)

combo_tickers = [
    "KXCPICOMBO-26JAN-0224",
    "KXCPICOMBO-26JAN-0125",
    "KXCPICOMBO-26JAN-0123"
]

for ticker in combo_tickers:
    r = requests.get(f"{BASE}/markets/{ticker}", timeout=30)
    if r.status_code == 200:
        m = r.json().get("market", {})
        print(f"Ticker: {ticker}")
