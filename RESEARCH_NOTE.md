# Quantitative Research Note: Event-Driven Rebound Dynamics in NIFTY 50

**Author:** Quantitative Research Candidate  
**Target Role:** Quant Engineer Intern, AlgoChowk  
**Date:** September 2026  
**Status:** Complete Empirical Investigation & Falsification Note  

---

### Abstract
We investigate the market hypothesis: *"After a significant one-day fall in NIFTY, the market tends to recover over the next few trading days."* Analyzing 4,664 daily bars of NIFTY 50 (`^NSEI`) spanning September 2007 through September 2026, we detect 352 events where daily return fell $\le -1.5\%$. When evaluated under realistic execution ($T+1$ Open entry) rather than theoretical look-ahead entry ($T$ Close), 1-day and 2-day mean forward returns are negative ($-0.021\%$ and $-0.002\%$, with win rates of $49.4\%$ and $50.9\%$). Across all holding horizons (1 to 10 days), Welch's two-sample $t$-tests fail to reject the null hypothesis of no excess return beyond the unconditional market baseline ($p > 0.50$, Bonferroni-adjusted $p = 1.000$). Furthermore, parameter sensitivity grids show severe performance deterioration during trending market crashes (2008 GFC, March 2020), yielding a strategy CAGR of $1.70\%$ vs. $9.07\%$ for Buy & Hold, alongside a $-57.63\%$ maximum drawdown. We conclude with a **qualified falsification** of the unconditioned mean-reversion hypothesis.

---

### 1. Research Design & Formal Definitions

#### 1.1 Mathematical Formulation
Let $C_t$ and $O_t$ represent the closing and opening prices of the NIFTY 50 Index on trading day $t$. The single-day return is defined as:
$$R_t = \frac{C_t - C_{t-1}}{C_{t-1}}$$

- **Significant Fall Event ($E_t$):** An event triggers on day $t$ if $R_t \le \theta$, where $\theta = -1.5\%$ is our primary benchmark threshold (representing the lower $\sim 7.5\%$ tail of the empirical daily distribution). We also evaluate robustness across $\theta \in \{-1.0\%, -2.0\%, -2.5\%, -3.0\%\}$.
- **Forward Holding Return ($R_{\text{fwd}, h}$):** Evaluated over holding horizons $h \in \{1, 2, 3, 5, 10\}$ trading days.
- **Execution Models:**
  1. *Theoretical Entry ($T$ Close):* $R_{t, h}^{\text{Close}} = \frac{C_{t+h} - C_t}{C_t}$ (assumes instantaneous trade execution at the exact closing bell).
  2. *Realistic Execution ($T+1$ Open):* $R_{t, h}^{\text{Open}} = \frac{C_{t+h} - O_{t+1}}{O_{t+1}}$ (accounts for the operational reality that an event can only be verified at $T$ Close, with executable market orders dispatched at the subsequent session Open).
- **Recovery Definition:** An event demonstrates recovery if $R_{\text{fwd}, h}$ is both statistically greater than zero and exhibits a statistically significant positive excess return over the unconditional baseline forward return of the same duration:
$$\mathbb{E}[R_{\text{fwd}, h} \mid E_t] > \mathbb{E}[R_{\text{fwd}, h}]$$

#### 1.2 Institutional & Trading Assumptions
- **Transaction Costs & Slippage:** 10 basis points (0.10%) round-trip (5 bps per leg), representing Indian equities cash/futures statutory STT, exchange turnover fees, SEBI/stamp charges, and bid-ask spread impact.
- **Capital Allocation:** 100% position size per trade; cash earns 0% when uninvested.
- **Overlapping Events:** Subsequent signals triggered during an active holding window are locked out to prevent leveraged cluster exposure and preserve sample independence.

---

### 2. Data & Validation Pipeline
Data was ingested from Yahoo Finance for the NIFTY 50 Index from 2007-09-17 to 2026-09-21 (4,664 trading sessions). Automated data quality audits confirmed:
1. **Zero missing bars** during recognized NSE trading hours; all weekday gaps correspond to verified exchange holidays.
2. **Strict chronological ordering** with no duplicate timestamps.
3. **OHLC Logical Consistency:** $High \ge \max(Open, Close)$ and $Low \le \min(Open, Close)$ validated on 100% of rows.
4. **Anomalies:** Extreme tail events (e.g., 2008 circuit breaks, 2020 COVID selloff, and 2024 general election result swing) were verified against official NSE circular records.

---

### 3. Empirical Findings & Statistical Evidence

#### Table 1: Primary Event Study (Threshold $\le -1.5\%$, Total Events $N = 352$, Independent $N = 244$)
| Horizon ($h$) | Realistic Mean ($T+1$ Open) | 95% Bootstrap CI | Theoretical Mean ($T$ Close) | Unconditional Baseline | Welch's $t$-stat | $p$-value | Win Rate (%) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1 Day** | **-0.021%** | [-0.233%, +0.195%] | +0.054% | +0.044% | -0.578 | 0.564 | 49.4% |
| **2 Days** | **-0.002%** | [-0.320%, +0.296%] | +0.076% | +0.088% | -0.552 | 0.582 | 50.9% |
| **3 Days** | **+0.199%** | [-0.155%, +0.566%] | +0.281% | +0.131% | +0.360 | 0.719 | 55.4% |
| **5 Days** | **+0.303%** | [-0.182%, +0.805%] | +0.384% | +0.215% | +0.345 | 0.730 | 54.5% |
| **10 Days**| **+0.478%** | [-0.187%, +1.124%] | +0.560% | +0.423% | +0.163 | 0.870 | 56.5% |

*Note: Welch's $t$-test evaluates $H_0: \mu_{\text{event}} = \mu_{\text{baseline}}$. Across all horizons, Bonferroni-corrected $p$-values equal 1.000.*

#### Key Observations:
1. **Disappearance of Short-Term Edge:** In theoretical Close entry, 1-day mean return is $+0.054\%$. Under realistic Open execution, it flips to **$-0.021\%$** with a sub-50% win rate ($49.4\%$). The apparent bounce is largely an artifact of overnight gap risk and continued selling at market open.
2. **Absence of Excess Alpha:** Over a 3-day holding horizon, realistic forward return is $+0.199\%$ vs. $+0.131\%$ for the baseline. The $+0.068\%$ difference yields $p = 0.719$. There is no statistical evidence that post-crash returns exceed natural market drift.

---

### 4. Robustness, Sensitivity & Out-of-Sample Validation

#### 4.1 Parameter Sensitivity Grid (Mean Return % under Realistic Execution)
| Threshold $\theta$ | $h = 1\text{d}$ | $h = 2\text{d}$ | $h = 3\text{d}$ | $h = 5\text{d}$ | $h = 10\text{d}$ | Events ($N$) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **-1.0%** | -0.01% | +0.04% | +0.18% | +0.25% | +0.45% | 648 |
| **-1.5%** | -0.02% | -0.00% | +0.20% | +0.30% | +0.48% | 352 |
| **-2.0%** | -0.04% | -0.06% | +0.12% | +0.16% | +0.44% | 200 |
| **-2.5%** | -0.09% | -0.08% | +0.14% | +0.22% | +0.58% | 114 |
| **-3.0%** | -0.18% | -0.15% | +0.05% | +0.26% | +0.72% | 68 |

*Observation:* As the severity of the drop increases from $-1.0\%$ to $-3.0\%$, the 1-day and 2-day returns become progressively *more negative* ($-0.01\% \to -0.18\%$). This confirms strong short-term **downside momentum / liquidation cascades**, completely contradicting naive mean-reversion.

#### 4.2 Out-of-Sample Regime Shift
Partitioning into **In-Sample (2007–2019, $N_{\text{events}} = 261$)** and **Out-of-Sample (2020–2026, $N_{\text{events}} = 91$)**:
- **In-Sample:** 1-day return = **$-0.09\%$** (Win Rate: $47.1\%$), 3-day return = **$+0.15\%$** (Win Rate: $52.5\%$).
- **Out-of-Sample:** 1-day return = **$+0.19\%$** (Win Rate: $56.0\%$), 3-day return = **$+0.34\%$** (Win Rate: $63.7\%$).
- *Diagnosis:* Mean-reversion was unprofitable for over a decade (2007–2019) and only turned positive post-2020 due to structural domestic retail liquidity inflows (SIPs) and aggressive RBI/global monetary easing. The edge is **non-stationary and regime-dependent**.

---

### 5. Event-Driven Backtest & Economic Viability

#### Table 2: Portfolio Simulation (10 bps Round-Trip Friction, 3-Day Holding Horizon)
| Performance Metric | Strategy: Realistic ($T+1$ Open) | Strategy: Theoretical ($T$ Close) | Benchmark: Buy & Hold NIFTY 50 |
| :--- | :---: | :---: | :---: |
| **Initial Capital** | ₹1,00,000 | ₹1,00,000 | ₹1,00,000 |
| **Final Portfolio Value** | ₹1,37,671 | ₹1,70,394 | ₹5,16,423 |
| **CAGR (%)** | **1.70%** | **2.84%** | **9.07%** |
| **Annualized Volatility** | 12.30% | 12.62% | 21.45% |
| **Sharpe Ratio ($R_f = 5\%$)** | **-0.27** | **-0.17** | **+0.19** |
| **Maximum Drawdown** | **-57.63%** | **-57.72%** | **-59.86%** |
| **Profit Factor** | 1.15 | 1.27 | N/A |
| **Market Exposure Time** | 11.36% | 17.05% | 100.0% |

The backtest demonstrates that while the strategy reduces exposure time to $11.4\%$, it suffers a severe **$-57.63\%$ drawdown** during the 2008 crash by repeatedly buying falling knives. Post-friction returns are negligible (₹1.37 lakh vs. ₹5.16 lakh for Buy & Hold).

---

### 6. Critical Thinking & Falsification Checklist
1. **Look-Ahead Bias:** Assuming entry at $T$ Close inflates 3-day returns by $41\%$ ($+0.281\%$ vs $+0.199\%$). In production, entering at $T+1$ Open eliminates this synthetic alpha.
2. **Downside Autocorrelation:** Extreme drops trigger margin calls and fund redemptions, causing serial negative returns over the immediate 48 hours.
3. **Falsification Threshold:** We formally reject the hypothesis because:
   - $p > 0.05$ across all parameterizations;
   - Net excess return over unconditional drift is statistically indistinguishable from zero;
   - Downside tail risk produces an intolerable $-57.6\%$ maximum drawdown.

### 7. Conclusion & Quant Recommendations
The unconditional hypothesis is **empirically rejected**. Simple dip-buying is not an alpha source in NIFTY 50. To transform this concept into a viable quantitative strategy, researchers must condition entries on:
- **Macro Trend Filter:** Only buy dips when NIFTY is trading above its 200-day Simple Moving Average.
- **Volatility Filter:** Avoid entries when India VIX is accelerating upward or exceeds the 90th percentile.
- **Dynamic Intraday Execution:** Execute limit orders only after morning price discovery stabilizes (e.g., VWAP cross post-10:30 AM IST) rather than blind market-on-open orders.
