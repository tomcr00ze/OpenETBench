"""Advanced Sprint 8 visualization helpers."""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from extraction.sites import SITES


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


def plot_spatial_performance(perf: pd.DataFrame, output_path: Path) -> Path:
    """Plot site-wise RMSE as a compact India performance map."""
    if perf.empty:
        raise ValueError("No spatial-performance records available.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Use the best-ranked product as the focal map to avoid producing 7 maps.
    product = (
        perf.groupby("Product")["RMSE"].median().sort_values().index[0]
    )
    p = perf[perf.Product == product].copy()
    fig, ax = plt.subplots(figsize=(8, 8))
    for _, row in p.iterrows():
        site = SITES.get(str(row.Site).upper())
        if site is None:
            continue
        ax.scatter(site.longitude, site.latitude, s=90, zorder=3)
        ax.annotate(f"{site.id}\n{row.RMSE:.2f}", (site.longitude, site.latitude), xytext=(5, 5), textcoords="offset points", fontsize=8)
    ax.set_xlim(67, 98)
    ax.set_ylim(6, 37)
    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°N)")
    ax.set_title(f"Spatial Performance Pattern — {product}\nSite-wise multi-year RMSE")
    ax.grid(True, linestyle=":", alpha=0.5)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path
