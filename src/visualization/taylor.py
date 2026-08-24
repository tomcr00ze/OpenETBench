"""Taylor-diagram utilities for OpenETBench Sprint 8."""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def build_taylor_statistics(raw: pd.DataFrame, primary: pd.DataFrame) -> pd.DataFrame:
    """Compute site-level normalized SD ratio/correlation and product medians."""
    rows = []
    keys = set(
        map(tuple, primary[["Site", "Product"]].drop_duplicates().to_records(index=False))
    )
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
        rows.append(
            {
                "Site": site,
                "Product": product,
                "N": len(x),
                "STD_OBSERVED": obs_sd,
                "STD_PRODUCT": pred_sd,
                "STD_RATIO": pred_sd / obs_sd,
                "CORRELATION": corr,
            }
        )

    site_stats = pd.DataFrame(rows)
    if site_stats.empty:
        return site_stats

    return (
        site_stats.groupby("Product")
        .agg(
            sites=("Site", "nunique"),
            median_STD_RATIO=("STD_RATIO", "median"),
            median_CORRELATION=("CORRELATION", "median"),
        )
        .reset_index()
        .sort_values("Product")
        .reset_index(drop=True)
    )


def plot_taylor_diagram(stats: pd.DataFrame, output_path: Path) -> Path:
    """Save a publication-style normalized Taylor diagram.

    The diagram keeps the Sprint-8 statistics unchanged, but improves the
    presentation substantially: each product gets a distinct color, labels
    are offset to avoid the central cluster, the observed reference is
    explicit, centered-RMSD contours are labelled, and a product legend is
    provided outside the polar axes.
    """
    if stats.empty:
        raise ValueError("No Taylor statistics available for plotting.")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    stats = stats.copy()
    stats["CORRELATION"] = np.clip(
        pd.to_numeric(stats["median_CORRELATION"], errors="coerce"), -1, 1
    )
    stats["STD_RATIO"] = pd.to_numeric(
        stats["median_STD_RATIO"], errors="coerce"
    )
    stats = stats.dropna(subset=["CORRELATION", "STD_RATIO"])
    stats = stats[np.isfinite(stats["STD_RATIO"]) & (stats["STD_RATIO"] >= 0)]
    if stats.empty:
        raise ValueError("No finite Taylor statistics available for plotting.")

    # Stable product palette so the same product has the same color across
    # repeated runs/figures.
    palette = {
        "ERA5-LAND": "#1f77b4",
        "FLDAS": "#2ca02c",
        "GLDAS": "#ff7f0e",
        "MERRA2": "#6a3d9a",
        "PMLV2": "#8c564b",
        "MOD16A2GF": "#d62728",
        "SSEBOP_V61": "#e377c2",
    }
    fallback = list(plt.get_cmap("tab10").colors)
    colors = {}
    for i, product in enumerate(stats["Product"]):
        colors[product] = palette.get(product, fallback[i % len(fallback)])

    corr = stats["CORRELATION"].to_numpy(float)
    ratio = stats["STD_RATIO"].to_numpy(float)
    theta = np.arccos(corr)

    rmax = max(2.0, float(np.nanmax(ratio) * 1.25))
    # Keep a little headroom for labels while avoiding an excessively large
    # radial axis when one product has a very large variance ratio.
    rmax = min(max(rmax, 2.0), 6.5)

    fig = plt.figure(figsize=(13, 9), dpi=150)
    ax = fig.add_subplot(111, projection="polar")
    ax.set_theta_zero_location("E")
    ax.set_theta_direction(1)
    ax.set_thetamin(0)
    ax.set_thetamax(180)
    ax.set_ylim(0, rmax)

    # Reference point: normalized standard deviation = 1, correlation = 1.
    ax.scatter(
        [0], [1],
        marker="*", s=240,
        facecolor="#5b2a86", edgecolor="white", linewidth=1.5,
        zorder=10, label="BharatFlux reference",
    )
    ax.annotate(
        "Reference\n(BharatFlux)",
        xy=(0, 1), xytext=(18, -8), textcoords="offset points",
        ha="left", va="top", fontsize=11, fontweight="bold",
        color="#5b2a86",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                  edgecolor="#5b2a86", alpha=0.92),
        arrowprops=dict(arrowstyle="-", color="#5b2a86", lw=1.2),
    )

    # Centered-RMSD contours.
    theta_grid = np.linspace(0, np.pi, 721)
    radius_grid = np.linspace(0, rmax, 500)
    T, R = np.meshgrid(theta_grid, radius_grid)
    crmsd = np.sqrt(np.maximum(0, 1 + R**2 - 2 * R * np.cos(T)))

    max_crmsd = float(np.nanmax(crmsd))
    candidate_levels = np.arange(0.5, np.ceil(max_crmsd * 2) / 2 + 0.01, 0.5)
    levels = candidate_levels[candidate_levels <= max_crmsd + 1e-9]
    contours = ax.contour(
        T, R, crmsd, levels=levels,
        colors="#7f8c8d", linestyles="--", linewidths=0.9, alpha=0.58,
    )
    ax.clabel(contours, inline=True, fontsize=8, fmt="%.1f", colors="#657174")

    # Product markers and readable labels.  The offsets are deliberately
    # product-aware because several products cluster near the reference.
    label_offsets = {
        "ERA5-LAND": (9, 14),
        "FLDAS": (9, 2),
        "GLDAS": (9, -16),
        "MERRA2": (10, 8),
        "PMLV2": (10, -15),
        "MOD16A2GF": (10, 7),
        "SSEBOP_V61": (10, -2),
    }

    for t, r, product in zip(theta, ratio, stats["Product"]):
        c = colors[product]
        ax.scatter(
            t, r, s=125, color=c, edgecolor="white", linewidth=1.4,
            zorder=8, label=product,
        )
        dx, dy = label_offsets.get(product, (9, 7))
        ax.annotate(
            product, (t, r), xytext=(dx, dy), textcoords="offset points",
            fontsize=10.5, fontweight="bold", color=c,
            ha="left", va="center",
            bbox=dict(boxstyle="round,pad=0.22", facecolor="white",
                      edgecolor=c, alpha=0.88, linewidth=0.8),
            zorder=9,
        )

    # Correlation ticks are placed at their mathematically correct angles.
    corr_ticks = np.array([1.0, 0.99, 0.95, 0.90, 0.75, 0.50, 0.25, 0.0, -0.5, -0.75, -0.9, -1.0])
    tick_theta = np.arccos(corr_ticks)
    ax.set_xticks(tick_theta)
    ax.set_xticklabels([
        "1.0", "0.99", "0.95", "0.90", "0.75", "0.50", "0.25",
        "0.0", "−0.50", "−0.75", "−0.90", "−1.0"
    ], fontsize=9.5)

    # Radial scale and light grid.
    ax.set_rlabel_position(90)
    ax.tick_params(axis="y", labelsize=9)
    ax.grid(True, linestyle=":", linewidth=0.8, alpha=0.55)
    ax.spines["polar"].set_linewidth(1.2)

    ax.set_title(
        "Taylor Diagram — Product-Level Multi-Year Benchmark",
        fontsize=18, fontweight="bold", pad=30,
    )
    fig.text(
        0.5, 0.935,
        "Reference: BharatFlux observations  |  Multi-year primary records (N ≥ 10)",
        ha="center", va="center", fontsize=11.5, color="#4d4d4d",
    )

    # Axis descriptions.
    fig.text(
        0.50, 0.075,
        "Normalized standard deviation  (σ / σ_ref)",
        ha="center", fontsize=12.5, fontweight="bold",
    )
    fig.text(
        0.80, 0.72,
        "Correlation coefficient (R)",
        rotation=-36, ha="center", va="center",
        fontsize=12, fontweight="bold", color="#2455a4",
    )

    # Interpretation box.
    guide = (
        "How to read\n"
        "• Closer to reference point = better agreement\n"
        "• Higher correlation (R) = better\n"
        "• Lower centered RMSD = better\n"
        "• σ/σ_ref ≈ 1 = similar variability"
    )
    fig.text(
        0.78, 0.27, guide, ha="left", va="center", fontsize=10.2,
        bbox=dict(boxstyle="round,pad=0.55", facecolor="white",
                  edgecolor="#555555", linestyle="--", alpha=0.96),
    )

    # Product legend outside the plotting area.
    handles = []
    labels = []
    for product in stats["Product"]:
        handle = plt.Line2D(
            [0], [0], marker="o", linestyle="", markersize=8.5,
            markerfacecolor=colors[product], markeredgecolor="white",
            markeredgewidth=1.0, label=product,
        )
        handles.append(handle)
        labels.append(product)
    ax.legend(
        handles, labels, title="Products", loc="upper left",
        bbox_to_anchor=(1.05, 1.00), borderaxespad=0.0,
        frameon=True, fancybox=True, framealpha=0.96,
        fontsize=9.8, title_fontsize=10.5,
    )

    # Small performance guide.
    fig.text(
        0.18, 0.035,
        "Perfect agreement", ha="center", fontsize=9.5,
        color="#5b2a86", fontweight="bold",
    )
    fig.text(
        0.50, 0.035,
        "Centered RMSD contours shown as dashed arcs",
        ha="center", fontsize=9.5, color="#657174",
    )

    fig.subplots_adjust(left=0.06, right=0.75, top=0.86, bottom=0.13)
    fig.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_path
