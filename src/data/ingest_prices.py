"""Data validation and ingestion helpers for European electricity prices.

The pipeline is intentionally offline-safe. It validates the canonical dataset
schema but does not require live ENTSO-E access for code execution or tests.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import (
    CANONICAL_COLUMNS,
    COUNTRIES,
    DEFAULT_BIDDING_ZONE_BY_COUNTRY,
    END_DATE,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    START_DATE,
)

REQUIRED_COLUMNS = ["timestamp_utc", "country_code", "price_eur_mwh"]


def _normalise_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Standardise common column names to the canonical schema used by the project."""
    result = frame.copy()
    rename_map = {
        "timestamp": "timestamp_utc",
        "time": "timestamp_utc",
        "date": "timestamp_utc",
        "country": "country_code",
        "country_code": "country_code",
        "price": "price_eur_mwh",
        "price_eur_mwh": "price_eur_mwh",
        "bidding_zone": "bidding_zone",
        "source": "source",
        "retrieved_at": "retrieved_at",
    }
    result = result.rename(columns={k: v for k, v in rename_map.items() if k in result.columns})
    if "bidding_zone" not in result.columns:
        result["bidding_zone"] = result["country_code"].map(DEFAULT_BIDDING_ZONE_BY_COUNTRY).fillna("unknown")
    if "source" not in result.columns:
        result["source"] = "manual"
    if "retrieved_at" not in result.columns:
        result["retrieved_at"] = pd.Timestamp.now(tz="UTC")
    return result


def validate_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and standardise a price dataset.

    Parameters
    ----------
    df : pandas.DataFrame
        A dataframe containing at least timestamp, country code, and price values.

    Returns
    -------
    pandas.DataFrame
        A canonical dataframe with UTC timestamps and sorted rows.
    """
    if df is None or df.empty:
        raise ValueError("Price dataset is empty. Supply at least one valid observation.")

    result = _normalise_columns(df)
    missing = set(REQUIRED_COLUMNS) - set(result.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    result["timestamp_utc"] = pd.to_datetime(result["timestamp_utc"], utc=True, errors="raise")
    result["country_code"] = result["country_code"].astype(str).str.upper()
    result["price_eur_mwh"] = pd.to_numeric(result["price_eur_mwh"], errors="raise")
    result["bidding_zone"] = result["bidding_zone"].astype(str).str.upper()
    result["source"] = result["source"].astype(str)

    if not result["country_code"].isin(COUNTRIES).all():
        unknown = sorted(set(result["country_code"]) - set(COUNTRIES))
        raise ValueError(f"Unknown country codes: {unknown}")

    if result["price_eur_mwh"].isna().any():
        raise ValueError("Price data contains missing values.")

    if result.duplicated(["timestamp_utc", "country_code", "bidding_zone"]).any():
        raise ValueError(
            "Duplicate country-hour rows detected. "
            "Check bidding zones and source data before aggregating."
        )

    return result.sort_values(["country_code", "timestamp_utc"]).reset_index(drop=True)


def load_real_prices(path: str | Path | None = None) -> pd.DataFrame:
    """Load the empirical dataset from disk when it exists.

    This function intentionally refuses to fabricate or synthesize market data.
    """
    file_path = Path(path) if path is not None else PROCESSED_DATA_DIR / "day_ahead_prices.csv"
    if not file_path.exists():
        raise FileNotFoundError(
            f"No real empirical price dataset was found at {file_path}. "
            "The pipeline is ready, but data has not been downloaded and validated yet."
        )
    df = pd.read_csv(file_path)
    return validate_prices(df)


def main() -> None:
    """Print the project status and data-ingestion readiness."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("European Electricity Market Risk Project")
    print(f"Study period: {START_DATE} to {END_DATE} (end exclusive)")
    print("\nConfigured countries:")
    for code, name in COUNTRIES.items():
        print(f"  {code}: {name}")

    print("\nCanonical schema:")
    for column in CANONICAL_COLUMNS:
        print(f"  - {column}")

    print("\nStatus: project structure is ready.")
    print("The empirical dataset is not available yet; the project is designed to fail gracefully until real data is added.")


if __name__ == "__main__":
    main()

