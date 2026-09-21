"""
visualizer.py
=============
Module for generating publication-quality figures for the research report:
1. Return distribution with event threshold cutoffs
2. Event-study forward returns comparison vs baseline with bootstrap 95% CIs
3. Parameter sensitivity matrix / heatmap
4. Strategy equity curve and underwater drawdowns vs benchmark
5. In-Sample vs Out-of-Sample regime comparison
"""

import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import numpy as np
import pandas as pd


# Set professional aesthetics
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.titleweight'] = 'bold'
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['figure.titlesize'] = 14


def plot_return_distribution(df, thresholds=[-0.015, -0.02], save_path="reports/figures/event_distribution.png"):
    """
    Plots the daily return distribution with marked event threshold cutoffs.
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    returns = df['daily_return'].dropna() * 100.0

    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    sns.histplot(returns, bins=120, kde=True, color='#2563eb', alpha=0.45, ax=ax, edgecolor='none')

    colors = ['#dc2626', '#b91c1c']
    for t, c in zip(thresholds, colors):
        val = t * 100.0
        n_hits = (df['daily_return'] <= t).sum()
        pct_hits = (n_hits / len(df)) * 100.0
        ax.axvline(val, color=c, linestyle='--', linewidth=2.0, label=f'Threshold: {val:.1f}% (N={n_hits}, {pct_hits:.1f}%)')

    ax.set_title("NIFTY 50 Daily Return Distribution & Extreme Downside Event Thresholds (2007–2026)")
    ax.set_xlabel("Daily Return (%)")
    ax.set_ylabel("Frequency / Density")
    ax.set_xlim(-8, 8)
    ax.legend(loc='upper right', frameon=True)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    print(f"[Visualizer] Saved return distribution plot to '{save_path}'")


def plot_forward_returns_comparison(res_open, res_close, save_path="reports/figures/forward_returns_comparison.png"):
    """
    Bar chart comparing forward returns across horizons with 95% bootstrap confidence intervals.
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    horizons = res_open['holding_days'].tolist()
    x = np.arange(len(horizons))
    width = 0.25

    fig, ax = plt.subplots(figsize=(11, 5.5), dpi=300)

    # Baseline
    base_means = res_open['baseline_mean'] * 100.0
    rects1 = ax.bar(x - width, base_means, width, label='Unconditional Baseline (All Days)', color='#64748b', alpha=0.85)

    # Theoretical Close Entry
    close_means = res_close['event_mean'] * 100.0
    close_err_low = (res_close['event_mean'] - res_close['ci_95_lower']) * 100.0
    close_err_high = (res_close['ci_95_upper'] - res_close['event_mean']) * 100.0
    close_err = [close_err_low.values, close_err_high.values]
    rects2 = ax.bar(x, close_means, width, yerr=close_err, capsize=4, label='Event: Theoretical (T Close Entry)', color='#3b82f6', alpha=0.9)

    # Realistic Open Entry
    open_means = res_open['event_mean'] * 100.0
    open_err_low = (res_open['event_mean'] - res_open['ci_95_lower']) * 100.0
    open_err_high = (res_open['ci_95_upper'] - res_open['event_mean']) * 100.0
    open_err = [open_err_low.values, open_err_high.values]
    rects3 = ax.bar(x + width, open_means, width, yerr=open_err, capsize=4, label='Event: Realistic Execution (T+1 Open Entry)', color='#10b981', alpha=0.9)

    ax.axhline(0, color='#94a3b8', linestyle='-', linewidth=0.8)
    ax.set_ylabel("Mean Forward Return (%)")
    ax.set_xlabel("Holding Period Horizon (Trading Days)")
    ax.set_title("Forward Return Post-Significant Fall (<= -1.5%) vs. Unconditional Market Baseline (with 95% Bootstrap CIs)")
    ax.set_xticks(x)
    ax.set_xticklabels([f'{h} Day{"s" if h>1 else ""}' for h in horizons])
    ax.legend(loc='upper left', frameon=True)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    print(f"[Visualizer] Saved forward returns comparison plot to '{save_path}'")


def plot_sensitivity_heatmap(sensitivity_df, save_path="reports/figures/parameter_sensitivity_heatmap.png"):
    """
    Plots a 2D parameter heatmap of mean forward returns across thresholds and holding periods.
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    pivot = sensitivity_df.pivot(index='threshold_pct', columns='holding_days', values='mean_return_pct')

    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
    sns.heatmap(pivot, annot=True, fmt=".2f", cmap="vlag", center=0, cbar_kws={'label': 'Mean Net Return (%)'}, ax=ax)
    ax.set_title("Parameter Sensitivity Matrix: Mean Forward Return (%) [Entry: T+1 Open]")
    ax.set_xlabel("Holding Period Horizon (Trading Days)")
    ax.set_ylabel("Daily Fall Threshold (%)")
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    print(f"[Visualizer] Saved sensitivity heatmap to '{save_path}'")


def plot_equity_and_drawdowns(daily_equity_open, daily_equity_close, save_path="reports/figures/equity_curve_and_drawdowns.png"):
    """
    Plots strategy equity curve vs Buy & Hold and the underwater drawdown profiles.
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), dpi=300, sharex=True, gridspec_kw={'height_ratios': [2.2, 1]})

    dates = pd.to_datetime(daily_equity_open['date'])

    # Top: Equity curves
    ax1.plot(dates, daily_equity_open['benchmark_value'], label='Benchmark: Buy & Hold NIFTY 50', color='#64748b', linewidth=1.5, alpha=0.9)
    ax1.plot(dates, daily_equity_close['portfolio_value'], label='Dip-Buyer Strategy (Theoretical T Close Entry)', color='#3b82f6', linewidth=1.8, linestyle='--')
    ax1.plot(dates, daily_equity_open['portfolio_value'], label='Dip-Buyer Strategy (Realistic T+1 Open Entry, 10 bps Cost)', color='#10b981', linewidth=2.0)

    ax1.set_yscale('log')
    ax1.set_ylabel("Portfolio Value (INR, Log Scale)")
    ax1.set_title("Cumulative Performance & Realistic Execution Impact (Initial Capital = 100,000 INR)")
    ax1.legend(loc='upper left', frameon=True)

    # Bottom: Underwater drawdowns
    ax2.plot(dates, daily_equity_open['bench_drawdown'] * 100.0, label='NIFTY Buy & Hold DD', color='#64748b', alpha=0.6, linewidth=1.2)
    ax2.plot(dates, daily_equity_open['drawdown'] * 100.0, label='Realistic Dip-Buyer Strategy DD', color='#ef4444', linewidth=1.4)
    ax2.fill_between(dates, daily_equity_open['drawdown'] * 100.0, 0, color='#ef4444', alpha=0.2)

    ax2.set_ylabel("Drawdown (%)")
    ax2.set_xlabel("Date")
    ax2.set_ylim(-65, 5)
    ax2.legend(loc='lower left', frameon=True)

    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    print(f"[Visualizer] Saved equity and drawdown plot to '{save_path}'")


def plot_regime_comparison(regime_df, save_path="reports/figures/regime_comparison.png"):
    """
    Plots In-Sample (2007-2019) vs Out-of-Sample (2020-2026) forward returns across horizons.
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)

    horizons = sorted(regime_df['holding_days'].unique())
    x = np.arange(len(horizons))
    width = 0.35

    is_df = regime_df[regime_df['regime'] == 'In-Sample (2007-2019)'].sort_values('holding_days')
    oos_df = regime_df[regime_df['regime'] == 'Out-of-Sample (2020-2026)'].sort_values('holding_days')

    ax.bar(x - width/2, is_df['mean_return_pct'], width, label='In-Sample (2007–2019)', color='#f97316', alpha=0.85)
    ax.bar(x + width/2, oos_df['mean_return_pct'], width, label='Out-of-Sample (2020–2026)', color='#8b5cf6', alpha=0.85)

    ax.axhline(0, color='#94a3b8', linestyle='-', linewidth=0.8)
    ax.set_ylabel("Mean Forward Return (%) [T+1 Open Entry]")
    ax.set_xlabel("Holding Period Horizon (Trading Days)")
    ax.set_title("Regime Shift: In-Sample (2007–2019) vs. Out-of-Sample (2020–2026) Forward Returns")
    ax.set_xticks(x)
    ax.set_xticklabels([f'{h} Day{"s" if h>1 else ""}' for h in horizons])
    ax.legend(loc='upper left', frameon=True)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    print(f"[Visualizer] Saved regime comparison plot to '{save_path}'")
