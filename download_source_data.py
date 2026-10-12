#!/usr/bin/env python3
"""Download the verified daily raw prices used by the project and build the canonical CSV.

This script intentionally downloads only the required source files for the project study
period from the public GitHub source repo that documents the day-ahead price schema.
It does not fabricate data and it preserves the original daily files before converting
observations into the project's canonical schema.

The repository root is assumed to be the directory containing this script.
"""

from __future__ import annotations

import csv
from datetime import date, datetime, timedelta
from pathlib import Path
import urllib.request
from urllib.error import HTTPError, URLError

PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "source_download"
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed" / "day_ahead_prices.csv"
SOURCE_BASE_URL = (
    "https://raw.githubusercontent.com/whipeeer-creator/european-power-prices/main/data/2026"
)
SOURCE_URL = "https://github.com/whipeeer-creator/european-power-prices"
SELECTED_ITALIAN_ZONE = "IT-North"

REQUIRED_ZONES = {
    "AT",
    "DE-LU",
    "FR",
    "ES",
    "PT",
    SELECTED_ITALIAN_ZONE,
}

COUNTRY_MAP = {
    "AT": "AT",
    "DE-LU": "DE",
    "FR": "FR",
    "ES": "ES",
    "PT": "PT",
    SELECTED_ITALIAN_ZONE: "IT",
}


def iter_dates(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def download_daily_files(start: date, end: date) -> list[Path]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    downloaded: list[Path] = []
    missing: list[str] = []
    for day in iter_dates(start, end):
        filename = day.isoformat() + ".csv"
        url = f"{SOURCE_BASE_URL}/{filename}"
        target = RAW_DIR / filename
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; energy-risk-lab/1.0)"},
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = response.read()
            target.write_bytes(payload)
            downloaded.append(target)
            print(f"Downloaded {filename}")
        except (HTTPError, URLError) as exc:
            missing.append(filename)
            print(f"Missing or inaccessible {filename}: {exc}")
    if missing:
        raise RuntimeError(
            "Incomplete source download; no canonical CSV was written. "
            f"Missing or inaccessible files: {', '.join(missing)}"
        )
    return downloaded


def build_canonical_csv(downloaded_files: list[Path]) -> Path:
    rows: list[dict[str, str]] = []
    for path in sorted(downloaded_files):
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                zone = row.get("zone", "").strip()
                if zone not in REQUIRED_ZONES:
                    continue
                rows.append(
                    {
                        "timestamp_utc": row["timestamp_utc"],
                        "country_code": COUNTRY_MAP[zone],
                        "bidding_zone": zone,
                        "price_eur_mwh": row["price_eur_mwh"],
                        "source": SOURCE_URL,
                        "retrieved_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    }
                )

    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PROCESSED_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "timestamp_utc",
                "country_code",
                "bidding_zone",
                "price_eur_mwh",
                "source",
                "retrieved_at",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    return PROCESSED_PATH


def main() -> None:
    start = date(2026, 5, 1)
    end = date(2026, 9, 30)
    print(f"Source URL: {SOURCE_URL}")
    print(f"Selected Italian zone: {SELECTED_ITALIAN_ZONE}")
    print(f"Downloading source files from {start.isoformat()} to {end.isoformat()}...")
    downloaded_files = download_daily_files(start, end)
    if not downloaded_files:
        raise RuntimeError("No source files were downloaded. Check network access and the raw GitHub repo URL.")
    output_path = build_canonical_csv(downloaded_files)
    print(f"Saved raw source files in {RAW_DIR}")
    print(f"Saved processed file in {output_path}")
    print("Record the source URL and retrieval date in the project documentation.")


if __name__ == "__main__":
    main()
