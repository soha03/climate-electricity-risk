# European Day-Ahead Electricity Prices: Empirical Risk Study

## Scope and data audit

This is a descriptive study of the observed 15-minute day-ahead auction prices from **2026-05-01 through 2026-09-30**. The source repository is [https://github.com/whipeeer-creator/european-power-prices](https://github.com/whipeeer-creator/european-power-prices); it documents timestamps in UTC, EUR/MWh prices, and the source-zone field. The selected Italian market is **IT-North**, not an Italy-wide aggregate. The preserved raw data contain 153 daily CSV files.

The canonical observations reconcile to **87,072** rows (14,512 DE-LU, 14,512 AT, 14,512 FR, 14,512 ES, 14,512 PT, 14,512 IT-North); the persisted country summary also reconciles to the same total. Each market contributes 14,512 rows. All six selected source zones report 15-minute resolution for this sample; no hourly/quarter-hourly mixing or hourly aggregation is used. Units are EUR/MWh. Prices include valid negative observations. Duplicate keys and missing/non-finite price values: **0**.

The complete-grid expectation is 88,128 intervals (14,688 per market). The audit found 1,056 missing intervals total, in the same two partial UTC days for each market: 2026-06-30 and 2026-09-07, each missing 88 of 96 intervals from 00:00 through 21:45 UTC. The remaining eight intervals occur from 22:00 through 23:45 UTC. No missing value was filled. Returns, model transitions, and rolling statistics require consecutive 15-minute observations, so gaps reduce their usable sample sizes.

## Descriptive results

Spike frequency is defined as the proportion of **absolute consecutive 15-minute price changes strictly greater than that market's empirical 99th percentile of absolute changes**. This is a transparent tail-event definition, not a universal market-regulatory definition. Quantiles are empirical sample quantiles. Negative frequency is a share of observed intervals, not hours.

| bidding_zone | observation_count | mean_price_eur_mwh | std_price_eur_mwh | p05_price_eur_mwh | p50_price_eur_mwh | p95_price_eur_mwh | p99_price_eur_mwh | negative_price_frequency_pct | absolute_change_p99_eur_mwh | absolute_change_spike_count | absolute_change_spike_frequency_pct | rolling_24h_std_p95_eur_mwh |
| ------------ | ----------------- | ------------------ | ----------------- | ----------------- | ----------------- | ----------------- | ----------------- | ---------------------------- | --------------------------- | --------------------------- | ----------------------------------- | --------------------------- |
| DE-LU        | 14512             | 116.05             | 75.09             | -0.58             | 126.10            | 212.99            | 300.14            | 8.19                         | 53.85                       | 146                         | 1.01                                | 95.47                       |
| AT           | 14512             | 128.50             | 72.63             | 0.00              | 136.30            | 229.11            | 290.23            | 4.17                         | 77.61                       | 146                         | 1.01                                | 93.72                       |
| FR           | 14512             | 95.29              | 73.34             | -0.02             | 104.50            | 205.01            | 252.78            | 8.99                         | 55.05                       | 146                         | 1.01                                | 80.16                       |
| ES           | 14512             | 97.55              | 73.06             | -0.02             | 100.00            | 207.09            | 244.08            | 7.97                         | 38.01                       | 146                         | 1.01                                | 89.20                       |
| PT           | 14512             | 98.87              | 72.39             | -0.01             | 100.93            | 207.14            | 245.83            | 5.94                         | 38.24                       | 146                         | 1.01                                | 88.82                       |
| IT-North     | 14512             | 158.63             | 49.48             | 66.25             | 157.12            | 238.97            | 270.67            | 0.00                         | 44.58                       | 146                         | 1.01                                | 60.95                       |

The highest observed sample mean is IT-North at 158.63 EUR/MWh. The largest negative-price share is FR at 8.99% of observed intervals. The largest 95th percentile of the 24-hour rolling standard deviation is DE-LU at 95.47 EUR/MWh. These are sample descriptions, not causal attributions.

The 96-slot UTC intraday profile, including the observation count in each slot, is in `data/processed/intraday_profile.csv`. The rolling volatility series is in `data/processed/rolling_volatility_15m.csv`; rolling values are missing until a full 96-consecutive-interval window is available and resume after source gaps only after a full window exists.

## Cross-market correlations

The following matrices are Pearson correlations calculated pairwise on matching timestamps. The intraday profile shows UTC-slot variation, and fitted AR coefficients indicate serial persistence; the change matrix is included as a complementary short-horizon view. Pair sample sizes are saved alongside the matrices.

Highest off-diagonal price-level correlation: ES / PT = 0.9936. Highest off-diagonal consecutive-change correlation: ES / PT = 0.9569.

The correlation matrix files are `data/processed/cross_country_price_correlation.csv`, `data/processed/cross_country_price_correlation_n.csv`, `data/processed/cross_country_change_correlation.csv`, and `data/processed/cross_country_change_correlation_n.csv`.

## Stochastic model and diagnostics

The model is an **additive intraday-seasonal AR(1)**, fitted separately by market:

`P[t] - m[slot(t)] = a + phi * (P[t-1] - m[slot(t-1)]) + epsilon[t]`.

The 96 UTC quarter-hour seasonal means, intercept, autoregressive coefficient, and empirical innovations are estimated from the first 80% of observations in chronological order. Only adjacent observed 15-minute pairs enter fitting. Evaluation is one-step-ahead on the final 20%, using the immediately previous observed price; transitions crossing missing intervals are excluded. The additive form permits negative prices. Simulations resample centered in-sample innovations with replacement; they are illustrative conditional paths, not empirical observations or calibrated forecast distributions.

| bidding_zone | train_consecutive_transitions | holdout_one_step_predictions | ar_phi | stationary_phi_abs_lt_1 | holdout_rmse_eur_mwh | seasonal_baseline_rmse_eur_mwh | persistence_baseline_rmse_eur_mwh | holdout_residual_mean_eur_mwh | holdout_residual_std_eur_mwh | holdout_residual_acf_lag1 | holdout_residual_acf_lag96 |
| ------------ | ----------------------------- | ---------------------------- | ------ | ----------------------- | -------------------- | ------------------------------ | --------------------------------- | ----------------------------- | ---------------------------- | ------------------------- | -------------------------- |
| DE-LU        | 11607                         | 2902                         | 0.9725 | True                    | 13.51                | 74.98                          | 16.84                             | 0.93                          | 13.48                        | 0.253                     | 0.219                      |
| AT           | 11607                         | 2902                         | 0.9585 | True                    | 18.23                | 76.39                          | 23.08                             | 2.32                          | 18.09                        | -0.042                    | 0.141                      |
| FR           | 11607                         | 2902                         | 0.9743 | True                    | 12.84                | 78.32                          | 16.85                             | 1.44                          | 12.76                        | -0.099                    | 0.247                      |
| ES           | 11607                         | 2902                         | 0.9885 | True                    | 10.04                | 70.90                          | 13.27                             | 0.62                          | 10.03                        | 0.254                     | 0.494                      |
| PT           | 11607                         | 2902                         | 0.9890 | True                    | 10.30                | 71.11                          | 13.33                             | 0.59                          | 10.29                        | 0.251                     | 0.479                      |
| IT-North     | 11607                         | 2902                         | 0.9616 | True                    | 13.29                | 65.15                          | 15.79                             | 2.21                          | 13.11                        | -0.196                    | 0.263                      |

The AR(1) has lower holdout RMSE than persistence in 6 of 6 markets. The largest holdout residual excess kurtosis is 22.70 for DE-LU; the largest absolute 96-interval residual autocorrelation is 0.494 for ES. Residual skew, quantiles, all autocorrelations, and the individual one-step predictions are in `data/processed/model_holdout_diagnostics.csv` and `data/processed/model_holdout_predictions.csv`. These residual patterns indicate that the compact model should not be treated as a complete market-price generator.

## Historical price-change risk

Risk uses a **long position of 1 MWh** and each consecutive 15-minute change: `loss[t] = -1 MWh * (P[t] - P[t-1])`. Positive loss means the price fell; negative loss means a gain. VaR is the empirical confidence quantile of losses. Expected Shortfall is the arithmetic mean of the worst `ceil((1-confidence) * n)` observed losses, a discrete finite-sample tail convention. Sample sizes exclude transitions spanning gaps.

### 95% Confidence

| bidding_zone | sample_size | historical_var_eur | historical_es_eur |
| ------------ | ----------- | ------------------ | ----------------- |
| DE-LU        | 14509       | 20.53              | 34.24             |
| AT           | 14509       | 27.27              | 46.72             |
| FR           | 14509       | 23.01              | 35.23             |
| ES           | 14509       | 15.44              | 25.08             |
| PT           | 14509       | 15.29              | 25.07             |
| IT-North     | 14509       | 19.82              | 29.50             |

### 99% Confidence

| bidding_zone | sample_size | historical_var_eur | historical_es_eur |
| ------------ | ----------- | ------------------ | ----------------- |
| DE-LU        | 14509       | 39.67              | 62.15             |
| AT           | 14509       | 58.96              | 81.87             |
| FR           | 14509       | 42.60              | 57.25             |
| ES           | 14509       | 31.20              | 40.08             |
| PT           | 14509       | 31.20              | 40.96             |
| IT-North     | 14509       | 35.73              | 45.80             |

Stress scenarios are deterministic one-interval price shocks, not estimated probabilities. For a 1 MWh long exposure, price shocks of -250, -100, +100, and +250 EUR/MWh imply losses of +250, +100, -100, and -250 EUR, respectively. Full risk and scenario tables are `data/processed/price_change_risk.csv` and `data/processed/stress_scenarios.csv`.

## Figures and reproducibility

- `figures/empirical_price_quantiles.png` — observed median and 5th-95th percentile range.
- `figures/empirical_intraday_profile.png` — observed UTC quarter-hour profiles.
- `figures/cross_country_price_correlation.png` — pairwise price-level correlations.
- `figures/model_holdout_residuals.png` — residual distributions against observed holdout outcomes.
- `figures/simulated_vs_observed_DE-LU.png` — 20 explicitly simulated paths beside actual DE-LU holdout observations.
- `figures/historical_price_change_risk.png` — historical 15-minute loss distributions and 95% VaR.

Run `python -m src.research` with the project virtual environment to re-audit existing local data and regenerate the tables, figures, and this report. The command does not download or modify raw data. The offline test suite is `python tests/run_tests.py`.

## Limitations

This is a five-month descriptive sample with two common partial days, no weather/fuel/load/fundamental covariates, and no causal identification. The model is additive, uses a simple UTC intraday seasonal profile, and bootstraps innovations independently; it does not model volatility clustering, weekday effects, market coupling mechanisms, or structural climate-transition scenarios. VaR/ES describe a 1 MWh linear price exposure, not a trading portfolio with collateral, volume, basis, or transaction costs. Empirical, holdout-predicted, and simulated series are stored and labelled separately.
