from pathlib import Path

import numpy as np
import pandas as pd

from benchmarking.metrics import calculate_metrics
from extraction.sites import get_site
from visualization.pipeline import generate_product_visualizations


PRODUCTS = [
    "MOD16A2GF",
    "ERA5-LAND",
    "FLDAS",
    "GLDAS",
    "MERRA2",
    "PMLV2",
]


def _sample_dataframe() -> pd.DataFrame:
    dates = pd.date_range("2025-01-01", periods=8, freq="8D")
    observed = np.array([1.0, 1.3, 1.7, 2.0, 1.8, 1.5, 1.2, 0.9])
    satellite = observed * 0.92 + 0.08
    return pd.DataFrame(
        {
            "Date": dates,
            "DoY": dates.dayofyear,
            "Observed_LE": np.arange(8, dtype=float),
            "Observed_ET": observed,
            "Satellite_ET": satellite,
        }
    )


def test_sprint3_generates_three_figures_per_product(tmp_path: Path):
    merged = _sample_dataframe()
    metrics = calculate_metrics(merged)
    site = get_site("BFT")

    for product in PRODUCTS:
        paths = generate_product_visualizations(
            merged=merged,
            metrics=metrics,
            site=site,
            product_name=product,
            results_root=tmp_path,
        )

        assert paths.scatter.exists()
        assert paths.timeseries.exists()
        assert paths.map.exists()
        assert paths.scatter.stat().st_size > 0
        assert paths.timeseries.stat().st_size > 0
        assert paths.map.stat().st_size > 0
