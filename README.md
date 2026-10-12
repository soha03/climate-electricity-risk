# Stochastic Electricity Market Risk under Climate Transition Scenarios

## Research objective

This repository is designed to analyse how European electricity prices vary across markets, with a focus on volatility, negative prices, spikes, and cross-country differences. It is structured as a reproducible research project for electricity-market analysis, stochastic modelling, and price-risk measurement in a climate-transition context.

The empirical sample compares six documented source bidding zones:

- Germany (DE-LU)
- Austria (AT)
- France (FR)
- Spain (ES)
- Portugal (PT)
- Italy (IT-North; not an Italy-wide aggregate)

Study period: 1 May 2026 through 30 September 2026, inclusive. The end date is treated as exclusive when building date ranges.

## Why this matters

European electricity markets are increasingly shaped by renewable penetration, weather, fuel prices, and grid constraints. Understanding the distribution of prices and the frequency of extreme moves is important for market monitoring, risk measurement, and model design for future power-market applications.

## Data and scope

Analysis runs offline after the data is present and does not require an API token. The repository includes the report, compact review tables, and final figures. It intentionally does not include the 153 raw daily CSVs or the full canonical observation file; those are generated locally by the documented download step.

The project is designed for real market data from the following sources:

- Original market source: ENTSO-E Transparency Platform
- Local redistribution used for this sample: [european-power-prices](https://github.com/whipeeer-creator/european-power-prices), which documents daily file schema, zones, UTC interval-start timestamps, and EUR/MWh prices
- The preserved original source files and per-observation source/retrieval metadata are retained for provenance

The canonical dataset contains six columns:

- timestamp_utc
- country_code
- bidding_zone
- price_eur_mwh
- source
- retrieved_at

All timestamps are timezone-aware UTC interval-start timestamps. The selected zones are 15-minute resolution throughout this sample. There are 87,072 observed rows: 14,512 per market. Two common partial days have gaps; no missing observations are filled and no hourly aggregation is applied. Negative prices are retained in EUR/MWh.

The canonical `country_code` for the Italian observation is `IT`, while its explicit source `bidding_zone` is `IT-NORTH` after canonical uppercasing. This is not an Italy-wide aggregate; Italy has multiple bidding zones.

## Repository structure

- src/config.py — project-wide constants, market definitions, and schema
- src/data/ingest_prices.py — data validation, schema standardisation, and future ENTSO-E adapter hooks
- src/analyze_prices.py — canonical validation and descriptive analysis helpers
- src/research.py — empirical audit, distributions, intraday profiles, rolling volatility, correlations, model evaluation, risk outputs, figures, and Markdown report
- src/models/stochastic.py — additive seasonal AR(1), chronological holdout evaluation, and bootstrap simulation
- src/risk/metrics.py — explicitly signed price-change VaR/ES and price-shock loss tools
- src/visualization/plots.py — plotting utilities for figures and diagnostics
- tests/test_analysis.py — offline verification suite
- tests/run_tests.py — test runner for the repository
- data/raw/ — raw downloaded files and metadata
- data/processed/ — validated empirical datasets
- data/synthetic/ — synthetic fixtures for software testing only; never included in empirical estimates
- reports/ — generated Markdown research report
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

### Files included in a clone

The tracked publication artifacts are:

- Report: `reports/european_electricity_market_research.md`
- Compact CSVs: `country_summary.csv`, `empirical_data_audit.csv`, `market_descriptive_statistics.csv`, `intraday_profile.csv`, both price/change correlation matrices and their pair-count matrices, `model_holdout_diagnostics.csv`, `price_change_risk.csv`, `stress_scenarios.csv`, and `stochastic_simulation_summary.csv` under `data/processed/`
- Figures: `cross_country_day_ahead_prices.png`, `cross_country_price_correlation.png`, `cross_country_rolling_volatility.png`, `empirical_intraday_profile.png`, `empirical_price_quantiles.png`, `historical_price_change_risk.png`, `model_holdout_residuals.png`, and `simulated_vs_observed_DE-LU.png` under `figures/`

Generated locally and not tracked: the 153 daily raw CSVs (about 19.5 MB in the current copy), the canonical 87,072-row `day_ahead_prices.csv` (about 10.0 MB), the full rolling-volatility series, per-interval holdout predictions, and individual stochastic paths. `.gitignore` keeps these local files and credentials out of Git while allowing the compact review artifacts above.

### Reproduce the empirical analysis from a fresh clone

From the repository root, install the declared dependencies if needed, then fetch the study-period source files and regenerate the canonical input:

```powershell
.\.venv\Scripts\python.exe .\download_source_data.py
```

This downloads `data/2026/YYYY-MM-DD.csv` from the documented public source for 2026-05-01 through 2026-09-30, preserving the daily files in `data/raw/source_download/`, and writes `data/processed/day_ahead_prices.csv`. The downloader now stops with the missing filenames if any request fails; do not use a partial output. Source: https://github.com/whipeeer-creator/european-power-prices

Regenerate the audit, all numerical tables, report, simulations, and figures from those files:

```powershell
.\.venv\Scripts\python.exe -m src.research
```

The runner verifies all 153 daily source files, expected zones, resolution, and raw-to-canonical row equality before writing outputs. It does not download data. `first_analysis.py` remains a lightweight summary/chart entry point. Run tests with `.\.venv\Scripts\python.exe .\tests\run_tests.py`.

## Running tests

```powershell
cd C:\Users\SOHA\Documents\energy-risk-lab
.\.venv\Scripts\python.exe tests/run_tests.py
```

This runs the offline suite without requiring a token or internet access. Unit tests use small synthetic fixtures; their values are not empirical findings.

## Data schema and quality rules

The canonical dataset must contain the following fields:

- timestamp_utc: UTC timestamp marking the start of a 15-minute interval for this sample
- country_code: ISO code in the set {DE, AT, FR, ES, PT, IT}
- bidding_zone: market zone identifier, if known
- price_eur_mwh: price in EUR/MWh, may be negative
- source: data source label such as ENTSO-E or synthetic
- retrieved_at: UTC retrieval timestamp

Quality rules:

- Reject duplicate timestamp-country-zone combinations.
- Treat timezone handling consistently using UTC.
- Do not interpret missing intervals as zero prices or fill them silently.
- Keep negative electricity prices as legitimate observations.
- Never silently substitute a neighbouring market for an unavailable zone.
- Validate country codes and time stamps before any descriptive analysis.
- Do not mix resolutions. The selected zones are all 15-minute products during this period.
- Count returns and model transitions only when timestamps are exactly 15 minutes apart.

## Future ENTSO-E integration

The project retains an adapter boundary for future direct ENTSO-E use. Credentials belong in environment variables, never in source files. Current empirical results come from the documented local daily CSV source and do not depend on an ENTSO-E API call.

Example configuration:

```powershell
$env:ENTSOE_API_TOKEN = "your-token-here"
```

The data ingestion step should later validate that the correct bidding-zone identifiers are used for each country, especially for Italy. API authentication is intentionally isolated and does not affect the offline pipeline.

## What is and is not available

Empirical outputs are only valid when real data is present and validated. Simulated outputs are labelled as simulations and do not represent actual market forecasts.

Current status:

- Empirical data: 87,072 observed rows across DE-LU, AT, FR, ES, PT, and IT-North, 2026-05-01 through 2026-09-30
- Missing data: 88 intervals on each of 2026-06-30 and 2026-09-07 in each market; no imputation
- Model outputs: additive seasonal AR(1) with chronological 80/20 holdout diagnostics; simulation outputs are explicitly labelled
- Risk outputs: historical 15-minute price-change loss VaR/ES for a 1 MWh long price exposure and deterministic shock scenarios
- Generated report: `reports/european_electricity_market_research.md`

## Methodological choices and limitations

- The project uses descriptive statistics and does not make causal claims about climate transition.
- Observations are 15-minute interval prices in EUR/MWh. The two partial days reduce return, holdout, and rolling-window sample sizes.
- Spike events are defined as absolute consecutive 15-minute price changes above the market-specific empirical 99th percentile of absolute changes.
- The stochastic model uses a UTC quarter-hour seasonal profile, additive AR(1) residual dynamics, and resampled training innovations. It does not model volatility clustering, weekday effects, or fundamentals.
- VaR/ES use loss = `-position_mwh * price_change`; positive losses mean a price fall for a long position. They do not represent a full trading portfolio.
- Simulated paths are not observations, forecasts, or climate scenarios. The sample is too short and lacks covariates for structural transition conclusions.

## Data availability status

The current working copy has valid local source data and generated outputs. A fresh clone must run the download command above before `python -m src.research`; the checked-in tables and figures are review snapshots, not substitutes for the raw or canonical input data.
