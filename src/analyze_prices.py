"""Exploratory statistics and descriptive analysis for electricity-price data."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.config import COUNTRIES, FIGURES_DIR, PROCESSED_DATA_DIR, PROJECT_ROOT
from src.data.ingest_prices import load_real_prices, validate_prices

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
    summary = data.groupby("country_code", as_index=False).agg(
        observation_count=("price_eur_mwh", "size"),
        mean_price_eur_mwh=("price_eur_mwh", "mean"),
        median_price_eur_mwh=("price_eur_mwh", "median"),
        std_price_eur_mwh=("price_eur_mwh", "std"),
        min_price_eur_mwh=("price_eur_mwh", "min"),
        max_price_eur_mwh=("price_eur_mwh", "max"),
        negative_price_hours=("price_eur_mwh", lambda x: int((x < 0).sum())),
    )
    return summary.sort_values("country_code").reset_index(drop=True)


def detect_missing_timestamps(df: pd.DataFrame, country: str | None = None) -> pd.DataFrame:
    """Return any missing hourly timestamps for the selected country or dataset."""
    data = validate_prices(df)
    if country is not None:
        data = data[data["country_code"] == country.upper()]
    if data.empty:
        return pd.DataFrame(columns=["country_code", "timestamp_utc", "expected_timestamp_utc"])

    min_ts = data["timestamp_utc"].min()
    max_ts = data["timestamp_utc"].max()
    full_index = pd.date_range(start=min_ts, end=max_ts, freq="h", tz="UTC")
    observed = pd.Index(data["timestamp_utc"].sort_values().unique())
    missing = full_index.difference(observed)
    result = pd.DataFrame({
        "country_code": country.upper() if country else data["country_code"].iloc[0],
        "timestamp_utc": missing,
    })
    result["expected_timestamp_utc"] = result["timestamp_utc"]
    return result.reset_index(drop=True)


def calculate_daily_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute daily summary statistics using UTC-aligned hourly observations."""
    data = validate_prices(df)
    data = data.copy()
    data["date_utc"] = data["timestamp_utc"].dt.floor("D")
    data["hour_utc"] = data["timestamp_utc"].dt.hour

    rows = []
    for (country, date), group in data.groupby(["country_code", "date_utc"]):
        midday = group.loc[group["hour_utc"].between(10, 15), "price_eur_mwh"]
        evening = group.loc[group["hour_utc"].between(18, 21), "price_eur_mwh"]
        rows.append(
            {
                "country_code": country,
                "date_utc": date,
                "observed_hours": int(len(group)),
                "mean_price_eur_mwh": float(group["price_eur_mwh"].mean()),
                "price_volatility_std": float(group["price_eur_mwh"].std(ddof=1)) if len(group) > 1 else 0.0,
                "negative_price_hours": int((group["price_eur_mwh"] < 0).sum()),
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
            "date_utc",
            "observed_hours",
            "mean_price_eur_mwh",
            "price_volatility_std",
            "negative_price_hours",
            "midday_mean_eur_mwh",
            "evening_mean_eur_mwh",
            "evening_minus_midday_eur_mwh",
        ])
    return pd.DataFrame(rows).sort_values(["country_code", "date_utc"]).reset_index(drop=True)


def calculate_rolling_volatility(series: pd.Series, window: int = 24) -> pd.Series:
    """Compute a rolling standard deviation of hourly price changes or levels."""
    if window <= 1:
        raise ValueError("window must be at least 2.")
    return series.rolling(window=window, min_periods=window).std()


def detect_irregular_intervals(df: pd.DataFrame) -> pd.DataFrame:
    """Return any non-hourly intervals within the same country."""
    data = validate_prices(df)
    if data.empty:
        return pd.DataFrame(columns=["country_code", "timestamp_utc", "diff_hours"])
    data = data.sort_values(["country_code", "timestamp_utc"]).copy()
    data["previous_timestamp_utc"] = data.groupby("country_code")["timestamp_utc"].shift(1)
    data["diff_hours"] = (data["timestamp_utc"] - data["previous_timestamp_utc"]).dt.total_seconds() / 3600.0
    irregular = data[data["diff_hours"].ne(1)]
    return irregular[["country_code", "timestamp_utc", "diff_hours"]].reset_index(drop=True)


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

    print(f"Loaded {len(df):,} hourly observations.")
    print(f"Countries found: {', '.join(sorted(df['country_code'].unique()))}")
    print(f"Country summary saved to: {output}")


if __name__ == "__main__":
    main()
