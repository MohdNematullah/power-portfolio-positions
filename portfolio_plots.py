"""Data visualization modules for half-hourly generation, positions, and market pricing."""

from datetime import date
from pathlib import Path
import matplotlib.pyplot as plt

def save_generation_demand_chart(
    file_path: Path,
    delivery_date: date,
    results: list[dict[str, float | str]],
) -> None:
    """Generate and save step plots showing power generation profiles against customer demand."""
    period_numbers = [result["settlement_period"] for result in results]
    if period_numbers != list(range(1, 49)):
        raise ValueError("This chart requires settlement periods 1 to 48 in order.")

    # 49 boundaries enclose 48 half-hours: 0, 0.5, ..., 23.5, 24.
    # These x-coordinates are hours after midnight on our ordinary sample day.
    edges = [number * 0.5 for number in range(49)] # [0, 0.5, 1, 1.5, 2 ,... 23.5, 24] , range49=0,1,...,48
    # these represent hours after midnight

    wind = [float(result["wind_mwh"]) for result in results]
    solar = [float(result["solar_mwh"]) for result in results]
    generation = [float(result["total_generation_mwh"]) for result in results]
    consumption = [float(result["demand_mwh"]) for result in results]

    fig, ax = plt.subplots(figsize=(12, 6.5))
    ax.stairs(wind, edges, baseline=None, label="Wind generation")
    ax.stairs(solar, edges, baseline=None, label="Solar PV generation")
    ax.stairs(
        generation, edges, baseline=None,
        label="Combined generation", linewidth=2.2,
    )
    ax.stairs(
        consumption, edges, baseline=None,
        label="Customer consumption", linewidth=2.2, linestyle="--",
    )

    ax.set_title(
        "Electricity generation and customer consumption\n"
        f"{delivery_date.isoformat()} | Illustrative data"
    )
    ax.set_xlabel("Local clock time (ordinary 48-period day)")
    ax.set_ylabel("Energy in each half-hour (MWh)")
    ax.set_xlim(0, 24)
    ax.margins(y=0.20)
    ax.set_ylim(bottom=0)

    tick_hours = list(range(0, 25, 3))
    tick_labels = [f"{hour:02d}:00" for hour in tick_hours]
    tick_labels[-1] = "00:00\n(+1 day)"
    ax.set_xticks(tick_hours, labels=tick_labels)
    ax.legend(loc="upper left", ncols=2)
    ax.grid(axis="y", alpha=0.25)

    file_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(file_path, dpi=160, bbox_inches="tight")
    finally:
        plt.close(fig)


def save_position_chart(
    file_path: Path,
    delivery_date: date,
    results: list[dict[str, float | str]],
) -> None:
    """Generate and save bar plots representing net long and short imbalance positions."""
    period_numbers = [result["settlement_period"] for result in results]
    if period_numbers != list(range(1, 49)):
        raise ValueError("This chart requires settlement periods 1 to 48 in order.")

    # Place the left edge of each bar at its half-hour start.
    start_hours = [(number - 1) * 0.5 for number in range(1, 49)]  #[0.0, 0.5, 1.0, 1.5, ..., 23.5]
    positions = [float(result["net_position_mwh"]) for result in results]

    fig, ax = plt.subplots(figsize=(12, 6.5))
    ax.bar(start_hours, positions, width=0.5, align="edge")
    ax.axhline(0.0, linewidth=1.2, linestyle="--")

    ax.set_title(
        "Power portfolio position before market trades\n"
        f"{delivery_date.isoformat()} | Illustrative data\n"
        "Above zero: LONG (surplus) | Below zero: SHORT (shortage)"
    )
    ax.set_xlabel("Local clock time (ordinary 48-period day)")
    ax.set_ylabel("Net electricity position in each half-hour (MWh)")
    ax.set_xlim(0, 24)

    # Equal space above and below zero. abs() is ONLY for the axis range.
    # Keep every plotted position signed. The minimum range handles all zeros.
    limit = 1.2 * max(1.0, max(abs(value) for value in positions))
    ax.set_ylim(-limit, limit)

    tick_hours = list(range(0, 25, 3))
    tick_labels = [f"{hour:02d}:00" for hour in tick_hours]
    tick_labels[-1] = "00:00\n(+1 day)"
    ax.set_xticks(tick_hours, labels=tick_labels)
    ax.set_axisbelow(True)
    ax.grid(axis="y", alpha=0.25)

    file_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(file_path, dpi=160, bbox_inches="tight")
    finally:
        plt.close(fig)

def save_price_cash_flow_charts(
    price_path: Path,
    cash_flow_path: Path,
    delivery_date: date,
    results: list[dict[str, float | str]],
) -> None:
    """Generate separate visual charts for wholesale power pricing and net market cash flows."""
    period_numbers = [result["settlement_period"] for result in results]
    if period_numbers != list(range(1, 49)):
        raise ValueError("These charts require settlement periods 1 to 48 in order.")
    if price_path.resolve() == cash_flow_path.resolve():
        raise ValueError("The two charts require different output paths.")

    # The existing calculation has already produced these signed cash flows.
    prices = [float(result["price_gbp_per_mwh"]) for result in results]
    cash_flows = [float(result["net_market_cash_flow_gbp"]) for result in results]
    edges = [number * 0.5 for number in range(49)]  #[0.0, 0.5, 1.0, 1.5, ..., 23.5, 24.0]
    start_hours = edges[:-1] # [0.0, 0.5, 1.0, ..., 23.5]

    # Two separate figures, each with one vertical unit and one plot.
    price_fig, price_ax = plt.subplots(figsize=(12, 5.5))
    cash_fig, cash_ax = plt.subplots(figsize=(12, 5.5))
    try:
        price_ax.stairs(prices, edges, baseline=None, linewidth=1.8)
        price_ax.set_title(
            "Assumed wholesale electricity prices\n"
            f"{delivery_date.isoformat()} | Illustrative data"
        )
        price_ax.set_ylabel("Assumed wholesale price (GBP/MWh)")

        cash_ax.bar(start_hours, cash_flows, width=0.5, align="edge")
        cash_ax.set_title(
            "Net wholesale market cash flow by settlement period\n"
            f"{delivery_date.isoformat()} | Illustrative data\n"
            "Above zero: cash inflow | Below zero: cash outflow"
        )
        cash_ax.set_ylabel("Net market cash flow for each half-hour (GBP)")

        # abs() chooses the display range only. Keep the plotted signs.
        cash_limit = 1.2 * max(1.0, max(abs(value) for value in cash_flows))
        cash_ax.set_ylim(-cash_limit, cash_limit)

        tick_hours = list(range(0, 25, 3))
        tick_labels = [f"{hour:02d}:00" for hour in tick_hours]
        tick_labels[-1] = "00:00\n(+1 day)"
        for ax in (price_ax, cash_ax):
            ax.axhline(0.0, linewidth=1.0, linestyle="--")
            ax.set_xlim(0, 24)
            ax.set_xticks(tick_hours, labels=tick_labels)
            ax.set_xlabel("Local clock time (ordinary 48-period day)")
            ax.set_axisbelow(True)
            ax.grid(axis="y", alpha=0.25)

        # Do not force the price axis above zero: negative prices remain visible.
        price_path.parent.mkdir(parents=True, exist_ok=True)
        cash_flow_path.parent.mkdir(parents=True, exist_ok=True)
        price_fig.savefig(price_path, dpi=160, bbox_inches="tight")
        cash_fig.savefig(cash_flow_path, dpi=160, bbox_inches="tight")
    finally:
        plt.close(price_fig)
        plt.close(cash_fig)