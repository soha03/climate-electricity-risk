import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
from src.analyze_prices import calculate_daily_metrics
from src.data.ingest_prices import validate_prices


class PriceAnalysisTests(unittest.TestCase):
    def test_price_validation(self):
        df = pd.DataFrame({
            "timestamp_utc": [
                "2026-05-01T00:00:00Z",
                "2026-05-01T01:00:00Z",
            ],
            "country_code": ["DE", "DE"],
            "price_eur_mwh": [50.0, 60.0],
        })
        result = validate_prices(df)
        self.assertEqual(len(result), 2)
        self.assertEqual(result["price_eur_mwh"].tolist(), [50.0, 60.0])

    def test_daily_metrics(self):
        timestamps = pd.date_range(
            "2026-05-01", periods=24, freq="h", tz="UTC"
        )
        df = pd.DataFrame({
            "timestamp_utc": timestamps,
            "country_code": ["DE"] * 24,
            "price_eur_mwh": [10.0] * 24,
        })
        metrics = calculate_daily_metrics(df)
        self.assertEqual(len(metrics), 1)
        self.assertEqual(metrics.loc[0, "observed_hours"], 24)
        self.assertEqual(metrics.loc[0, "mean_price_eur_mwh"], 10.0)
        self.assertEqual(metrics.loc[0, "negative_price_hours"], 0)
        self.assertEqual(metrics.loc[0, "evening_minus_midday_eur_mwh"], 0.0)

    def test_negative_prices(self):
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
        self.assertEqual(metrics.loc[0, "negative_price_hours"], 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
