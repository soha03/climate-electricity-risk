# European Day-Ahead Electricity Prices: Market Dynamics and Short-Horizon Risk

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

The analysis uses day-ahead electricity prices published in the public [`european-power-prices`](https://github.com/whipeeer-creator/european-power-prices) GitHub repository. That repository republishes daily CSV files, is updated daily, and identifies the ENTSO-E Transparency Platform as the underlying source of the market prices. This project uses the redistributed CSV files; it does not retrieve prices directly through the ENTSO-E API.

### Sample and markets

- Period: 1 May 2026 to 30 September 2026, inclusive
- Bidding zones: DE-LU, AT, FR, ES, PT, and IT-North
- Resolution: 15 minutes
- Unit: EUR/MWh
- Expected complete grid: 14,688 intervals per market
- Observed sample: 14,512 intervals per market, 87,072 rows in total

The Italian series is IT-North, not an Italy-wide aggregate. Negative prices are retained. Missing intervals are left missing and are not filled or treated as zero.

### How the data was obtained

The source repository was cloned locally, then its `merge.py` script was used to extract each bidding zone and the required date range. The resulting CSV exports were used in this project's analysis.

Example commands, run from the cloned `european-power-prices` folder:

```powershell
python merge.py --zone DE-LU --resolution 15 --from 2026-05-01 --to 2026-09-30
python merge.py --zone AT --resolution 15 --from 2026-05-01 --to 2026-09-30
python merge.py --zone FR --resolution 15 --from 2026-05-01 --to 2026-09-30
python merge.py --zone ES --resolution 15 --from 2026-05-01 --to 2026-09-30
python merge.py --zone PT --resolution 15 --from 2026-05-01 --to 2026-09-30
python merge.py --zone IT-North --resolution 15 --from 2026-05-01 --to 2026-09-30
```

The source files use UTC interval-start timestamps and include the zone, price in EUR/MWh, and resolution in minutes. The source repository documents that it collects prices from ENTSO-E and updates its daily files; see its README for source notes, resolution details, corrections, and licence information.

The extracted sample has gaps on 30 June and 7 September 2026: 88 missing 15-minute intervals per market on each date. No imputation is applied. The source CSVs are not bundled in this repository; obtain them using the steps above before reproducing the empirical results.

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

Run the full analysis without downloading or changing raw files:

```powershell
cd C:\Users\SOHA\Documents\energy-risk-lab
.\.venv\Scripts\python.exe -m src.research
```

The analysis runner reads the locally prepared empirical dataset and writes reports and figures. Ensure the source data has been extracted and placed in the paths expected by the project before running it. `first_analysis.py` remains a lightweight summary/chart entry point.

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
- source: provenance label for the observation
- retrieved_at: UTC retrieval timestamp, when recorded

Quality rules:

- Reject duplicate timestamp-country-zone combinations.
- Treat timezone handling consistently using UTC.
- Do not interpret missing intervals as zero prices or fill them silently.
- Keep negative electricity prices as legitimate observations.
- Never silently substitute a neighbouring market for an unavailable zone.
- Validate country codes and time stamps before any descriptive analysis.
- Do not mix resolutions. The selected zones are all 15-minute products during this period.
- Count returns and model transitions only when timestamps are exactly 15 minutes apart.

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

The full source dataset is not committed here. After extracting the six market series and placing the data where the project expects it, run `python -m src.research` to reproduce the analysis. The analysis command itself does not download the upstream data.
