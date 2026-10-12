"""Offline tests for the electricity-market risk analysis project."""

import unittest

import numpy as np
import pandas as pd

from src.analyze_prices import (
    calculate_daily_metrics,
    compute_country_summary,
    detect_missing_timestamps,
    detect_irregular_intervals,
    load_prices,
)
from src.data.ingest_prices import validate_market_mapping, validate_prices
from src.models.stochastic import (
    fit_additive_seasonal_ar1,
    simulate_additive_seasonal_ar1,
    simulate_price_path,
)
from src.risk.metrics import (
    expected_shortfall,
    historical_var,
    price_change_losses,
    price_shock_loss,
)


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

    def test_verified_source_zones_pass_market_mapping(self):
        frame = pd.DataFrame(
            {
                "timestamp_utc": ["2026-05-01T00:00:00Z", "2026-05-01T00:00:00Z"],
                "country_code": ["DE", "IT"],
                "bidding_zone": ["DE-LU", "IT-North"],
                "price_eur_mwh": [50.0, 60.0],
            }
        )
        validated = validate_market_mapping(frame)
        self.assertEqual(validated["bidding_zone"].tolist(), ["DE-LU", "IT-NORTH"])

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
        self.assertEqual(metrics.loc[0, "observed_intervals"], 24)
        self.assertEqual(metrics.loc[0, "mean_price_eur_mwh"], 10.0)
        self.assertEqual(metrics.loc[0, "negative_price_intervals"], 0)
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
        self.assertEqual(metrics.loc[0, "negative_price_intervals"], 2)

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

    def test_quarter_hour_gap_detection_uses_market_cadence(self):
        df = pd.DataFrame(
            {
                "timestamp_utc": pd.to_datetime(
                    [
                        "2026-05-01T00:00:00Z",
                        "2026-05-01T00:15:00Z",
                        "2026-05-01T00:45:00Z",
                        "2026-05-01T01:00:00Z",
                    ],
                    utc=True,
                ),
                "country_code": ["DE"] * 4,
                "price_eur_mwh": [10.0, 11.0, 13.0, 14.0],
            }
        )

        missing = detect_missing_timestamps(df, "DE")
        irregular = detect_irregular_intervals(df)
        self.assertEqual(missing["timestamp_utc"].tolist(), [pd.Timestamp("2026-05-01T00:30:00Z")])
        self.assertEqual(irregular["diff_minutes"].tolist(), [30.0])
        self.assertEqual(irregular["expected_interval_minutes"].tolist(), [15.0])

    def test_var_and_es_known_example(self):
        losses = [10.0, 20.0, 30.0, 40.0, 50.0]
        self.assertAlmostEqual(historical_var(losses, 0.8), 42.0)
        self.assertAlmostEqual(expected_shortfall(losses, 0.8), 50.0)

    def test_simulation_reproducibility(self):
        path_1 = simulate_price_path(initial_price=50.0, drift=0.2, volatility=3.0, steps=12, seed=7)
        path_2 = simulate_price_path(initial_price=50.0, drift=0.2, volatility=3.0, steps=12, seed=7)
        self.assertTrue((path_1 == path_2).all())
        self.assertEqual(len(path_1), 12)

    def test_additive_seasonal_model_preserves_negative_prices_and_skips_gaps(self):
        timestamps = pd.date_range("2026-05-01", periods=12 * 96, freq="15min", tz="UTC")
        prices = -80.0 + 12.0 * np.sin(np.arange(len(timestamps)) % 96 * 2 * np.pi / 96)
        frame = pd.DataFrame({"timestamp_utc": timestamps, "price_eur_mwh": prices})
        frame = frame.drop(index=[720, 721]).reset_index(drop=True)

        fit = fit_additive_seasonal_ar1(frame, interval_minutes=15, train_fraction=0.8)
        expected_training_pairs = int(
            ((frame.loc[:fit.training_observations - 1, "timestamp_utc"].diff()) == pd.Timedelta(minutes=15)).sum()
        )
        self.assertEqual(fit.training_transitions, expected_training_pairs)
        self.assertGreater(len(fit.holdout_predictions), 0)
        self.assertTrue((fit.holdout_predictions["actual_price_eur_mwh"] < 0).all())

        origin = frame.loc[fit.training_observations - 1]
        first = simulate_additive_seasonal_ar1(fit, origin.price_eur_mwh, origin.timestamp_utc, 96, 3, seed=42)
        second = simulate_additive_seasonal_ar1(fit, origin.price_eur_mwh, origin.timestamp_utc, 96, 3, seed=42)
        pd.testing.assert_frame_equal(first, second)
        self.assertEqual(set(first["series_type"]), {"simulated"})
        self.assertTrue((first["price_eur_mwh"] < 0).all())

    def test_price_change_losses_skip_gaps_and_follow_position_sign(self):
        prices = pd.DataFrame(
            {
                "timestamp_utc": pd.to_datetime(
                    [
                        "2026-05-01T00:00:00Z",
                        "2026-05-01T00:15:00Z",
                        "2026-05-01T00:45:00Z",
                        "2026-05-01T01:00:00Z",
                    ],
                    utc=True,
                ),
                "price_eur_mwh": [100.0, 90.0, 95.0, 80.0],
            }
        )

        long_losses = price_change_losses(prices, position_mwh=1.0)
        short_losses = price_change_losses(prices, position_mwh=-1.0)
        self.assertEqual(long_losses["loss_eur_per_position"].tolist(), [10.0, 15.0])
        self.assertEqual(short_losses["loss_eur_per_position"].tolist(), [-10.0, -15.0])
        self.assertEqual(price_shock_loss(-100.0, position_mwh=1.0), 100.0)
        self.assertEqual(price_shock_loss(-100.0, position_mwh=-1.0), -100.0)

    def test_expected_shortfall_is_worst_discrete_tail_mean(self):
        losses = [1.0, 2.0, 3.0, 4.0, 20.0]
        self.assertAlmostEqual(historical_var(losses, confidence=0.8), 7.2)
        self.assertEqual(expected_shortfall(losses, confidence=0.8), 20.0)

    def test_load_prices_missing_data_raises(self):
        with self.assertRaises(FileNotFoundError):
            load_prices(path="nonexistent.csv")

    def test_empty_dataset_rejected(self):
        with self.assertRaises(ValueError):
            validate_prices(pd.DataFrame(columns=["timestamp_utc", "country_code", "price_eur_mwh"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
