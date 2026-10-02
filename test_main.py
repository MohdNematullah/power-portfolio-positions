"""Test suite validating portfolio calculations, sample generators, and price shifting."""

import pytest

from portfolio_calculations import (
    calculate_portfolio_period,
    calculate_portfolio_periods,
    summarise_period_results,
)
from sample_data import generate_sample_day
from price_examples import shift_wholesale_prices


def test_short_portfolio_cash_flow() -> None:
    """Validate calculation metrics for an isolated period facing a generation shortage."""

    # Inputs for this test.
    wind_mwh = 8.0
    solar_mwh = 2.0
    demand_mwh = 12.0
    price_gbp_per_mwh = 80.0

    result = calculate_portfolio_period(
        wind_mwh=wind_mwh,
        solar_mwh=solar_mwh,
        demand_mwh=demand_mwh,
        price_gbp_per_mwh=price_gbp_per_mwh,
    )

    # Compare with results established by hand before running the test.
    # 10 MWh generation; 12 MWh consumption; buy the 2 MWh shortage.
    # A 160 GBP purchase and no sale . Ie: -160 GBP net cash flow.
    # For numbers, allow only a tiny absolute floating-point tolerance.
    assert result["total_generation_mwh"] == pytest.approx(10.0, rel=0, abs=1e-9)
    assert result["net_position_mwh"] == pytest.approx(-2.0, rel=0, abs=1e-9)
    assert result["position"] == "SHORT"
    assert result["purchase_mwh"] == pytest.approx(2.0, rel=0, abs=1e-9)
    assert result["sale_mwh"] == pytest.approx(0.0, rel=0, abs=1e-9)
    assert result["purchase_cost_gbp"] == pytest.approx(160.0, rel=0, abs=1e-9)
    assert result["sale_revenue_gbp"] == pytest.approx(0.0, rel=0, abs=1e-9)
    assert result["net_market_cash_flow_gbp"] == pytest.approx(
        -160.0, rel=0, abs=1e-9
    )

def test_three_period_results_and_totals() -> None:
    """Verify sequential batch execution and aggregate summation over three periods."""
    period_inputs: list[dict[str, int | float]] = [
        {
            "settlement_period": 25,
            "wind_mwh": 8.0,
            "solar_mwh": 2.0,
            "demand_mwh": 12.0,
            "price_gbp_per_mwh": 80.0,
        },
        {
            "settlement_period": 26,
            "wind_mwh": 12.0,
            "solar_mwh": 2.0,
            "demand_mwh": 12.0,
            "price_gbp_per_mwh": 100.0,
        },
        {
            "settlement_period": 27,
            "wind_mwh": 10.0,
            "solar_mwh": 2.0,
            "demand_mwh": 12.0,
            "price_gbp_per_mwh": 60.0,
        },
    ]

    results = calculate_portfolio_periods(period_inputs)

    assert len(results) == 3
    assert [r["settlement_period"] for r in results] == [25, 26, 27]
    assert [r["position"] for r in results] == ["SHORT", "LONG", "BALANCED"]

    # Check each period, so incorrect rows cannot be hidden by the totals.
    expected_by_period = {
        "total_generation_mwh": [10.0, 14.0, 12.0],
        "net_position_mwh": [-2.0, 2.0, 0.0],
        "purchase_mwh": [2.0, 0.0, 0.0],
        "sale_mwh": [0.0, 2.0, 0.0],
        "price_gbp_per_mwh": [80.0, 100.0, 60.0],
        "purchase_cost_gbp": [160.0, 0.0, 0.0],
        "sale_revenue_gbp": [0.0, 200.0, 0.0],
        "net_market_cash_flow_gbp": [-160.0, 200.0, 0.0],
    }
    for field, expected_values in expected_by_period.items():
        actual_values = [result[field] for result in results]
        assert actual_values == pytest.approx(
            expected_values, rel=0, abs=1e-9
        ), field

    totals = summarise_period_results(results)

    expected_totals = {
        "wind_mwh": 30.0,
        "solar_mwh": 6.0,
        "demand_mwh": 36.0,
        "total_generation_mwh": 36.0,
        "net_position_mwh": 0.0,
        "purchase_mwh": 2.0,
        "sale_mwh": 2.0,
        "purchase_cost_gbp": 160.0,
        "sale_revenue_gbp": 200.0,
        "net_market_cash_flow_gbp": 40.0,
    }
    assert totals == pytest.approx(expected_totals, rel=0, abs=1e-9)

def test_sample_day_contains_all_48_periods() -> None:
    """Ensure the sample data generator produces 48 sequential settlement intervals."""
    inputs = generate_sample_day(seed=42)
    numbers = [period["settlement_period"] for period in inputs]

    # Equality checks the count, identifiers, uniqueness and order together.
    assert numbers == list(range(1, 49))

def test_sample_day_is_reproducible() -> None:
    """Ensure seeded pseudo-random data output produces consistent outcomes."""
    first_run = generate_sample_day(seed=42)
    second_run = generate_sample_day(seed=42)

    assert first_run == second_run

def test_positive_zero_and_negative_price_cash_flows() -> None:
    """Verify that settlement cash flows behave correctly across multiple price environments."""
    # Wind MWh, price GBP/MWh, purchase cost GBP, sale revenue GBP, net cash GBP.
    cases = [
        (8.0, 80.0, 160.0, 0.0, -160.0),
        (8.0, 0.0, 0.0, 0.0, 0.0),
        (8.0, -20.0, -40.0, 0.0, 40.0),
        (12.0, 80.0, 0.0, 160.0, 160.0),
        (12.0, 0.0, 0.0, 0.0, 0.0),
        (12.0, -20.0, 0.0, -40.0, -40.0),
    ]

    for wind, price, expected_cost, expected_revenue, expected_cash in cases:
        result = calculate_portfolio_period(
            wind_mwh=wind,
            solar_mwh=2.0,
            demand_mwh=12.0,
            price_gbp_per_mwh=price,
        )
        actual_amounts = (
            result["purchase_cost_gbp"],
            result["sale_revenue_gbp"],
            result["net_market_cash_flow_gbp"],
        )
        assert actual_amounts == pytest.approx(
            (expected_cost, expected_revenue, expected_cash), rel=0, abs=1e-9
        ), f"wind={wind}, price={price}"



def test_price_shift_preserves_inputs_and_changes_cash_flow() -> None:
    """Ensure price adjustment retains core volume invariants while modifying cash metrics."""
    original = [{
        "settlement_period": 25,
        "wind_mwh": 8.0,
        "solar_mwh": 2.0,
        "demand_mwh": 12.0,
        "price_gbp_per_mwh": 80.0,
    }]
    shifted = shift_wholesale_prices(original, 20.0)

    assert original[0]["price_gbp_per_mwh"] == 80.0
    assert shifted[0]["price_gbp_per_mwh"] == 100.0
    for field in ("settlement_period", "wind_mwh", "solar_mwh", "demand_mwh"):
        assert shifted[0][field] == original[0][field]

    result = calculate_portfolio_periods(shifted)[0]
    assert result["purchase_mwh"] == pytest.approx(2.0)
    assert result["net_market_cash_flow_gbp"] == pytest.approx(-200.0)