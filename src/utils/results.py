"""
OpenETBench
-----------

Standardized result-path and export utilities for product benchmarking.

Sprint 1 responsibilities
-------------------------
- Keep all product outputs under ``results/<site>/<product>/``.
- Provide stable paths for extraction, benchmark, and figure artifacts.
- Export benchmark-ready data and JSON metadata consistently.

The module deliberately contains no GEE or benchmarking logic. It only
handles the filesystem/output contract used by the pipeline.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
import json
from pathlib import Path
from typing import Any

import pandas as pd


# ============================================================
# Result Paths
# ============================================================

@dataclass(frozen=True)
class ProductResultPaths:
    """Standard output paths for one site/product benchmark run."""

    root: Path
    extraction: Path
    benchmark: Path
    scatter: Path
    timeseries: Path
    map: Path


def project_root() -> Path:
    """Return the OpenETBench project root."""

    return Path(__file__).resolve().parents[2]


def get_product_result_paths(
    site_id: str,
    product_id: str,
    results_root: Path | None = None,
) -> ProductResultPaths:
    """
    Return the canonical output paths for one site/product run.

    Parameters
    ----------
    site_id:
        BharatFlux site identifier, e.g. ``BFT``.
    product_id:
        Stable product identifier, e.g. ``MOD16A2GF``.
    results_root:
        Optional override for the project's ``results`` directory.

    Returns
    -------
    ProductResultPaths
        Paths for the result directory and all standard artifacts.
    """

    site = site_id.strip().upper()
    product = product_id.strip().upper()

    if not site:
        raise ValueError("site_id must not be empty.")
    if not product:
        raise ValueError("product_id must not be empty.")

    root = (
        Path(results_root)
        if results_root is not None
        else project_root() / "results"
    ) / site / product

    return ProductResultPaths(
        root=root,
        extraction=root / "extraction.csv",
        benchmark=root / "benchmark.json",
        scatter=root / "scatter.png",
        timeseries=root / "timeseries.png",
        map=root / "map.png",
    )


def ensure_product_result_dir(
    site_id: str,
    product_id: str,
    results_root: Path | None = None,
) -> ProductResultPaths:
    """
    Create the canonical result directory and return its paths.
    """

    paths = get_product_result_paths(
        site_id=site_id,
        product_id=product_id,
        results_root=results_root,
    )
    paths.root.mkdir(parents=True, exist_ok=True)
    return paths


# ============================================================
# Data Export
# ============================================================

def save_extraction(
    dataframe: pd.DataFrame,
    paths: ProductResultPaths,
) -> Path:
    """Save the benchmark-ready extraction dataframe as CSV."""

    paths.root.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(paths.extraction, index=False)
    return paths.extraction


def _json_safe(value: Any) -> Any:
    """Convert common Python/numpy/path/dataclass values to JSON-safe values."""

    if is_dataclass(value):
        return _json_safe(asdict(value))

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]

    # numpy scalar support without making numpy a hard dependency here.
    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, TypeError):
            pass

    return value


def save_benchmark(
    report: Any,
    paths: ProductResultPaths,
    *,
    site: str,
    product: str,
    start_date: str,
    end_date: str,
    n: int,
) -> Path:
    """
    Save benchmark metrics and run metadata as JSON.

    ``report`` may be a ``MetricsReport`` dataclass or a mapping.
    """

    paths.root.mkdir(parents=True, exist_ok=True)

    if is_dataclass(report):
        metrics = asdict(report)
    elif isinstance(report, dict):
        metrics = dict(report)
    else:
        raise TypeError(
            "report must be a dataclass instance or a dictionary."
        )

    payload = {
        "site": site,
        "product": product,
        "period": {
            "start": start_date,
            "end": end_date,
        },
        "n": int(n),
        "metrics": metrics,
    }

    with paths.benchmark.open("w", encoding="utf-8") as handle:
        json.dump(
            _json_safe(payload),
            handle,
            indent=4,
        )

    return paths.benchmark
