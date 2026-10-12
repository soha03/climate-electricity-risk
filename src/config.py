"""Project-wide configuration for the European electricity-market risk project."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SYNTHETIC_DATA_DIR = DATA_DIR / "synthetic"
FIGURES_DIR = PROJECT_ROOT / "figures"

COUNTRIES = {
    "DE": "Germany",
    "AT": "Austria",
    "FR": "France",
    "ES": "Spain",
    "PT": "Portugal",
    "IT": "Italy",
}

# Italy is not a single homogeneous market. For the offline project baseline, we
# retain the country code as IT but document when a bidding-zone filter is needed.
# The actual ENTSO-E zone identifier must be confirmed with the source data before
# claiming full Italian market coverage.
ITALY_BIDDING_ZONES = [
    "IT-North",
    "IT-Centre-North",
    "IT-South",
    "IT-Brindisi",
    "IT-Foggia",
]
DEFAULT_BIDDING_ZONE_BY_COUNTRY = {
    "DE": "DE",
    "AT": "AT",
    "FR": "FR",
    "ES": "ES",
    "PT": "PT",
    "IT": "IT-North",
}

START_DATE = "2026-05-01"
END_DATE = "2026-10-01"  # Exclusive end date: covers May through September
STUDY_PERIOD = (START_DATE, END_DATE)

PRICE_COLUMN = "price_eur_mwh"
TIMESTAMP_COLUMN = "timestamp_utc"
COUNTRY_COLUMN = "country_code"
CANONICAL_COLUMNS = [
    "timestamp_utc",
    "country_code",
    "bidding_zone",
    "price_eur_mwh",
    "source",
    "retrieved_at",
]

ENTSOE_API_BASE_URL = "https://web-api.tp.entsoe.eu/api"
ENTSOE_API_TOKEN_ENV = "ENTSOE_API_TOKEN"

REAL_DATA_PATH = PROCESSED_DATA_DIR / "day_ahead_prices.csv"

# The canonical hourly dataset uses UTC timestamps. Daylight-saving transitions are
# handled by pandas' tz-aware timestamps; a missing hour at DST boundaries is a
# data-quality issue, not a price of zero.

# The project is intentionally offline-safe: no real market data is required for
# software validation, but the pipeline clearly reports when the empirical dataset
# is missing.
