"""Historical VaR and Expected Shortfall for price-risk measures."""

from __future__ import annotations

import numpy as np


def historical_var(values, confidence: float = 0.95):
    """Return the historical VaR of a loss series at the requested confidence level.

    The random variable is defined explicitly as the loss variable, so callers must
    pass losses (for example, -price_change values or downside price shocks) rather
    than raw prices.
    """
    if confidence <= 0.0 or confidence >= 1.0:
        raise ValueError("confidence must lie between 0 and 1.")
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        raise ValueError("At least one value is required to compute VaR.")
    return float(np.quantile(arr, confidence))


def expected_shortfall(values, confidence: float = 0.95):
    """Return the tail-average beyond the VaR threshold.

    This is a loss-based measure: values are treated as a loss distribution.
    """
    if confidence <= 0.0 or confidence >= 1.0:
        raise ValueError("confidence must lie between 0 and 1.")
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        raise ValueError("At least one value is required to compute Expected Shortfall.")
    var_value = historical_var(arr, confidence)
    tail = arr[arr >= var_value]
    if tail.size == 0:
        return float(var_value)
    return float(tail.mean())


def stress_scenario(values, shock: float = 0.0):
    """Apply a deterministic scenario shock to a loss or price-change series."""
    arr = np.asarray(values, dtype=float)
    return arr + float(shock)
