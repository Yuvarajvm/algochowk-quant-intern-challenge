"""
backtester.py
=============
Event-driven simulation engine for NIFTY dip-buying strategy.
Incorporates realistic execution (T+1 Open entry), transaction costs,
slippage, cash tracking, drawdown metrics, and benchmark comparisons.
"""

import numpy as np
import pandas as pd


class EventBacktester:
    """
    Simulates an event-driven trading strategy on daily OHLC data.
    """
    def __init__(self, df, initial_capital=100000.0, transaction_cost_bps=10.0):
        """
        Parameters:
        -----------
        df : pd.DataFrame
            Daily OHLC data sorted chronologically with 'date', 'open', 'high', 'low', 'close'.
        initial_capital : float
            Starting cash portfolio value.
        transaction_cost_bps : float
            Round-trip transaction cost + slippage in basis points (e.g. 10 bps = 0.10%).
        """
        self.df = df.copy().reset_index(drop=True)
        self.initial_capital = initial_capital
        self.cost_rate = (transaction_cost_bps / 10000.0) / 2.0  # Per-leg cost rate

    def run_backtest(self, event_mask, holding_days=3, entry_mode='open'):
        """
        Simulates the strategy:
        - When event_mask[t] is True:
          - If entry_mode == 'open': Enter at open of t+1, exit at close of t+holding_days.
          - If entry_mode == 'close': Enter at close of t, exit at close of t+holding_days.
        - Single active position (no overlapping leverage; subsequent triggers during holding are ignored).

        Returns:
        --------
        dict containing:
          - 'trades': pd.DataFrame of executed trades
          - 'daily_equity': pd.DataFrame of daily portfolio equity and drawdown
          - 'metrics': dict of strategy performance statistics
        """
        df = self.df
        n_bars = len(df)
        trades = []

        cash = self.initial_capital
        position = 0  # 1 if in trade, 0 if cash
        entry_idx = None
        entry_price = 0.0
        entry_date = None
        shares = 0.0

        daily_equity = pd.DataFrame({
            'date': df['date'],
            'close': df['close'],
            'cash': np.nan,
            'portfolio_value': np.nan,
            'position': 0
        })

        # Track simulation bar by bar
        i = 0
        while i < n_bars:
            # Check exit first if in position
            if position == 1:
                # Check if holding period has completed
                held_bars = i - entry_idx
                # If entry was at open of entry_idx, on day entry_idx at close we have held 1 day (intraday)
                # Exit at close of entry_idx + holding_days - 1
                exit_bar = entry_idx + (holding_days - 1 if entry_mode == 'open' else holding_days)
                
                if i >= exit_bar or i == n_bars - 1:
                    # Exit at today's Close
                    exit_price = df.loc[i, 'close'] * (1.0 - self.cost_rate)
                    exit_date = df.loc[i, 'date']
                    gross_ret = (df.loc[i, 'close'] - raw_entry_price) / raw_entry_price
                    net_ret = (exit_price - entry_price) / entry_price
                    pnl = (shares * exit_price) - (shares * entry_price)
                    cash = shares * exit_price
                    position = 0
                    shares = 0.0

                    trades.append({
                        'entry_date': entry_date,
                        'exit_date': exit_date,
                        'entry_idx': entry_idx,
                        'exit_idx': i,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'gross_return': gross_ret,
                        'net_return': net_ret,
                        'pnl': pnl,
                        'holding_bars': i - entry_idx + 1
                    })

            # Check new entry signal if not currently in position
            if position == 0 and i < n_bars - 1:
                if event_mask.iloc[i]:
                    # Signal triggered on bar i (crash day)
                    if entry_mode == 'open':
                        # Enter at open of next day (i + 1)
                        entry_idx = i + 1
                        raw_entry_price = df.loc[entry_idx, 'open']
                        entry_price = raw_entry_price * (1.0 + self.cost_rate)
                        entry_date = df.loc[entry_idx, 'date']
                        shares = cash / entry_price
                        cash = 0.0
                        position = 1
                        # Jump index to entry_idx
                        daily_equity.loc[i, 'portfolio_value'] = self.initial_capital if i == 0 else daily_equity.loc[i-1, 'portfolio_value']
                        daily_equity.loc[i, 'cash'] = self.initial_capital if i == 0 else daily_equity.loc[i-1, 'cash']
                        i += 1
                        continue
                    else:
                        # Enter at close of day i
                        entry_idx = i
                        raw_entry_price = df.loc[i, 'close']
                        entry_price = raw_entry_price * (1.0 + self.cost_rate)
                        entry_date = df.loc[i, 'date']
                        shares = cash / entry_price
                        cash = 0.0
                        position = 1

            # Compute daily mark-to-market portfolio value
            if position == 1:
                cur_val = shares * df.loc[i, 'close']
            else:
                cur_val = cash

            daily_equity.loc[i, 'cash'] = cash
            daily_equity.loc[i, 'portfolio_value'] = cur_val
            daily_equity.loc[i, 'position'] = position
            i += 1

        # Fill forward any missing values
        daily_equity['portfolio_value'] = daily_equity['portfolio_value'].ffill().fillna(self.initial_capital)
        daily_equity['cash'] = daily_equity['cash'].ffill().fillna(self.initial_capital)

        # Benchmark (Buy and Hold NIFTY)
        daily_equity['benchmark_value'] = (df['close'] / df['close'].iloc[0]) * self.initial_capital

        # Calculate drawdowns
        daily_equity['hwm'] = daily_equity['portfolio_value'].cummax()
        daily_equity['drawdown'] = (daily_equity['portfolio_value'] - daily_equity['hwm']) / daily_equity['hwm']

        daily_equity['bench_hwm'] = daily_equity['benchmark_value'].cummax()
        daily_equity['bench_drawdown'] = (daily_equity['benchmark_value'] - daily_equity['bench_hwm']) / daily_equity['bench_hwm']

        trades_df = pd.DataFrame(trades)
        metrics = self._calculate_performance_metrics(daily_equity, trades_df)

        return {
            'trades': trades_df,
            'daily_equity': daily_equity,
            'metrics': metrics
        }

    def _calculate_performance_metrics(self, daily_equity, trades_df, rf_rate=0.05):
        """
        Calculates annualized performance metrics.
        """
        total_days = (daily_equity['date'].iloc[-1] - daily_equity['date'].iloc[0]).days
        years = total_days / 365.25

        init_val = self.initial_capital
        final_val = daily_equity['portfolio_value'].iloc[-1]
        bench_final = daily_equity['benchmark_value'].iloc[-1]

        cagr = (final_val / init_val) ** (1.0 / years) - 1.0 if years > 0 else np.nan
        bench_cagr = (bench_final / init_val) ** (1.0 / years) - 1.0 if years > 0 else np.nan

        daily_ret = daily_equity['portfolio_value'].pct_change().dropna()
        ann_vol = daily_ret.std() * np.sqrt(252)
        sharpe = (cagr - rf_rate) / ann_vol if ann_vol > 0 else np.nan

        downside_ret = daily_ret[daily_ret < 0]
        downside_vol = downside_ret.std() * np.sqrt(252) if len(downside_ret) > 1 else np.nan
        sortino = (cagr - rf_rate) / downside_vol if downside_vol and downside_vol > 0 else np.nan

        max_dd = daily_equity['drawdown'].min()
        bench_max_dd = daily_equity['bench_drawdown'].min()
        calmar = cagr / abs(max_dd) if abs(max_dd) > 0 else np.nan

        n_trades = len(trades_df)
        if n_trades > 0:
            win_rate = (trades_df['net_return'] > 0).mean()
            avg_ret = trades_df['net_return'].mean()
            median_ret = trades_df['net_return'].median()
            wins = trades_df[trades_df['net_return'] > 0]['pnl']
            losses = trades_df[trades_df['net_return'] < 0]['pnl']
            profit_factor = wins.sum() / abs(losses.sum()) if abs(losses.sum()) > 0 else np.nan
        else:
            win_rate = avg_ret = median_ret = profit_factor = np.nan

        market_exposure = (daily_equity['position'] > 0).mean()

        return {
            'initial_capital': init_val,
            'final_equity': final_val,
            'total_return_pct': (final_val - init_val) / init_val * 100.0,
            'cagr_pct': cagr * 100.0,
            'benchmark_cagr_pct': bench_cagr * 100.0,
            'annualized_vol_pct': ann_vol * 100.0,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'calmar_ratio': calmar,
            'max_drawdown_pct': max_dd * 100.0,
            'bench_max_drawdown_pct': bench_max_dd * 100.0,
            'total_trades': n_trades,
            'win_rate_pct': win_rate * 100.0 if not np.isnan(win_rate) else np.nan,
            'avg_trade_return_pct': avg_ret * 100.0 if not np.isnan(avg_ret) else np.nan,
            'median_trade_return_pct': median_ret * 100.0 if not np.isnan(median_ret) else np.nan,
            'profit_factor': profit_factor,
            'market_exposure_pct': market_exposure * 100.0
        }


if __name__ == "__main__":
    from data_loader import fetch_nifty_data
    from event_engine import EventEngine

    df = fetch_nifty_data()
    engine = EventEngine(df)
    mask = engine.detect_events(threshold=-0.015)

    bt = EventBacktester(df, transaction_cost_bps=10.0)
    res = bt.run_backtest(mask, holding_days=3, entry_mode='open')
    print("Backtest Performance Metrics:")
    for k, v in res['metrics'].items():
        print(f"  {k}: {v:.2f}" if isinstance(v, float) else f"  {k}: {v}")
