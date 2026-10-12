import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Synthetic hourly electricity prices: setup test only
rng = np.random.default_rng(42)
n = 24 * 365
time = pd.date_range("2025-01-01", periods=n, freq="h")

daily = 15 * np.sin(2 * np.pi * time.hour / 24)
seasonal = 10 * np.cos(2 * np.pi * time.dayofyear / 365)
prices = 80 + daily + seasonal + rng.normal(0, 12, n)

df = pd.DataFrame({
    "timestamp": time,
    "price_eur_mwh": prices
})

print("\nPRICE SUMMARY")
print(df["price_eur_mwh"].describe())

daily_prices = df.set_index("timestamp")["price_eur_mwh"].resample("D").mean()
daily_prices.plot(figsize=(12, 5), title="Simulated Daily Electricity Prices")
plt.xlabel("Date")
plt.ylabel("Price (EUR/MWh)")
plt.tight_layout()
plt.savefig("daily_prices.png", dpi=150)
print("\nChart saved to daily_prices.png")
plt.show()
