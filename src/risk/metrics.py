"""Historical VaR and Expected Shortfall for price-risk measures."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _finite_values(values, metric_name: str) -> np.ndarray:
    arr = np.asarray(values, dtype=float).reshape(-1)
    if arr.size == 0:
        raise ValueError(f"At least one value is required to compute {metric_name}.")
    if not np.isfinite(arr).all():
        raise ValueError(f"{metric_name} values must be finite.")
    return arr


def historical_var(values, confidence: float = 0.95):
    """Return the historical VaR of a loss series at the requested confidence level.

    The random variable is defined explicitly as the loss variable, so callers must
    pass losses (for example, -price_change values or downside price shocks) rather
    than raw prices.
    """
    if confidence <= 0.0 or confidence >= 1.0:
        raise ValueError("confidence must lie between 0 and 1.")
    arr = _finite_values(values, "VaR")
    return float(np.quantile(arr, confidence))


def expected_shortfall(values, confidence: float = 0.95):
    """Return the tail-average beyond the VaR threshold.

    This is a loss-based measure: values are treated as a loss distribution.
    """
    if confidence <= 0.0 or confidence >= 1.0:
        raise ValueError("confidence must lie between 0 and 1.")
    arr = _finite_values(values, "Expected Shortfall")
    if confidence <= 0.0 or confidence >= 1.0:
        raise ValueError("confidence must lie between 0 and 1.")
    tail_count = max(1, int(np.ceil((1.0 - confidence) * arr.size)))
    tail = np.partition(arr, arr.size - tail_count)[-tail_count:]
    return float(tail.mean())


def stress_scenario(values, shock: float = 0.0):
    """Apply a deterministic scenario shock to a loss or price-change series."""
    arr = _finite_values(values, "stress scenario")
    return arr + float(shock)


def price_change_losses(
    observations: pd.DataFrame,
    interval_minutes: int = 15,
    position_mwh: float = 1.0,
) -> pd.DataFrame:
    """Build mark-to-market losses from consecutive prices for a signed position.

    ``position_mwh > 0`` is long price exposure. Loss is defined as
    ``-position_mwh * (P[t] - P[t-1])`` in EUR; a price decrease is a positive
    loss for a long position. Pairs spanning missing intervals are excluded.
    """
    if interval_minutes <= 0:
        raise ValueError("interval_minutes must be positive.")
    if not np.isfinite(position_mwh):
        raise ValueError("position_mwh must be finite.")
    required = {"timestamp_utc", "price_eur_mwh"}
    if not required.issubset(observations.columns):
        raise ValueError(f"observations must contain {sorted(required)}.")
    data = observations[["timestamp_utc", "price_eur_mwh"]].copy()
    data["timestamp_utc"] = pd.to_datetime(data["timestamp_utc"], utc=True, errors="raise")
    data["price_eur_mwh"] = pd.to_numeric(data["price_eur_mwh"], errors="raise")
    data = data.sort_values("timestamp_utc").reset_index(drop=True)
    if data.empty or data["price_eur_mwh"].isna().any() or not np.isfinite(data["price_eur_mwh"]).all():
        raise ValueError("observations must contain finite prices.")
    if data["timestamp_utc"].duplicated().any():
        raise ValueError("observations contain duplicate timestamps.")
    timestamps = pd.DatetimeIndex(data["timestamp_utc"])
    changes = data["price_eur_mwh"].diff().to_numpy(dtype=float)[1:]
    consecutive = (timestamps[1:] - timestamps[:-1]) == pd.Timedelta(minutes=interval_minutes)
    current_prices = data["price_eur_mwh"].to_numpy(dtype=float)[1:]
    return pd.DataFrame(
        {
            "timestamp_utc": timestamps[1:][consecutive],
            "price_change_eur_mwh": changes[consecutive],
            "loss_eur_per_position": -float(position_mwh) * changes[consecutive],
            "position_mwh": float(position_mwh),
            "current_price_eur_mwh": current_prices[consecutive],
        }
    ).reset_index(drop=True)


def price_shock_loss(price_change_eur_mwh: float, position_mwh: float = 1.0) -> float:
    """Return the signed loss for a price shock and signed MWh position."""
    if not np.isfinite(price_change_eur_mwh) or not np.isfinite(position_mwh):
        raise ValueError("price change and position must be finite.")
    return float(-position_mwh * price_change_eur_mwh)
