"""Offline tests for the electricity-market risk analysis project."""

import unittest

import pandas as pd

from src.analyze_prices import (
    calculate_daily_metrics,
    compute_country_summary,
    detect_missing_timestamps,
    load_prices,
)
from src.data.ingest_prices import validate_prices
from src.models.stochastic import simulate_price_path
from src.risk.metrics import expected_shortfall, historical_var


class ElectricityMarketAnalysisTests(unittest.TestCase):
    def test_price_validation(self):
        df = pd.DataFrame(
            {
                "timestamp_utc": [
                    "2026-05-01T00:00:00Z",
                    "2026-05-01T01:00:00Z",
                ],
                "country_code": ["DE", "DE"],
                "price_eur_mwh": [50.0, 60.0],
            }
        )

        result = validate_prices(df)
        self.assertEqual(len(result), 2)
        self.assertEqual(result["country_code"].tolist(), ["DE", "DE"])
        self.assertEqual(result["price_eur_mwh"].tolist(), [50.0, 60.0])

    def test_missing_timestamps_and_duplicates(self):
        timestamps = pd.to_datetime(
            [
                "2026-05-01T00:00:00Z",
                "2026-05-01T01:00:00Z",
                "2026-05-01T01:00:00Z",
                "2026-05-01T03:00:00Z",
            ],
            utc=True,
        )
        df = pd.DataFrame(
            {
                "timestamp_utc": timestamps,
                "country_code": ["DE", "DE", "DE", "DE"],
                "price_eur_mwh": [10.0, 12.0, 12.0, 14.0],
            }
        )

        with self.assertRaises(ValueError):
            validate_prices(df)

    def test_daily_metrics(self):
        timestamps = pd.date_range("2026-05-01", periods=24, freq="h", tz="UTC")
        df = pd.DataFrame(
            {
                "timestamp_utc": timestamps,
                "country_code": ["DE"] * 24,
                "price_eur_mwh": [10.0] * 24,
            }
        )

        metrics = calculate_daily_metrics(df)
        self.assertEqual(len(metrics), 1)
        self.assertEqual(metrics.loc[0, "observed_hours"], 24)
        self.assertEqual(metrics.loc[0, "mean_price_eur_mwh"], 10.0)
        self.assertEqual(metrics.loc[0, "negative_price_hours"], 0)
        self.assertEqual(metrics.loc[0, "evening_minus_midday_eur_mwh"], 0.0)

    def test_negative_prices(self):
        timestamps = pd.date_range("2026-05-01", periods=24, freq="h", tz="UTC")
        prices = [20.0] * 24
        prices[12] = -5.0
        prices[13] = -2.0
        df = pd.DataFrame(
            {
                "timestamp_utc": timestamps,
                "country_code": ["DE"] * 24,
                "price_eur_mwh": prices,
            }
        )

        metrics = calculate_daily_metrics(df)
        self.assertEqual(metrics.loc[0, "negative_price_hours"], 2)

    def test_summary_statistics_and_missing_timestamps(self):
        timestamps = pd.date_range("2026-05-01", periods=6, freq="h", tz="UTC")
        timestamps = timestamps.delete(2)
        df = pd.DataFrame(
            {
                "timestamp_utc": timestamps,
                "country_code": ["DE"] * 5,
                "price_eur_mwh": [10.0, 20.0, 30.0, 40.0, 50.0],
            }
        )
        summary = compute_country_summary(df)
        missing = detect_missing_timestamps(df, "DE")

        self.assertEqual(summary.loc[0, "observation_count"], 5)
        self.assertEqual(summary.loc[0, "mean_price_eur_mwh"], 30.0)
        self.assertEqual(len(missing), 1)

    def test_var_and_es_known_example(self):
        losses = [10.0, 20.0, 30.0, 40.0, 50.0]
        self.assertAlmostEqual(historical_var(losses, 0.8), 42.0)
        self.assertAlmostEqual(expected_shortfall(losses, 0.8), 50.0)

    def test_simulation_reproducibility(self):
        path_1 = simulate_price_path(initial_price=50.0, drift=0.2, volatility=3.0, steps=12, seed=7)
        path_2 = simulate_price_path(initial_price=50.0, drift=0.2, volatility=3.0, steps=12, seed=7)
        self.assertTrue((path_1 == path_2).all())
        self.assertEqual(len(path_1), 12)

    def test_load_prices_missing_data_raises(self):
        with self.assertRaises(FileNotFoundError):
            load_prices(path="nonexistent.csv")

    def test_empty_dataset_rejected(self):
        with self.assertRaises(ValueError):
            validate_prices(pd.DataFrame(columns=["timestamp_utc", "country_code", "price_eur_mwh"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
