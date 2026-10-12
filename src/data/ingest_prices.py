"""Data validation and ingestion helpers for European electricity prices.

The pipeline is intentionally offline-safe. It validates the canonical dataset
schema and supports future ENTSO-E or SMARD-style raw files without requiring a
live API token for tests or local analysis.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

import pandas as pd

from src.config import (
    CANONICAL_COLUMNS,
    COUNTRIES,
    DATASET_ZONE_BY_COUNTRY,
    DEFAULT_BIDDING_ZONE_BY_COUNTRY,
    ENTSOE_COUNTRY_TO_ZONE,
    END_DATE,
    ITALY_BIDDING_ZONES,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    START_DATE,
)

REQUIRED_COLUMNS = ["timestamp_utc", "country_code", "price_eur_mwh"]


def _normalise_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Standardise common raw fields to the canonical schema used by the project."""
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
    """Validate and standardise a price dataset."""
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


def validate_market_mapping(df: pd.DataFrame) -> pd.DataFrame:
    """Check that country-bidding-zone pairs are explicit and do not silently substitute other markets."""
    data = validate_prices(df)
    invalid = []
    for country, zone in zip(data["country_code"], data["bidding_zone"]):
        allowed_zones = ENTSOE_COUNTRY_TO_ZONE.get(country, [])
        dataset_zone = DATASET_ZONE_BY_COUNTRY.get(country)
        if dataset_zone:
            allowed_zones = [*allowed_zones, dataset_zone]
        if country == "IT":
            allowed_zones = [*allowed_zones, *ITALY_BIDDING_ZONES]
        if zone not in {z.upper() for z in allowed_zones} and zone.upper() != country:
            invalid.append((country, zone))
    if invalid:
        pairs = ", ".join(f"{country}:{zone}" for country, zone in invalid[:5])
        raise ValueError(
            "Detected non-matching bidding-zone identifiers for the configured country. "
            f"Review the market mapping before analysis. Examples: {pairs}"
        )
    return data


def load_raw_dataset(path: str | Path) -> pd.DataFrame:
    """Load a raw source file from disk and standardise it to the project schema."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Raw dataset not found: {file_path}")
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(file_path)
    elif suffix in {".xlsx", ".xls"}:
        df = pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported file format for {file_path}: {suffix}")
    return validate_prices(df)


def entsoe_api_ready() -> bool:
    """Return True when an ENTSO-E token is configured in the environment."""
    return bool(os.getenv("ENTSOE_API_TOKEN"))


def future_entsoe_query_for_country(country_code: str, start: str, end: str, bidding_zone: str | None = None) -> dict:
    """Document the future ENTSO-E query contract without performing an API call.

    This function is intentionally a contract for later use when a live token is
    available. It does not connect to the internet and does not fabricate results.
    """
    country = country_code.upper()
    if country not in COUNTRIES:
        raise ValueError(f"Unsupported country code: {country}")
    zone = (bidding_zone or DEFAULT_BIDDING_ZONE_BY_COUNTRY.get(country, country)).upper()
    allowed = [item.upper() for item in ENTSOE_COUNTRY_TO_ZONE.get(country, [country])]
    if zone not in allowed and zone != country:
        raise ValueError(
            f"Unexpected zone '{zone}' for {country}. "
            f"Allowed zones are {allowed}."
        )
    return {
        "country_code": country,
        "bidding_zone": zone,
        "start": start,
        "end": end,
        "product_type": "day_ahead",
        "api_token_configured": entsoe_api_ready(),
    }


def load_real_prices(path: str | Path | None = None) -> pd.DataFrame:
    """Load the empirical dataset from disk when it exists."""
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

    print("\nData source notes:")
    print("  - ENTSO-E Transparency Platform: primary source for market prices and bidding zones")
    print("  - SMARD: useful German market validation and metadata")
    print("  - The project requires no API token to run offline; live ingestion is isolated for later use.")

    print("\nStatus: project structure is ready.")
    print("The empirical dataset is not available yet; the project is designed to fail gracefully until real data is added.")


if __name__ == "__main__":
    main()

