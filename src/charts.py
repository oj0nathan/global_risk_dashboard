import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

def plot_rolling_betas(beta_df, ticker):
    """
    Plots the evolution of factor betas over time for a single stock.
    Input: beta_df (DataFrame with dates as index and factors as columns)
    """
    fig = go.Figure()
    
    # Iterate through columns (factors)
    for col in beta_df.columns:
        if col == "Intercept": continue  # Skip intercept
        
        fig.add_trace(go.Scatter(
            x=beta_df.index, 
            y=beta_df[col], 
            mode='lines', 
            name=col,
            hovertemplate=f"<b>{col}</b>: %{{y:.2f}}<extra></extra>"
        ))
    
    fig.update_layout(
        title=f"Rolling Factor Betas: {ticker}",
        yaxis_title="Beta Sensitivity",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=80, b=40),
        height=400
    )
    return fig

def plot_heatmap(betas_dict):
    """
    Aggregates the *latest* betas for all stocks into a heatmap.
    Input: betas_dict {ticker: DataFrame}
    """
    # 1. Extract the last row (most recent beta) for each ticker
    data = []
    tickers = []
    
    for tkr, df in betas_dict.items():
        if not df.empty:
            # Get last row, drop intercept
            last_beta = df.iloc[-1].drop("Intercept", errors="ignore")
            data.append(last_beta)
            tickers.append(tkr)
            
    if not data:
        return go.Figure()

    # 2. Create DataFrame for Heatmap
    df_heatmap = pd.DataFrame(data, index=tickers).fillna(0)
    
    # 3. Calculate symmetric range to ensure 0 is white/neutral
    # We find the largest absolute number (e.g. 1.5) and set range to -1.5 to +1.5
    limit = df_heatmap.abs().max().max()
    
    # 4. Plot
    fig = px.imshow(
        df_heatmap,
        labels=dict(x="Risk Factor", y="Asset", color="Beta"),
        x=df_heatmap.columns,
        y=df_heatmap.index,
        aspect="auto",
        color_continuous_scale="RdBu_r", # Red=Negative, Blue=Positive
        zmin=-limit,   # Explicitly set min
        zmax=limit     # Explicitly set max
    )
    
    fig.update_layout(
        title="Portfolio Risk Factor Sensitivities (Current)",
        height=600,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    return fig

def plot_risk_breakdown(var_sys, var_idio):
    """
    Donut chart showing Systematic vs Idiosyncratic Risk Variance.
    """
    labels = ['Systematic (Market Risk)', 'Idiosyncratic (Stock Specific)']
    values = [var_sys, var_idio]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=.6,
        marker_colors=['#1f77b4', '#d62728'] # Blue vs Red
    )])
    
    fig.update_layout(
        showlegend=False,
        annotations=[dict(text='Risk<br>Source', x=0.5, y=0.5, font_size=20, showarrow=False)],
        margin=dict(l=20, r=20, t=20, b=20),
        height=300
    )
    return fig

def plot_pnl_attribution(pnl_series, total_pnl):
    """
    Bar chart showing which factors contributed to the PnL in the stress test.
    """
    # Color logic: Green for profit, Red for loss
    colors = ['#2ca02c' if v >= 0 else '#d62728' for v in pnl_series.values]
    
    fig = go.Figure()
    
    # Factor Bars
    fig.add_trace(go.Bar(
        x=pnl_series.index,
        y=pnl_series.values,
        marker_color=colors,
        text=pnl_series.values,
        texttemplate="%{y:.1%}",
        textposition="auto",
        name="Factor PnL"
    ))
    
    fig.update_layout(
        title=f"Projected Impact Breakdown (Total: {total_pnl:.2%})",
        yaxis_title="PnL Contribution",
        yaxis_tickformat=".1%",
        template="plotly_white",
        showlegend=False
    )
    return fig

def plot_factor_corr(factor_rets):
    """
    Correlation Matrix of the input factors to check for Multicollinearity.
    """
    corr = factor_rets.corr()
    
    fig = px.imshow(
        corr,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="RdBu",
        zmin=-1, zmax=1,
        title="Input Factor Correlation Matrix"
    )
    
    fig.update_layout(height=500)
    return fig