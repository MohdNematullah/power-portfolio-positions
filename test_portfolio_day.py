"""Test suite validating boundary conditions and integrity checks on PortfolioDay collections."""

from datetime import date
import pytest
from portfolio_day import PortfolioDay

def example_inputs() -> list[dict[str, int | float]]:
    """Produce deterministic mock input dictionaries for unit validation."""
    return [
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


def test_portfolio_day_results_and_totals() -> None:
    """Verify that PortfolioDay calculates identical period results and cumulative totals."""
    day = PortfolioDay(date(2026, 9, 1), example_inputs())
    results = day.calculate_results()

    assert day.delivery_date == date(2026, 9, 1)
    assert day.period_count == 3
    assert [r["settlement_period"] for r in results] == [25, 26, 27]
    assert [r["position"] for r in results] == ["SHORT", "LONG", "BALANCED"]
    assert [r["net_market_cash_flow_gbp"] for r in results] == pytest.approx(
        [-160.0, 200.0, 0.0], rel=0, abs=1e-9
    )

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
    assert day.calculate_totals() == pytest.approx(
        expected_totals, rel=0, abs=1e-9
    )


def test_portfolio_day_rejects_empty_inputs() -> None:
    """Ensure instantiating PortfolioDay with empty records raises a ValueError."""
    with pytest.raises(ValueError, match="At least one"):
        PortfolioDay(date(2026, 9, 1), [])


def test_portfolio_day_rejects_duplicate_periods() -> None:
    """Ensure duplicate settlement period indices raise an exception."""
    inputs = example_inputs()
    inputs[1]["settlement_period"] = 25

    with pytest.raises(ValueError, match="unique and in increasing order"):
        PortfolioDay(date(2026, 9, 1), inputs)


def test_portfolio_day_rejects_wrong_order() -> None:
    """Ensure periods not provided in strictly increasing order trigger an error."""
    inputs = example_inputs()
    inputs.reverse()

    with pytest.raises(ValueError, match="unique and in increasing order"):
        PortfolioDay(date(2026, 9, 1), inputs)


def test_portfolio_day_rejects_out_of_range_periods() -> None:
    """Ensure period identifiers outside 1 to 48 trigger boundary errors."""
    for invalid_number in (0, 49):
        inputs = example_inputs()
        inputs[0]["settlement_period"] = invalid_number
        with pytest.raises(ValueError, match="between 1 and 48"):
            PortfolioDay(date(2026, 9, 1), inputs)


def test_portfolio_day_rejects_non_integer_periods() -> None:
    """Ensure floating-point numbers or boolean period indicators trigger type checks."""
    for invalid_number in (25.5, True):
        inputs = example_inputs()
        inputs[0]["settlement_period"] = invalid_number
        with pytest.raises(TypeError, match="must be integers"):
            PortfolioDay(date(2026, 9, 1), inputs)


def test_portfolio_day_requires_a_date_object() -> None:
    """Ensure passing strings instead of strict datetime.date objects raises a TypeError."""
    # Intentionally pass a wrong type to check runtime validation.
    with pytest.raises(TypeError, match="must be a datetime.date object"):
        PortfolioDay("2026-09-01", example_inputs())  # type: ignore[arg-type]


def test_portfolio_day_copies_its_input_records() -> None:
    """Verify internal encapsulation prevents external mutation of input dictionaries."""
    inputs = example_inputs()
    day = PortfolioDay(date(2026, 9, 1), inputs)
    inputs[0]["wind_mwh"] = 999.0
    inputs.clear()

    assert day.period_count == 3
    assert day.calculate_totals()["net_market_cash_flow_gbp"] == pytest.approx(
        40.0, rel=0, abs=1e-9
    )


def test_portfolio_day_allows_an_incomplete_day() -> None:
    """Verify that non-contiguous partial subsets of periods can still be computed."""
    inputs = example_inputs()
    day = PortfolioDay(date(2026, 9, 1), [inputs[0], inputs[2]])

    # Gaps are allowed. Completeness checking is a later modelling step.
    assert day.period_count == 2
    assert [r["settlement_period"] for r in day.calculate_results()] == [25, 27]
    assert day.calculate_totals()["net_market_cash_flow_gbp"] == pytest.approx(
        -160.0, rel=0, abs=1e-9
    )