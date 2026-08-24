"""OpenETBench India map visualizations.

Provides publication-quality BharatFlux site maps using the
supervisor-provided India administrative boundary shapefile.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman"]

from extraction.sites import Site


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INDIA_MAP_DIR = PROJECT_ROOT / "data" / "maps" / "india"
INDIA_SHP = INDIA_MAP_DIR / "in.shp"


def _load_india(india_shp: Path | None = None) -> gpd.GeoDataFrame | None:
    """Load the supervisor-provided India boundary in EPSG:4326."""
    shp = Path(india_shp) if india_shp is not None else INDIA_SHP
    if not shp.exists():
        return None
    try:
        india = gpd.read_file(shp)
        if india.crs is not None and india.crs.to_string() != "EPSG:4326":
            india = india.to_crs("EPSG:4326")
        return india
    except Exception:
        return None


def plot_site(
    site: Site,
    output_dir: Path,
    *,
    product_name: str | None = None,
    figure_path: Path | None = None,
    india_shp: Path | None = None,
) -> Path:
    """Plot one BharatFlux site on the India administrative map.

    The map styling intentionally matches the Sprint-8 spatial-performance
    map: white India polygons, light administrative boundaries, India-focused
    extent, latitude/longitude axes, and a clearly labelled site marker.
    """
    if figure_path is None:
        figure_dir = output_dir / "maps"
        figure_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{site.id}.png" if product_name is None else f"{product_name}_{site.id}.png"
        figure_path = figure_dir / filename
    else:
        figure_path.parent.mkdir(parents=True, exist_ok=True)

    india = _load_india(india_shp)

    fig, ax = plt.subplots(figsize=(8, 8))

    if india is not None:
        india.plot(
            ax=ax,
            facecolor="white",
            edgecolor="0.65",
            linewidth=0.55,
            zorder=1,
        )
        minx, miny, maxx, maxy = india.total_bounds
        ax.set_xlim(max(67, minx - 1), min(98, maxx + 1))
        ax.set_ylim(max(6, miny - 1), min(38, maxy + 1))
    else:
        # Keep the visualization usable if the map resource is absent.
        ax.set_xlim(67, 98)
        ax.set_ylim(6, 38)

    ax.scatter(
        site.longitude,
        site.latitude,
        s=120,
        facecolor="black",
        edgecolor="white",
        linewidth=1.0,
        zorder=4,
    )
    ax.annotate(
        site.id,
        (site.longitude, site.latitude),
        xytext=(6, 6),
        textcoords="offset points",
        fontsize=10,
        fontweight="bold",
        zorder=5,
    )

    title = f"Flux Tower Site — {site.id}"
    if product_name:
        title = f"{product_name} — Flux Tower Site: {site.id}"
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°N)")
    ax.grid(True, linestyle=":", alpha=0.35)

    fig.tight_layout()
    fig.savefig(figure_path, dpi=600, bbox_inches="tight")
    plt.close(fig)
    return figure_path
