"""
OpenETBench
------------

Cleaner for BharatFlux datasets.

Responsibilities
----------------
- Standardize column names
- Merge split ET/LE datasets
- Handle missing values
- Convert data types
- Validate datasets

Author: Adarsh Jha
"""
from dataclasses import replace
import pandas as pd

# pyrefly: ignore [missing-import]
from src.preprocessing.loader import BharatFluxDataset


# ============================================================
# Column Name Mapping
# ============================================================

COLUMN_MAPPING = {

    # --------------------------------------------------------
    # Day of Year
    # --------------------------------------------------------
    "Day": "DoY",
    "DoY": "DoY",

    # --------------------------------------------------------
    # Latent Heat Flux (Mean)
    # --------------------------------------------------------
    "LE_daily_mean (W m-2)": "LE",
    "H_daily_mean (W m-2)": "LE",
    "LE": "LE",

    # --------------------------------------------------------
    # Evapotranspiration (Mean)
    # --------------------------------------------------------
    "ET_daily_mean (mm d-1)": "ET",
    "ET": "ET",

    # --------------------------------------------------------
    # Latent Heat Flux Standard Deviation
    # --------------------------------------------------------
    "LE_daily_sd (W m-2)": "LE_SD",
    "H_daily_sd (W m-2)": "LE_SD",

    # --------------------------------------------------------
    # ET Standard Deviation
    # --------------------------------------------------------
    "ET_daily_sd (mm d-1)": "ET_SD",
}


# ============================================================
# Column Name Standardization
# ============================================================

def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize BharatFlux column names.

    This function converts the heterogeneous BharatFlux column
    names into a common naming convention used throughout
    OpenETBench.

    Examples
    --------
    Day                     -> DoY
    DoY                     -> DoY

    LE_daily_mean (W m-2)   -> LE
    H_daily_mean (W m-2)    -> LE

    ET_daily_mean (mm d-1)  -> ET

    LE_daily_sd (W m-2)     -> LE_SD
    H_daily_sd (W m-2)      -> LE_SD

    ET_daily_sd (mm d-1)    -> ET_SD

    Parameters
    ----------
    df : pandas.DataFrame
        Original BharatFlux dataframe.

    Returns
    -------
    pandas.DataFrame
        DataFrame with standardized column names.
    """

    # Create a copy so the original dataframe remains unchanged
    cleaned_df = df.copy()

    # Rename only the columns present in the dataframe
    cleaned_df.rename(
        columns=COLUMN_MAPPING,
        inplace=True,
    )

    return cleaned_df

# ============================================================
# Merge Split Files
# ============================================================

def merge_split_files(
    datasets: dict[str, BharatFluxDataset]
) -> dict[str, BharatFluxDataset]:
    """
    Merge BharatFlux ET-only and LE-only datasets into a single dataset.

    BharatFlux stores some site-years as two separate CSV files:

        Site_Year_ET_dmean.csv
        Site_Year_LE_dmean.csv

    This function merges them into a single BharatFluxDataset
    containing both LE and ET observations.

    Datasets that are already combined are left unchanged.

    Parameters
    ----------
    datasets : dict[str, BharatFluxDataset]
        Dictionary returned by load_all().

    Returns
    -------
    dict[str, BharatFluxDataset]
        Dictionary where every site-year appears exactly once.
    """

    merged_datasets: dict[str, BharatFluxDataset] = {}

    processed: set[str] = set()

    for dataset_name, dataset in datasets.items():

        # ----------------------------------------------------
        # Skip datasets that have already been processed
        # ----------------------------------------------------
        if dataset_name in processed:
            continue

        info = dataset.info

        # ----------------------------------------------------
        # Dataset is already combined
        # Simply copy it to the output dictionary.
        # ----------------------------------------------------
        if info.file_type == "combined":
            merged_datasets[dataset_name] = dataset
            processed.add(dataset_name)
            continue

        # ----------------------------------------------------
        # Build Site-Year identifier
        #
        # Example:
        #   BKC_2014_ET_dmean
        #   BKC_2014_LE_dmean
        #
        # becomes
        #
        #   BKC_2014
        # ----------------------------------------------------
        site_year = f"{info.site}_{info.year}"

        et_key = f"{site_year}_ET_dmean"
        le_key = f"{site_year}_LE_dmean"

        # ----------------------------------------------------
        # Ensure both ET and LE files exist
        # ----------------------------------------------------
        if et_key not in datasets or le_key not in datasets:
            raise FileNotFoundError(
                f"Missing ET/LE pair for {site_year}"
            )

        et_dataset = datasets[et_key]
        le_dataset = datasets[le_key]

        # ----------------------------------------------------
        # Merge on Day of Year
        #
        # We use an outer join to preserve all observations.
        # Missing values become NaN automatically.
        # ----------------------------------------------------
        merged_df = pd.merge(
            le_dataset.data,
            et_dataset.data,
            on="DoY",
            how="outer",
            sort=True,
        )

        # ----------------------------------------------------
        # Create updated metadata.
        #
        # After preprocessing every dataset should be treated
        # as a combined dataset regardless of how it was
        # originally stored.
        # ----------------------------------------------------
        merged_info = replace(
            le_dataset.info,
            file_type="combined",
        )

        merged_dataset = BharatFluxDataset(
            info=merged_info,
            data=merged_df,
        )

        # ----------------------------------------------------
        # Store using Site_Year as the dictionary key.
        #
        # Example:
        #     BKC_2014
        # ----------------------------------------------------
        merged_datasets[site_year] = merged_dataset

        processed.add(et_key)
        processed.add(le_key)

    return merged_datasets