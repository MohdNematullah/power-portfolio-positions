"""Time calculation and interval labelling for standard half-hourly market periods."""

from datetime import date, datetime, time, timedelta


def settlement_period_times(
    delivery_date: date,
    settlement_period: int,
) -> tuple[datetime, datetime]:
    """Calculate the bounding start and end timestamp objects for a settlement period."""



    # Validate this helper's arguments even when called without PortfolioDay.
    if type(delivery_date) is not date:
        raise TypeError("delivery_date must be a datetime.date object.")
    if type(settlement_period) is not int:
        raise TypeError("settlement_period must be an integer.")
    if not 1 <= settlement_period <= 48:
        raise ValueError("settlement_period must be between 1 and 48.")

    # Combine the supplied date with midnight, not the computer's current time.
    day_start = datetime.combine(delivery_date, time(0, 0))
    period_duration = timedelta(minutes=30)

    # Period numbering starts at 1, so period 1 has a zero-minute offset.
    start_time = day_start + (settlement_period - 1) * period_duration
    end_time = start_time + period_duration

    # Full datetimes preserve the date when the final period ends at midnight.
    return start_time, end_time


def settlement_period_label(
    delivery_date: date,
    settlement_period: int,
) -> str:
    """Format and return a readable HH:MM-HH:MM window descriptor string."""
    start_time, end_time = settlement_period_times(
        delivery_date, settlement_period
    )

    # %H gives the 24-hour clock hour. %M gives the minutes.
    label = f"{start_time:%H:%M}-{end_time:%H:%M}"


    if end_time.date() != start_time.date():
        label += " (+1 day)"

    return label