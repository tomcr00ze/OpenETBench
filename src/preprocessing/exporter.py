"""
OpenETBench
-----------

Result export utilities.

Responsibilities
----------------
- Export extracted ET time series
- Export benchmark statistics
- Keep result-writing consistent across products
"""

from dataclasses import asdict, is_dataclass
import json
from pathlib import Path

import pandas as pd


def export_extraction(
    dataframe: pd.DataFrame,
    output_dir: Path,
) -> Path:
    """
    Export extracted/harmonized benchmark dataframe.
    """

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = output_dir / "extraction.csv"

    dataframe.to_csv(
        path,
        index=False,
    )

    return path


def export_benchmark(
    metrics,
    output_dir: Path,
) -> Path:
    """
    Export benchmark statistics as JSON.
    """

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = output_dir / "benchmark.json"

    if is_dataclass(metrics):
        data = asdict(metrics)
    elif isinstance(metrics, dict):
        data = metrics
    else:
        raise TypeError(
            "metrics must be a dataclass or dictionary."
        )

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            data,
            f,
            indent=4,
        )

    return path


def export_results(
    dataframe: pd.DataFrame,
    metrics,
    output_dir: Path,
) -> tuple[Path, Path]:
    """
    Export complete benchmark results.
    """

    extraction_path = export_extraction(
        dataframe,
        output_dir,
    )

    benchmark_path = export_benchmark(
        metrics,
        output_dir,
    )

    return (
        extraction_path,
        benchmark_path,
    )