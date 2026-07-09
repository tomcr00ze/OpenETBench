"""
OpenETBench
-----------

Scatter plot visualization for ET benchmarking.

Responsibilities
----------------
- Plot observed vs satellite ET
- Draw 1:1 reference line
- Display benchmark metrics
- Save publication-quality figures

Author: Adarsh Jha
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from benchmarking.metrics import MetricsReport


# ============================================================
# Scatter Plot
# ============================================================

def plot_scatter(
    merged: pd.DataFrame,
    metrics: MetricsReport,
    product_name: str,
    site: str,
    year: int,
    output_dir: Path,
) -> Path:
    """
    Plot observed vs satellite ET.

    Parameters
    ----------
    merged : pandas.DataFrame
        Output from merge_observed_satellite().

    metrics : MetricsReport
        Benchmark metrics.

    product_name : str
        ET product name.

    site : str
        Flux tower ID.

    year : int
        Observation year.

    output_dir : Path
        Root figures directory.

    Returns
    -------
    Path
        Saved figure path.
    """

    # --------------------------------------------------------
    # Create output directory
    # --------------------------------------------------------

    figure_dir = output_dir / "scatter"
    figure_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    figure_path = (
        figure_dir /
        f"{product_name}_{site}_{year}.png"
    )

    # --------------------------------------------------------
    # Prepare figure
    # --------------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(6, 6)
    )

    ax.scatter(
        merged["Observed_ET"],
        merged["Satellite_ET"],
        s=35,
        alpha=0.8,
    )

    # --------------------------------------------------------
    # 1:1 Reference Line
    # --------------------------------------------------------

    minimum = min(
        merged["Observed_ET"].min(),
        merged["Satellite_ET"].min(),
    )

    maximum = max(
        merged["Observed_ET"].max(),
        merged["Satellite_ET"].max(),
    )

    ax.plot(
        [minimum, maximum],
        [minimum, maximum],
        "--",
        linewidth=1.5,
    )

    # --------------------------------------------------------
    # Labels
    # --------------------------------------------------------

    ax.set_xlabel(
        "Observed ET (mm/day)"
    )

    ax.set_ylabel(
        "Satellite ET (mm/day)"
    )

    ax.set_title(
        f"{product_name} vs BharatFlux\n"
        f"{site} ({year})"
    )

    # --------------------------------------------------------
    # Metrics textbox
    # --------------------------------------------------------

    text = (
        f"RMSE : {metrics.rmse:.2f}\n"
        f"MAE  : {metrics.mae:.2f}\n"
        f"Bias : {metrics.bias:.2f}\n"
        f"r    : {metrics.correlation:.3f}\n"
        f"R²   : {metrics.r2:.3f}"
    )

    ax.text(
        0.05,
        0.95,
        text,
        transform=ax.transAxes,
        verticalalignment="top",
        bbox=dict(
            boxstyle="round",
            facecolor="white",
            alpha=0.9,
        ),
    )

    ax.grid(True)

    fig.tight_layout()

    fig.savefig(
        figure_path,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(fig)

    return figure_path