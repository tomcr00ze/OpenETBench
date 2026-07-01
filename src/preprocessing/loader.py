"""
OpenETBench - BharatFlux Data Loader

This module is responsible for discovering and loading BharatFlux CSV files.
No cleaning or preprocessing is performed here.

Author: Adarsh Jha
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Dict, List

import pandas as pd

logger = logging.getLogger(__name__)


# ------------------------------------------------------------
# Filename Patterns
# ------------------------------------------------------------

COMBINED_PATTERN = re.compile(
    r"^(?P<site>[A-Z]{3})_(?P<year>\d{4})_(LE_ET|ET_LE)_dmean\.csv$",
    re.IGNORECASE,
)

LE_PATTERN = re.compile(
    r"^(?P<site>[A-Z]{3})_(?P<year>\d{4})_LE_dmean\.csv$",
    re.IGNORECASE,
)

ET_PATTERN = re.compile(
    r"^(?P<site>[A-Z]{3})_(?P<year>\d{4})_ET_dmean\.csv$",
    re.IGNORECASE,
)


# ------------------------------------------------------------
# Public Functions
# ------------------------------------------------------------

def list_csv_files(root_dir: str | Path) -> List[Path]:
    """
    Recursively find all CSV files.

    Parameters
    ----------
    root_dir : str or Path

    Returns
    -------
    List[Path]
    """

    root_dir = Path(root_dir)

    if not root_dir.exists():
        raise FileNotFoundError(f"{root_dir} does not exist.")

    files = sorted(root_dir.rglob("*.csv"))

    logger.info("Found %d CSV files.", len(files))

    return files


def parse_filename(path: str | Path) -> Dict:
    """
    Parse BharatFlux filename.

    Returns
    -------
    dict

    Example
    -------
    BFT_2016_LE_ET_dmean.csv

    ->
    {
        "site":"BFT",
        "year":2016,
        "file_type":"combined"
    }
    """

    filename = Path(path).name

    if match := COMBINED_PATTERN.match(filename):
        return {
            "site": match.group("site"),
            "year": int(match.group("year")),
            "file_type": "combined",
        }

    if match := LE_PATTERN.match(filename):
        return {
            "site": match.group("site"),
            "year": int(match.group("year")),
            "file_type": "LE_only",
        }

    if match := ET_PATTERN.match(filename):
        return {
            "site": match.group("site"),
            "year": int(match.group("year")),
            "file_type": "ET_only",
        }

    raise ValueError(f"Unrecognized filename format: {filename}")


def load_csv(path: str | Path) -> pd.DataFrame:
    """
    Load a BharatFlux CSV file.

    Parameters
    ----------
    path : str or Path

    Returns
    -------
    pandas.DataFrame
    """

    path = Path(path)

    df = pd.read_csv(path)

    logger.info("Loaded %s (%d rows)", path.name, len(df))

    return df


def load_all(root_dir: str | Path) -> Dict[str, Dict]:
    """
    Load every BharatFlux CSV.

    Returns
    -------
    dict

    {
        "BFT_2016": {
            ...
        }
    }
    """

    datasets = {}

    files = list_csv_files(root_dir)

    for file in files:

        metadata = parse_filename(file)

        key = file.stem

        datasets[key] = {
            "site": metadata["site"],
            "year": metadata["year"],
            "file_type": metadata["file_type"],
            "path": file,
            "data": load_csv(file),
        }

    logger.info("Loaded %d datasets.", len(datasets))

    return datasets