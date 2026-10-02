"""Orchestrate portfolio data ingestion, calculations, logging, and visual reporting."""


from portfolio_io import load_portfolio_inputs_csv, save_portfolio_results_csv
from pathlib import Path

from portfolio_day import PortfolioDay
from settlement_periods import settlement_period_label
from portfolio_plots import save_generation_demand_chart, save_position_chart, save_price_cash_flow_charts

def main(
    input_csv: Path | None = None,
    output_directory: Path | None = None,
) -> None:
    """Execute end-to-end portfolio workflow, summary metrics, and artifact export."""

    if input_csv is None:
        input_csv = (
            Path(__file__).resolve().parent
            / "data"
            / "portfolio_inputs_2026-09-01.csv"
        )

    # The contents of the CSV supply both the date and the energy/price inputs.
    # A missing file raises an error.

    delivery_date, period_inputs = load_portfolio_inputs_csv(input_csv)




    portfolio_day = PortfolioDay(
        delivery_date=delivery_date,
        period_inputs=period_inputs,
    )

    results = portfolio_day.calculate_results()

    period_numbers = [result["settlement_period"] for result in results]
    # previous versions allowed the model to have less than 48 periods. Now only 48.
    if period_numbers != list(range(1, 49)):
        raise ValueError(
            "This full-day report requires settlement periods 1 to 48 in order."
        )


    totals = portfolio_day.calculate_totals()

    print(f"POWER PORTFOLIO: {portfolio_day.period_count} SETTLEMENT PERIODS")
    print(f"Delivery date: {portfolio_day.delivery_date.isoformat()}")
    print(f"Input CSV: {input_csv}")

    for result in results:
        # PortfolioDay has already checked that this identifier is an integer.
        period_number = int(result["settlement_period"])
        period_label = settlement_period_label(
            portfolio_day.delivery_date, period_number
        )

        print()
        print(f"SETTLEMENT PERIOD {period_number} | {period_label}")
        print(
            f"Wind: {result['wind_mwh']:.2f} MWh | "
            f"Solar PV: {result['solar_mwh']:.2f} MWh"
        )
        print(
            f"Generation: {result['total_generation_mwh']:.2f} MWh | "
            f"Customer consumption: {result['demand_mwh']:.2f} MWh"
        )
        print(
            f"Position before market trades: {result['position']} "
            f"({result['net_position_mwh']:+.2f} MWh)"
        )
        print(
            f"Required purchase: {result['purchase_mwh']:.2f} MWh | "
            f"Required sale: {result['sale_mwh']:.2f} MWh"
        )
        print(f"Wholesale price: {result['price_gbp_per_mwh']:.2f} GBP/MWh")
        print(
            f"Purchase cost: {result['purchase_cost_gbp']:.2f} GBP | "
            f"Sale revenue: {result['sale_revenue_gbp']:.2f} GBP"
        )
        print(f"Net market cash flow: {result['net_market_cash_flow_gbp']:+.2f} GBP")

    print()
    print(f"TOTALS FOR THESE {len(results)} PERIODS ONLY")
    print(f"Wind generation: {totals['wind_mwh']:.2f} MWh")
    print(f"Solar PV generation: {totals['solar_mwh']:.2f} MWh")
    print(f"Total generation: {totals['total_generation_mwh']:.2f} MWh")
    print(f"Customer consumption: {totals['demand_mwh']:.2f} MWh")
    print(f"Sum of pre-trade net positions: {totals['net_position_mwh']:+.2f} MWh")
    print(f"Total purchases: {totals['purchase_mwh']:.2f} MWh")
    print(f"Total sales: {totals['sale_mwh']:.2f} MWh")
    print(f"Total purchase cost: {totals['purchase_cost_gbp']:.2f} GBP")
    print(f"Total sale revenue: {totals['sale_revenue_gbp']:.2f} GBP")
    print(f"Total net market cash flow: {totals['net_market_cash_flow_gbp']:+.2f} GBP")

    positions = [result["position"] for result in results]
    print()
    print("DAILY INTERPRETATION")
    print(f"Long periods: {positions.count('LONG')}")
    print(f"Short periods: {positions.count('SHORT')}")
    print(f"Balanced periods: {positions.count('BALANCED')}")

    #Monetary totals divided by traded MWh give volume-weighted prices.
    # Use unrounded totals for the division. Round only the displayed values.
    if totals["purchase_mwh"] > 0.0:
        average_purchase_price = totals["purchase_cost_gbp"] / totals["purchase_mwh"]
        print(
            f"Volume-weighted purchase price: {average_purchase_price:.2f} GBP/MWh"
        )
    else:
        print("Volume-weighted purchase price: N/A (no purchases)")

    if totals["sale_mwh"] > 0.0:
        average_sale_price = totals["sale_revenue_gbp"] / totals["sale_mwh"]
        print(f"Volume-weighted sale price: {average_sale_price:.2f} GBP/MWh")
    else:
        print("Volume-weighted sale price: N/A (no sales)")

    if output_directory is None:
        output_directory = Path(__file__).resolve().parent / "outputs"

    output_csv = output_directory / f"{input_csv.stem}_results.csv"
    if output_csv.exists() and output_csv.samefile(input_csv):
        raise ValueError("The results CSV must not overwrite the input CSV.")

    save_portfolio_results_csv(
        file_path=output_csv,
        delivery_date=portfolio_day.delivery_date,
        results=results,
    )
    print()
    print(f"Saved {len(results)} result records to: {output_csv}")

    chart_path = output_directory / f"{input_csv.stem}_generation_demand.png"
    if chart_path.exists() and chart_path.samefile(input_csv):
        raise ValueError("The chart must not overwrite the input CSV.")

    save_generation_demand_chart(
        file_path=chart_path,
        delivery_date=portfolio_day.delivery_date,
        results=results,
    )
    print(f"Saved generation and consumption chart to: {chart_path}")

    position_chart_path = output_directory / f"{input_csv.stem}_positions.png"
    if position_chart_path.exists() and position_chart_path.samefile(input_csv):
        raise ValueError("The position chart must not overwrite the input CSV.")

    save_position_chart(
        file_path=position_chart_path,
        delivery_date=portfolio_day.delivery_date,
        results=results,
    )
    print(f"Saved portfolio position chart to: {position_chart_path}")

    price_chart_path = output_directory / f"{input_csv.stem}_prices.png"
    cash_flow_chart_path = output_directory / f"{input_csv.stem}_cash_flows.png"
    for path in (price_chart_path, cash_flow_chart_path):
        if path.exists() and path.samefile(input_csv):
            raise ValueError("A chart must not overwrite the input CSV.")

    save_price_cash_flow_charts(
        price_path=price_chart_path,
        cash_flow_path=cash_flow_chart_path,
        delivery_date=portfolio_day.delivery_date,
        results=results,
    )
    print(f"Saved wholesale-price chart to: {price_chart_path}")
    print(f"Saved market-cash-flow chart to: {cash_flow_chart_path}")

if __name__ == "__main__":
    main()