"""Plotting utilities for exploratory electricity-market analysis."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def plot_price_series(df: pd.DataFrame, output_path: str | Path | None = None, title: str = "Electricity price time series"):
    """Create a simple time-series plot if a real dataset exists."""
    if df.empty:
        raise ValueError("A non-empty dataset is required for plotting.")
    chart = df.sort_values("timestamp_utc").copy()
    chart = chart.set_index("timestamp_utc")
    fig, ax = plt.subplots(figsize=(12, 5))
    for country in sorted(chart["country_code"].unique()):
        subset = chart[chart["country_code"] == country]
        ax.plot(subset.index, subset["price_eur_mwh"], label=country, alpha=0.8)
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
