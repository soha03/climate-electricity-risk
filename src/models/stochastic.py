"""Simple stochastic models for electricity-price dynamics.

The project is built to work without a live API. These components are meant for
offline testing, demonstration, and research design rather than for forecasting
actual market prices.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


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


@dataclass
class AdditiveSeasonalAR1Fit:
    """Fitted additive AR(1) around an intraday seasonal price profile."""

    interval_minutes: int
    seasonal_means: np.ndarray
    intercept: float
    autoregression: float
    innovations: np.ndarray
    cutoff: pd.Timestamp
    training_observations: int
    training_transitions: int
    holdout_predictions: pd.DataFrame


def fit_additive_seasonal_ar1(
    observations: pd.DataFrame,
    interval_minutes: int = 15,
    train_fraction: float = 0.8,
) -> AdditiveSeasonalAR1Fit:
    """Fit a seasonal additive AR(1), using only consecutive intervals.

    The model is ``p[t] - m[slot[t]] = a + phi * (p[t-1] -
    m[slot[t-1]]) + epsilon[t]``. Seasonal means and coefficients are fitted
    on the chronological training segment. Missing intervals are never filled;
    transitions spanning a gap are excluded from fitting and holdout scoring.
    """
    if interval_minutes <= 0 or 60 % interval_minutes != 0:
        raise ValueError("interval_minutes must be a positive divisor of 60.")
    if not 0.5 <= train_fraction < 1.0:
        raise ValueError("train_fraction must be at least 0.5 and less than 1.0.")
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
    prices = data["price_eur_mwh"].to_numpy(dtype=float)
    minute_of_day = timestamps.hour * 60 + timestamps.minute
    if (timestamps.second != 0).any() or (minute_of_day % interval_minutes != 0).any():
        raise ValueError("timestamps do not align with interval_minutes.")

    train_count = int(len(data) * train_fraction)
    if train_count < 4 or train_count >= len(data):
        raise ValueError("insufficient observations for chronological training and holdout.")
    cutoff = timestamps[train_count]
    slots_per_day = 1440 // interval_minutes
    slots = (minute_of_day // interval_minutes).to_numpy(dtype=int)
    training_mask = timestamps < cutoff
    global_mean = float(prices[training_mask].mean())
    seasonal_means = np.full(slots_per_day, global_mean, dtype=float)
    for slot, value in data.loc[training_mask].assign(slot=slots[training_mask]).groupby("slot")["price_eur_mwh"].mean().items():
        seasonal_means[int(slot)] = float(value)

    centered = prices - seasonal_means[slots]
    consecutive = (timestamps[1:] - timestamps[:-1]) == pd.Timedelta(minutes=interval_minutes)
    previous_centered = centered[:-1]
    current_centered = centered[1:]
    train_pairs = consecutive & (timestamps[1:] < cutoff)
    holdout_pairs = consecutive & (timestamps[1:] >= cutoff)
    if int(train_pairs.sum()) < 3:
        raise ValueError("insufficient consecutive training transitions for AR(1) fit.")

    design = np.column_stack((np.ones(int(train_pairs.sum())), previous_centered[train_pairs]))
    intercept, autoregression = np.linalg.lstsq(design, current_centered[train_pairs], rcond=None)[0]
    innovations = current_centered[train_pairs] - (intercept + autoregression * previous_centered[train_pairs])
    if not np.isfinite(innovations).all():
        raise ValueError("model fit produced non-finite innovations.")

    holdout_indices = np.flatnonzero(holdout_pairs) + 1
    holdout = pd.DataFrame(
        {
            "timestamp_utc": timestamps[holdout_indices],
            "actual_price_eur_mwh": prices[holdout_indices],
            "prediction_eur_mwh": seasonal_means[slots[holdout_indices]]
            + intercept
            + autoregression * centered[holdout_indices - 1],
            "seasonal_baseline_eur_mwh": seasonal_means[slots[holdout_indices]],
            "persistence_baseline_eur_mwh": prices[holdout_indices - 1],
        }
    )
    holdout["residual_eur_mwh"] = holdout["actual_price_eur_mwh"] - holdout["prediction_eur_mwh"]

    return AdditiveSeasonalAR1Fit(
        interval_minutes=interval_minutes,
        seasonal_means=seasonal_means,
        intercept=float(intercept),
        autoregression=float(autoregression),
        innovations=np.asarray(innovations, dtype=float),
        cutoff=cutoff,
        training_observations=train_count,
        training_transitions=int(train_pairs.sum()),
        holdout_predictions=holdout,
    )


def simulate_additive_seasonal_ar1(
    model: AdditiveSeasonalAR1Fit,
    initial_price: float,
    initial_timestamp,
    steps: int,
    paths: int = 1,
    seed: int | None = None,
) -> pd.DataFrame:
    """Bootstrap fitted innovations to produce explicitly simulated price paths."""
    if steps <= 0 or paths <= 0:
        raise ValueError("steps and paths must be positive.")
    if model.innovations.size == 0:
        raise ValueError("the fitted model has no innovations to resample.")
    timestamp = pd.Timestamp(initial_timestamp)
    timestamp = timestamp.tz_localize("UTC") if timestamp.tzinfo is None else timestamp.tz_convert("UTC")
    rng = np.random.default_rng(seed)
    centered_innovations = model.innovations - model.innovations.mean()
    interval = pd.Timedelta(minutes=model.interval_minutes)
    output = []
    for path_id in range(paths):
        previous_price = float(initial_price)
        previous_timestamp = timestamp
        for step in range(1, steps + 1):
            current_timestamp = timestamp + step * interval
            previous_slot = (previous_timestamp.hour * 60 + previous_timestamp.minute) // model.interval_minutes
            current_slot = (current_timestamp.hour * 60 + current_timestamp.minute) // model.interval_minutes
            previous_deviation = previous_price - model.seasonal_means[previous_slot]
            innovation = float(rng.choice(centered_innovations))
            current_price = (
                model.seasonal_means[current_slot]
                + model.intercept
                + model.autoregression * previous_deviation
                + innovation
            )
            output.append(
                {
                    "path_id": path_id,
                    "timestamp_utc": current_timestamp,
                    "price_eur_mwh": current_price,
                    "series_type": "simulated",
                }
            )
            previous_price = current_price
            previous_timestamp = current_timestamp
    return pd.DataFrame(output)
