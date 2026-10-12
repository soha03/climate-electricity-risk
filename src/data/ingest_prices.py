"""Download and validate European electricity-market price data.

This module defines the expected dataset structure.
It does not download data until a source and credentials are configured.
"""

from pathlib import Path

import pandas as pd

from src.config import COUNTRIES, START_DATE, END_DATE

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

REQUIRED_COLUMNS = [
    "timestamp_utc",
    "country_code",
    "price_eur_mwh",
]


def validate_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and standardise a price dataset."""
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    result = df[REQUIRED_COLUMNS].copy()

    result["timestamp_utc"] = pd.to_datetime(
        result["timestamp_utc"], utc=True, errors="raise"
    )
    result["country_code"] = result["country_code"].astype(str).str.upper()
    result["price_eur_mwh"] = pd.to_numeric(
        result["price_eur_mwh"], errors="raise"
    )

    if result["country_code"].isin(COUNTRIES).all() is False:
        unknown = sorted(set(result["country_code"]) - set(COUNTRIES))
        raise ValueError(f"Unknown country codes: {unknown}")

    if result["price_eur_mwh"].isna().any():
        raise ValueError("Price data contains missing values.")

    if result.duplicated(["timestamp_utc", "country_code"]).any():
        raise ValueError(
            "Duplicate timestamp-country rows found. "
            "Check bidding zones and source data before aggregating."
        )

    return result.sort_values(
        ["country_code", "timestamp_utc"]
    ).reset_index(drop=True)


def main() -> None:
    """Print project configuration and data-source readiness."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("European Power Market Dynamics")
    print(f"Study period: {START_DATE} to {END_DATE} (end exclusive)")
    print("\nConfigured countries:")
    for code, name in COUNTRIES.items():
        print(f"  {code}: {name}")

    print("\nData directories:")
    print(f"  Raw:       {RAW_DIR}")
    print(f"  Processed: {PROCESSED_DIR}")

    print("\nStatus: project structure ready.")
    print("Real price data has not been downloaded yet.")


if __name__ == "__main__":
    main()

