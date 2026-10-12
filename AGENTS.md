# Research Project Instructions

- Preserve all files and Git history. Do not reset, rebase, merge, or delete existing data unless explicitly requested.
- Treat `data/raw/source_download/` as the preserved source input. Do not download again during analysis unless the files are missing or fail validation.
- Use `data/processed/day_ahead_prices.csv` as the empirical canonical input and verify it against raw source rows before reporting findings.
- The current sample contains six 15-minute zones: DE-LU, AT, FR, ES, PT, and IT-North. The canonical validator uppercases bidding-zone strings; normalize keys when joining.
- Timestamps are UTC interval starts and prices are EUR/MWh. Negative prices are valid. Never fill missing intervals silently or mix hourly and quarter-hourly products.
- For changes, rolling windows, and model transitions, require exact consecutive 15-minute timestamps. A gap is not a zero price or an adjacent return.
- Keep observed, holdout-predicted, and simulated data clearly labelled and stored separately. Synthetic fixtures and simulated paths are not empirical observations.
- Reproduce the empirical report from the project root with `.\.venv\Scripts\python.exe -m src.research` and run tests with `.\.venv\Scripts\python.exe .\tests\run_tests.py`.
- Report sample sizes, date coverage, missing intervals, model diagnostics, risk units, position sign conventions, and limitations with every result.
