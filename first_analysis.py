"""Repository entry point for the electricity-market risk project.

This script remains offline-safe. It checks for real empirical observations first;
only when they are absent does it gracefully report the current status and explain
how to supply real data later.
"""

from __future__ import annotations

from pathlib import Path

from src.analyze_prices import compute_country_summary, load_prices
from src.config import FIGURES_DIR, PROCESSED_DATA_DIR


def main() -> None:
    """Run the project in its no-data state without requiring API access."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    data_path = PROCESSED_DATA_DIR / "day_ahead_prices.csv"
    if not data_path.exists():
        print("No empirical data file was found at:")
        print(f"  {data_path}")
        print("\nThis project is intentionally designed to run without a live ENTSO-E token.")
        print("To enable the empirical analysis, download and validate a canonical hourly price dataset into the processed directory.")
        print("The repository will then run the descriptive statistics and visualisation pipeline automatically.")
        return

    try:
        df = load_prices(data_path)
        summary = compute_country_summary(df)
        print(f"Loaded {len(df):,} observed price intervals across {len(summary)} market rows.")
        print(summary.to_string(index=False))
    except (FileNotFoundError, ValueError) as exc:
        print(f"Unable to run the empirical pipeline: {exc}")
        print("Please populate the canonical dataset and ensure no duplicates or invalid country codes remain.")


if __name__ == "__main__":
    main()

