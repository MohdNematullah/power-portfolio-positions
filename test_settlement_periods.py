"""Integration and unit tests verifying period timing calculations, labels, and full report execution."""

from datetime import date, datetime, timedelta
from pathlib import Path
import pytest
import csv

from main import main
from settlement_periods import settlement_period_label, settlement_period_times
from portfolio_io import load_portfolio_inputs_csv, save_portfolio_inputs_csv
from sample_data import generate_sample_day


def test_first_settlement_period_times() -> None:
    start_time, end_time = settlement_period_times(date(2026, 9, 1), 1)

    assert start_time == datetime(2026, 9, 1, 0, 0)
    assert end_time == datetime(2026, 9, 1, 0, 30)
    assert settlement_period_label(date(2026, 9, 1), 1) == "00:00-00:30"


def test_existing_period_times_and_labels() -> None:
    # Fixed expectations for the three records already used in main.py.
    expected = [
        (25, datetime(2026, 9, 1, 12, 0), datetime(2026, 9, 1, 12, 30),
         "12:00-12:30"),
        (26, datetime(2026, 9, 1, 12, 30), datetime(2026, 9, 1, 13, 0),
         "12:30-13:00"),
        (27, datetime(2026, 9, 1, 13, 0), datetime(2026, 9, 1, 13, 30),
         "13:00-13:30"),
    ]
    for number, expected_start, expected_end, expected_label in expected:
        assert settlement_period_times(date(2026, 9, 1), number) == (
            expected_start, expected_end
        )
        assert settlement_period_label(date(2026, 9, 1), number) == expected_label


def test_last_period_ends_on_next_date() -> None:
    start_time, end_time = settlement_period_times(date(2026, 9, 1), 48)

    assert start_time == datetime(2026, 9, 1, 23, 30)
    assert end_time == datetime(2026, 9, 2, 0, 0)
    assert end_time - start_time == timedelta(minutes=30)
    assert settlement_period_label(date(2026, 9, 1), 48) == (
        "23:30-00:00 (+1 day)"
    )


def test_last_period_rolls_into_next_year() -> None:
    start_time, end_time = settlement_period_times(date(2026, 12, 31), 48)

    assert start_time == datetime(2026, 12, 31, 23, 30)
    assert end_time == datetime(2027, 1, 1, 0, 0)
    assert settlement_period_label(date(2026, 12, 31), 48) == (
        "23:30-00:00 (+1 day)"
    )


def test_all_periods_are_adjacent_and_half_hour_long() -> None:
    # Test the clock grid without generating any electricity or price data.
    previous_end = datetime(2026, 9, 1, 0, 0)

    for number in range(1, 49):
        start_time, end_time = settlement_period_times(date(2026, 9, 1), number)
        assert start_time == previous_end
        assert end_time - start_time == timedelta(minutes=30)
        previous_end = end_time

    assert previous_end == datetime(2026, 9, 2, 0, 0)


def test_rejects_out_of_range_periods() -> None:
    for number in (0, 49):
        with pytest.raises(ValueError, match="between 1 and 48"):
            settlement_period_times(date(2026, 9, 1), number)
        with pytest.raises(ValueError, match="between 1 and 48"):
            settlement_period_label(date(2026, 9, 1), number)


def test_rejects_invalid_period_types() -> None:
    # Wrong types are intentional here. Even 25.0 is not an int.
    for number in (25.0, 25.5, True, "25"):
        with pytest.raises(TypeError, match="must be an integer"):
            settlement_period_times(date(2026, 9, 1), number)  # type: ignore[arg-type]


def test_requires_a_date_object() -> None:
    # A date string or datetime is not the date-only object this helper requires.
    for invalid_date in ("2026-09-01", datetime(2026, 9, 1, 0, 0)):
        with pytest.raises(TypeError, match="must be a datetime.date object"):
            settlement_period_times(invalid_date, 25)  # type: ignore[arg-type]


def test_report_shows_time_labels(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    # Create a temporary input file, not a new project-data export.
    csv_path = tmp_path / "portfolio_inputs_2026-09-01.csv"
    original_inputs = generate_sample_day(seed=42)
    save_portfolio_inputs_csv(csv_path, date(2026, 9, 1), original_inputs)
    original_file = csv_path.read_bytes()

    loaded_date, loaded_inputs = load_portfolio_inputs_csv(csv_path)
    assert loaded_date == date(2026, 9, 1)
    assert loaded_inputs == original_inputs

    main(input_csv=csv_path, output_directory=tmp_path / "outputs")
    output = capsys.readouterr().out
    assert csv_path.read_bytes() == original_file  # The report must not overwrite it.

    assert "POWER PORTFOLIO: 48 SETTLEMENT PERIODS" in output
    assert "Delivery date: 2026-09-01" in output
    assert "SETTLEMENT PERIOD 1 | 00:00-00:30" in output
    assert "SETTLEMENT PERIOD 25 | 12:00-12:30" in output
    assert "SETTLEMENT PERIOD 26 | 12:30-13:00" in output
    assert "SETTLEMENT PERIOD 27 | 13:00-13:30" in output
    assert "SETTLEMENT PERIOD 48 | 23:30-00:00 (+1 day)" in output
    assert "TOTALS FOR THESE 48 PERIODS ONLY" in output
    assert "Total net market cash flow:" in output
    assert output.count("\nSETTLEMENT PERIOD ") == 48

    assert "Long periods: 30" in output
    assert "Short periods: 18" in output
    assert "Balanced periods: 0" in output
    assert "Volume-weighted purchase price: 115.15 GBP/MWh" in output
    assert "Volume-weighted sale price: 71.73 GBP/MWh" in output

    lines = csv_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 49  # One header plus 48 input records.
    assert lines[0] == (
        "delivery_date,settlement_period,wind_mwh,solar_mwh,"
        "demand_mwh,price_gbp_per_mwh"
    )
    assert lines[1].startswith("2026-09-01,1,")
    assert lines[-1].startswith("2026-09-01,48,")

    results_path = tmp_path / "outputs" / f"{csv_path.stem}_results.csv"
    with results_path.open("r", newline="", encoding="utf-8") as results_file:
        rows = list(csv.DictReader(results_file))

    assert [int(row["settlement_period"]) for row in rows] == list(range(1, 49))
    assert all(row["delivery_date"] == "2026-09-01" for row in rows)
    assert float(rows[0]["sale_mwh"]) == pytest.approx(5.81)
    exported_cash = sum(float(row["net_market_cash_flow_gbp"]) for row in rows)
    assert f"Total net market cash flow: {exported_cash:+.2f} GBP" in output

    chart_path = tmp_path / "outputs" / f"{csv_path.stem}_generation_demand.png"
    assert chart_path.is_file()
    assert chart_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")

    position_chart = tmp_path / "outputs" / f"{csv_path.stem}_positions.png"
    assert position_chart.is_file()
    assert position_chart.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")

    for suffix in ("prices", "cash_flows"):
        chart = tmp_path / "outputs" / f"{csv_path.stem}_{suffix}.png"
        assert chart.is_file()
        assert chart.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")