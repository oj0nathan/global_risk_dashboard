import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge
from src.config import IDX_PREF, FX_PREF, GLOBAL_FACTORS, US_TIMED_FACTORS

class RiskEngine:
    def __init__(self, stock_rets, factor_rets, window=252):
        self.stock_rets = stock_rets
        self.factor_rets = factor_rets
        self.window = window
        self.betas = {}
        self.r2 = {}
        self.model_success_count = 0

    def infer_region(self, tkr: str) -> str:
        if tkr.endswith(".T"):  return "JP"
        if tkr.endswith(".KS"): return "KR"
        if tkr.endswith(".HK"): return "HK"
        if tkr.endswith((".SS", ".SZ")): return "CN"
        return "OTHER"

    def get_X_for_ticker(self, tkr: str) -> pd.DataFrame:
        """
        Builds the factor matrix X specific to a ticker's region.
        CRITICAL: Applies Timezone Lag for US-timed factors against Asian stocks.
        """
        reg = self.infer_region(tkr)
        avail = list(self.factor_rets.columns)
        
        # 1. Select Factors based on Region Prefs
        cols = []
        # Local Index
        for c in IDX_PREF.get(reg, []): 
            if c in avail: cols.append(c); break
        # Local FX
        for c in FX_PREF.get(reg, []):
            if c in avail: cols.append(c); break
        # Global Factors
        cols.extend([g for g in GLOBAL_FACTORS if g in avail])
        
        X = self.factor_rets[cols].copy()

        # 2. Timezone Fix: Lag US-timed factors for APAC stocks
        # If the stock is Asian, 'Yesterday's' VIX affects 'Today's' Samsung Close.
        if reg in ["JP", "KR", "HK", "CN"]:
            lag_cols = [c for c in X.columns if c in US_TIMED_FACTORS]
            if lag_cols:
                X[lag_cols] = X[lag_cols].shift(1)

        # 3. Clean up
        # Drop columns that are mostly NaN after shifting
        good_cols = [c for c in X.columns if X[c].notna().mean() >= 0.85]
        return X[good_cols]

    def run_rolling_regression(self):
        """Fits Rolling Ridge Regression for all tickers."""
        for tkr in self.stock_rets.columns:
            if self.infer_region(tkr) == "OTHER": continue
            
            y = self.stock_rets[tkr]
            X = self.get_X_for_ticker(tkr)
            
            # Align Data
            common = y.dropna().index.intersection(X.dropna().index)
            y_aligned, X_aligned = y.loc[common], X.loc[common]
            
            if len(common) < self.window: continue

            # Rolling Loop
            betas_rows = []
            dates = []
            
            # Optimization: We don't need to run every single day for the UI, 
            # but for accuracy we should. To speed up, we can step by 5 days if needed, 
            # but let's stick to full daily to match notebook.
            for i in range(self.window, len(common)):
                # Training Window
                y_train = y_aligned.iloc[i-self.window : i]
                X_train = X_aligned.iloc[i-self.window : i]
                
                # Fit Ridge
                model = Ridge(alpha=1.0)
                model.fit(X_train, y_train)
                
                # Store
                b = pd.Series(model.coef_, index=X_train.columns)
                b["Intercept"] = model.intercept_
                betas_rows.append(b)
                dates.append(y_aligned.index[i])
            
            if betas_rows:
                self.betas[tkr] = pd.DataFrame(betas_rows, index=dates)
                self.model_success_count += 1

    def generate_coherent_scenario(self, shock_factor="^VIX", shock_size=0.20):
        """
        Notebook Logic: 'Identify worst 2% of days... Average moves... Scale'
        """
        if shock_factor not in self.factor_rets.columns:
            return {}

        vix = self.factor_rets[shock_factor].dropna()
        # 1. Identify worst 2% of days (High VIX)
        stress_cutoff = vix.quantile(0.98)
        stress_dates = vix[vix >= stress_cutoff].index
        
        # 2. Average moves on those days
        avg_moves = self.factor_rets.loc[stress_dates].mean(numeric_only=True)
        
        # 3. Scale to match target shock exactly
        # If VIX avg move on bad days was +10%, but we want +20%, we double everything.
        current_shock_avg = avg_moves.get(shock_factor, 1.0)
        if current_shock_avg == 0: scaler = 1.0
        else: scaler = shock_size / current_shock_avg
        
        scenario = (avg_moves * scaler).to_dict()
        return scenario