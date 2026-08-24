"""Advanced Sprint 8 visualization helpers."""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd

from extraction.sites import SITES


DEFAULT_INDIA_SHP = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "maps"
    / "india"
    / "in.shp"
)


def _primary_keys(primary: pd.DataFrame) -> set[tuple[str, str]]:
    return set(map(tuple, primary[["Site", "Product"]].drop_duplicates().to_records(index=False)))


def build_seasonal_cycle(raw: pd.DataFrame, primary: pd.DataFrame) -> pd.DataFrame:
    """Build product-level standardized monthly climatologies.

    Each Site × Product series is standardized before pooling. This avoids
    treating products with different native temporal sampling/units as if
    their raw magnitudes were directly interchangeable in the visualization.
    """
    keys = _primary_keys(primary)
    rows = []
    for (site, product), g in raw.groupby(["Site", "Product"], sort=True):
        if (site, product) not in keys:
            continue
        x = g[["Date", "Observed_ET", "Satellite_ET"]].dropna().copy()
        if len(x) < 3:
            continue
        x["Month"] = pd.to_datetime(x["Date"]).dt.month
        for col, label in [("Observed_ET", "Observed"), ("Satellite_ET", "Product")]:
            mean = x[col].mean()
            sd = x[col].std(ddof=0)
            if not np.isfinite(sd) or sd == 0:
                continue
            x[f"z_{label}"] = (x[col] - mean) / sd
            m = x.groupby("Month")[f"z_{label}"].mean().reset_index()
            m["Site"] = site
            m["Product"] = product
            m["Series"] = label
            rows.append(m.rename(columns={f"z_{label}": "Z"}))
    if not rows:
        return pd.DataFrame()
    site_month = pd.concat(rows, ignore_index=True)
    return (
        site_month.groupby(["Product", "Series", "Month"])["Z"]
        .median()
        .reset_index()
        .sort_values(["Product", "Series", "Month"])
    )


def plot_seasonal_cycle(cycle: pd.DataFrame, output_path: Path) -> Path:
    """Save product seasonal-cycle comparison using standardized ET."""
    if cycle.empty:
        raise ValueError("No seasonal-cycle data available.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    products = sorted(cycle["Product"].unique())
    fig, ax = plt.subplots(figsize=(11, 6))
    for product in products:
        p = cycle[(cycle.Product == product) & (cycle.Series == "Product")]
        if not p.empty:
            ax.plot(p["Month"], p["Z"], marker="o", linewidth=1.5, label=product)
    obs = cycle[cycle.Series == "Observed"]
    if not obs.empty:
        o = obs.groupby("Month")["Z"].median()
        ax.plot(o.index, o.values, marker="o", linewidth=2.5, linestyle="--", label="Observed")
    ax.axhline(0, linewidth=0.8)
    ax.set_xticks(range(1, 13))
    ax.set_xlabel("Month")
    ax.set_ylabel("Standardized ET (z-score)")
    ax.set_title("Seasonal Cycle — Multi-Year Primary Benchmark")
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(ncol=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path


def build_interannual(raw: pd.DataFrame, primary: pd.DataFrame) -> pd.DataFrame:
    """Build annual standardized anomalies for each Site × Product."""
    keys = _primary_keys(primary)
    rows = []
    for (site, product), g in raw.groupby(["Site", "Product"], sort=True):
        if (site, product) not in keys:
            continue
        x = g.copy()
        x["Year"] = pd.to_datetime(x["Date"]).dt.year
        annual = x.groupby("Year").agg(
            Observed_ET=("Observed_ET", "mean"),
            Satellite_ET=("Satellite_ET", "mean"),
        ).reset_index()
        if len(annual) < 2:
            continue
        for col, label in [("Observed_ET", "Observed"), ("Satellite_ET", "Product")]:
            sd = annual[col].std(ddof=0)
            mean = annual[col].mean()
            if not np.isfinite(sd) or sd == 0:
                annual[f"Z_{label}"] = 0.0
            else:
                annual[f"Z_{label}"] = (annual[col] - mean) / sd
        annual["Site"] = site
        annual["Product"] = product
        rows.append(annual)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def plot_interannual(annual: pd.DataFrame, output_path: Path) -> Path:
    """Save product-level interannual standardized anomalies."""
    if annual.empty:
        raise ValueError("No interannual data available.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prod = annual.groupby(["Product", "Year"])["Z_Product"].median().reset_index()
    obs = annual.groupby("Year")["Z_Observed"].median()
    fig, ax = plt.subplots(figsize=(11, 6))
    for product, g in prod.groupby("Product"):
        ax.plot(g["Year"], g["Z_Product"], marker="o", linewidth=1.5, label=product)
    if not obs.empty:
        ax.plot(obs.index, obs.values, marker="o", linewidth=2.5, linestyle="--", label="Observed")
    ax.axhline(0, linewidth=0.8)
    ax.set_xlabel("Year")
    ax.set_ylabel("Standardized annual ET anomaly")
    ax.set_title("Interannual Variability — Multi-Year Primary Benchmark")
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(ncol=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path


def build_spatial_performance(multiyear: pd.DataFrame, min_n: int) -> pd.DataFrame:
    """Return site-wise RMSE for primary Site × Product records."""
    x = multiyear.copy()
    x = x[(x["N"] >= min_n) & x["RMSE"].notna()].copy()
    return x[["Site", "Product", "N", "RMSE", "MAE", "ABS_BIAS", "CORRELATION", "R2"]]


def plot_spatial_performance(
    perf: pd.DataFrame,
    output_path: Path,
    india_shp: Path | None = None,
) -> Path:
    """Plot site-wise RMSE on the supplied India administrative boundary.

    The map is intentionally a site-based performance map, not a gridded
    spatial ET validation.  The focal product is the product with the lowest
    median multi-year RMSE among the primary benchmark records.
    """
    if perf.empty:
        raise ValueError("No spatial-performance records available.")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    india_shp = Path(india_shp) if india_shp is not None else DEFAULT_INDIA_SHP
    if not india_shp.exists():
        raise FileNotFoundError(
            f"India shapefile not found: {india_shp}. "
            """Place the supervisor-provided in.shp, in.shx, in.dbf and in.prj
            files under data/maps/india/."""
        )

    india = gpd.read_file(india_shp)
    if india.crs is not None and india.crs.to_string() != "EPSG:4326":
        india = india.to_crs("EPSG:4326")

    # Use the best-ranked product as the focal map to avoid producing 7 maps.
    product = perf.groupby("Product")["RMSE"].median().sort_values().index[0]
    p = perf[perf.Product == product].copy()

    fig, ax = plt.subplots(figsize=(9, 9))
    india.plot(
        ax=ax,
        facecolor="white",
        edgecolor="0.55",
        linewidth=0.55,
        zorder=1,
    )

    points = []
    for _, row in p.iterrows():
        site = SITES.get(str(row.Site).upper())
        if site is None:
            continue
        points.append((site.id, site.longitude, site.latitude, float(row.RMSE)))

    if not points:
        raise ValueError("No benchmark sites could be matched to the BharatFlux registry.")

    sc = ax.scatter(
        [x[1] for x in points],
        [x[2] for x in points],
        c=[x[3] for x in points],
        cmap="viridis",
        s=110,
        edgecolor="black",
        linewidth=0.6,
        zorder=3,
    )
    cbar = fig.colorbar(sc, ax=ax, shrink=0.72, pad=0.02)
    cbar.set_label("Multi-year RMSE")

    for site_id, lon, lat, rmse in points:
        ax.annotate(
            f"{site_id}\n{rmse:.2f}",
            (lon, lat),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
            zorder=4,
        )

    # Use the boundary extent rather than a generic world-map crop.
    minx, miny, maxx, maxy = india.total_bounds
    ax.set_xlim(max(67, minx - 1), min(98, maxx + 1))
    ax.set_ylim(max(6, miny - 1), min(38, maxy + 1))
    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°N)")
    ax.set_title(
        f"Spatial Performance Pattern — {product}\n"
        "BharatFlux site-wise multi-year RMSE",
        fontsize=14,
        fontweight="bold",
    )
    ax.grid(True, linestyle=":", alpha=0.35)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path
