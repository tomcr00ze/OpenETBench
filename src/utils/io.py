"""
OpenETBench
-----------

Input / Output utilities.

Responsibilities
----------------
- Save processed BharatFlux datasets
- Load processed BharatFlux datasets
- Save validation summary
- Load validation summary

Author: Adarsh Jha
"""

from dataclasses import asdict
import json
from pathlib import Path

import pandas as pd

# pyrefly: ignore [missing-import]
from preprocessing.loader import (
    DatasetInfo,
    BharatFluxDataset,
)


# ============================================================
# Save BharatFlux Datasets
# ============================================================

def save_bharatflux(
    datasets: dict[str, BharatFluxDataset],
    output_dir: Path,
) -> None:
    """
    Save processed BharatFlux datasets.

    Each dataset is stored as

        <dataset>.parquet
        <dataset>.json

    The parquet file stores the dataframe while the JSON file
    stores DatasetInfo metadata.

    Parameters
    ----------
    datasets : dict[str, BharatFluxDataset]
        Cleaned BharatFlux datasets.

    output_dir : Path
        Output directory.
    """

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    for name, dataset in datasets.items():

        parquet_path = output_dir / f"{name}.parquet"
        metadata_path = output_dir / f"{name}.json"

        # Save dataframe
        dataset.data.to_parquet(
            parquet_path,
            index=False,
        )

        # Convert dataclass to dictionary
        metadata = asdict(dataset.info)

        # Convert Path object to string for JSON serialization
        metadata["path"] = str(metadata["path"])
        
        with open(metadata_path, "w") as f:
            json.dump(
                metadata,
                f,
                indent=4,
            )


# ============================================================
# Load BharatFlux Datasets
# ============================================================

def load_bharatflux(
    input_dir: Path,
) -> dict[str, BharatFluxDataset]:
    """
    Load processed BharatFlux datasets.

    Parameters
    ----------
    input_dir : Path

    Returns
    -------
    dict[str, BharatFluxDataset]
    """

    datasets = {}

    for parquet_path in sorted(
        input_dir.glob("*.parquet")
    ):

        dataset_name = parquet_path.stem

        metadata_path = input_dir / f"{dataset_name}.json"

        if not metadata_path.exists():
            raise FileNotFoundError(
                f"Missing metadata file: {metadata_path.name}"
            )

        # Load dataframe
        df = pd.read_parquet(parquet_path)

        # Load metadata
        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        # Convert serialized Path string back to Path object
        metadata["path"] = Path(metadata["path"])

        info = DatasetInfo(**metadata)

        datasets[dataset_name] = BharatFluxDataset(
            info=info,
            data=df,
        )

    return datasets


# ============================================================
# Save Validation Summary
# ============================================================

def save_validation_summary(
    validation_summary: pd.DataFrame,
    output_dir: Path,
) -> None:
    """
    Save validation summary.

    Parameters
    ----------
    validation_summary : pandas.DataFrame

    output_dir : Path
    """

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    validation_summary.to_csv(
        output_dir / "validation_summary.csv",
        index=False,
    )


# ============================================================
# Load Validation Summary
# ============================================================

def load_validation_summary(
    input_dir: Path,
) -> pd.DataFrame:
    """
    Load validation summary.

    Parameters
    ----------
    input_dir : Path

    Returns
    -------
    pandas.DataFrame
    """

    summary_path = (
        input_dir /
        "validation_summary.csv"
    )

    if not summary_path.exists():
        raise FileNotFoundError(
            "validation_summary.csv not found."
        )

    return pd.read_csv(summary_path)