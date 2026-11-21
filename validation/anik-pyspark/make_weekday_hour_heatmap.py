"""Plot the building-weighted weekday/hour summary produced by PySpark."""

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle


DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summary_csv", type=Path)
    parser.add_argument("output_png", type=Path)
    args = parser.parse_args()

    values = np.full((7, 24), np.nan)
    total_readings = 0
    with args.summary_csv.open(newline="", encoding="utf-8") as source:
        for record in csv.DictReader(source):
            day = (int(record["day_of_week"]) - 1) % 7
            hour = int(record["hour"])
            if not 0 <= hour < 24 or np.isfinite(values[day, hour]):
                raise ValueError("Expected at most one row for each weekday and hour.")
            values[day, hour] = float(record["mean_meter_reading"])
            total_readings += int(record["readings"])
    if not np.isfinite(values).all():
        raise ValueError("The heatmap needs all 168 weekday/hour cells.")

    peak_day, peak_hour = np.unravel_index(values.argmax(), values.shape)
    peak_value = values[peak_day, peak_hour]

    fig = plt.figure(figsize=(12, 5.15), facecolor="white")
    ax = fig.add_axes((0.106, 0.24, 0.765, 0.52))
    scale = fig.add_axes((0.898, 0.24, 0.016, 0.52))
    image = ax.imshow(values, aspect="auto", cmap="viridis", interpolation="nearest")
    fig.colorbar(image, cax=scale, label="Mean meter reading (kWh)")

    ax.set_xticks(range(24), [f"{hour:02}" for hour in range(24)])
    ax.set_yticks(range(7), DAYS)
    ax.set_xlabel("Hour in the dataset timestamps", labelpad=9)
    ax.tick_params(axis="both", which="both", length=0, pad=6)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.axhline(4.5, color="white", alpha=0.9, linewidth=1.4)
    ax.add_patch(
        Rectangle((peak_hour - 0.5, peak_day - 0.5), 1, 1, fill=False,
                  edgecolor="#ffffff", linewidth=1.7)
    )

    fig.text(0.106, 0.906, "Electricity use across the week",
             fontsize=21, fontweight="bold", color="#142538")
    fig.text(0.106, 0.836,
             f"ASHRAE 2016 electricity data  |  {total_readings:,} readings  |  Site 0 excluded",
             fontsize=10.5, color="#41576a")
    fig.text(0.106, 0.102,
             f"Outlined cell: {DAYS[peak_day]} at {peak_hour:02}:00 "
             f"({peak_value:.1f} kWh). Each cell gives equal weight to each building.",
             fontsize=10, color="#41576a")
    fig.savefig(args.output_png, dpi=240, facecolor=fig.get_facecolor())
    plt.close(fig)


if __name__ == "__main__":
    main()
