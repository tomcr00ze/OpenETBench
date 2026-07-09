"""
OpenETBench
-----------

Merge harmonized observed and satellite datasets.

Responsibilities
----------------
- Merge temporally aligned datasets
- Prepare benchmark-ready dataframe

Author: Adarsh Jha
"""

import pandas as pd


# ============================================================
# Merge Datasets
# ============================================================

def merge_observed_satellite(
    observed: pd.DataFrame,
    satellite: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge temporally aligned BharatFlux and satellite ET datasets.

    Parameters
    ----------
    observed : pandas.DataFrame
        BharatFlux dataframe containing:
            DoY, LE, ET

    satellite : pandas.DataFrame
        Satellite dataframe containing:
            Date, DoY, ET

    Returns
    -------
    pandas.DataFrame
        Benchmark-ready dataframe.
    """

    merged = pd.merge(
        observed,
        satellite,
        on="DoY",
        how="inner",
        suffixes=(
            "_Observed",
            "_Satellite",
        ),
    )

    merged.rename(
        columns={
            "ET_Observed": "Observed_ET",
            "ET_Satellite": "Satellite_ET",
            "LE": "Observed_LE",
        },
        inplace=True,
    )

    return merged[
        [
            "Date",
            "DoY",
            "Observed_LE",
            "Observed_ET",
            "Satellite_ET",
        ]
    ]