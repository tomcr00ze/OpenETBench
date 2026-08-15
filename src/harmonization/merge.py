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

    The merge is performed using DoY because temporal alignment has
    already established the common observation dates.

    A canonical Date column is retained regardless of whether both
    input
    dataframes contain Date.

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
        suffixes=("_Observed", "_Satellite"),
    )

    # --------------------------------------------------------
    # Resolve canonical Date column
    # --------------------------------------------------------

    if "Date_Observed" in merged.columns:
        merged["Date"] = pd.to_datetime(
            merged["Date_Observed"]
        )

    elif "Date_Satellite" in merged.columns:
        merged["Date"] = pd.to_datetime(
            merged["Date_Satellite"]
        )

    elif "Date" in merged.columns:
        merged["Date"] = pd.to_datetime(
            merged["Date"]
        )

    else:
        raise KeyError(
            "Merged dataframe does not contain a Date column."
        )

    # --------------------------------------------------------
    # Rename benchmark variables
    # --------------------------------------------------------

    merged.rename(
        columns={
            "ET_Observed": "Observed_ET",
            "ET_Satellite": "Satellite_ET",
            "LE": "Observed_LE",
        },
        inplace=True,
    )

    # --------------------------------------------------------
    # Return canonical benchmark dataframe
    # --------------------------------------------------------

    return merged[
        [
            "Date",
            "DoY",
            "Observed_LE",
            "Observed_ET",
            "Satellite_ET",
        ]
    ].sort_values(
        "Date"
    ).reset_index(
        drop=True
    )