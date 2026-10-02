
# Power Portfolio Positions and Cash Flows

A modular Python model that links half-hourly electricity generation and customer consumption to wholesale market positions, required purchases or sales, and market cash flows.

> **Scope:** This is a position-and-cash-flow model for portfolio analysis and decision support. It is not a live trading system or a complete company P&L model.

## Overview

The model represents a power portfolio with:

- Wind generation
- Solar PV generation
- Customer electricity demand
- Wholesale electricity prices

For each of the 48 half-hour settlement periods in an ordinary day, the model:

1. Calculates total generation.
2. Compares generation with customer demand.
3. Classifies the portfolio as **LONG** (surplus) or **SHORT** (deficit).
4. Calculates the required wholesale purchase or sale.
5. Calculates the resulting market cash flow.
6. Produces daily totals, CSV results, and four visual reports.

## Model Logic

All generation and demand inputs are **energy quantities in MWh for one half-hour**. They are not MW power values.

```text
total_generation_mwh = wind_mwh + solar_mwh
net_position_mwh = total_generation_mwh - demand_mwh

purchase_mwh = max(-net_position_mwh, 0)
sale_mwh = max(net_position_mwh, 0)

purchase_cost_gbp = purchase_mwh * price_gbp_per_mwh
sale_revenue_gbp = sale_mwh * price_gbp_per_mwh

net_market_cash_flow_gbp = sale_revenue_gbp - purchase_cost_gbp

```

Transactions are settled independently for each period. This version has no storage, trading fees, or price-responsive generation/demand.

## Input Data

The CSV input contains six columns:

| Column | Description |
| --- | --- |
| `delivery_date` | Delivery date |
| `settlement_period` | Period number 1–48 |
| `wind_mwh` | Wind generation during the half-hour |
| `solar_mwh` | Solar PV generation during the half-hour |
| `demand_mwh` | Customer consumption during the half-hour |
| `price_gbp_per_mwh` | Assumed wholesale price |

The reference dataset is illustrative and uses reproducible sample inputs. Energy values must be finite and non-negative; negative electricity prices are supported.

## Reference Results

Results below correspond to the supplied reference input (`2026-09-01`, seed `42`) and are rounded for display.

| Metric | Value |
| --- | --- |
| Wind generation | 648.73 MWh |
| Solar PV generation | 96.00 MWh |
| Combined generation | 744.73 MWh |
| Customer consumption | 666.02 MWh |
| Pre-trade net position | +78.71 MWh |
| Wholesale purchases | 73.12 MWh |
| Wholesale sales | 151.83 MWh |
| Purchase cost | £8,419.88 |
| Sale revenue | £10,890.77 |
| **Net wholesale market cash flow** | **+£2,470.88** |
| Long / Short / Balanced periods | 30 / 18 / 0 |
| Volume-weighted purchase price | £115.15/MWh |
| Volume-weighted sale price | £71.73/MWh |

The largest physical shortage occurs in period 38 (9.37 MWh), while the largest cash outflow occurs in period 37 (-£1,182.06) due to elevated evening wholesale prices (£134.02/MWh).

## Visual Outputs

Running the main pipeline generates four charts:

* **Generation & Demand** — wind, solar, combined generation, and customer consumption.
* **Portfolio Positions** — LONG and SHORT positions before market trades.
* **Wholesale Prices** — assumed half-hourly price profile.
* **Market Cash Flows** — cash inflows and outflows by settlement period.

Outputs are saved in `outputs/`.

## Project Structure

```text
power_portfolio/
├── main.py
├── portfolio_calculations.py
├── portfolio_day.py
├── portfolio_io.py
├── portfolio_plots.py
├── settlement_periods.py
├── sample_data.py
├── price_examples.py
├── test_main.py
├── test_portfolio_day.py
├── test_settlement_periods.py
├── requirements.txt
├── README.md
├── data/
│   └── portfolio_inputs_2026-09-01.csv
└── outputs/

```

## Installation and Usage

Install dependencies:

```bash
pip install -r requirements.txt

```

Run the main analysis:

```bash
python main.py

```

Run price scenarios and sensitivity examples:

```bash
python price_examples.py

```

Run the automated tests:

```bash
pytest

```

## Limitations

This model intentionally represents a simplified portfolio cash-flow framework. It does not include:

* Battery storage or intertemporal optimization
* Trading or transaction fees
* Bid/offer spreads
* Forecast uncertainty
* Imbalance-price mechanisms
* Network constraints
* Curtailment
* Asset degradation
* Taxes or full company-level P&L
* Live market execution

It is therefore best treated as a transparent foundation for extending the model toward more advanced electricity-market and portfolio analysis.
