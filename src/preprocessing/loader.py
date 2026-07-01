"""
OpenETBench
------------

Loader for BharatFlux daily ET observations.

Responsibilities
----------------
- Discover all BharatFlux CSV files
- Parse metadata from filenames
- Load CSVs into pandas DataFrames
- Store metadata using dataclasses
- Build an inventory table for downstream processing

Author: Adarsh Jha
"""

from dataclasses import dataclass
from pathlib import Path
import re

import pandas as pd


# ============================================================
# Dataclasses
# ============================================================

@dataclass(slots=True)
class DatasetInfo:
    """
    Metadata describing one BharatFlux dataset.
    """

    site: str
    year: int
    file_type: str
    path: Path


@dataclass(slots=True)
class Dataset:
    """
    One loaded BharatFlux dataset.

    Attributes
    ----------
    info : DatasetInfo
        Metadata parsed from filename.

    data : pandas.DataFrame
        Loaded CSV.
    """

    info: DatasetInfo
    data: pd.DataFrame


# ============================================================
# File Discovery
# ============================================================

def list_csv_files(data_dir: Path) -> list[Path]:
    """
    Recursively list all CSV files.

    Parameters
    ----------
    data_dir : Path

    Returns
    -------
    list[Path]
    """

    return sorted(data_dir.rglob("*.csv"))


# ============================================================
# Filename Parsing
# ============================================================

def parse_filename(filepath: Path) -> DatasetInfo:
    """
    Parse BharatFlux filename.

    Examples
    --------
    BFT_2016_LE_ET_dmean.csv
    BKC_2014_ET_dmean.csv
    KNP_2016_LE_dmean.csv
    """

    name = filepath.stem

    # Combined LE + ET
    pattern_combined = (
        r"(?P<site>[A-Z]+)_(?P<year>\d{4})_(LE_ET|ET_LE)_dmean"
    )

    # LE only
    pattern_le = (
        r"(?P<site>[A-Z]+)_(?P<year>\d{4})_LE_dmean"
    )

    # ET only
    pattern_et = (
        r"(?P<site>[A-Z]+)_(?P<year>\d{4})_ET_dmean"
    )

    if match := re.fullmatch(pattern_combined, name):
        return DatasetInfo(
            site=match.group("site"),
            year=int(match.group("year")),
            file_type="combined",
            path=filepath,
        )

    if match := re.fullmatch(pattern_le, name):
        return DatasetInfo(
            site=match.group("site"),
            year=int(match.group("year")),
            file_type="LE_only",
            path=filepath,
        )

    if match := re.fullmatch(pattern_et, name):
        return DatasetInfo(
            site=match.group("site"),
            year=int(match.group("year")),
            file_type="ET_only",
            path=filepath,
        )

    raise ValueError(f"Unrecognized filename: {filepath.name}")


# ============================================================
# CSV Loader
# ============================================================

def load_csv(filepath: Path) -> pd.DataFrame:
    """
    Load one BharatFlux CSV.

    Parameters
    ----------
    filepath : Path

    Returns
    -------
    pandas.DataFrame
    """

    return pd.read_csv(filepath)


# ============================================================
# Load Everything
# ============================================================

def load_all(data_dir: Path) -> dict[str, Dataset]:
    """
    Load every BharatFlux CSV.

    Parameters
    ----------
    data_dir : Path

    Returns
    -------
    dict[str, Dataset]

    Example
    -------
    datasets["BFT_2016_LE_ET_dmean"].info.site
    datasets["BFT_2016_LE_ET_dmean"].data
    """

    datasets: dict[str, Dataset] = {}

    for filepath in list_csv_files(data_dir):

        info = parse_filename(filepath)

        df = load_csv(filepath)

        datasets[filepath.stem] = Dataset(
            info=info,
            data=df,
        )

    return datasets


# ============================================================
# Inventory Builder
# ============================================================

def build_inventory(
    datasets: dict[str, Dataset],
) -> pd.DataFrame:
    """
    Build a summary table of all datasets.

    Returns
    -------
    pandas.DataFrame
    """

    rows = []

    for name, dataset in datasets.items():

        rows.append(
            {
                "Dataset": name,
                "Site": dataset.info.site,
                "Year": dataset.info.year,
                "File Type": dataset.info.file_type,
                "Rows": len(dataset.data),
                "Columns": len(dataset.data.columns),
                "Column Names": ", ".join(dataset.data.columns),
                "Path": str(dataset.info.path),
            }
        )

    inventory = pd.DataFrame(rows)

    inventory = inventory.sort_values(
        ["Site", "Year", "File Type"]
    ).reset_index(drop=True)

    return inventory