"""
OpenETBench
-----------

Benchmarking metrics for evapotranspiration products.

Responsibilities
----------------
- Compute statistical agreement between observed and satellite ET.

Author: Adarsh Jha
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd


# ============================================================
# Metrics Report
# ============================================================

@dataclass(frozen=True)
class MetricsReport:
    """
    Statistical comparison between observed and satellite ET.
    """

    rmse: float
    mae: float
    bias: float
    correlation: float
    r2: float


# ============================================================
# Calculate Metrics
# ============================================================

def calculate_metrics(
    merged: pd.DataFrame,
) -> MetricsReport:
    """
    Calculate benchmark metrics.

    Parameters
    ----------
    merged : pandas.DataFrame
        Merged dataframe containing:
            Observed_ET
            Satellite_ET

    Returns
    -------
    MetricsReport
    """

    observed = merged["Observed_ET"].to_numpy()
    satellite = merged["Satellite_ET"].to_numpy()

    # --------------------------------------------------------
    # Error
    # --------------------------------------------------------

    error = satellite - observed

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    rmse = float(
        np.sqrt(
            np.mean(error**2)
        )
    )

    mae = float(
        np.mean(
            np.abs(error)
        )
    )

    bias = float(
        np.mean(error)
    )

    correlation = float(
        np.corrcoef(
            observed,
            satellite,
        )[0, 1]
    )

    r2 = correlation**2

    return MetricsReport(
        rmse=rmse,
        mae=mae,
        bias=bias,
        correlation=correlation,
        r2=r2,
    )