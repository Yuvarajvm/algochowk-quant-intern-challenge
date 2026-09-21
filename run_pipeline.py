"""
run_pipeline.py
===============
Master script that runs the entire end-to-end quantitative research study:
1. Data ingestion and quality validation
2. Event detection and forward return computation
3. Comparative statistical hypothesis testing & bootstrapping
4. Robustness & parameter sensitivity exploration
5. In-Sample vs. Out-of-Sample validation
6. Event-driven backtest simulation (with transaction costs and slippage)
7. Generation and export of all publication-grade figures
"""

import os
import sys
import numpy as np
import pandas as pd

# Ensure workspace directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'src'))

from src.data_loader import fetch_nifty_data
from src.event_engine import EventEngine
from src.statistical_tests import (
    analyze_horizons,
    compute_summary_statistics,
    bootstrap_confidence_interval,
    run_comparative_hypothesis_tests
)
from src.backtester import EventBacktester
from src.visualizer import (
    plot_return_distribution,
    plot_forward_returns_comparison,
    plot_sensitivity_heatmap,
    plot_equity_and_drawdowns,
    plot_regime_comparison
)


def run_full_pipeline():
    print("=" * 80)
    print(" ALGOCHOWK QUANT ENGINEER INTERN CHALLENGE: RESEARCH PIPELINE ")
    print(" Investigating: 'After a significant one-day fall in NIFTY,")
    print("                 the market tends to recover over the next few trading days.'")
    print("=" * 80)

    # 1. Load Data
    print("\n[STEP 1] Data Ingestion & Validation...")
    df = fetch_nifty_data()
    print(f"Total trading days: {len(df)}")
    print(f"Coverage: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")

    # Plot return distribution
    plot_return_distribution(df, thresholds=[-0.015, -0.020])

    # 2. Event Engine & Baseline Forward Returns
    print("\n[STEP 2] Event Detection & Forward Return Extraction...")
    engine = EventEngine(df)
    full_fwd = engine.calculate_forward_returns(holding_periods=[1, 2, 3, 5, 10])

    # Primary event threshold: -1.5% drop
    events_raw = engine.extract_event_dataset(threshold=-0.015, filter_overlapping=False)
    events_indep = engine.extract_event_dataset(threshold=-0.015, filter_overlapping=True, lockout_window=3)

    print(f"Total qualifying events (drop <= -1.5%): {len(events_raw)}")
    print(f"Independent events (with 3-day lockout): {len(events_indep)}")

    # 3. Statistical Analysis: Realistic (T+1 Open) vs. Theoretical (T Close)
    print("\n[STEP 3] Statistical Testing & Horizon Evaluation (Primary Threshold = -1.5%)...")
    res_open = analyze_horizons(events_raw, full_fwd, holding_periods=[1, 2, 3, 5, 10], entry_mode='open')
    res_close = analyze_horizons(events_raw, full_fwd, holding_periods=[1, 2, 3, 5, 10], entry_mode='close')

    print("\n--- STATISTICAL RESULTS: REALISTIC EXECUTION (T+1 Open Entry) ---")
    open_display = res_open[['holding_days', 'event_mean', 'ci_95_lower', 'ci_95_upper', 'baseline_mean', 'diff_means', 'event_win_rate', 'welch_t_stat', 'welch_p_val', 'bonferroni_p_val']].copy()
    open_display['event_mean'] *= 100.0
    open_display['ci_95_lower'] *= 100.0
    open_display['ci_95_upper'] *= 100.0
    open_display['baseline_mean'] *= 100.0
    open_display['diff_means'] *= 100.0
    open_display['event_win_rate'] *= 100.0
    print(open_display.to_string(index=False, float_format=lambda x: f"{x:8.3f}"))

    print("\n--- STATISTICAL RESULTS: THEORETICAL EXECUTION (T Close Entry) ---")
    close_display = res_close[['holding_days', 'event_mean', 'ci_95_lower', 'ci_95_upper', 'baseline_mean', 'diff_means', 'event_win_rate', 'welch_t_stat', 'welch_p_val', 'bonferroni_p_val']].copy()
    close_display['event_mean'] *= 100.0
    close_display['ci_95_lower'] *= 100.0
    close_display['ci_95_upper'] *= 100.0
    close_display['baseline_mean'] *= 100.0
    close_display['diff_means'] *= 100.0
    close_display['event_win_rate'] *= 100.0
    print(close_display.to_string(index=False, float_format=lambda x: f"{x:8.3f}"))

    # Plot forward returns comparison
    plot_forward_returns_comparison(res_open, res_close)

    # 4. Parameter Sensitivity & Robustness Matrix
    print("\n[STEP 4] Parameter Sensitivity & Robustness Analysis...")
    thresholds = [-0.010, -0.015, -0.020, -0.025, -0.030]
    horizons = [1, 2, 3, 5, 10]
    sensitivity_rows = []

    for t in thresholds:
        ev_sub = engine.extract_event_dataset(threshold=t, filter_overlapping=False)
        for h in horizons:
            ret_series = ev_sub[f'fwd_ret_open_{h}d'].dropna()
            mean_ret = ret_series.mean() * 100.0 if len(ret_series) > 0 else np.nan
            win_r = (ret_series > 0).mean() * 100.0 if len(ret_series) > 0 else np.nan
            sensitivity_rows.append({
                'threshold_pct': f"{t*100:.1f}%",
                'holding_days': h,
                'events_n': len(ret_series),
                'mean_return_pct': mean_ret,
                'win_rate_pct': win_r
            })

    sensitivity_df = pd.DataFrame(sensitivity_rows)
    plot_sensitivity_heatmap(sensitivity_df)

    # 5. Out-of-Sample Validation
    print("\n[STEP 5] In-Sample (2007–2019) vs. Out-of-Sample (2020–2026) Validation...")
    split_date = '2020-01-01'
    df_is = df[df['date'] < split_date].copy()
    df_oos = df[df['date'] >= split_date].copy()

    engine_is = EventEngine(df_is)
    engine_oos = EventEngine(df_oos)

    events_is = engine_is.extract_event_dataset(threshold=-0.015)
    events_oos = engine_oos.extract_event_dataset(threshold=-0.015)

    regime_rows = []
    for h in [1, 2, 3, 5, 10]:
        ret_is = events_is[f'fwd_ret_open_{h}d'].dropna()
        ret_oos = events_oos[f'fwd_ret_open_{h}d'].dropna()
        regime_rows.append({
            'regime': 'In-Sample (2007-2019)',
            'holding_days': h,
            'n_events': len(ret_is),
            'mean_return_pct': ret_is.mean() * 100.0,
            'win_rate_pct': (ret_is > 0).mean() * 100.0
        })
        regime_rows.append({
            'regime': 'Out-of-Sample (2020-2026)',
            'holding_days': h,
            'n_events': len(ret_oos),
            'mean_return_pct': ret_oos.mean() * 100.0,
            'win_rate_pct': (ret_oos > 0).mean() * 100.0
        })

    regime_df = pd.DataFrame(regime_rows)
    print("\n--- REGIME COMPARISON TABLE ---")
    regime_pivot = regime_df.pivot(index='holding_days', columns='regime', values=['mean_return_pct', 'win_rate_pct'])
    print(regime_pivot.to_string(float_format=lambda x: f"{x:6.2f}%"))
    plot_regime_comparison(regime_df)

    # 6. Event-Driven Backtest Simulation
    print("\n[STEP 6] Event-Driven Backtesting Simulation...")
    mask_primary = engine.detect_events(threshold=-0.015)
    backtester = EventBacktester(df, initial_capital=100000.0, transaction_cost_bps=10.0)

    res_bt_open = backtester.run_backtest(mask_primary, holding_days=3, entry_mode='open')
    res_bt_close = backtester.run_backtest(mask_primary, holding_days=3, entry_mode='close')

    print("\n--- BACKTEST PERFORMANCE COMPARISON ---")
    m_open = res_bt_open['metrics']
    m_close = res_bt_close['metrics']

    comparison_table = pd.DataFrame({
        'Metric': [
            'Initial Capital (INR)',
            'Final Portfolio Equity (INR)',
            'Total Return (%)',
            'Strategy CAGR (%)',
            'Benchmark NIFTY CAGR (%)',
            'Annualized Volatility (%)',
            'Sharpe Ratio (Rf=5%)',
            'Sortino Ratio',
            'Maximum Drawdown (%)',
            'Benchmark Max DD (%)',
            'Total Completed Trades',
            'Win Rate (%)',
            'Average Trade Return (%)',
            'Profit Factor',
            'Market Exposure Time (%)'
        ],
        'Realistic (T+1 Open Entry)': [
            f"{m_open['initial_capital']:,.0f}",
            f"{m_open['final_equity']:,.0f}",
            f"{m_open['total_return_pct']:.2f}%",
            f"{m_open['cagr_pct']:.2f}%",
            f"{m_open['benchmark_cagr_pct']:.2f}%",
            f"{m_open['annualized_vol_pct']:.2f}%",
            f"{m_open['sharpe_ratio']:.2f}",
            f"{m_open['sortino_ratio']:.2f}",
            f"{m_open['max_drawdown_pct']:.2f}%",
            f"{m_open['bench_max_drawdown_pct']:.2f}%",
            f"{m_open['total_trades']}",
            f"{m_open['win_rate_pct']:.2f}%",
            f"{m_open['avg_trade_return_pct']:.2f}%",
            f"{m_open['profit_factor']:.2f}",
            f"{m_open['market_exposure_pct']:.2f}%"
        ],
        'Theoretical (T Close Entry)': [
            f"{m_close['initial_capital']:,.0f}",
            f"{m_close['final_equity']:,.0f}",
            f"{m_close['total_return_pct']:.2f}%",
            f"{m_close['cagr_pct']:.2f}%",
            f"{m_close['benchmark_cagr_pct']:.2f}%",
            f"{m_close['annualized_vol_pct']:.2f}%",
            f"{m_close['sharpe_ratio']:.2f}",
            f"{m_close['sortino_ratio']:.2f}",
            f"{m_close['max_drawdown_pct']:.2f}%",
            f"{m_close['bench_max_drawdown_pct']:.2f}%",
            f"{m_close['total_trades']}",
            f"{m_close['win_rate_pct']:.2f}%",
            f"{m_close['avg_trade_return_pct']:.2f}%",
            f"{m_close['profit_factor']:.2f}",
            f"{m_close['market_exposure_pct']:.2f}%"
        ]
    })
    print(comparison_table.to_string(index=False))

    plot_equity_and_drawdowns(res_bt_open['daily_equity'], res_bt_close['daily_equity'])

    print("\n" + "=" * 80)
    print(" PIPELINE EXECUTION COMPLETE. ALL FIGURES EXPORTED TO 'reports/figures/' ")
    print("=" * 80)


if __name__ == "__main__":
    run_full_pipeline()
