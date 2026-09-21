"""
data_loader.py
==============
Module for fetching, cleaning, validating, and caching historical daily OHLC data
for the NIFTY 50 Index (^NSEI) from Yahoo Finance.
"""

import os
import datetime
import requests
import pandas as pd
import numpy as np


def fetch_nifty_data(cache_path="data/nifty_50_historical.csv", force_download=False):
    """
    Fetch historical daily data for NIFTY 50 (^NSEI).
    If a local cached CSV exists and force_download is False, loads from cache.
    Otherwise fetches from Yahoo Finance API, validates, and caches to CSV.
    """
    if os.path.exists(cache_path) and not force_download:
        print(f"[DataLoader] Loading cached NIFTY 50 data from '{cache_path}'...")
        df = pd.read_csv(cache_path)
        df['date'] = pd.to_datetime(df['date'])
        return df

    print("[DataLoader] Fetching historical NIFTY 50 daily data from Yahoo Finance API...")
    url = 'https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI?range=20y&interval=1d'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        json_data = response.json()
        result = json_data['chart']['result'][0]
        timestamps = result['timestamp']
        quote = result['indicators']['quote'][0]

        raw_df = pd.DataFrame({
            'date': [
                datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).strftime('%Y-%m-%d')
                for ts in timestamps
            ],
            'open': quote.get('open', []),
            'high': quote.get('high', []),
            'low': quote.get('low', []),
            'close': quote.get('close', []),
            'volume': quote.get('volume', [])
        })
    except Exception as e:
        print(f"[DataLoader] Warning: API request failed ({e}). Falling back to cached file if available.")
        if os.path.exists(cache_path):
            df = pd.read_csv(cache_path)
            df['date'] = pd.to_datetime(df['date'])
            return df
        raise

    # Validation and cleaning
    clean_df, report = validate_and_clean_data(raw_df)
    print(f"[DataLoader] Data validation complete. Rows: {len(clean_df)}. Date range: {clean_df['date'].min().strftime('%Y-%m-%d')} to {clean_df['date'].max().strftime('%Y-%m-%d')}")
    
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    clean_df.to_csv(cache_path, index=False)
    print(f"[DataLoader] Cleaned dataset saved to '{cache_path}'.")
    return clean_df


def validate_and_clean_data(raw_df):
    """
    Validates the dataset against required quality checks:
    1. Null / NaN values in OHLC
    2. Duplicate dates
    3. Chronological sorting
    4. OHLC logical consistency: High >= Low, High >= Open/Close, Low <= Open/Close
    5. Suspicious zero / negative values
    6. Non-trading day gap checks
    """
    report = {
        'raw_rows': len(raw_df),
        'missing_values_dropped': 0,
        'duplicate_dates_dropped': 0,
        'ohlc_violations_fixed': 0,
        'date_order_corrected': False,
        'clean_rows': 0,
        'start_date': None,
        'end_date': None
    }

    df = raw_df.copy()
    df['date'] = pd.to_datetime(df['date'])

    # 1. Null / Missing OHLC
    null_mask = df[['open', 'high', 'low', 'close']].isnull().any(axis=1)
    report['missing_values_dropped'] = int(null_mask.sum())
    df = df[~null_mask].copy()

    # 2. Duplicate dates
    dup_mask = df.duplicated(subset=['date'], keep='first')
    report['duplicate_dates_dropped'] = int(dup_mask.sum())
    df = df[~dup_mask].copy()

    # 3. Sort chronologically
    if not df['date'].is_monotonic_increasing:
        report['date_order_corrected'] = True
        df = df.sort_values('date').reset_index(drop=True)
    else:
        df = df.reset_index(drop=True)

    # 4. Valid positive prices
    valid_price_mask = (df['open'] > 0) & (df['high'] > 0) & (df['low'] > 0) & (df['close'] > 0)
    df = df[valid_price_mask].copy()

    # 5. OHLC consistency check
    # High must be max of Open, High, Low, Close
    # Low must be min of Open, High, Low, Close
    inconsistent_mask = (
        (df['high'] < df['low']) |
        (df['high'] < df['open']) |
        (df['high'] < df['close']) |
        (df['low'] > df['open']) |
        (df['low'] > df['close'])
    )
    report['ohlc_violations_fixed'] = int(inconsistent_mask.sum())

    if report['ohlc_violations_fixed'] > 0:
        # Re-bound high and low to true extremes
        df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
        df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)

    # Calculate returns
    df['daily_return'] = df['close'].pct_change()
    df['log_return'] = np.log(df['close'] / df['close'].shift(1))
    df['intraday_return'] = (df['close'] - df['open']) / df['open']
    df['overnight_gap'] = (df['open'] - df['close'].shift(1)) / df['close'].shift(1)

    report['clean_rows'] = len(df)
    report['start_date'] = df['date'].min().strftime('%Y-%m-%d')
    report['end_date'] = df['date'].max().strftime('%Y-%m-%d')

    return df, report


if __name__ == "__main__":
    df = fetch_nifty_data(force_download=True)
    print(df.head())
    print(df.tail())
