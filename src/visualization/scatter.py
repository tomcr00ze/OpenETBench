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
        Path to the saved figure.
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
        figure_dir
        / f"{product_name}_{site}_{year}.png"
    )

    # --------------------------------------------------------
    # Create figure
    # --------------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(6, 6),
    )

    # --------------------------------------------------------
    # Scatter points
    # --------------------------------------------------------

    ax.scatter(
        merged["Observed_ET"],
        merged["Satellite_ET"],
        s=40,
        alpha=0.6,
    )

    # --------------------------------------------------------
    # 1:1 reference line
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
        linestyle="--",
        color="gray",
        linewidth=1.5,
        label="1:1 Line",
    )

    # --------------------------------------------------------
    # Axis labels
    # --------------------------------------------------------

    ax.set_xlabel(
        "Observed ET (mm/day)",
        fontsize=12,
    )

    ax.set_ylabel(
        "Satellite ET (mm/day)",
        fontsize=12,
    )

    ax.set_title(
        f"{product_name} vs BharatFlux\n"
        f"{site} ({year})",
        fontsize=15,
        fontweight="bold",
    )

    # --------------------------------------------------------
    # Equal aspect ratio
    # --------------------------------------------------------

    ax.set_aspect(
        "equal",
        adjustable="box",
    )

    # --------------------------------------------------------
    # Grid
    # --------------------------------------------------------

    ax.grid(
        True,
        linestyle=":",
        alpha=0.6,
    )

    # --------------------------------------------------------
    # Metrics textbox
    # --------------------------------------------------------

    n = len(merged)

    textbox = (
        f"n    : {n}\n"
        f"RMSE : {metrics.rmse:.2f}\n"
        f"MAE  : {metrics.mae:.2f}\n"
        f"Bias : {metrics.bias:.2f}\n"
        f"r    : {metrics.correlation:.3f}\n"
        f"R²   : {metrics.r2:.3f}"
    )

    ax.text(
        0.95,
        0.95,
        textbox,
        transform=ax.transAxes,
        fontsize=11,
        horizontalalignment="right",
        verticalalignment="bottom",
        bbox=dict(
            boxstyle="round",
            facecolor="white",
            edgecolor="black",
            alpha=0.90,
        ),
    )

    # --------------------------------------------------------
    # Layout
    # --------------------------------------------------------

    fig.tight_layout()

    # --------------------------------------------------------
    # Save figure
    # --------------------------------------------------------

    fig.savefig(
        figure_path,
        dpi=600,
        bbox_inches="tight",
    )

    plt.close(fig)

    return figure_path