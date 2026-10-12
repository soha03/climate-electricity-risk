"""Tests for electricity-price analysis."""

import pandas as pd

from src.analyze_prices import calculate_daily_metrics
from src.data.ingest_prices import validate_prices


def test_price_validation():
    df = pd.DataFrame({
        "timestamp_utc": [
            "2026-05-01T00:00:00Z",
            "2026-05-01T01:00:00Z",
        ],
        "country_code": ["DE", "DE"],
        "price_eur_mwh": [50.0, 60.0],
    })

    result = validate_prices(df)

    assert len(result) == 2
    assert result["country_code"].tolist() == ["DE", "DE"]
    assert result["price_eur_mwh"].tolist() == [50.0, 60.0]


def test_daily_metrics():
    timestamps = pd.date_range(
        "2026-05-01", periods=24, freq="h", tz="UTC"
    )

    df = pd.DataFrame({
        "timestamp_utc": timestamps,
        "country_code": ["DE"] * 24,
        "price_eur_mwh": [10.0] * 24,
    })

    metrics = calculate_daily_metrics(df)

    assert len(metrics) == 1
    assert metrics.loc[0, "observed_hours"] == 24
    assert metrics.loc[0, "mean_price_eur_mwh"] == 10.0
    assert metrics.loc[0, "negative_price_hours"] == 0
    assert metrics.loc[0, "evening_minus_midday_eur_mwh"] == 0.0


def test_negative_prices():
    timestamps = pd.date_range(
        "2026-05-01", periods=24, freq="h", tz="UTC"
    )

    prices = [20.0] * 24
    prices[12] = -5.0
    prices[13] = -2.0

    df = pd.DataFrame({
        "timestamp_utc": timestamps,
        "country_code": ["DE"] * 24,
        "price_eur_mwh": prices,
    })

    metrics = calculate_daily_metrics(df)

    assert metrics.loc[0, "negative_price_hours"] == 2
