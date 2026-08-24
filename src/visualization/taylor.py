"""Taylor-diagram utilities for OpenETBench Sprint 8."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def build_taylor_statistics(raw: pd.DataFrame, primary: pd.DataFrame) -> pd.DataFrame:
    """Compute site-level normalized SD ratio/correlation and product medians."""
    rows = []
    keys = set(map(tuple, primary[["Site", "Product"]].drop_duplicates().to_records(index=False)))
    for (site, product), g in raw.groupby(["Site", "Product"], sort=True):
        if (site, product) not in keys:
            continue
        x = g[["Observed_ET", "Satellite_ET"]].dropna()
        if len(x) < 2:
            continue
        obs = x["Observed_ET"].to_numpy(float)
        pred = x["Satellite_ET"].to_numpy(float)
        obs_sd = float(np.std(obs, ddof=1))
        pred_sd = float(np.std(pred, ddof=1))
        if not np.isfinite(obs_sd) or obs_sd <= 0:
            continue
        corr = float(np.corrcoef(obs, pred)[0, 1])
        if not np.isfinite(corr):
            continue
        rows.append({"Site": site, "Product": product, "N": len(x),
                     "STD_OBSERVED": obs_sd, "STD_PRODUCT": pred_sd,
                     "STD_RATIO": pred_sd / obs_sd, "CORRELATION": corr})
    site_stats = pd.DataFrame(rows)
    if site_stats.empty:
        return site_stats
    return (site_stats.groupby("Product")
            .agg(sites=("Site", "nunique"), median_STD_RATIO=("STD_RATIO", "median"),
                 median_CORRELATION=("CORRELATION", "median"))
            .reset_index().sort_values("Product").reset_index(drop=True))

def plot_taylor_diagram(stats: pd.DataFrame, output_path: Path) -> Path:
    """Save a normalized Taylor diagram."""
    if stats.empty:
        raise ValueError("No Taylor statistics available for plotting.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    corr = np.clip(stats["median_CORRELATION"].to_numpy(float), -1, 1)
    ratio = stats["median_STD_RATIO"].to_numpy(float)
    theta = np.arccos(corr)
    rmax = max(2.0, float(np.nanmax(ratio) * 1.25))
    fig = plt.figure(figsize=(8, 7))
    ax = fig.add_subplot(111, projection="polar")
    ax.set_thetamin(0); ax.set_thetamax(180)
    ax.set_ylim(0, rmax); ax.set_theta_zero_location("E"); ax.set_theta_direction(1)
    ax.plot([0], [1], marker="*", markersize=12, label="Observed reference")
    theta_grid = np.linspace(0, np.pi, 361)
    radius_grid = np.linspace(0, rmax, 300)
    T, R = np.meshgrid(theta_grid, radius_grid)
    crmsd = np.sqrt(1 + R**2 - 2 * R * np.cos(T))
    levels = np.linspace(max(0.25, crmsd.min()), crmsd.max(), 5)
    contours = ax.contour(T, R, crmsd, levels=levels, linestyles="--", alpha=0.45)
    ax.clabel(contours, inline=True, fontsize=8, fmt="%.1f")
    ax.scatter(theta, ratio, s=70, zorder=5)
    for t, r, product in zip(theta, ratio, stats["Product"]):
        ax.annotate(product, (t, r), xytext=(6, 4), textcoords="offset points", fontsize=9)
    ax.set_title("Taylor Diagram — Product-Level Multi-Year Benchmark", pad=22, fontsize=14)
    ax.set_ylabel("Normalized standard deviation", labelpad=28)
    ax.set_thetagrids(np.arange(0, 181, 30),
                      labels=["1.0", "0.87", "0.50", "0.0", "−0.50", "−0.87", "−1.0"])
    ax.grid(True, linestyle=":", alpha=0.5)
    fig.tight_layout(); fig.savefig(output_path, dpi=300, bbox_inches="tight"); plt.close(fig)
    return output_path
