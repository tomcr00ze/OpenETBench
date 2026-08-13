"""
OpenETBench
-----------

Sprint 3 visualization orchestration.

This module connects the existing benchmark output to the three standard
visualizations without embedding plotting logic in workflow notebooks.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from benchmarking.metrics import MetricsReport
from extraction.sites import Site
from utils.results import ProductResultPaths, ensure_product_result_dir
from visualization.maps import plot_site
from visualization.scatter import plot_scatter
from visualization.timeseries import plot_timeseries


def _infer_year(dataframe: pd.DataFrame) -> int | None:
    if "Date" not in dataframe.columns or dataframe.empty:
        return None
    dates = pd.to_datetime(dataframe["Date"], errors="coerce").dropna()
    if dates.empty:
        return None
    years = dates.dt.year.unique()
    return int(years[0]) if len(years) == 1 else None


def generate_product_visualizations(
    merged: pd.DataFrame,
    metrics: MetricsReport,
    site: Site,
    product_name: str,
    *,
    results_root: Path | None = None,
    year: int | None = None,
) -> ProductResultPaths:
    """Generate the complete Sprint 3 figure set for one product.

    The canonical outputs are saved directly under::

        results/<site>/<product>/
            scatter.png
            timeseries.png
            map.png

    The extraction CSV and benchmark JSON paths are returned as part of the
    same result contract but are not overwritten by this function.
    """

    if merged.empty:
        raise ValueError("Cannot generate visualizations from an empty dataframe.")

    paths = ensure_product_result_dir(
        site_id=site.id,
        product_id=product_name,
        results_root=results_root,
    )

    if year is None:
        year = _infer_year(merged)

    plot_scatter(
        merged=merged,
        metrics=metrics,
        product_name=product_name,
        site=site.id,
        year=year,
        output_dir=paths.root,
        figure_path=paths.scatter,
    )

    plot_timeseries(
        merged=merged,
        product_name=product_name,
        site=site.id,
        year=year,
        output_dir=paths.root,
        figure_path=paths.timeseries,
    )

    plot_site(
        site=site,
        output_dir=paths.root,
        product_name=product_name,
        figure_path=paths.map,
    )

    return paths
