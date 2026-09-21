# 2–3 Minute Video Presentation Script & Storyboard
### AlgoChowk — Quant Engineer Intern Research Submission
**Topic:** Quantitative Investigation of NIFTY 50 Post-Crash Recovery Dynamics  
**Total Target Duration:** ~2 minutes 30 seconds (150 seconds)  

---

### Storyboard & Script Breakdown

```
[0:00 - 0:25] INTRO & HYPOTHESIS FORMULATION
[0:25 - 0:55] RESEARCH DESIGN & REALISTIC EXECUTION
[0:55 - 1:30] STATISTICAL EVIDENCE & BASELINE COMPARISON
[1:30 - 2:05] PARAMETER ROBUSTNESS, OUT-OF-SAMPLE & BACKTEST
[2:05 - 2:30] CONCLUSION & KEY QUANT LEARNINGS
```

---

#### Scene 1: Introduction & The Hypothesis [0:00 – 0:25]
**Visual:** Show the Title Slide or README header, then display the NIFTY 50 Daily Return Distribution chart (`reports/figures/event_distribution.png`).

**Spoken Script:**
> *"Hello everyone. Today I'm presenting my investigation of the hypothesis: **'After a significant one-day fall in NIFTY, the market tends to recover over the next few trading days.'**  
> In quantitative trading, this tests a core market microstructure question: Is a sharp drop an overreaction that offers a profitable mean-reversion opportunity, or is it the onset of a liquidation cascade where buying the dip is catching a falling knife?  
> To answer this scientifically, I analyzed 19 years of daily NIFTY 50 data from 2007 through 2026, comprising 4,664 trading sessions."*

---

#### Scene 2: Research Design & Realistic Execution [0:25 – 0:55]
**Visual:** Screen-record the Jupyter notebook code cell or show the Primary Event Study Table from the Research Note.

**Spoken Script:**
> *"I defined a significant drop as a daily fall of 1.5% or greater, identifying 352 events.  
> The first crucial quantitative decision was execution realism. A common trap in amateur research is assuming entry at the crash day's Close. But in production, you can only confirm the day's return at the closing bell, meaning executable market orders can only be placed at the next day's Open.  
> When comparing theoretical Close entry to realistic Open entry, the apparent edge completely shifts. Over a 1-day holding horizon, the return drops from positive 0.05% to negative 0.02%, with a win rate below 50%, because opening gaps and continued morning volatility erase the bounce."*

---

#### Scene 3: Statistical Evidence & Baseline Benchmarking [0:55 – 1:30]
**Visual:** Switch to `reports/figures/forward_returns_comparison.png` showing the bar chart with 95% bootstrap error bars.

**Spoken Script:**
> *"Next, I benchmarked post-event forward returns against the unconditional market baseline. Because NIFTY naturally drifts upward at about 0.04% per day, any dip-buying strategy must demonstrate statistically significant excess return beyond this natural drift.  
> Over a 3-day holding period, the realistic post-event return was +0.199% compared to the baseline of +0.131%. Using a two-sample Welch’s t-test and 5,000-sample bootstrap confidence intervals, the p-value was 0.719, and the Bonferroni-adjusted p-value across all horizons was 1.0.  
> In other words, there is zero statistically significant evidence that NIFTY recovers faster after a crash than it does during normal market conditions."*

---

#### Scene 4: Robustness Grid, Out-of-Sample & Backtest [1:30 – 2:05]
**Visual:** Show the Sensitivity Heatmap (`reports/figures/parameter_sensitivity_heatmap.png`), followed by the Equity & Drawdown curves (`reports/figures/equity_curve_and_drawdowns.png`).

**Spoken Script:**
> *"To ensure I didn't fall prey to data snooping, I tested a parameter grid from -1.0% to -3.0% drops. Remarkably, as drops became more severe, next-day returns became progressively more negative (-0.18% for drops $\le -3.0\%$), confirming downside momentum.  
> Splitting the data chronologically revealed that between 2007 and 2019, buying dips had a negative 1-day return (-0.09%). It only appeared profitable post-2020 due to aggressive monetary liquidity and retail SIP flows.  
> Simulating an event-driven backtest with realistic 10 basis points transaction costs yielded a CAGR of just 1.7% versus 9.1% for Buy-and-Hold, while suffering a brutal 57.6% maximum drawdown during the 2008 financial crisis."*

---

#### Scene 5: Conclusion & Key Learnings [2:05 – 2:30]
**Visual:** Switch back to the conclusion section of `RESEARCH_NOTE.md` or face camera.

**Spoken Script:**
> *"In conclusion, I reject the naive hypothesis. Buying after a one-day drop is not a robust standalone edge in NIFTY 50.  
> My key takeaway from this challenge is that good quantitative research is not about torturing data to produce an artificial backtest. It is about intellectual honesty, rigorous falsification, and respecting execution friction.  
> To make dip-buying viable in production, it must be conditioned on macro trend filters, such as the 200-day moving average, and volatility regime filters.  
> Thank you for your time and consideration!"*

---

### Tips for Recording
1. **Pacing:** Speak at a confident, deliberate pace (~130 words per minute).
2. **Screen Highlights:** Use your mouse cursor or presentation pointer to highlight the p-value column ($p = 0.719$) and the drawdown curve during Scene 3 and 4.
3. **Tone:** Keep the tone objective, analytical, and professional.
