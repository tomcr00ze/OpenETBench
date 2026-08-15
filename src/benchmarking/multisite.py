"""
OpenETBench
-----------

Utilities for consolidating benchmark results across multiple sites.

Sprint 4 responsibilities
--------------------------
- Convert individual site/product benchmark reports into a common table.
- Save a consolidated multi-site benchmark summary.

This module deliberately does not perform extraction, harmonization, or
visualization. Those responsibilities remain in their existing modules.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import pandas as pd


REQUIRED_METRICS = [
    "rmse",
    "mae",
    "bias",
    "correlation",
    "r2",
]


def build_multisite_summary(
    records: Iterable[dict],
) -> pd.DataFrame:
    """Build a standardized site × product benchmark table."""

    rows = []

    for record in records:
        row = {
            "Site": record["site"],
            "Product": record["product"],
            "Year": int(record["year"]),
            "N": int(record["n"]),
            "Start": record["start_date"],
            "End": record["end_date"],
        }

        metrics = record["metrics"]
        for metric in REQUIRED_METRICS:
            value = metrics.get(metric)
            row[metric.upper()] = float(value) if value is not None else None

        rows.append(row)

    columns = [
        "Site",
        "Product",
        "Year",
        "N",
        "Start",
        "End",
        "RMSE",
        "MAE",
        "BIAS",
        "CORRELATION",
        "R2",
    ]

    if not rows:
        return pd.DataFrame(columns=columns)

    return (
        pd.DataFrame(rows)
        .sort_values(["Site", "Product"])
        .reset_index(drop=True)
    )


def save_multisite_summary(
    summary: pd.DataFrame,
    output_dir: Path,
) -> tuple[Path, Path]:
    """Save the consolidated benchmark as CSV and JSON."""

    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "multisite_benchmark.csv"
    json_path = output_dir / "multisite_benchmark.json"

    summary.to_csv(csv_path, index=False)

    payload = {
        "n_site_product_combinations": int(len(summary)),
        "sites": sorted(summary["Site"].dropna().unique().tolist()),
        "products": sorted(summary["Product"].dropna().unique().tolist()),
        "results": summary.to_dict(orient="records"),
    }

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=4, allow_nan=False)

    return csv_path, json_path
