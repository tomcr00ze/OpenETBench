"""Run Sprint 3 visualization generation for existing benchmark outputs.

Expected result contract for each product::

    results/<site>/<product>/
        extraction.csv
        benchmark.json

The script creates/refreshes::

    scatter.png
    timeseries.png
    map.png

It intentionally does not rerun Google Earth Engine extraction or modify
benchmark metrics.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from benchmarking.metrics import MetricsReport
from extraction.products import ET_PRODUCTS
from extraction.sites import get_site
from utils.results import get_product_result_paths
from visualization.pipeline import generate_product_visualizations

DEFAULT_PRODUCTS = [
    "MOD16A2GF",
    "ERA5-LAND",
    "FLDAS",
    "GLDAS",
    "MERRA2",
    "PMLV2",
]


def _load_metrics(path: Path) -> MetricsReport:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    return MetricsReport(
        rmse=float(payload["rmse"]),
        mae=float(payload["mae"]),
        bias=float(payload["bias"]),
        correlation=float(payload["correlation"]),
        r2=float(payload["r2"]),
    )


def _validate_input(data: pd.DataFrame, product: str) -> None:
    required = {"Date", "Observed_ET", "Satellite_ET"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(
            f"{product}: extraction.csv is missing columns: "
            + ", ".join(sorted(missing))
        )
    if data.empty:
        raise ValueError(f"{product}: extraction.csv is empty.")


def run(site_id: str, results_root: Path, products: list[str]) -> int:
    site = get_site(site_id)
    passed = 0

    print("=" * 64)
    print("SPRINT 3 VALIDATION")
    print("=" * 64)

    for product in products:
        product = product.upper()
        if product not in ET_PRODUCTS:
            print(f"✗ {product:<12} unknown product")
            continue

        paths = get_product_result_paths(
            site_id=site.id,
            product_id=product,
            results_root=results_root,
        )

        try:
            if not paths.extraction.exists():
                raise FileNotFoundError(paths.extraction)
            if not paths.benchmark.exists():
                raise FileNotFoundError(paths.benchmark)

            merged = pd.read_csv(paths.extraction)
            _validate_input(merged, product)
            metrics = _load_metrics(paths.benchmark)

            generate_product_visualizations(
                merged=merged,
                metrics=metrics,
                site=site,
                product_name=product,
                results_root=results_root,
            )

            expected = [paths.scatter, paths.timeseries, paths.map]
            missing_outputs = [str(path) for path in expected if not path.exists()]
            if missing_outputs:
                raise RuntimeError(
                    "Missing generated outputs: " + ", ".join(missing_outputs)
                )

            print(f"✓ {product:<12} scatter ✓  timeseries ✓  map ✓")
            passed += 1

        except Exception as exc:
            print(f"✗ {product:<12} {type(exc).__name__}: {exc}")

    print("-" * 64)
    print(f"Passed: {passed}/{len(products)}")
    print(f"Failed: {len(products) - passed}/{len(products)}")
    print("=" * 64)

    return 0 if passed == len(products) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", default="BFT")
    parser.add_argument("--results-root", type=Path, default=Path("results"))
    parser.add_argument(
        "--products",
        nargs="+",
        default=DEFAULT_PRODUCTS,
        help="Product IDs to validate.",
    )
    args = parser.parse_args()
    return run(args.site, args.results_root, args.products)


if __name__ == "__main__":
    raise SystemExit(main())
