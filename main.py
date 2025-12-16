import streamlit as st
import pandas as pd
import numpy as np
from src.config import WATCHLIST, FACTOR_TICKERS
from src.data_loader import fetch_and_clean_data
from src.risk_engine import RiskEngine
from src.charts import (
    plot_rolling_betas, plot_heatmap, plot_pnl_attribution, 
    plot_risk_breakdown, plot_factor_corr
)

# --- CONFIGURATION ---
st.set_page_config(page_title="Asian Equity Risk Model", layout="wide")

# --- CSS FOR PROFESSIONAL LOOK ---
st.markdown("""
<style>
    .block-container {padding-top: 1rem; padding-bottom: 5rem;}
    h1 {font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-weight: 700; color: #333;}
    h2, h3 {font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-weight: 400; color: #555;}
    .stAlert {background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 5px;}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.title("Model Configuration")
lookback = st.sidebar.slider("Lookback Window (Days)", 60, 500, 252, help="Number of trading days used to calculate regression coefficients.")
shock_size = st.sidebar.slider("VIX Stress Scenario", 0.10, 0.50, 0.20, help="Simulate a percentage spike in the VIX Index.")

st.sidebar.markdown("---")
st.sidebar.info(
    "**Methodology Note:**\n"
    "This model uses Rolling Ridge Regression with lagged US factors to account for time-zone differences between Asian markets and US macro indicators."
)

# --- MAIN HEADER ---
st.title("Asian Equity Risk Dashboard")
st.markdown("""
**Executive Summary:** This dashboard decomposes the risk drivers of the Asian Equity portfolio. 
It helps identify unintended exposures to Global Macro factors (VIX, Rates, Commodities) and Local Market indices.
""")

# --- 1. DATA LOADING ---
stock_rets, factor_rets = fetch_and_clean_data(WATCHLIST, FACTOR_TICKERS)

if stock_rets.empty:
    st.error("Data connection failed. Please check network.")
    st.stop()

# --- 2. RISK ENGINE EXECUTION ---
if "engine" not in st.session_state or st.sidebar.button("Refresh Model"):
    
    # 1. Create a placeholder to give feedback
    status_placeholder = st.empty()
    status_placeholder.info("⏳ Initializing Risk Model... Please wait.")
    
    # 2. Run the heavy calculation inside a spinner
    with st.spinner("Crunching numbers... Fitting rolling regressions for all stocks..."):
        try:
            engine = RiskEngine(stock_rets, factor_rets, window=lookback)
            engine.run_rolling_regression()
            
            # Save to session state so it doesn't re-run when you click tabs
            st.session_state["engine"] = engine
            
            # 3. Success feedback
            status_placeholder.success("✅ Model Updated Successfully!")
            
        except Exception as e:
            status_placeholder.error(f"Error running model: {e}")
            st.stop()
else:
    # Retrieve from cache if already calculated
    engine = st.session_state["engine"]

# --- 3. DASHBOARD TABS ---
tab_overview, tab_deep_dive, tab_scenario, tab_validation = st.tabs([
    "Portfolio Overview", "Ticker Deep Dive", "Stress Testing", "Model Diagnostics"
])

# TAB 1: OVERVIEW
with tab_overview:
    st.subheader("Regional Risk Exposure")
    st.markdown("The heatmap below visualizes the sensitivity (Beta) of each stock to global and local risk factors.")
    
    st.plotly_chart(plot_heatmap(engine.betas), use_container_width=True)
    
    st.caption("**Interpretation:** 'Blocky' patterns indicate regional clustering. For example, Japanese stocks (top rows) should show strong blue sensitivity to `^N225`, while ignoring `^HSI`.")

# TAB 2: DEEP DIVE
with tab_deep_dive:
    col_sel, _ = st.columns([1, 3])
    with col_sel:
        ticker = st.selectbox("Select Asset for Analysis", sorted(engine.betas.keys()))

    # --- Calculate Variance Decomposition ---
    # 1. Get Actual Returns vs Predicted Returns
    y_actual = stock_rets[ticker].tail(lookback)
    X = engine.get_X_for_ticker(ticker).loc[y_actual.index]
    latest_betas = engine.betas[ticker].iloc[-1].drop("Intercept", errors="ignore")
    
    # Predicted = X * Beta
    y_pred = X.mul(latest_betas, axis=1).sum(axis=1)
    
    # Variances
    var_sys = y_pred.var()
    var_total = y_actual.var()
    var_idio = var_total - var_sys
    if var_idio < 0: var_idio = 0 # Numerical noise safety

    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.plotly_chart(plot_rolling_betas(engine.betas[ticker], ticker), use_container_width=True)
        
    with col2:
        st.markdown("#### Risk Composition")
        st.plotly_chart(plot_risk_breakdown(var_sys, var_idio), use_container_width=True)
        st.markdown(
            f"""
            **Systematic Risk:** {var_sys/var_total:.1%}  
            **Idiosyncratic Risk:** {var_idio/var_total:.1%}
            
            *A high systematic risk % means this stock is driven mostly by macro factors. 
            A high idiosyncratic % means it is driven by company-specific news.*
            """
        )

# TAB 3: STRESS TEST
with tab_scenario:
    st.subheader("Scenario Analysis: Volatility Shock")
    st.markdown(f"""
    **Hypothesis:** If the **VIX Index spikes by +{shock_size:.0%}** (implying a US market panic), 
    how will that impact the Asian portfolio based on historical correlations?
    """)
    
    scenario = engine.generate_coherent_scenario(shock_factor="^VIX", shock_size=shock_size)
    
    # Portfolio Calculation (Equal Weight for Demo)
    weights = {t: 1.0/len(engine.betas) for t in engine.betas.keys()}
    pnl_stats = {}
    total_pnl = 0.0
    
    for tkr, w in weights.items():
        betas = engine.betas[tkr].iloc[-1]
        stock_ret = sum(betas.get(f, 0) * val for f, val in scenario.items())
        
        # Attribution
        for f, val in scenario.items():
            if f in betas:
                pnl_stats[f] = pnl_stats.get(f, 0) + (betas[f] * val * w)
        total_pnl += stock_ret * w
        
    col_a, col_b = st.columns([1, 2])
    with col_a:
        st.markdown("#### Projected Factor Moves")
        df_scen = pd.Series(scenario, name="Change").sort_values(ascending=False).to_frame()
        st.dataframe(df_scen.style.format("{:.2%}"))
        
    with col_b:
        st.plotly_chart(plot_pnl_attribution(pd.Series(pnl_stats).sort_values(), total_pnl), use_container_width=True)

# TAB 4: DIAGNOSTICS
with tab_validation:
    st.subheader("Model Diagnostics")
    st.markdown("Ensure the input factors are not highly collinear (Multicollinearity check).")
    
    # 1. Correlation Matrix
    st.plotly_chart(plot_factor_corr(factor_rets), use_container_width=True)
    st.caption("Ideally, factors should not have correlations > 0.7 or < -0.7, unless they are expected proxies.")