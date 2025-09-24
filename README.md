# Volatility-Aware Multi-Market Strategy

> Systematic trading strategy that sizes risk by volatility and trades across U.S. equities, crypto, and FX.

## Overview

This is a Python strategy for the QuantConnect Lean engine. It combines a trend-following entry stack with an ATR-based position sizing rule so each position contributes comparable risk. A portfolio-level exposure cap and macro regime gate aim to keep the book resilient during equity bear regimes.

This repository includes the full algorithm `main.py` and the accompanying paper with methodology, rationale, and notes on extensions.

## Strategy at a glance

- **Markets**
  - Equities (U.S.): curated list of liquid names
  - Crypto: `BTCUSD`, `ETHUSD`
  - FX: `GBPUSD`, `EURUSD`, `USDJPY`
- **Signals / filters**
  - Trend filter: dual _SuperTrend_ (e.g., 10/2.5 and 10/3.0) must both be below price for long entries
  - Momentum: `RSI(10)` > threshold (e.g., 55)
  - Trend confirmation: `EMA(100)` with price above it
  - Overextension guard: weekly TWAP multiple check to avoid buying stretched breakouts
  - Macro risk gate (equities): take stock longs only when SPY > EMA(200)
- **Sizing & risk**
  - ATR(14)-based volatility targeting; typical per-position bounds 5%–20% of equity
  - Portfolio exposure cap: ≤ 95% long exposure
  - Exit: close below both SuperTrends
- **Backtest defaults**
  - Dates: 2019-01-01 → 2025-01-01
  - Capital: \$100,000
  - Benchmark: SPY
  - Resolution: Daily

> Numbers above are defaults; tune them in `main.py` to match your experiments.

## Paper

[**Open the full paper (PDF)**](Volatility_Aware_Strategy.pdf)

## Quick start

### Option A — QuantConnect (cloud)

1. Create a new **Python** algorithm on QuantConnect.
2. Copy the contents of `main.py` into your project.
3. Set **Start**/**End** dates, then run a backtest.

### Option B — Lean CLI (local, Docker)

1. Install Docker and the **Lean CLI** (see QuantConnect docs).
2. Create or open a Lean project and place `main.py` in the algorithm folder.
3. Configure your project to reference `main.py`, then run:
   ```bash
   lean backtest "VolatilityShield"
   ```
