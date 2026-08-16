"""
Run Sprint 4 multi-site validation for the GEE-backed ET products.

The runner intentionally reuses the existing OpenETBench modules:

    BharatFlux observations
            ↓
    GEE extraction
            ↓
    temporal harmonization
            ↓
    benchmark merge
            ↓
    metrics
            ↓
    standard visualizations
            ↓
    site/product results

Default validation scope:

    Sites:    BFT, BIT, BKC
    Year:     2016
    Products: MOD16A2GF, ERA5-LAND, FLDAS, GLDAS, MERRA2, PMLV2

Each successful combination is written to:

    results/<SITE>/<PRODUCT>/
        extraction.csv
        benchmark.json
        scatter.png
        timeseries.png
        map.png

A consolidated summary is written to:

    results/summary/
        multisite_benchmark.csv
        multisite_benchmark.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Project import path
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from benchmarking.metrics import calculate_metrics
from benchmarking.multisite import build_multisite_summary, save_multisite_summary
from extraction.extractor import extract_timeseries
from extraction.gee import initialize
from extraction.products import ET_PRODUCTS, get_product
from extraction.sites import get_site
from harmonization.merge import merge_observed_satellite
from harmonization.temporal import align_to_common_dates
from utils.io import load_bharatflux
from utils.results import (
    ensure_product_result_dir,
    save_benchmark,
    save_extraction,
)
from visualization.pipeline import generate_product_visualizations


DEFAULT_SITES = ["BFT", "BIT", "BKC"]
DEFAULT_PRODUCTS = [
    "MOD16A2GF",
    "ERA5-LAND",
    "FLDAS",
    "GLDAS",
    "MERRA2",
    "PMLV2",
]
DEFAULT_YEAR = 2016
DEFAULT_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "bharatflux"
DEFAULT_RESULTS_ROOT = PROJECT_ROOT / "results"


def _find_site_year_dataset(
    datasets: dict,
    site_id: str,
    year: int,
):
    """Find the processed BharatFlux dataset for one site and year."""

    matches = [
        dataset
        for dataset in datasets.values()
        if dataset.info.site.upper() == site_id.upper()
        and int(dataset.info.year) == int(year)
    ]

    if not matches:
        raise FileNotFoundError(
            f"No processed BharatFlux dataset found for {site_id} {year}."
        )

    if len(matches) > 1:
        names = [dataset.info.path.name for dataset in matches]
        raise RuntimeError(
            f"Multiple processed BharatFlux datasets found for "
            f"{site_id} {year}: {names}"
        )

    return matches[0]


def _prepare_observations(dataset, year: int) -> pd.DataFrame:
    """Prepare one processed BharatFlux site-year for benchmarking."""

    data = dataset.data.copy()

    required = {"DoY", "ET"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(
            f"{dataset.info.site} {year}: processed dataset is missing "
            f"columns: {', '.join(sorted(missing))}"
        )

    # The benchmark merge currently keeps Observed_LE as part of its
    # canonical output contract. If LE is unavailable, fail explicitly
    # instead of silently fabricating it.
    if "LE" not in data.columns:
        raise ValueError(
            f"{dataset.info.site} {year}: processed dataset does not contain LE."
        )

    data["DoY"] = pd.to_numeric(data["DoY"], errors="coerce")
    data["ET"] = pd.to_numeric(data["ET"], errors="coerce")
    data["LE"] = pd.to_numeric(data["LE"], errors="coerce")

    data = data.dropna(subset=["DoY", "ET"]).copy()
    data["DoY"] = data["DoY"].astype(int)

    # Convert DoY to a real calendar date for the common output contract.
    data["Date"] = (
        pd.Timestamp(year=year, month=1, day=1)
        + pd.to_timedelta(data["DoY"] - 1, unit="D")
    )

    return (
        data[["Date", "DoY", "LE", "ET"]]
        .sort_values("DoY")
        .drop_duplicates(subset=["DoY"])
        .reset_index(drop=True)
    )


def _run_one_product(
    *,
    site_id: str,
    year: int,
    product_id: str,
    observed: pd.DataFrame,
    results_root: Path,
) -> dict:
    """Run the complete common pipeline for one site/product combination."""

    site = get_site(site_id)
    product = get_product(product_id)

    start_date = f"{year}-01-01"
    end_date = f"{year + 1}-01-01"

    print(f"    → Extracting {product_id} for {site_id} ({year})")

    satellite = extract_timeseries(
        site=site,
        product=product,
        start_date=start_date,
        end_date=end_date,
    )

    if satellite.empty:
        raise ValueError(
            f"{site_id}/{product_id}: GEE extraction returned no observations."
        )

    observed_aligned, satellite_aligned = align_to_common_dates(
        observed=observed,
        satellite=satellite,
    )

    if observed_aligned.empty or satellite_aligned.empty:
        raise ValueError(
            f"{site_id}/{product_id}: no common DoY values after temporal alignment."
        )

    merged = merge_observed_satellite(
        observed=observed_aligned,
        satellite=satellite_aligned,
    )

    if merged.empty:
        raise ValueError(
            f"{site_id}/{product_id}: benchmark dataframe is empty."
        )

    # Benchmark metrics operate only on complete observation/product pairs.
    merged = merged.dropna(subset=["Observed_ET", "Satellite_ET"]).reset_index(drop=True)

    if merged.empty:
        raise ValueError(
            f"{site_id}/{product_id}: no complete ET pairs remain for benchmarking."
        )

    metrics = calculate_metrics(merged)

    paths = ensure_product_result_dir(
        site_id=site_id,
        product_id=product_id,
        results_root=results_root,
    )

    save_extraction(merged, paths)
    save_benchmark(
        metrics,
        paths,
        site=site_id,
        product=product_id,
        start_date=start_date,
        end_date=end_date,
        n=len(merged),
    )

    generate_product_visualizations(
        merged=merged,
        metrics=metrics,
        site=site,
        product_name=product_id,
        results_root=results_root,
        year=year,
    )

    return {
        "site": site_id,
        "product": product_id,
        "year": year,
        "n": len(merged),
        "start_date": start_date,
        "end_date": end_date,
        "metrics": {
            "rmse": metrics.rmse,
            "mae": metrics.mae,
            "bias": metrics.bias,
            "correlation": metrics.correlation,
            "r2": metrics.r2,
        },
    }


def run(
    *,
    sites: list[str] | None,
    products: list[str],
    year: int,
    processed_dir: Path,
    results_root: Path,
    all_sites: bool = False,
) -> int:
    """Run Sprint 4 validation and create the consolidated benchmark."""

    products = [product.strip().upper() for product in products]

    for product_id in products:
        if product_id not in ET_PRODUCTS:
            raise ValueError(f"Unknown ET product: {product_id}")

    if not processed_dir.exists():
        raise FileNotFoundError(
            f"Processed BharatFlux directory not found: {processed_dir}"
        )

    print("=" * 72)
    print("SPRINT 4 — MULTI-SITE VALIDATION")
    print("=" * 72)
    print(f"Sites:    {', '.join(sites)}")
    print(f"Year:     {year}")
    print(f"Products: {', '.join(products)}")
    print("=" * 72)

    initialize()

    print("Loading processed BharatFlux datasets...")
    datasets = load_bharatflux(processed_dir)

    if all_sites:
        sites = sorted(
            {
                dataset.info.site.upper()
                for dataset in datasets.values()
                if int(dataset.info.year) == int(year)
            }
        )

        if not sites:
            raise FileNotFoundError(
                f"No processed BharatFlux datasets found for year {year}."
            )

        print(
            f"Auto-discovered {len(sites)} processed sites for {year}: "
            f"{', '.join(sites)}"
        )
    else:
        sites = [
            site.strip().upper()
            for site in (sites or [])
        ]

    # Validate requested/discovered sites against the site registry.
    for site_id in sites:
        get_site(site_id)

    records: list[dict] = []
    failures: list[dict] = []

    for site_id in sites:
        print(f"\n[{site_id}]")

        try:
            dataset = _find_site_year_dataset(datasets, site_id, year)
            observed = _prepare_observations(dataset, year)
            print(
                f"  ✓ observations: {len(observed)} rows, "
                f"DoY {observed['DoY'].min()}–{observed['DoY'].max()}"
            )
        except Exception as exc:
            print(f"  ✗ observation preparation failed: {type(exc).__name__}: {exc}")
            for product_id in products:
                failures.append(
                    {
                        "site": site_id,
                        "product": product_id,
                        "stage": "observations",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
            continue

        for product_id in products:
            try:
                record = _run_one_product(
                    site_id=site_id,
                    year=year,
                    product_id=product_id,
                    observed=observed,
                    results_root=results_root,
                )
                records.append(record)

                metrics = record["metrics"]
                print(
                    f"    ✓ {product_id:<12} "
                    f"N={record['n']:<4} "
                    f"RMSE={metrics['rmse']:.3f} "
                    f"R={metrics['correlation']:.3f}"
                )

            except Exception as exc:
                print(
                    f"    ✗ {product_id:<12} "
                    f"{type(exc).__name__}: {exc}"
                )
                failures.append(
                    {
                        "site": site_id,
                        "product": product_id,
                        "stage": "pipeline",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )

    summary = build_multisite_summary(records)
    summary_dir = results_root / "summary"

    if not summary.empty:
        csv_path, json_path = save_multisite_summary(summary, summary_dir)
        print("\nConsolidated benchmark:")
        print(summary.to_string(index=False))
        print(f"\n✓ Summary CSV:  {csv_path}")
        print(f"✓ Summary JSON: {json_path}")

    if failures:
        failure_path = summary_dir / "multisite_failures.json"
        summary_dir.mkdir(parents=True, exist_ok=True)
        with failure_path.open("w", encoding="utf-8") as handle:
            json.dump(failures, handle, indent=4)
        print(f"⚠ Failure log:  {failure_path}")

    expected = len(sites) * len(products)
    passed = len(records)
    failed = expected - passed

    print("\n" + "=" * 72)
    print(f"Sprint 4 result: {passed}/{expected} site-product combinations passed")
    print(f"Failed: {failed}/{expected}")
    print("=" * 72)

    return 0 if failed == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sites",
        nargs="+",
        default=DEFAULT_SITES,
        help="BharatFlux site IDs.",
    )
    parser.add_argument(
        "--all-sites",
        action="store_true",
        help=(
            "Automatically discover all processed BharatFlux sites "
            "available for the requested year."
        ),
    )
    parser.add_argument(
        "--products",
        nargs="+",
        default=DEFAULT_PRODUCTS,
        help="ET product IDs.",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=DEFAULT_YEAR,
        help="BharatFlux year to benchmark.",
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=DEFAULT_PROCESSED_DIR,
        help="Processed BharatFlux directory.",
    )
    parser.add_argument(
        "--results-root",
        type=Path,
        default=DEFAULT_RESULTS_ROOT,
        help="Results directory.",
    )

    args = parser.parse_args()

    return run(
        sites=args.sites,
        products=args.products,
        year=args.year,
        processed_dir=args.processed_dir,
        results_root=args.results_root,
        all_sites=args.all_sites,
    )


if __name__ == "__main__":
    raise SystemExit(main())
