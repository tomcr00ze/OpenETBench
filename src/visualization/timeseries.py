"""
OpenETBench
-----------

Time-series visualization for ET benchmarking.

Responsibilities
----------------
- Plot observed and product ET against date.
- Preserve the benchmark-ready dataframe schema.
- Save publication-quality figures.

Author: Adarsh Jha
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


_REQUIRED_COLUMNS = {"Date", "Observed_ET", "Satellite_ET"}


def plot_timeseries(
    merged: pd.DataFrame,
    product_name: str,
    site: str,
    year: int | None,
    output_dir: Path,
    *,
    figure_path: Path | None = None,
) -> Path:
    """Plot observed and product ET time series.

    Parameters
    ----------
    merged:
        Benchmark-ready dataframe produced by ``merge_observed_satellite``.
    product_name:
        ET product name.
    site:
        Flux tower ID.
    year:
        Observation year used in the title. ``None`` is allowed for
        multi-year data.
    output_dir:
        Root figures directory used when ``figure_path`` is not supplied.
    figure_path:
        Optional explicit output path. This is used by the Sprint 3 result
        contract to save ``results/<site>/<product>/timeseries.png``.
    """

    missing = _REQUIRED_COLUMNS.difference(merged.columns)
    if missing:
        raise KeyError(
            "Missing required columns for time-series plot: "
            + ", ".join(sorted(missing))
        )

    data = merged.copy()
    data["Date"] = pd.to_datetime(data["Date"])
    data = data.sort_values("Date")

    if data.empty:
        raise ValueError("Cannot create a time-series plot from an empty dataframe.")

    if figure_path is None:
        figure_dir = output_dir / "timeseries"
        figure_dir.mkdir(parents=True, exist_ok=True)
        suffix = str(year) if year is not None else "all"
        figure_path = figure_dir / f"{product_name}_{site}_{suffix}.png"
    else:
        figure_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(
        data["Date"],
        data["Observed_ET"],
        marker="o",
        markersize=3,
        linewidth=1.2,
        label="Observed ET",
    )
    ax.plot(
        data["Date"],
        data["Satellite_ET"],
        marker="o",
        markersize=3,
        linewidth=1.2,
        label=product_name,
    )

    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("ET (mm day⁻¹)", fontsize=12)

    period = f" ({year})" if year is not None else ""
    ax.set_title(
        f"ET Time Series: {product_name} vs Observed ET\n"
        f"{site}{period}",
        fontsize=15,
        fontweight="bold",
    )

    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(figure_path, dpi=600, bbox_inches="tight")
    plt.close(fig)

    return figure_path
