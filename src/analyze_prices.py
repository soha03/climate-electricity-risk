"""Exploratory analysis of European day-ahead electricity prices."""

from pathlib import Path

import pandas as pd

from src.config import COUNTRIES

ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"
FIGURES_DIR = ROOT / "figures"

PRICE_FILE = PROCESSED_DIR / "day_ahead_prices.csv"


def load_prices(path: Path = PRICE_FILE) -> pd.DataFrame:
    """Load and validate the standardised price dataset."""
    if not path.exists():
        raise FileNotFoundError(
            f"No real price dataset found at {path}. "
            "The analysis module is ready, but data has not been downloaded."
        )

    df = pd.read_csv(path, parse_dates=["timestamp_utc"])

    required = {"timestamp_utc", "country_code", "price_eur_mwh"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing columns: {sorted(missing)}")

    df["timestamp_utc"] = pd.to_datetime(
        df["timestamp_utc"], utc=True, errors="raise"
    )
    df["country_code"] = df["country_code"].str.upper()
    df["price_eur_mwh"] = pd.to_numeric(
        df["price_eur_mwh"], errors="raise"
    )

    unknown = set(df["country_code"].dropna()) - set(COUNTRIES)
    if unknown:
        raise ValueError(f"Unexpected country codes: {sorted(unknown)}")

    if df[["timestamp_utc", "country_code", "price_eur_mwh"]].isna().any().any():
        raise ValueError("Dataset contains missing required values.")

    if df.duplicated(["timestamp_utc", "country_code"]).any():
        raise ValueError(
            "Duplicate country-hour rows detected. "
            "Resolve bidding-zone definitions before analysis."
        )

    return df.sort_values(["country_code", "timestamp_utc"])


def calculate_daily_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate daily price metrics using UTC hours."""
    data = df.copy()
    data["date_utc"] = data["timestamp_utc"].dt.floor("D")
    data["hour_utc"] = data["timestamp_utc"].dt.hour

    rows = []

    for (country, date), group in data.groupby(["country_code", "date_utc"]):
        midday = group.loc[group["hour_utc"].between(10, 15), "price_eur_mwh"]
        evening = group.loc[group["hour_utc"].between(18, 21), "price_eur_mwh"]

        rows.append({
            "country_code": country,
            "date_utc": date,
            "mean_price_eur_mwh": group["price_eur_mwh"].mean(),
            "price_volatility_std": group["price_eur_mwh"].std(),
            "negative_price_hours": int((group["price_eur_mwh"] < 0).sum()),
            "midday_mean_eur_mwh": midday.mean(),
            "evening_mean_eur_mwh": evening.mean(),
            "evening_minus_midday_eur_mwh": (
                evening.mean() - midday.mean()
                if not midday.empty and not evening.empty
                else float("nan")
            ),
            "observed_hours": len(group),
        })

    return pd.DataFrame(rows)


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    df = load_prices()
    metrics = calculate_daily_metrics(df)

    output = PROCESSED_DIR / "daily_price_metrics.csv"
    metrics.to_csv(output, index=False)

    print(f"Loaded {len(df):,} hourly price observations.")
    print(f"Countries found: {', '.join(sorted(df['country_code'].unique()))}")
    print(f"Daily metrics saved to: {output}")


if __name__ == "__main__":
    main()
