"""Visualization API for OpenETBench."""

from visualization.pipeline import generate_product_visualizations
from visualization.scatter import plot_scatter
from visualization.timeseries import plot_timeseries
from visualization.maps import plot_site

__all__ = [
    "generate_product_visualizations",
    "plot_scatter",
    "plot_timeseries",
    "plot_site",
]
