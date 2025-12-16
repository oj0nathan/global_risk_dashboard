# Global Risk Dashboard

This repository contains a modular, **institutional-grade risk monitoring system** designed to decompose portfolio risk in real-time. It mimics the "prop shop" style of analytics, focusing on:

  * **Real-time Data Ingestion** (via custom data loaders)
  * **Statistical Risk Decomposition** (VaR, Volatility, Beta, Correlations)
  * **Live Visualization** of portfolio health and market stress

The project is structured as a **production-lite application**, separating the core calculation engine from the visualization layer to ensure scalability and clean architecture.

## 1\. Project Overview

### The Core Goal

**How can we decompose complex multi-asset risk into actionable metrics for immediate decision-making?**

To answer this, the project builds a Python-based risk engine that ingests market data, calculates statistical risk measures, and presents them in a dense, information-rich dashboard format.

### Key Elements

**Universe:**

  * **Multi-Asset Capabilities:** Designed to handle Equities, ETFs, and potentially Futures/FX (depending on data source configuration).
  * **Benchmarks:** Configurable benchmark tracking for relative risk (Beta/Alpha) analysis.

**Risk Engine (`src/risk_engine.py`):**

  * **Value at Risk (VaR):** Calculation of Historical and Parametric VaR at various confidence intervals (95%, 99%).
  * **Volatility Analysis:** Rolling volatility windows and volatility cone analysis.
  * **Correlation Dynamics:** Real-time correlation matrices to detect breakdown in diversification.
  * **Drawdown Tracking:** Monitoring peak-to-trough declines across the portfolio.

**Research & Prototyping:**

  * **`prop_shop_style.ipynb`:** A playground for designing high-density "trader views" and testing UX layouts before implementation.
  * **`risk_decomp.ipynb`:** A research notebook for validating the mathematical models used in the risk engine (e.g., component VaR, factor decomposition).

## 2\. Technical Architecture

The project follows a clean "Data $\to$ Engine $\to$ View" architecture:

| Component | File | Description |
| :--- | :--- | :--- |
| **Data Layer** | `src/data_loader.py` | Handles API connections, data cleaning, and timestamp synchronization. |
| **Logic Layer** | `src/risk_engine.py` | The mathematical core. Contains pure functions for statistical calculations (agnostic of the UI). |
| **Config** | `src/config.py` | Centralized settings for tickers, lookback windows, and risk parameters. |
| **Visualization** | `src/charts.py` | Plotly/Matplotlib wrappers for generating standardized risk plots. |
| **Entry Point** | `main.py` | The executable script that ties everything together to launch the dashboard. |

-----

*Disclaimer: This project is for educational and research purposes. It is not financial advice and should not be used for live trading without extensive validation.*
