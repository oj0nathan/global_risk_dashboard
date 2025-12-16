import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st

@st.cache_data(ttl=3600)
def fetch_and_clean_data(tickers, factors, start_date="2012-01-01"):
    """
    Downloads data and computes returns exactly as per the notebook logic.
    Special handling for ^TNX (Yield changes) vs Price changes.
    """
    all_symbols = list(set(tickers + factors))
    
    # 1. Download with Auto Adjust (Fixes 'Adj Close' error)
    try:
        data = yf.download(all_symbols, start=start_date, progress=False, auto_adjust=True, threads=True)
    except Exception as e:
        st.error(f"Download Error: {e}")
        return pd.DataFrame(), pd.DataFrame()

    if data.empty:
        return pd.DataFrame(), pd.DataFrame()

    # robust column selection
    try:
        px = data["Close"]
    except KeyError:
        # Fallback if single level index
        if "Close" in data.columns:
            px = data[["Close"]]
        else:
            # Maybe the data IS the close prices (yfinance version dependent)
            px = data
            
    px = px.ffill().dropna()

    # 2. Split Stocks vs Factors
    stock_cols = [c for c in tickers if c in px.columns]
    factor_cols = [c for c in factors if c in px.columns]

    stock_px = px[stock_cols]
    factor_px = px[factor_cols]

    # 3. Compute Returns (Stocks)
    # replace infs which happen if price is 0
    stock_rets = stock_px.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan)

    # 4. Compute Factor Moves (Special Logic)
    factor_rets = pd.DataFrame(index=factor_px.index)
    
    # Normal pct change for most
    pct_cols = [c for c in factor_px.columns if c != "^TNX"]
    factor_rets[pct_cols] = factor_px[pct_cols].pct_change(fill_method=None)
    
    # Special: TNX is yield percentage (e.g., 4.00), so we want change in yield (diff), not % change
    if "^TNX" in factor_px.columns:
        factor_rets["^TNX"] = factor_px["^TNX"].diff() / 100.0
        
    factor_rets = factor_rets.replace([np.inf, -np.inf], np.nan)

    # 5. Drop Sparse Factors (>20% Missing)
    nan_frac = factor_rets.isna().mean()
    drop_cols = nan_frac[nan_frac > 0.20].index.tolist()
    if drop_cols:
        factor_rets = factor_rets.drop(columns=drop_cols)
        # st.warning(f"Dropped sparse factors: {drop_cols}")

    return stock_rets, factor_rets