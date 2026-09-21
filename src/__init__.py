"""
NIFTY Quantitative Research Package
"""

from .data_loader import fetch_nifty_data, validate_and_clean_data
from .event_engine import EventEngine
from .statistical_tests import (
    analyze_horizons,
    compute_summary_statistics,
    bootstrap_confidence_interval,
    run_comparative_hypothesis_tests
)
from .backtester import EventBacktester
from .visualizer import (
    plot_return_distribution,
    plot_forward_returns_comparison,
    plot_sensitivity_heatmap,
    plot_equity_and_drawdowns,
    plot_regime_comparison
)

__all__ = [
    'fetch_nifty_data',
    'validate_and_clean_data',
    'EventEngine',
    'analyze_horizons',
    'compute_summary_statistics',
    'bootstrap_confidence_interval',
    'run_comparative_hypothesis_tests',
    'EventBacktester',
    'plot_return_distribution',
    'plot_forward_returns_comparison',
    'plot_sensitivity_heatmap',
    'plot_equity_and_drawdowns',
    'plot_regime_comparison'
]
