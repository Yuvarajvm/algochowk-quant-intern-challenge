"""
statistical_tests.py
====================
Statistical evaluation module for event study analysis:
- Descriptive statistics (mean, median, win rate, volatility, skewness, kurtosis)
- Parametric hypothesis tests (Two-sample Welch's t-test vs unconditional baseline)
- Non-parametric hypothesis tests (Mann-Whitney U test, Wilcoxon signed-rank test)
- Bootstrap resampling for empirical 95% confidence intervals
- Multi-horizon Bonferroni corrections
"""

import numpy as np
import pandas as pd
from scipy import stats


def compute_summary_statistics(returns_series):
    """
    Computes comprehensive descriptive statistics for a returns series.
    """
    clean_s = returns_series.dropna()
    n = len(clean_s)
    if n == 0:
        return {}

    mean_val = clean_s.mean()
    median_val = clean_s.median()
    std_val = clean_s.std()
    skew_val = clean_s.skew()
    kurt_val = clean_s.kurtosis()
    win_rate = (clean_s > 0).mean()
    min_val = clean_s.min()
    max_val = clean_s.max()

    # Semi-deviation (downside risk)
    negative_returns = clean_s[clean_s < 0]
    downside_dev = negative_returns.std() if len(negative_returns) > 1 else np.nan

    return {
        'count': n,
        'mean': mean_val,
        'median': median_val,
        'std': std_val,
        'skewness': skew_val,
        'kurtosis': kurt_val,
        'win_rate': win_rate,
        'min': min_val,
        'max': max_val,
        'downside_std': downside_dev
    }


def bootstrap_confidence_interval(series, n_bootstrap=5000, ci=0.95, random_state=42):
    """
    Computes empirical bootstrap confidence interval for the mean.
    Does not assume normality.
    """
    clean_s = series.dropna().values
    n = len(clean_s)
    if n < 2:
        return np.nan, np.nan

    rng = np.random.default_rng(random_state)
    boot_samples = rng.choice(clean_s, size=(n_bootstrap, n), replace=True)
    boot_means = boot_samples.mean(axis=1)

    alpha = (1.0 - ci) / 2.0
    lower_pct = alpha * 100
    upper_pct = (1.0 - alpha) * 100

    ci_lower = np.percentile(boot_means, lower_pct)
    ci_upper = np.percentile(boot_means, upper_pct)
    return ci_lower, ci_upper, boot_means


def run_comparative_hypothesis_tests(event_returns, baseline_returns):
    """
    Compares event forward returns against unconditional baseline forward returns
    using both parametric and non-parametric tests.

    Tests performed:
    1. Two-sample Welch's t-test (difference in means, unequal variances)
    2. Mann-Whitney U test (difference in rank/median distributions)
    3. One-sample t-test of event returns vs 0
    4. One-sample Wilcoxon signed-rank test of event returns vs 0
    """
    e_clean = event_returns.dropna()
    b_clean = baseline_returns.dropna()

    if len(e_clean) < 2 or len(b_clean) < 2:
        return {}

    # 1. Welch's t-test vs baseline
    t_stat_welch, p_val_welch = stats.ttest_ind(e_clean, b_clean, equal_var=False)

    # 2. Mann-Whitney U test vs baseline
    mw_stat, p_val_mw = stats.mannwhitneyu(e_clean, b_clean, alternative='two-sided')

    # 3. One-sample t-test vs 0
    t_stat_zero, p_val_zero = stats.ttest_1samp(e_clean, 0.0)

    # 4. Wilcoxon signed rank test vs 0
    try:
        wilc_stat, p_val_wilc = stats.wilcoxon(e_clean, alternative='two-sided')
    except Exception:
        wilc_stat, p_val_wilc = np.nan, np.nan

    # Effect size: Cohen's d
    pooled_std = np.sqrt(((len(e_clean) - 1) * e_clean.var() + (len(b_clean) - 1) * b_clean.var()) / (len(e_clean) + len(b_clean) - 2))
    cohens_d = (e_clean.mean() - b_clean.mean()) / pooled_std if pooled_std > 0 else np.nan

    return {
        'welch_t_stat': t_stat_welch,
        'welch_p_val': p_val_welch,
        'mann_whitney_u': mw_stat,
        'mann_whitney_p_val': p_val_mw,
        't_stat_vs_zero': t_stat_zero,
        'p_val_vs_zero': p_val_zero,
        'wilcoxon_stat': wilc_stat,
        'wilcoxon_p_val': p_val_wilc,
        'cohens_d': cohens_d,
        'diff_of_means': e_clean.mean() - b_clean.mean()
    }


def analyze_horizons(events_df, full_df, holding_periods=[1, 2, 3, 5, 10], entry_mode='open'):
    """
    Comprehensive horizon analysis comparing event forward returns to baseline.
    entry_mode: 'open' (realistic T+1 Open) or 'close' (theoretical T Close)
    """
    results = []

    prefix = 'fwd_ret_open_' if entry_mode == 'open' else 'fwd_ret_close_'

    for h in holding_periods:
        col = f'{prefix}{h}d'
        base_col = f'fwd_ret_close_{h}d'  # baseline is always market holding return

        ev_s = events_df[col].dropna()
        base_s = full_df[base_col].dropna()

        ev_stats = compute_summary_statistics(ev_s)
        base_stats = compute_summary_statistics(base_s)

        ci_low, ci_high, _ = bootstrap_confidence_interval(ev_s, n_bootstrap=5000)
        tests = run_comparative_hypothesis_tests(ev_s, base_s)

        row = {
            'holding_days': h,
            'entry_mode': entry_mode,
            'event_count': ev_stats.get('count', 0),
            'event_mean': ev_stats.get('mean', np.nan),
            'event_median': ev_stats.get('median', np.nan),
            'event_std': ev_stats.get('std', np.nan),
            'event_win_rate': ev_stats.get('win_rate', np.nan),
            'ci_95_lower': ci_low,
            'ci_95_upper': ci_high,
            'baseline_mean': base_stats.get('mean', np.nan),
            'baseline_median': base_stats.get('median', np.nan),
            'baseline_win_rate': base_stats.get('win_rate', np.nan),
            'diff_means': tests.get('diff_of_means', np.nan),
            'welch_t_stat': tests.get('welch_t_stat', np.nan),
            'welch_p_val': tests.get('welch_p_val', np.nan),
            'mann_whitney_p_val': tests.get('mann_whitney_p_val', np.nan),
            'p_val_vs_zero': tests.get('p_val_vs_zero', np.nan),
            'cohens_d': tests.get('cohens_d', np.nan)
        }
        results.append(row)

    res_df = pd.DataFrame(results)
    # Apply Bonferroni correction for multiple horizons
    res_df['bonferroni_p_val'] = np.minimum(res_df['welch_p_val'] * len(holding_periods), 1.0)
    return res_df


if __name__ == "__main__":
    from data_loader import fetch_nifty_data
    from event_engine import EventEngine

    df = fetch_nifty_data()
    engine = EventEngine(df)
    events = engine.extract_event_dataset(threshold=-0.015)
    full_fwd = engine.calculate_forward_returns()

    print("\n--- REALISTIC EXECUTION (Entry T+1 Open) ---")
    res_open = analyze_horizons(events, full_fwd, entry_mode='open')
    print(res_open[['holding_days', 'event_mean', 'baseline_mean', 'diff_means', 'event_win_rate', 'welch_t_stat', 'welch_p_val']])

    print("\n--- THEORETICAL EXECUTION (Entry T Close) ---")
    res_close = analyze_horizons(events, full_fwd, entry_mode='close')
    print(res_close[['holding_days', 'event_mean', 'baseline_mean', 'diff_means', 'event_win_rate', 'welch_t_stat', 'welch_p_val']])
