from pathlib import Path
import pandas as pd
import yfinance as yf

START = "2020-01-01"
TICKERS = {
    "VIX": "^VIX",
    "SPX": "^GSPC",
    "VIX9D": "^VIX9D",
    "VIX1D": "^VIX1D",
}

def ensure_data_dir():
    Path("data").mkdir(exist_ok=True)

def main():
    print("=" * 60)
    print("Yahoo Finance Data Pull Started")
    print("=" * 60)
    
    ensure_data_dir()
    
    print(f"\nFetching data from {START} to present...")
    print(f"Tickers to fetch: {list(TICKERS.keys())}")
    
    dfs = []
    
    for name, tkr in TICKERS.items():
        print(f"\nFetching {name} ({tkr})...", end=" ")
        
        try:
            df = yf.download(tkr, start=START, progress=False)
            
            if df.empty:
                print("✗ No data available")
                continue
            
            # Handle multi-level columns from yfinance
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)
            
            if "Adj Close" in df.columns:
                series = df["Adj Close"].copy()
            elif "Close" in df.columns:
                series = df["Close"].copy()
            else:
                print(f"✗ No price column found")
                continue
            
            series.name = name
            dfs.append(series.to_frame())
            
            print(f"✓ {len(df)} days")
            
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    if not dfs:
        print("\nERROR: No data retrieved from Yahoo Finance")
        return
    
    print("\nCombining data...")
    out = pd.concat(dfs, axis=1)
    
    out.index = pd.to_datetime(out.index).date
    out = out.reset_index()
    out = out.rename(columns={"index": "date"})
    
    print(f"\nData shape: {out.shape}")
    print(f"Columns: {out.columns.tolist()}")
    print(f"Date range: {out['date'].min()} to {out['date'].max()}")
    
    out_path = "data/yahoo_iv_proxy.csv"
    out.to_csv(out_path, index=False)
    
    print(f"\n✓ Saved to {out_path}")
    print("\nSample data:")
    print(out.head(10))
    
    print("\n" + "=" * 60)
    print("Yahoo Finance data pull complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
