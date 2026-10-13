"""Rebuild the canonical dataset and empirical outputs from the six preserved CSVs.

Run from the repository root with the project virtual environment:
    .\.venv\Scripts\python.exe finalize_pipeline.py

This pipeline is offline and does not call the ENTSO-E API.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
from src.config import PROCESSED_DATA_DIR, PROJECT_ROOT
from src.data.ingest_prices import validate_market_mapping
from src.research import MARKETS, run_research

INPUT_DIR = PROJECT_ROOT / "data" / "raw" / "day_ahead_prices_2026_05_01_2026_09_30"
EXPECTED_COLUMNS = {"timestamp_utc", "zone", "price_eur_mwh", "resolution_min"}
START = pd.Timestamp("2026-05-01T00:00:00Z")
END = pd.Timestamp("2026-10-01T00:00:00Z")  # exclusive


def read_source(path: Path) -> pd.DataFrame:
    try:
        frame = pd.read_csv(path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        frame = pd.read_csv(path, encoding="utf-16")
    if not EXPECTED_COLUMNS.issubset(frame.columns):
        frame = pd.read_csv(path, encoding="utf-16")
    if not EXPECTED_COLUMNS.issubset(frame.columns):
        raise ValueError(f"Unexpected columns in {path.name}: {list(frame.columns)}")
    frame = frame.dropna(how="all").copy()
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="raise")
    frame["price_eur_mwh"] = pd.to_numeric(frame["price_eur_mwh"], errors="raise")
    frame["resolution_min"] = pd.to_numeric(frame["resolution_min"], errors="raise")
    return frame


def main() -> None:
    records = []
    audit = []
    expected_index = pd.date_range(START, END, freq="15min", inclusive="left")
    for country, zone, label in MARKETS:
        path = INPUT_DIR / f"{zone}.csv"
        if not path.exists():
            raise FileNotFoundError(f"Missing source extract: {path}")
        frame = read_source(path)
        if set(frame["zone"].astype(str)) != {zone}:
            raise ValueError(f"Unexpected zone label in {path.name}")
        if set(frame["resolution_min"].astype(int)) != {15}:
            raise ValueError(f"{zone} is not consistently 15-minute resolution")
        if frame["timestamp_utc"].duplicated().any():
            raise ValueError(f"Duplicate timestamps in {path.name}")
        if ((frame["timestamp_utc"] < START) | (frame["timestamp_utc"] >= END)).any():
            raise ValueError(f"Out-of-period timestamps in {path.name}")
        if frame["price_eur_mwh"].isna().any():
            raise ValueError(f"Missing prices in {path.name}")
        observed = pd.DatetimeIndex(frame["timestamp_utc"])
        missing = expected_index.difference(observed)
        audit.append({
            "country_code": country, "bidding_zone": zone, "market": label,
            "observations": len(frame), "expected_intervals": len(expected_index),
            "missing_intervals": len(missing),
            "missing_dates_utc": ";".join(sorted(missing.strftime("%Y-%m-%d").unique())),
            "duplicate_timestamps": int(frame["timestamp_utc"].duplicated().sum()),
            "resolution_minutes": 15,
        })
        records.append(pd.DataFrame({
            "timestamp_utc": frame["timestamp_utc"],
            "country_code": country,
            "bidding_zone": zone,
            "price_eur_mwh": frame["price_eur_mwh"].astype(float),
            "source": "european-power-prices (ENTSO-E via public redistribution)",
            "retrieved_at": pd.Timestamp.now(tz="UTC").isoformat(),
        }))

    data = pd.concat(records, ignore_index=True)
    data = validate_market_mapping(data)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    canonical = PROCESSED_DATA_DIR / "day_ahead_prices.csv"
    data.to_csv(canonical, index=False)
    pd.DataFrame(audit).to_csv(PROCESSED_DATA_DIR / "source_extract_audit.csv", index=False)

    run_research(data_path=canonical, raw_dir=INPUT_DIR)
    print(f"Validated and analysed {len(data):,} observations across {len(MARKETS)} markets.")
    print(f"Canonical data: {canonical.relative_to(PROJECT_ROOT)}")
    print(f"Source audit: {(PROCESSED_DATA_DIR / 'source_extract_audit.csv').relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
