"""Core mathematical formulas for wholesale energy settlement and position accounting."""


def calculate_portfolio_period(
    wind_mwh: float,
    solar_mwh: float,
    demand_mwh: float,
    price_gbp_per_mwh: float,
) -> dict[str, float | str]:
    """Calculate net position imbalances and resultant trading cash flows for a settlement period."""
    # All energy quantities refer to the SAME half-hour settlement period.
    total_generation_mwh = wind_mwh + solar_mwh
    net_position_mwh = total_generation_mwh - demand_mwh

    # Calculate the position BEFORE the model's wholesale market trade.
    if net_position_mwh > 0.0:
        position = "LONG"
        purchase_mwh = 0.0
        sale_mwh = net_position_mwh
    elif net_position_mwh < 0.0:
        position = "SHORT"
        purchase_mwh = -net_position_mwh
        sale_mwh = 0.0
    else:
        position = "BALANCED"
        purchase_mwh = 0.0
        sale_mwh = 0.0

    # Preserve the cash-flow formulas from Lecture 2.3.
    # At negative prices, purchase cost or sale revenue can be negative.
    purchase_cost_gbp = purchase_mwh * price_gbp_per_mwh
    sale_revenue_gbp = sale_mwh * price_gbp_per_mwh
    net_market_cash_flow_gbp = sale_revenue_gbp - purchase_cost_gbp

    # Return labelled values so the report and tests can use the same results.
    # Net market cash flow is NOT the company's complete profit or loss.
    return {
        "wind_mwh": wind_mwh,
        "solar_mwh": solar_mwh,
        "demand_mwh":  demand_mwh,
        "price_gbp_per_mwh": price_gbp_per_mwh,
        "total_generation_mwh": total_generation_mwh,
        "net_position_mwh": net_position_mwh,
        "position": position,
        "purchase_mwh": purchase_mwh,
        "sale_mwh": sale_mwh,
        "purchase_cost_gbp": purchase_cost_gbp,
        "sale_revenue_gbp": sale_revenue_gbp,
        "net_market_cash_flow_gbp": net_market_cash_flow_gbp,
    }


def calculate_portfolio_periods(
    period_inputs: list[dict[str, int | float]],
) -> list[dict[str, float | str]]:
    """Iteratively apply single-period calculation logic across multiple input records."""
    results: list[dict[str, float | str]] = []

    for period in period_inputs:
        result = calculate_portfolio_period(
            wind_mwh=period["wind_mwh"],
            solar_mwh=period["solar_mwh"],
            demand_mwh=period["demand_mwh"],
            price_gbp_per_mwh=period["price_gbp_per_mwh"],
        )
        # Keep the period identifier with the result it belongs to.
        result["settlement_period"] = period["settlement_period"]
        results.append(result)

    return results


def summarise_period_results(
    results: list[dict[str, float | str]],
) -> dict[str, float]:
    """Aggregate period-level metrics into cumulative portfolio totals."""

    totals = {
        "wind_mwh": 0.0,
        "solar_mwh": 0.0,
        "demand_mwh": 0.0,
        "total_generation_mwh": 0.0,
        "net_position_mwh": 0.0,
        "purchase_mwh": 0.0,
        "sale_mwh": 0.0,
        "purchase_cost_gbp": 0.0,
        "sale_revenue_gbp": 0.0,
        "net_market_cash_flow_gbp": 0.0,
    }

    for result in results:
        for field in totals:
            # Select numeric fields from our mixed numeric/text dictionary.
            totals[field] += float(result[field])


    return totals