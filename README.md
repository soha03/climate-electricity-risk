# Stochastic Electricity Market Risk under Climate Transition Scenarios

## Research Objective

This project investigates how renewable generation, electricity demand, cross-border market conditions and climate-transition uncertainty influence European electricity markets and price risk.

The project begins with empirical analysis of day-ahead electricity prices and will progressively develop towards statistical modelling, stochastic simulation and quantitative risk measurement.

## Phase 1: European Electricity Market Analysis

The initial study compares six European markets:

- Germany
- Austria
- France
- Spain
- Portugal
- Italy

**Initial study period:** May to September 2026, subject to data availability.

Planned analysis includes:

- Hourly and monthly electricity-price profiles
- Midday-to-evening price spreads
- Negative-price frequency and price volatility
- Cross-country price differences
- Renewable generation, electricity demand and residual load
- Cross-border electricity flows and market structure

Italian bidding zones will be considered explicitly rather than assuming a single uniform national price.

## Phase 2: Market Drivers

The analysis will investigate relationships between electricity prices and renewable generation, demand, generation mix, cross-border exchanges, fuel prices, carbon prices and other relevant market conditions.

Observed associations will not automatically be interpreted as causal relationships.

## Phase 3: Stochastic Modelling and Risk

Subject to data quality and empirical findings, subsequent work will explore:

- Seasonality and mean reversion
- Volatility clustering and extreme price events
- Models accommodating zero and negative electricity prices
- Monte Carlo simulation and price-risk measurement
- Value at Risk (VaR) and Expected Shortfall
- Flexibility and battery-storage scenarios

## Data Sources

- [ENTSO-E Transparency Platform](https://transparency.entsoe.eu/)
- [SMARD](https://www.smard.de/en/)

Data sources, market definitions, timestamps, units, missing observations and processing decisions will be documented.

## Technology

Python, NumPy, pandas, Matplotlib and automated testing. Additional statistical and modelling libraries will be introduced when required.

## Research Principles

- Reproducible data pipelines
- Transparent assumptions and validation
- Separation of raw and processed data
- Empirical conclusions grounded in observed data
- Model selection justified by market characteristics
- Synthetic data used for software testing only, never presented as real market findings

## Current Status

The initial project structure, price-analysis functions and basic tests have been created. Real market data acquisition and empirical validation remain in progress.
