import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# --- 1. HEATMAP (FIXED SCALING) ---
def plot_heatmap(betas_dict):
    """
    Displays the factor sensitivities across the universe.
    """
    rows = []
    for tkr, df in betas_dict.items():
        row = df.iloc[-1].drop("Intercept", errors="ignore")
        row.name = tkr
        rows.append(row)
        
    df = pd.DataFrame(rows)
    
    # Dynamic height calculation: 30px per ticker, minimum 600px
    chart_height = max(600, len(df) * 30)

    # Center the color scale at 0 (White)
    max_val = df.abs().max().max()
    
    fig = px.imshow(
        df,
        labels=dict(x="Risk Factor", y="Ticker", color="Sensitivity (Beta)"),
        x=df.columns, y=df.index,
        color_continuous_scale="RdBu",
        zmin=-max_val, 
        zmax=max_val,
        aspect="auto",  # <--- CRITICAL FIX: Allows cells to stretch horizontally
        height=chart_height
    )
    
    fig.update_layout(
        title={
            'text': "Portfolio Risk Sensitivities (Red = Inverse Relationship, Blue = Positive Relationship)",
            'y':0.98, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top'
        },
        margin=dict(l=150, r=50, t=80, b=50), # Extra left margin for ticker names
        yaxis_nticks=len(df) # Ensure every ticker name is shown
    )
    return fig

# --- 2. ROLLING BETAS (Line Chart) ---
def plot_rolling_betas(beta_df, ticker):
    """
    Shows how a stock's sensitivity changes over time.
    """
    df_long = beta_df.drop(columns=["Intercept"], errors="ignore").reset_index()
    df_long = df_long.melt(id_vars="index", var_name="Factor", value_name="Beta")
    df_long.rename(columns={"index": "Date"}, inplace=True)
    
    fig = px.line(
        df_long, x="Date", y="Beta", color="Factor",
        facet_col="Factor", facet_col_wrap=3,
        height=700
    )
    fig.update_yaxes(matches=None, showgrid=True, gridcolor='lightgrey')
    fig.update_xaxes(showgrid=True, gridcolor='lightgrey')
    fig.update_layout(
        title=f"Time-Varying Risk Exposure: {ticker}",
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(orientation="h", y=-0.1)
    )
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1])) # Clean facet titles
    return fig

# --- 3. NEW: RISK BREAKDOWN (Donut Chart) ---
def plot_risk_breakdown(explained_var, residual_var):
    """
    Visualizes Systematic vs. Idiosyncratic Risk.
    """
    total = explained_var + residual_var
    sys_pct = explained_var / total
    idio_pct = residual_var / total
    
    labels = ["Systematic Risk (Market Driven)", "Idiosyncratic Risk (Company Specific)"]
    values = [explained_var, residual_var]
    colors = ['#4682B4', '#D3D3D3'] # SteelBlue vs LightGrey
    
    fig = go.Figure(data=[go.Pie(
        labels=labels, values=values, hole=.6,
        marker=dict(colors=colors, line=dict(color='#000000', width=1))
    )])
    
    fig.update_layout(
        title="Risk Variance Decomposition",
        annotations=[dict(text=f"{sys_pct:.1%} Explained", x=0.5, y=0.5, font_size=20, showarrow=False)]
    )
    return fig

# --- 4. NEW: FACTOR CORRELATION (Validation) ---
def plot_factor_corr(factor_rets):
    """
    Shows correlations between input factors.
    """
    corr = factor_rets.corr()
    
    fig = px.imshow(
        corr,
        text_auto=".2f",
        color_continuous_scale="RdBu",
        zmin=-1, zmax=1,
        aspect="auto",
        height=600,
        title="Factor Correlation Matrix (Validation)"
    )
    return fig

# --- 5. SCENARIO PnL (Bar Chart) ---
def plot_pnl_attribution(pnl_series, total_ret):
    df = pnl_series.reset_index()
    df.columns = ["Factor", "PnL"]
    
    # Color logic: Red for loss, Green for profit
    colors = ['#d62728' if v < 0 else '#2ca02c' for v in df["PnL"]]

    fig = go.Figure(go.Bar(
        x=df["PnL"],
        y=df["Factor"],
        orientation='h',
        marker_color=colors
    ))
    
    fig.update_layout(
        title=f"Projected Portfolio Impact: {total_ret:.2%}",
        xaxis_title="Estimated Return Contribution",
        yaxis_title="Risk Factor",
        height=500
    )
    return fig