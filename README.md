# Stochastic Electricity Market Risk under Climate Transition Scenarios

## Research objective

This repository is designed to analyse how European electricity prices vary across markets, with a focus on volatility, negative prices, spikes, and cross-country differences. It is structured as a reproducible research project for electricity-market analysis, stochastic modelling, and price-risk measurement in a climate-transition context.

The project compares six European markets:

- Germany (DE)
- Austria (AT)
- France (FR)
- Spain (ES)
- Portugal (PT)
- Italy (IT)

Study period: 1 May 2026 through 30 September 2026, inclusive. The end date is treated as exclusive when building date ranges.

## Why this matters

European electricity markets are increasingly shaped by renewable penetration, weather, fuel prices, and grid constraints. Understanding the distribution of prices and the frequency of extreme moves is important for market monitoring, risk measurement, and model design for future power-market applications.

## Data and scope

This project is intentionally built to work without a live API token. The code and tests run offline and fail gracefully when real observations are not available.

The canonical hourly dataset is defined as:

- timestamp_utc
- country_code
- bidding_zone
- price_eur_mwh
- source
- retrieved_at

All timestamps are handled in UTC, with timezone-aware pandas timestamps. Duplicate records are rejected, missing hours are flagged, and electricity prices are kept in EUR/MWh without applying logarithms to negative values.

Italy is treated as a country-level label only unless a specific bidding-zone identifier is supplied from the source data. This is an important limitation because Italy has multiple bidding zones and should not be treated as a single homogeneous market without explicit documentation.

## Repository structure

- src/config.py — project-wide constants, market definitions, and schema
- src/data/ingest_prices.py — data validation, schema standardisation, and future ENTSO-E adapter hooks
- src/analyze_prices.py — summary statistics, coverage checks, and market diagnostics
- src/models/stochastic.py — simple stochastic simulation and benchmark logic
- src/risk/metrics.py — VaR, Expected Shortfall, and stress-scenario tools
- src/visualization/plots.py — plotting utilities for figures and diagnostics
- tests/test_analysis.py — offline verification suite
- tests/run_tests.py — test runner for the repository
- data/raw/ — raw downloaded files and metadata
- data/processed/ — validated empirical datasets
- data/synthetic/ — synthetic fixtures for software testing only
- figures/ — saved plots and publication outputs

## Installation

This project expects the repo virtual environment to be used. On Windows PowerShell:

```powershell
cd C:\Users\SOHA\Documents\energy-risk-lab
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install numpy pandas matplotlib
```

If the environment already contains the required dependencies, the install step may be skipped.

## Running the project

```powershell
cd C:\Users\SOHA\Documents\energy-risk-lab
.\.venv\Scripts\python.exe first_analysis.py
```

If no empirical dataset is present, the script exits gracefully and explains that real observations have not yet been downloaded.

## Running tests

```powershell
cd C:\Users\SOHA\Documents\energy-risk-lab
.\.venv\Scripts\python.exe tests/run_tests.py
```

This runs the offline suite without requiring a token or internet access.

## Data schema and quality rules

The canonical dataset must contain the following fields:

- timestamp_utc: UTC timestamp for each hourly observation
- country_code: ISO code in the set {DE, AT, FR, ES, PT, IT}
- bidding_zone: market zone identifier, if known
- price_eur_mwh: price in EUR/MWh, may be negative
- source: data source label such as ENTSO-E or synthetic
- retrieved_at: timestamp when the observation was retrieved, when available

Quality rules:

- Reject duplicate timestamp-country-zone combinations.
- Treat timezone handling consistently using UTC.
- Do not interpret missing hours as zero prices.
- Keep negative electricity prices as legitimate observations.
- Never silently substitute a neighbouring market for an unavailable zone.
- Validate country codes and time stamps before any descriptive analysis.

## Future ENTSO-E integration

The project includes a clear adapter boundary for future ENTSO-E Transparency Platform use. The actual API credentials are kept in environment variables rather than embedded in code.

Example configuration:

```powershell
$env:ENTSOE_API_TOKEN = "your-token-here"
```

The data ingestion step should later validate that the correct bidding-zone identifiers are used for each country, especially for Italy. API authentication is intentionally isolated and does not affect the offline pipeline.

## What is and is not available

Empirical outputs are only valid when real data is present and validated. Simulated outputs are labelled as simulations and do not represent actual market forecasts.

Current status:

- Empirical analysis: awaiting real observations
- Stochastic modelling: implemented as a synthetic, reproducible offline component
- Risk functions: implemented and testable on synthetic loss series
- Visual outputs: ready to generate when real data is available

## Methodological choices and limitations

- The project uses descriptive, reproducible statistics rather than causal inference.
- Prices are analysed as observed hourly values in EUR/MWh, not as portfolio cash flows.
- VaR and Expected Shortfall are reported as price-risk measures unless a market position is explicitly modelled.
- The baseline stochastic model is intentionally simple and is suitable for illustration and research setup, not for live trading decisions.
- Without real ENTSO-E observations, no empirical findings should be reported as completed market conclusions.

## Data availability status

This repository is ready for the next stage once the real price series are downloaded and validated. Until then, all analysis modules remain in a clean offline-safe state.
