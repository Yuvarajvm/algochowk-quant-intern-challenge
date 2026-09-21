# Quantitative Research & Event-Driven Backtesting Challenge
### AlgoChowk — Quant Engineer Intern Assessment

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status: Research Complete](https://img.shields.io/badge/Status-Falsified%20Hypothesis-red.svg)]()

This repository contains the complete quantitative research codebase, statistical engine, event-driven backtester, and analytical documentation investigating the market hypothesis:

> **"After a significant one-day fall in NIFTY, the market tends to recover over the next few trading days."**

---

## Executive Summary of Findings

| Metric / Dimension | Realistic Execution ($T+1$ Open Entry) | Theoretical Execution ($T$ Close Entry) | Unconditional Market Baseline |
| :--- | :---: | :---: | :---: |
| **1-Day Forward Return** | **-0.021%** (Win Rate: 49.4%) | +0.054% (Win Rate: 54.3%) | +0.044% (Win Rate: 52.9%) |
| **3-Day Forward Return** | **+0.199%** (Win Rate: 55.4%) | +0.281% (Win Rate: 54.5%) | +0.131% (Win Rate: 54.6%) |
| **Welch's $t$-stat (3-Day vs. Baseline)** | **+0.360** ($p = 0.719$) | +0.738 ($p = 0.461$) | N/A |
| **Bonferroni-Adjusted $p$-value** | **1.000** (Not Significant) | 1.000 (Not Significant) | N/A |
| **Backtest CAGR (2007–2026)** | **1.70%** (Sharpe: -0.27) | 2.84% (Sharpe: -0.17) | **9.07%** (Sharpe: +0.19) |
| **Maximum Drawdown** | **-57.63%** | -57.72% | -59.86% |
| **Scientific Verdict** | **REJECT HYPOTHESIS** | Rejected (Fails Out-of-Sample) | Benchmark Baseline |

### Core Takeaways
1. **Absence of Alpha:** Post-crash returns do not statistically exceed the unconditional drift of NIFTY 50 ($p > 0.50$ across all horizons).
2. **Look-Ahead Bias:** Entering at $T$ Close creates synthetic profit from overnight gap-ups. When executed realistically at $T+1$ Open, 1-day and 2-day returns turn negative.
3. **Liquidation Cascades:** During severe crashes (2008 GFC, March 2020), single-day drops trigger margin liquidations, causing serial negative returns rather than mean-reversion.
4. **Economic Non-Viability:** After accounting for 10 bps round-trip transaction costs and slippage, the strategy severely underperforms Buy & Hold (₹1.37 lakh vs. ₹5.16 lakh).

---

## Repository Structure

```
├── data/
│   └── nifty_50_historical.csv         # Validated NIFTY 50 OHLC data (2007–2026)
├── src/
│   ├── data_loader.py                  # API ingestion, cleaning & validation pipeline
│   ├── event_engine.py                 # Configurable drop detector & forward return engine
│   ├── statistical_tests.py            # Welch t-tests, Mann-Whitney U, 5000-bootstrap CIs
│   ├── backtester.py                   # Event-driven portfolio simulator with realistic execution
│   └── visualizer.py                   # Publication-grade chart generation
├── notebooks/
│   └── quant_research_nifty.ipynb      # Fully executed, interactive research notebook
├── reports/
│   └── figures/                        # Exported high-resolution research charts
│       ├── event_distribution.png
│       ├── forward_returns_comparison.png
│       ├── parameter_sensitivity_heatmap.png
│       ├── equity_curve_and_drawdowns.png
│       └── regime_comparison.png
├── RESEARCH_NOTE.md                    # Formal 2-page quant research paper
├── AI_USAGE_NOTE.md                    # 1-page reflection on AI tools, decisions & learnings
├── VIDEO_SCRIPT.md                     # 2-3 minute presentation script for video submission
├── run_pipeline.py                     # One-click master script to reproduce entire research
├── requirements.txt                    # Project dependencies
└── README.md                           # Documentation & reproduction guide
```

---

## Quickstart & Reproduction

### 1. Prerequisites
Python 3.10+ with standard scientific libraries:
```bash
pip install -r requirements.txt
```

### 2. Run the Full Research Pipeline (One-Click)
To execute the end-to-end data pipeline, run hypothesis tests, simulate the backtest, and generate all figures:
```bash
python run_pipeline.py
```

### 3. Run the Interactive Jupyter Notebook
To inspect the research interactively:
```bash
jupyter notebook notebooks/quant_research_nifty.ipynb
```

---

## Methodology & Experimental Design

### 1. Data Ingestion & Validation
- **Asset:** NIFTY 50 Index (`^NSEI`), daily OHLC bars from 2007-09-17 to 2026-09-21 (4,664 trading sessions).
- **Validation Audits:** Automated verification for zero missing trading days, strict chronological monotonicity, positive price values, and mathematical OHLC consistency ($High \ge \max(Open, Close)$, $Low \le \min(Open, Close)$).

### 2. Event & Recovery Definitions
- **Significant Fall ($E_t$):** Daily return $R_t = \frac{C_t - C_{t-1}}{C_{t-1}} \le \theta$, where $\theta = -1.5\%$ is the primary threshold (352 qualifying sessions).
- **Execution Models:**
  - *Theoretical ($T$ Close):* Instantaneous execution at $T$ Close ($R = \frac{C_{t+h} - C_t}{C_t}$).
  - *Realistic ($T+1$ Open):* Executed at next-session Open after signal confirmation ($R = \frac{C_{t+h} - O_{t+1}}{O_{t+1}}$).
- **Observation Independence:** Implemented a 3-day lockout window to filter overlapping clustered events (yielding 244 independent observations).

### 3. Statistical Testing Framework
- **Two-Sample Welch's $t$-Test:** Compares event forward returns directly against unconditional baseline returns of the same duration.
- **Mann-Whitney U Test:** Non-parametric evaluation of median and distributional shifts.
- **5,000-Iteration Bootstrap:** Empirical resampling with replacement to construct 95% confidence intervals without assuming normality.
- **Bonferroni Multi-Testing Correction:** Controls Family-Wise Error Rate (FWER) across multi-horizon comparisons.

### 4. Parameter Sensitivity & Robustness Grid
Tested a 2D matrix of thresholds ($\theta \in \{-1.0\%, -1.5\%, -2.0\%, -2.5\%, -3.0\%\}$) against holding horizons ($h \in \{1, 2, 3, 5, 10\}$ days). Results show that deeper drops ($\le -3.0\%$) lead to larger negative forward returns on days 1 and 2, confirming **short-term downside momentum**.

### 5. In-Sample vs. Out-of-Sample Split
- **In-Sample (2007–2019):** 261 events. 1-day mean return = $-0.09\%$ (Win Rate: $47.1\%$). Dip-buying was persistently unprofitable.
- **Out-of-Sample (2020–2026):** 91 events. 1-day mean return = $+0.19\%$ (Win Rate: $56.0\%$). Post-COVID central bank liquidity and domestic SIP inflows created a transient regime where dip-buying appeared to work. The edge is **non-stationary**.

### 6. Event-Driven Backtest
- Capital: ₹100,000.
- Costs: 10 bps round-trip transaction costs + slippage.
- Strategy CAGR: **1.70%** (vs. Benchmark **9.07%**).
- Max Drawdown: **-57.63%** during the 2008 crash.

---

## Submission Artifacts

- [Research Note (2 Pages)](RESEARCH_NOTE.md)
- [AI Usage Note (1 Page)](AI_USAGE_NOTE.md)
- [Video Presentation Script (2-3 Minutes)](VIDEO_SCRIPT.md)
- [Interactive Jupyter Notebook](notebooks/quant_research_nifty.ipynb)
- [Master Pipeline Script](run_pipeline.py)
- [Figures & Visualizations](reports/figures/)

---

## License
MIT License. Free for educational and research purposes.
