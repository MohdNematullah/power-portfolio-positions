"""Demonstration scenarios and stress testing for price sensitivity and cash-flow mechanics."""

from datetime import date
from math import isfinite

from portfolio_calculations import calculate_portfolio_period
from portfolio_day import PortfolioDay
from sample_data import generate_sample_day


def show_single_period_examples() -> None:
    """Display portfolio cash-flow response across discrete price and wind variations."""
    solar_mwh: float = 3.0
    demand_mwh: float = 15.0

    # Wind of 10 MWh gives a 2 MWh shortage; 18 MWh gives a 6 MWh surplus.
    wind_examples = (10.0, 18.0)
    price_examples = (95.0, 0.0, -15.0)  # GBP/MWh, not customer tariffs.

    print("CONTROLLED PRICE EXAMPLES: ONE HALF-HOUR")
    print("Alternative cases, not six consecutive settlement periods.")
    print(f"Solar PV: {solar_mwh:.2f} MWh | Customer consumption: {demand_mwh:.2f} MWh")
    print("Position is measured BEFORE the model's purchase or sale.")
    print()
    print(
        f"{'Position':<8} {'Price GBP/MWh':>14} "
        f"{'Buy MWh':>9} {'Sell MWh':>10} "
        f"{'Net cash GBP':>15} {'Cash flow':>10}"
    )

    for wind_mwh in wind_examples:
        for price_gbp_per_mwh in price_examples:
            result = calculate_portfolio_period(
                wind_mwh=wind_mwh,
                solar_mwh=solar_mwh,
                demand_mwh=demand_mwh,
                price_gbp_per_mwh=price_gbp_per_mwh,
            )

            cash_flow_gbp = float(result["net_market_cash_flow_gbp"])
            if cash_flow_gbp > 0.0:
                direction = "INFLOW"
            elif cash_flow_gbp < 0.0:
                direction = "OUTFLOW"
            else:
                direction = "ZERO"

            print(
                f"{result['position']:<8} {price_gbp_per_mwh:>14.2f} "
                f"{result['purchase_mwh']:>9.2f} "
                f"{result['sale_mwh']:>10.2f} "
                f"{cash_flow_gbp:>+15.2f} {direction:>10}"
            )



def shift_wholesale_prices(
    period_inputs: list[dict[str, int | float]],
    shift_gbp_per_mwh: float,
) -> list[dict[str, int | float]]:
    """Uniformly adjust wholesale power prices across an entire set of period inputs."""
    if type(shift_gbp_per_mwh) not in (int, float):
        raise TypeError("The price shift must be a number.")
    if not isfinite(shift_gbp_per_mwh):
        raise ValueError("The price shift must be finite.")



    shifted_inputs: list[dict[str, int | float]] = []
    for period in period_inputs:
        # Each record is flat, so copying its dictionary is sufficient here.
        updated_period = period.copy()
        updated_period["price_gbp_per_mwh"] = (
            period["price_gbp_per_mwh"] + shift_gbp_per_mwh
        )
        shifted_inputs.append(updated_period)

    return shifted_inputs


def show_daily_price_sensitivity() -> None:
    """Evaluate financial variations resulting from parallel wholesale price curve shifts."""
    delivery_date = date(2026, 9, 1)
    baseline_inputs = generate_sample_day(seed=42)
    baseline_day = PortfolioDay(delivery_date, baseline_inputs)
    baseline_totals = baseline_day.calculate_totals()
    baseline_cash = baseline_totals["net_market_cash_flow_gbp"]

    # Every shift is relative to the ORIGINAL prices, not the previous case.
    cases = (("Baseline", 0.0), ("Prices lower", -25.0), ("Prices higher", 25.0))

    print("DAILY PRICE SENSITIVITY: 48 SETTLEMENT PERIODS")
    print(f"Delivery date: {delivery_date.isoformat()} | Example-data seed: 42")
    print("Same electricity quantities. Alternative prices for the same day.")
    print()
    print(
        f"{'Case':<14} {'Shift GBP/MWh':>14} {'Buy MWh':>9} "
        f"{'Sell MWh':>10} {'Net cash GBP':>15} {'Change GBP':>13}"
    )


    for label, shift in cases:
        scenario_inputs = shift_wholesale_prices(baseline_inputs, shift)
        scenario_day = PortfolioDay(delivery_date, scenario_inputs)
        totals = scenario_day.calculate_totals()
        cash = totals["net_market_cash_flow_gbp"]
        change_from_baseline = cash - baseline_cash

        print(
            f"{label:<14} {shift:>+14.2f} {totals['purchase_mwh']:>9.2f} "
            f"{totals['sale_mwh']:>10.2f} {cash:>+15.2f} "
            f"{change_from_baseline:>+13.2f}"
        )


def main() -> None:
    """Execute isolated period evaluations and aggregate daily market sensitivity runs."""
    show_single_period_examples()
    print()
    show_daily_price_sensitivity()


if __name__ == "__main__":
    main()