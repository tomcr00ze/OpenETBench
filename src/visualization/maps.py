"""
OpenETBench
-----------

Flux tower location visualization.

Responsibilities
----------------
- Plot BharatFlux tower locations
- Save publication-quality map

Author: Adarsh Jha
"""

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt

# Set default font to Times New Roman
plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman"]

from extraction.sites import Site


# ============================================================
# Natural Earth Data
# ============================================================

MAP_DIR = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "maps"
    / "natural_earth"
)

WORLD_SHP = (
    MAP_DIR
    / "ne_110m_admin_0_countries.shp"
)


# ============================================================
# Plot Flux Tower
# ============================================================

def plot_site(
    site: Site,
    output_dir: Path,
    *,
    product_name: str | None = None,
    figure_path: Path | None = None,
) -> Path:
    """
    Plot the location of a BharatFlux site.

    Parameters
    ----------
    site : Site
        Flux tower metadata.

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

    if figure_path is None:
        figure_dir = output_dir / "maps"
        figure_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{site.id}.png" if product_name is None else f"{product_name}_{site.id}.png"
        figure_path = figure_dir / filename
    else:
        figure_path.parent.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------
    # Load Natural Earth shapefile when available.
    # Otherwise fall back to a lightweight coordinate map so the
    # visualization layer remains usable in a clean source checkout.
    # --------------------------------------------------------

    world = None
    if WORLD_SHP.exists():
        try:
            world = gpd.read_file(WORLD_SHP)
        except Exception:
            world = None

    # --------------------------------------------------------
    # Create site GeoDataFrame
    # --------------------------------------------------------

    point = gpd.GeoDataFrame(
        {
            "Site": [site.id],
        },
        geometry=gpd.points_from_xy(
            [site.longitude],
            [site.latitude],
        ),
        crs="EPSG:4326",
    )

    # --------------------------------------------------------
    # Plot
    # --------------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(8, 8),
    )

    if world is not None:
        world.plot(
            ax=ax,
            color="whitesmoke",
            edgecolor="gray",
            linewidth=0.5,
        )

    point.plot(
        ax=ax,
        color="red",
        markersize=120,
        zorder=5,
    )

    # --------------------------------------------------------
    # Site label
    # --------------------------------------------------------

    ax.text(
        site.longitude + 0.4,
        site.latitude + 0.2,
        site.id,
        fontsize=11,
        fontweight="bold",
        color="darkred",
    )

    # --------------------------------------------------------
    # Zoom to India
    # --------------------------------------------------------

    ax.set_xlim(67, 98)
    ax.set_ylim(6, 37)

    # --------------------------------------------------------
    # Labels
    # --------------------------------------------------------

    title = f"Flux Tower Site: {site.id}"
    if product_name:
        title = f"{product_name} — Flux Tower Site: {site.id}"

    ax.set_title(
        title,
        fontsize=15,
        fontweight="bold",
    )

    ax.set_xlabel(
        "Longitude (°E)"
    )

    ax.set_ylabel(
        "Latitude (°N)"
    )

    ax.grid(
        linestyle=":",
        alpha=0.5,
    )

    fig.tight_layout()

    fig.savefig(
        figure_path,
        dpi=600,
        bbox_inches="tight",
    )

    plt.close(fig)

    return figure_path