import requests
from datetime import datetime, timezone, timedelta

BASE = "https://api.elections.kalshi.com/trade-api/v2"

# Try a recent finalized market
ticker = "KXCPICOREYOY-25DEC-T2.9"
series = "KXCPICOREYOY"

print(f"Testing market: {ticker}")
print("=" * 60)

# Get market details
r = requests.get(f"{BASE}/markets/{ticker}", timeout=30)
if r.status_code == 200:
    market = r.json().get("market", {})
    print(f"Status: {market.get('status')}")
    print(f"Open time: {market.get('open_time')}")
    print(f"Close time: {market.get('close_time')}")
    print(f"Last price: {market.get('last_price')}")
    print(f"Yes bid: {market.get('yes_bid')}")
    print(f"Yes ask: {market.get('yes_ask')}")

# Try different time ranges for candlesticks
print("\n" + "=" * 60)
print("Trying candlesticks with different date ranges:")

# Try 1: Last 30 days
end = datetime.now(timezone.utc)
start = end - timedelta(days=30)

url = f"{BASE}/series/{series}/markets/{ticker}/candlesticks"
params = {
    "start_ts": int(start.timestamp()),
    "end_ts": int(end.timestamp()),
    "period_interval": 1440
}

print(f"\nAttempt 1: Last 30 days")
print(f"URL: {url}")
print(f"Params: {params}")

r = requests.get(url, params=params, timeout=30)
print(f"Status: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    print(f"Response keys: {data.keys()}")
    candles = data.get("candlesticks", [])
    print(f"Candles found: {len(candles)}")
    if candles:
        print(f"First candle: {candles[0]}")
else:
    print(f"Error: {r.text}")

# Try 2: Since market open time if available
if market.get('open_time'):
    print(f"\nAttempt 2: Since market open time")
    open_dt = datetime.fromisoformat(market['open_time'].replace('Z', '+00:00'))
    params['start_ts'] = int(open_dt.timestamp())
    
    r = requests.get(url, params=params, timeout=30)
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        candles = data.get("candlesticks", [])
        print(f"Candles found: {len(candles)}")
        if candles:
            print(f"First candle: {candles[0]}")
            print(f"Last candle: {candles[-1]}")

print("\n" + "=" * 60)
