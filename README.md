# Stochastic Electricity Market Risk under Climate Transition Scenarios

## Research Project

This project investigates how climate transition and renewable-generation uncertainty affect the dynamics and financial risk of European electricity markets.

The project combines:

- stochastic modelling
- electricity-market analysis
- renewable-generation uncertainty
- climate-transition scenarios
- Monte Carlo simulation
- quantitative financial risk measurement

## Research Question

> How do renewable-generation uncertainty and climate-transition variables affect the dynamics and financial tail risk of European electricity prices?

## Motivation

The increasing penetration of variable renewable energy sources such as wind and solar changes the structure and uncertainty of electricity markets.

Electricity prices differ from many conventional financial assets because they can exhibit:

- strong seasonality
- mean reversion
- volatility clustering
- extreme price spikes
- negative prices
- dependence on weather and renewable generation

The project aims to develop a stochastic framework that captures these characteristics and examines their implications for financial risk.

## Research Framework

The project follows the transmission mechanism:

Climate and transition scenarios  
↓  
Renewable-generation uncertainty  
↓  
Electricity-market dynamics  
↓  
Stochastic electricity-price model  
↓  
Monte Carlo simulation  
↓  
Financial exposure  
↓  
VaR, Expected Shortfall and stress testing

## Methodology

The project will progressively investigate:

1. Statistical characteristics of European electricity prices
2. Price seasonality, volatility and extreme observations
3. Relationships between renewable generation and electricity prices
4. Stochastic models for electricity prices
5. Calibration of model parameters using market data
6. Monte Carlo simulation of electricity-price paths
7. Climate-transition scenario analysis
8. Financial exposure and portfolio risk
9. Value-at-Risk and Expected Shortfall
10. Potential hedging applications

## Data

The project will use publicly available data where possible, including:

- European electricity prices
- electricity demand
- wind generation
- solar generation
- natural gas prices
- European carbon allowance (EUA) prices
- climate-transition scenario data

All datasets and sources will be documented in the repository.

## Technology

### Programming

- Python
- Jupyter

### Main libraries

- NumPy
- Pandas
- SciPy
- Statsmodels
- Matplotlib

Additional libraries will be introduced as required by the research.

## Repository Structure

```text
climate-electricity-risk/
│
├── README.md
├── .gitignore
│
├── data/
│   ├── raw/
│   └── processed/
│
├── notebooks/
│
├── src/
│   ├── data/
│   ├── models/
│   ├── risk/
│   └── visualization/
│
├── tests/
│
└── figures/
