"""Simple stochastic models for electricity-price dynamics.

The project is built to work without a live API. These components are meant for
offline testing, demonstration, and research design rather than for forecasting
actual market prices.
"""

from __future__ import annotations

import numpy as np


def historical_benchmark(series):
    """Return the most recent observed value as a naive benchmark."""
    values = np.asarray(series, dtype=float)
    if values.size == 0:
        raise ValueError("A non-empty series is required for the historical benchmark.")
    return float(values[-1])


def simulate_price_changes(steps: int, drift: float = 0.0, volatility: float = 5.0, seed: int | None = None):
    """Generate Gaussian price changes with a fixed random seed when provided."""
    if steps <= 0:
        raise ValueError("steps must be positive.")
    rng = np.random.default_rng(seed)
    return rng.normal(loc=drift, scale=volatility, size=steps)


def simulate_price_path(
    initial_price: float = 50.0,
    drift: float = 0.0,
    volatility: float = 5.0,
    steps: int = 24,
    seed: int | None = None,
):
    """Simulate a simple price path in EUR/MWh using additive Gaussian changes.

    The model is intentionally simple and designed for software testing and
    illustrative scenarios only; it is not a live market forecast.
    """
    if steps <= 0:
        raise ValueError("steps must be positive.")
    rng = np.random.default_rng(seed)
    path = np.empty(steps, dtype=float)
    path[0] = float(initial_price)
    for idx in range(1, steps):
        path[idx] = path[idx - 1] + rng.normal(loc=drift, scale=volatility)
    return path
