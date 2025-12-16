# --- UNIVERSE DEFINITIONS ---

# 1. Target Stocks (Asia Only)
JP_TICKERS = [
    "7203.T", "6758.T", "9984.T", "7974.T", "8306.T", "9432.T", "9433.T", "8035.T",
    "4063.T", "6861.T", "6501.T", "8766.T", "8058.T", "8001.T", "6367.T", "6954.T", 
    "9983.T", "4502.T"
]

KR_TICKERS = [
    "005930.KS", "000660.KS", "035420.KS", "035720.KS", "051910.KS", "006400.KS",
    "207940.KS", "068270.KS", "005380.KS", "000270.KS", "105560.KS", "055550.KS"
]

CN_HK_TICKERS = [
    "0700.HK", "9988.HK", "3690.HK", "9618.HK", "1810.HK", "1211.HK", "2318.HK",
    "0939.HK", "1398.HK", "0941.HK", "0883.HK", "0857.HK", "2628.HK",
    "600519.SS", "601318.SS", "300750.SZ"
]

# Combined Watchlist
WATCHLIST = sorted(set(JP_TICKERS + KR_TICKERS + CN_HK_TICKERS))

# 2. Risk Factors
FACTOR_TICKERS = [
    "^N225", "^KS11", "^HSI", "000300.SS",  # Local Indices
    "EWJ", "EWY", "EWH", "MCHI", "FXI",     # US-Listed ETFs (Timezone: US)
    "JPY=X", "KRW=X", "CNY=X",              # Currencies
    "^VIX", "^TNX", "CL=F", "HG=F"          # Global Macro
]

# 3. Logic Constants
GLOBAL_FACTORS = ["^VIX", "^TNX", "CL=F", "HG=F"]
# Factors that trade in US Time (NY) and need lagging for Asia
US_TIMED_FACTORS = set(GLOBAL_FACTORS + ["EWJ", "EWY", "EWH", "MCHI", "FXI"])

# Region Mappings
IDX_PREF = {
    "JP": ["^N225", "EWJ"], 
    "KR": ["^KS11", "EWY"],
    "HK": ["^HSI", "EWH"],  
    "CN": ["MCHI", "FXI"]
}
FX_PREF = {
    "JP": ["JPY=X"], 
    "KR": ["KRW=X"], 
    "CN": ["CNY=X"]
}