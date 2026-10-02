"""CSV serialization and validation utilities for portfolio inputs and calculation outputs."""

import csv
from datetime import date
from pathlib import Path

from math import isfinite

def save_portfolio_inputs_csv(
    file_path: Path,
    delivery_date: date,
    period_inputs: list[dict[str, int | float]],
) -> None:
    """Export raw settlement period inputs to a standardized CSV format."""
    fieldnames = [
        "delivery_date",
        "settlement_period",
        "wind_mwh",
        "solar_mwh",
        "demand_mwh",
        "price_gbp_per_mwh",
    ]

    file_path.parent.mkdir(parents=True, exist_ok=True)

    # "w" replaces the existing file; it does not append another day's rows.
    # newline="" lets the csv module handle line endings correctly.
    with file_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for period in period_inputs:
            # Repeat the date so each record identifies both date and period.
            writer.writerow(
                {
                    "delivery_date": delivery_date.isoformat(),
                    "settlement_period": period["settlement_period"],
                    "wind_mwh": period["wind_mwh"],
                    "solar_mwh": period["solar_mwh"],
                    "demand_mwh": period["demand_mwh"],
                    "price_gbp_per_mwh": period["price_gbp_per_mwh"],
                }
            )


def load_portfolio_inputs_csv(
    file_path: Path,
) -> tuple[date, list[dict[str, int | float]]]:
    """Ingest, parse, and validate portfolio input records from a designated CSV file."""
    expected_columns = [
        "delivery_date",
        "settlement_period",
        "wind_mwh",
        "solar_mwh",
        "demand_mwh",
        "price_gbp_per_mwh",
    ]
    numeric_fields = expected_columns[2:]
    delivery_date: date | None = None
    period_inputs: list[dict[str, int | float]] = []

    # Read only.
    with file_path.open("r", newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        print(reader.fieldnames)
        if reader.fieldnames != expected_columns:
            raise ValueError("CSV columns must be: " + ", ".join(expected_columns))

        for record_number, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"CSV record {record_number}: expected six fields.")

            # CSV values arrive as text. Restore the date and numeric types.
            try:
                row_date = date.fromisoformat(row["delivery_date"].strip())
                period: dict[str, int | float] = {
                    "settlement_period": int(row["settlement_period"])
                }
                for field in numeric_fields:
                    period[field] = float(row[field])

            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"CSV record {record_number}: invalid date or numeric value."
                ) from exc

            if delivery_date is None:
                delivery_date = row_date
            elif row_date != delivery_date:
                raise ValueError("All CSV records must have the same delivery date.")

            # Small input checks at the file boundary. Negative prices are valid.
            if any(not isfinite(period[field]) for field in numeric_fields):
                raise ValueError(f"CSV record {record_number}: values must be finite.")
            if any(period[field] < 0.0 for field in numeric_fields[:3]):
                raise ValueError(f"CSV record {record_number}: energy cannot be negative.")

            period_inputs.append(period)

    if delivery_date is None:
        raise ValueError("The CSV contains no input records.")

    return delivery_date, period_inputs

def save_portfolio_results_csv(
    file_path: Path,
    delivery_date: date,
    results: list[dict[str, float | str]],
) -> None:
    """Export calculated settlement results and financial outputs to a CSV file."""
    fieldnames = [
        "delivery_date",
        "settlement_period",
        "wind_mwh",
        "solar_mwh",
        "demand_mwh",
        "price_gbp_per_mwh",
        "total_generation_mwh",
        "net_position_mwh",
        "position",
        "purchase_mwh",
        "sale_mwh",
        "purchase_cost_gbp",
        "sale_revenue_gbp",
        "net_market_cash_flow_gbp",
    ]

    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for result in results:
            row: dict[str, float | str] = {
                "delivery_date": delivery_date.isoformat()
            }
            # Copy existing results. Do not calculate a second version here.
            for field in fieldnames[1:]:
                row[field] = result[field]
            writer.writerow(row)