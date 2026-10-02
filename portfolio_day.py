"""Domain model representing a full or partial delivery day of energy settlement periods."""

from datetime import date

from portfolio_calculations import (
    calculate_portfolio_periods,
    summarise_period_results,
)


class PortfolioDay:
    """A dated collection of period inputs, with calculations and totals."""

    def __init__(
        self,
        delivery_date: date,
        period_inputs: list[dict[str, int | float]],
    ) -> None:
        # Require a date, rather than a date string or a datetime with a time.
        if type(delivery_date) is not date:
            raise TypeError("delivery_date must be a datetime.date object.")
        if not period_inputs:
            raise ValueError("At least one settlement period is required.")

        self.delivery_date = delivery_date

        # Copy each flat input dictionary so later edits to the original list
        # or its records do not silently alter this object's inputs.


        self._period_inputs = [period.copy() for period in period_inputs]
        self._validate_period_order()

    def _validate_period_order(self) -> None:
        """Reject invalid identifiers, duplicates and decreasing order."""
        previous_number = 0

        for period in self._period_inputs:
            number = period["settlement_period"]

            # Exact int check also rejects booleans and numbers such as 25.5.
            if type(number) is not int:
                raise TypeError("Settlement period numbers must be integers.")
            if not 1 <= number <= 48:
                raise ValueError("Settlement period numbers must be between 1 and 48.")
            if number <= previous_number:
                raise ValueError(
                    "Settlement periods must be unique and in increasing order."
                )

            previous_number = number

    @property
    def period_count(self) -> int:
        """Return the total count of registered settlement periods."""
        return len(self._period_inputs)

    def calculate_results(self) -> list[dict[str, float | str]]:
        """Compute imbalance and market outcome records for each contained period."""
        return calculate_portfolio_periods(self._period_inputs)

    def calculate_totals(self) -> dict[str, float]:
        """Aggregate calculated metrics across all periods without netting time steps."""

        results = self.calculate_results()
        return summarise_period_results(results)