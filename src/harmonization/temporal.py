"""
OpenETBench
-----------

Temporal harmonization utilities.

Responsibilities
----------------
- Align observed and satellite ET time series
- Prepare datasets for benchmarking

Author: Adarsh Jha
"""

import pandas as pd


# ============================================================
# Temporal Alignment
# ============================================================

def align_to_common_dates(
    observed: pd.DataFrame,
    satellite: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Align observed and satellite datasets using common Day-of-Year (DoY).

    BharatFlux provides daily observations, whereas many satellite
    products (e.g., MOD16A2GF) provide ET at coarser temporal
    resolutions. This function keeps only the observed records that
    coincide with the satellite acquisition dates.

    Parameters
    ----------
    observed : pandas.DataFrame
        BharatFlux dataframe containing a "DoY" column.

    satellite : pandas.DataFrame
        Satellite dataframe containing a "DoY" column.

    Returns
    -------
    tuple[pandas.DataFrame, pandas.DataFrame]
        Temporally aligned observed and satellite dataframes.
    """

    if "DoY" not in observed.columns:
        raise KeyError("Observed dataframe must contain 'DoY' column.")

    if "DoY" not in satellite.columns:
        raise KeyError("Satellite dataframe must contain 'DoY' column.")

    # --------------------------------------------------------
    # Find common Day-of-Year values
    # --------------------------------------------------------

    common_doy = sorted(
        set(observed["DoY"])
        & set(satellite["DoY"])
    )

    # --------------------------------------------------------
    # Keep only common observations
    # --------------------------------------------------------

    observed_aligned = (
        observed[
            observed["DoY"].isin(common_doy)
        ]
        .sort_values("DoY")
        .reset_index(drop=True)
    )

    satellite_aligned = (
        satellite[
            satellite["DoY"].isin(common_doy)
        ]
        .sort_values("DoY")
        .reset_index(drop=True)
    )

    return observed_aligned, satellite_aligned