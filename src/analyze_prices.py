"""Exploratory statistics and descriptive analysis for electricity-price data."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.config import COUNTRIES, FIGURES_DIR, PROCESSED_DATA_DIR, PROJECT_ROOT
from src.data.ingest_prices import load_real_prices, validate_prices
from src.visualization.plots import plot_price_series, plot_rolling_volatility

DEFAULT_PRICE_FILE = PROCESSED_DATA_DIR / "day_ahead_prices.csv"


def load_prices(path: str | Path = DEFAULT_PRICE_FILE) -> pd.DataFrame:
    """Load the empirical price dataset if it exists; otherwise fail with context."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(
            f"No real price dataset is available at {file_path}. "
            "The analysis pipeline is documented and ready, but empirical data has not been downloaded yet."
        )
    df = pd.read_csv(file_path)
    return validate_prices(df)


def compute_country_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Compute descriptive statistics at the country level."""
    data = validate_prices(df)
    summary = data.groupby(["country_code", "bidding_zone"], as_index=False).agg(
        observation_count=("price_eur_mwh", "size"),
        mean_price_eur_mwh=("price_eur_mwh", "mean"),
        median_price_eur_mwh=("price_eur_mwh", "median"),
        std_price_eur_mwh=("price_eur_mwh", "std"),
        min_price_eur_mwh=("price_eur_mwh", "min"),
        max_price_eur_mwh=("price_eur_mwh", "max"),
        negative_price_intervals=("price_eur_mwh", lambda x: int((x < 0).sum())),
    )
    return summary.sort_values(["country_code", "bidding_zone"]).reset_index(drop=True)


def detect_missing_timestamps(
    df: pd.DataFrame,
    country: str | None = None,
    interval_minutes: int | None = None,
) -> pd.DataFrame:
    """Return missing timestamps at the explicit or inferred market cadence."""
    data = validate_prices(df)
    if country is not None:
        data = data[data["country_code"] == country.upper()]
    if data.empty:
        return pd.DataFrame(columns=[
            "country_code", "bidding_zone", "timestamp_utc", "expected_timestamp_utc"
        ])
    if interval_minutes is not None and interval_minutes <= 0:
        raise ValueError("interval_minutes must be positive.")

    missing_rows = []
    for (country_code, bidding_zone), market in data.groupby(["country_code", "bidding_zone"]):
        observed = pd.DatetimeIndex(market["timestamp_utc"].sort_values().unique())
        if interval_minutes is None:
            differences = observed[1:] - observed[:-1]
            cadence = int(differences.min().total_seconds() // 60) if len(differences) else 60
        else:
            cadence = interval_minutes
        full_index = pd.date_range(start=observed.min(), end=observed.max(), freq=f"{cadence}min")
        missing = full_index.difference(observed)
        missing_rows.extend(
            {
                "country_code": country_code,
                "bidding_zone": bidding_zone,
                "timestamp_utc": timestamp,
                "expected_timestamp_utc": timestamp,
            }
            for timestamp in missing
        )
    return pd.DataFrame(
        missing_rows,
        columns=["country_code", "bidding_zone", "timestamp_utc", "expected_timestamp_utc"],
    )


def calculate_daily_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute daily summary statistics over observed UTC price intervals."""
    data = validate_prices(df)
    data = data.copy()
    data["date_utc"] = data["timestamp_utc"].dt.floor("D")
    data["hour_utc"] = data["timestamp_utc"].dt.hour

    rows = []
    for (country, zone, date), group in data.groupby(["country_code", "bidding_zone", "date_utc"]):
        midday = group.loc[group["hour_utc"].between(10, 15), "price_eur_mwh"]
        evening = group.loc[group["hour_utc"].between(18, 21), "price_eur_mwh"]
        rows.append(
            {
                "country_code": country,
                "bidding_zone": zone,
                "date_utc": date,
                "observed_intervals": int(len(group)),
                "mean_price_eur_mwh": float(group["price_eur_mwh"].mean()),
                "price_volatility_std": float(group["price_eur_mwh"].std(ddof=1)) if len(group) > 1 else 0.0,
                "negative_price_intervals": int((group["price_eur_mwh"] < 0).sum()),
                "midday_mean_eur_mwh": float(midday.mean()) if not midday.empty else np.nan,
                "evening_mean_eur_mwh": float(evening.mean()) if not evening.empty else np.nan,
                "evening_minus_midday_eur_mwh": (
                    float(evening.mean() - midday.mean()) if not midday.empty and not evening.empty else np.nan
                ),
            }
        )
    if not rows:
        return pd.DataFrame(columns=[
            "country_code",
            "bidding_zone",
            "date_utc",
            "observed_intervals",
            "mean_price_eur_mwh",
            "price_volatility_std",
            "negative_price_intervals",
            "midday_mean_eur_mwh",
            "evening_mean_eur_mwh",
            "evening_minus_midday_eur_mwh",
        ])
    return pd.DataFrame(rows).sort_values(["country_code", "date_utc"]).reset_index(drop=True)


def calculate_rolling_volatility(series: pd.Series, window: int = 24) -> pd.Series:
    """Compute rolling standard deviation over a count of observed intervals."""
    if window <= 1:
        raise ValueError("window must be at least 2.")
    return series.rolling(window=window, min_periods=window).std()


def detect_irregular_intervals(df: pd.DataFrame, interval_minutes: int | None = None) -> pd.DataFrame:
    """Return intervals that differ from an explicit or inferred market cadence."""
    data = validate_prices(df)
    if data.empty:
        return pd.DataFrame(columns=["country_code", "bidding_zone", "timestamp_utc", "diff_minutes"])
    if interval_minutes is not None and interval_minutes <= 0:
        raise ValueError("interval_minutes must be positive.")
    data = data.sort_values(["country_code", "bidding_zone", "timestamp_utc"]).copy()
    data["previous_timestamp_utc"] = data.groupby(["country_code", "bidding_zone"])["timestamp_utc"].shift(1)
    data["diff_minutes"] = (
        data["timestamp_utc"] - data["previous_timestamp_utc"]
    ).dt.total_seconds() / 60.0
    expected_by_market = {}
    for key, market in data.groupby(["country_code", "bidding_zone"]):
        differences = market["diff_minutes"].dropna()
        expected_by_market[key] = (
            interval_minutes
            if interval_minutes is not None
            else (float(differences.min()) if not differences.empty else 60.0)
        )
    data["expected_interval_minutes"] = [
        expected_by_market[(country, zone)]
        for country, zone in zip(data["country_code"], data["bidding_zone"])
    ]
    irregular = data[
        data["previous_timestamp_utc"].notna()
        & data["diff_minutes"].ne(data["expected_interval_minutes"])
    ]
    return irregular[[
        "country_code", "bidding_zone", "timestamp_utc", "diff_minutes", "expected_interval_minutes"
    ]].reset_index(drop=True)


def main() -> None:
    """Gracefully report that real market data is required for empirical analysis."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    try:
        df = load_real_prices()
    except FileNotFoundError as exc:
        print(str(exc))
        print("\nThis repository is ready for empirical analysis, but no real market observations have been downloaded yet.")
        print("Add data/processed/day_ahead_prices.csv to enable the descriptive statistics and visualisation pipeline.")
        return

    summary = compute_country_summary(df)
    output = PROCESSED_DATA_DIR / "country_summary.csv"
    summary.to_csv(output, index=False)

    print(f"Loaded {len(df):,} observed price intervals at the verified 15-minute resolution.")
    print(f"Countries found: {', '.join(sorted(df['country_code'].unique()))}")
    print(f"Country summary saved to: {output}")
    price_chart = FIGURES_DIR / "cross_country_day_ahead_prices.png"
    volatility_chart = FIGURES_DIR / "cross_country_rolling_volatility.png"
    plot_price_series(df, price_chart, interval_minutes=15)
    plot_rolling_volatility(df, volatility_chart, interval_minutes=15, window_intervals=96)
    print(f"Price chart saved to: {price_chart}")
    print(f"Volatility chart saved to: {volatility_chart}")


if __name__ == "__main__":
    main()
