"""Plotting utilities for exploratory electricity-market analysis."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def plot_price_series(
    df: pd.DataFrame,
    output_path: str | Path | None = None,
    title: str = "Day-ahead price by bidding zone (15-minute, EUR/MWh)",
    interval_minutes: int = 15,
):
    """Plot observed prices by market, leaving missing intervals as visible gaps."""
    if df.empty:
        raise ValueError("A non-empty dataset is required for plotting.")
    if interval_minutes <= 0:
        raise ValueError("interval_minutes must be positive.")
    chart = df.sort_values("timestamp_utc").copy()
    label_column = "bidding_zone" if "bidding_zone" in chart.columns else "country_code"
    start = chart["timestamp_utc"].min().floor(f"{interval_minutes}min")
    end = chart["timestamp_utc"].max().floor(f"{interval_minutes}min")
    full_index = pd.date_range(start=start, end=end, freq=f"{interval_minutes}min")
    fig, ax = plt.subplots(figsize=(12, 5))
    for market in sorted(chart[label_column].unique()):
        subset = chart[chart[label_column] == market].set_index("timestamp_utc")
        prices = subset["price_eur_mwh"].reindex(full_index)
        ax.plot(full_index, prices, label=market, alpha=0.8)
    ax.set_title(title)
    ax.set_xlabel("Timestamp (UTC)")
    ax.set_ylabel("Price (EUR/MWh)")
    ax.legend(loc="best", fontsize="small")
    fig.tight_layout()
    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=150)
    plt.close(fig)
    return output_path


def plot_rolling_volatility(
    df: pd.DataFrame,
    output_path: str | Path | None = None,
    interval_minutes: int = 15,
    window_intervals: int = 96,
):
    """Plot a rolling 24-hour price-level standard deviation per market."""
    if df.empty:
        raise ValueError("A non-empty dataset is required for plotting.")
    if interval_minutes <= 0 or window_intervals <= 1:
        raise ValueError("interval_minutes must be positive and window_intervals must exceed 1.")
    chart = df.sort_values("timestamp_utc").copy()
    label_column = "bidding_zone" if "bidding_zone" in chart.columns else "country_code"
    start = chart["timestamp_utc"].min().floor(f"{interval_minutes}min")
    end = chart["timestamp_utc"].max().floor(f"{interval_minutes}min")
    full_index = pd.date_range(start=start, end=end, freq=f"{interval_minutes}min")
    fig, ax = plt.subplots(figsize=(12, 5))
    for market in sorted(chart[label_column].unique()):
        subset = chart[chart[label_column] == market].set_index("timestamp_utc")
        prices = subset["price_eur_mwh"].reindex(full_index)
        volatility = prices.rolling(window_intervals, min_periods=window_intervals).std()
        ax.plot(full_index, volatility, label=market, alpha=0.8)
    ax.set_title("24-hour rolling price volatility by bidding zone")
    ax.set_xlabel("Timestamp (UTC)")
    ax.set_ylabel("Rolling standard deviation (EUR/MWh)")
    ax.legend(loc="best", fontsize="small")
    fig.tight_layout()
    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=150)
    plt.close(fig)
    return output_path


def plot_distribution_by_country(df: pd.DataFrame, output_path: str | Path | None = None):
    """Box plot of price distributions by country, if enough valid observations exist."""
    if df.empty:
        raise ValueError("A non-empty dataset is required for plotting.")
    fig, ax = plt.subplots(figsize=(10, 6))
    df.boxplot(column="price_eur_mwh", by="country_code", ax=ax)
    ax.set_title("Electricity price distribution by country")
    ax.set_xlabel("Country")
    ax.set_ylabel("Price (EUR/MWh)")
    fig.tight_layout()
    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=150)
    plt.close(fig)
    return output_path


def plot_intraday_pattern(df: pd.DataFrame, output_path: str | Path | None = None):
    """Plot the average hour-of-day profile for each country."""
    if df.empty:
        raise ValueError("A non-empty dataset is required for plotting.")
    fig, ax = plt.subplots(figsize=(10, 5))
    hourly = df.assign(hour=df["timestamp_utc"].dt.hour)
    for country in sorted(hourly["country_code"].unique()):
        subset = hourly[hourly["country_code"] == country]
        mean_profile = subset.groupby("hour")["price_eur_mwh"].mean()
        ax.plot(mean_profile.index, mean_profile.values, label=country)
    ax.set_title("Average intraday price profile")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Price (EUR/MWh)")
    ax.legend()
    fig.tight_layout()
    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=150)
    plt.close(fig)
    return output_path
