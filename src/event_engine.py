"""
event_engine.py
===============
Configurable event detection and forward return computation engine.
Supports multiple event definitions (fixed percentage drop, volatility-adjusted, quantiles),
overlapping event filtering (lockout window), and realistic vs theoretical entry execution.
"""

import pandas as pd
import numpy as np


class EventEngine:
    """
    Configurable Event Detection and Forward Return Analysis Engine.
    """
    def __init__(self, df):
        self.df = df.copy()
        if 'daily_return' not in self.df.columns:
            self.df['daily_return'] = self.df['close'].pct_change()

    def detect_events(self, threshold=-0.015, method='fixed', filter_overlapping=False, lockout_window=3, rolling_window=60):
        """
        Detects qualifying market drop events.

        Parameters:
        -----------
        threshold : float
            Threshold value (e.g., -0.015 for -1.5%).
        method : str
            'fixed' : daily_return <= threshold
            'rolling_std' : daily_return <= -k * rolling_std
            'quantile' : daily_return <= historical quantile
        filter_overlapping : bool
            If True, enforces independent observations by locking out subsequent events
            for `lockout_window` trading days.
        lockout_window : int
            Number of days to ignore new signals after an initial event.
        rolling_window : int
            Window for rolling volatility calculations (if method == 'rolling_std').

        Returns:
        --------
        pd.Series (bool mask of event days)
        """
        df = self.df

        if method == 'fixed':
            raw_mask = df['daily_return'] <= threshold

        elif method == 'rolling_std':
            # e.g. threshold = 2.0 (meaning <= -2 standard deviations)
            rolling_std = df['daily_return'].rolling(window=rolling_window).std()
            k = abs(threshold) if threshold > 0 else abs(threshold) * 100
            raw_mask = df['daily_return'] <= -(k * rolling_std)

        elif method == 'quantile':
            # e.g. threshold = 0.05 for worst 5% of days
            q_val = df['daily_return'].quantile(threshold)
            raw_mask = df['daily_return'] <= q_val

        else:
            raise ValueError(f"Unknown detection method '{method}'. Choose 'fixed', 'rolling_std', or 'quantile'.")

        if not filter_overlapping:
            return raw_mask

        # Apply lockout window to ensure observation independence
        filtered_mask = pd.Series(False, index=df.index)
        last_event_idx = -lockout_window - 1

        for idx in range(len(df)):
            if raw_mask.iloc[idx]:
                if idx - last_event_idx > lockout_window:
                    filtered_mask.iloc[idx] = True
                    last_event_idx = idx

        return filtered_mask

    def calculate_forward_returns(self, holding_periods=[1, 2, 3, 5, 10]):
        """
        Calculates forward returns for every bar in the dataset for multiple holding periods.
        Computes both:
        - Theoretical Entry: T Close to T+h Close
        - Realistic Execution: T+1 Open to T+h Close
        - Overnight Gap: T Close to T+1 Open
        """
        df = self.df.copy()

        for h in holding_periods:
            # Theoretical Entry at T Close
            df[f'fwd_ret_close_{h}d'] = (df['close'].shift(-h) - df['close']) / df['close']

            # Realistic Entry at T+1 Open
            # Price is entered at open of T+1, held until close of T+h
            df[f'fwd_ret_open_{h}d'] = (df['close'].shift(-h) - df['open'].shift(-1)) / df['open'].shift(-1)

        # Immediate Next Day Gap and Next Day Intraday
        df['next_day_open_gap'] = (df['open'].shift(-1) - df['close']) / df['close']
        df['next_day_intraday'] = (df['close'].shift(-1) - df['open'].shift(-1)) / df['open'].shift(-1)

        return df

    def extract_event_dataset(self, threshold=-0.015, method='fixed', filter_overlapping=False,
                               lockout_window=3, holding_periods=[1, 2, 3, 5, 10]):
        """
        Extracts a clean, tabular dataset of all qualifying events with their forward returns.
        """
        fwd_df = self.calculate_forward_returns(holding_periods=holding_periods)
        event_mask = self.detect_events(
            threshold=threshold,
            method=method,
            filter_overlapping=filter_overlapping,
            lockout_window=lockout_window
        )

        events = fwd_df[event_mask].copy()
        events['event_index'] = events.index
        events['event_threshold'] = threshold
        events['is_filtered'] = filter_overlapping
        return events


if __name__ == "__main__":
    from data_loader import fetch_nifty_data
    df = fetch_nifty_data()
    engine = EventEngine(df)

    # Test raw vs filtered
    raw_events = engine.extract_event_dataset(threshold=-0.015, filter_overlapping=False)
    filtered_events = engine.extract_event_dataset(threshold=-0.015, filter_overlapping=True, lockout_window=3)

    print(f"Raw events (<= -1.5%): {len(raw_events)}")
    print(f"Independent events (lockout=3d): {len(filtered_events)}")
    print("Sample event row:")
    print(raw_events[['date', 'close', 'daily_return', 'fwd_ret_close_3d', 'fwd_ret_open_3d']].head())
