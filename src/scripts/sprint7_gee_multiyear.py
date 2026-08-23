"""
OpenETBench Sprint 7 — GEE multi-year extension.

Extends the common-year GEE benchmark to all available BharatFlux
site-years (2014–2018), without changing the existing Sprint-4
benchmark logic.

Outputs
-------
results/summary/sprint7_gee/
    yearly_benchmark.csv
    gee_multiyear_report.json

Per site/product:
results/<SITE>/<PRODUCT>/
    extraction.csv       # combined raw benchmark pairs across all years
    benchmark.json       # pooled metrics across available years

Usage
-----
    python src/scripts/sprint7_gee_multiyear.py --all-sites --years 2014 2015 2016 2017 2018

Optional:
    --sites BFT BIT ...
    --products MOD16A2GF ERA5-LAND FLDAS GLDAS MERRA2 PMLV2
    --min-n 10
    --processed-dir PATH
    --results-root PATH

The script auto-discovers which site-years actually exist in the
processed BharatFlux directory, so unavailable site-years are skipped.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from benchmarking.metrics import calculate_metrics
from extraction.extractor import extract_timeseries
from extraction.gee import initialize
from extraction.products import ET_PRODUCTS, get_product
from extraction.sites import get_site
from harmonization.merge import merge_observed_satellite
from harmonization.temporal import align_to_common_dates
from utils.io import load_bharatflux
from utils.results import ensure_product_result_dir, save_benchmark, save_extraction


DEFAULT_PRODUCTS = [
    "MOD16A2GF",
    "ERA5-LAND",
    "FLDAS",
    "GLDAS",
    "MERRA2",
    "PMLV2",
]
DEFAULT_YEARS = [2014, 2015, 2016, 2017, 2018]
DEFAULT_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "bharatflux"
DEFAULT_RESULTS_ROOT = PROJECT_ROOT / "results"
DEFAULT_OUTPUT = DEFAULT_RESULTS_ROOT / "summary" / "sprint7_gee"


def _find_site_year_dataset(datasets: dict, site_id: str, year: int):
    matches = [
        dataset
        for dataset in datasets.values()
        if dataset.info.site.upper() == site_id.upper()
        and int(dataset.info.year) == int(year)
    ]

    if not matches:
        return None

    if len(matches) > 1:
        names = [dataset.info.path.name for dataset in matches]
        raise RuntimeError(
            f"Multiple processed BharatFlux datasets found for "
            f"{site_id} {year}: {names}"
        )

    return matches[0]


def _prepare_observations(dataset, year: int) -> pd.DataFrame:
    data = dataset.data.copy()

    required = {"DoY", "ET", "LE"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(
            f"{dataset.info.site} {year}: processed dataset is missing "
            f"columns: {', '.join(sorted(missing))}"
        )

    for col in ["DoY", "ET", "LE"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data = data.dropna(subset=["DoY", "ET"]).copy()
    data["DoY"] = data["DoY"].astype(int)

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


def _benchmark_one_year(
    *,
    site_id: str,
    year: int,
    product_id: str,
    observed: pd.DataFrame,
) -> pd.DataFrame:
    site = get_site(site_id)
    product = get_product(product_id)

    start_date = f"{year}-01-01"
    end_date = f"{year + 1}-01-01"

    satellite = extract_timeseries(
        site=site,
        product=product,
        start_date=start_date,
        end_date=end_date,
    )

    if satellite.empty:
        raise ValueError(
            f"{site_id}/{product_id}/{year}: GEE extraction returned no observations."
        )

    observed_aligned, satellite_aligned = align_to_common_dates(
        observed=observed,
        satellite=satellite,
    )

    if observed_aligned.empty or satellite_aligned.empty:
        raise ValueError(
            f"{site_id}/{product_id}/{year}: no common DoY values after temporal alignment."
        )

    merged = merge_observed_satellite(
        observed=observed_aligned,
        satellite=satellite_aligned,
    )

    if merged.empty:
        raise ValueError(
            f"{site_id}/{product_id}/{year}: benchmark dataframe is empty."
        )

    merged = merged.dropna(
        subset=["Observed_ET", "Satellite_ET"]
    ).reset_index(drop=True)

    if merged.empty:
        raise ValueError(
            f"{site_id}/{product_id}/{year}: no complete ET pairs remain."
        )

    return merged


def _year_record(
    site: str,
    product: str,
    year: int,
    merged: pd.DataFrame,
) -> dict:
    metrics = calculate_metrics(merged)

    return {
        "Site": site,
        "Product": product,
        "Year": year,
        "N": len(merged),
        "Start": merged["Date"].min().strftime("%Y-%m-%d"),
        "End": merged["Date"].max().strftime("%Y-%m-%d"),
        "RMSE": metrics.rmse,
        "MAE": metrics.mae,
        "BIAS": metrics.bias,
        "CORRELATION": metrics.correlation,
        "R2": metrics.r2,
        "STATUS": "BENCHMARKED",
        "SOURCE_LAYER": "GEE_MULTI_YEAR",
    }


def _classify_n(n: int) -> str:
    if n < 5:
        return "INSUFFICIENT"
    if n < 10:
        return "LIMITED"
    if n < 30:
        return "ADEQUATE"
    return "STRONG"


def run(
    *,
    sites: list[str] | None,
    products: list[str],
    years: list[int],
    processed_dir: Path,
    results_root: Path,
    output: Path,
    all_sites: bool,
    min_n: int,
) -> int:

    products = [p.strip().upper() for p in products]
    years = sorted(set(int(y) for y in years))

    for product_id in products:
        if product_id not in ET_PRODUCTS:
            raise ValueError(f"Unknown ET product: {product_id}")

    datasets = load_bharatflux(processed_dir)

    available = {
        (dataset.info.site.upper(), int(dataset.info.year))
        for dataset in datasets.values()
        if int(dataset.info.year) in years
    }

    if all_sites:
        sites = sorted({site for site, _ in available})
    else:
        sites = [s.strip().upper() for s in (sites or [])]

    for site_id in sites:
        get_site(site_id)

    print("=" * 72)
    print("SPRINT 7 — GEE MULTI-YEAR EXTENSION")
    print("=" * 72)
    print(f"Sites:    {', '.join(sites)}")
    print(f"Years:    {', '.join(map(str, years))}")
    print(f"Products: {', '.join(products)}")
    print(f"Minimum N: {min_n}")
    print("=" * 72)

    initialize()

    yearly_records: list[dict] = []
    failures: list[dict] = []

    for site_id in sites:
        site_years = [y for y in years if (site_id, y) in available]

        if not site_years:
            print(f"\n[{site_id}] no requested processed years found; skipping.")
            continue

        print(f"\n[{site_id}] available years: {', '.join(map(str, site_years))}")

        for product_id in products:
            combined_frames: list[pd.DataFrame] = []
            successful_years: list[int] = []

            for year in site_years:
                dataset = _find_site_year_dataset(
                    datasets, site_id, year
                )

                try:
                    observed = _prepare_observations(dataset, year)

                    print(
                        f"  → Extracting {product_id} for {site_id} ({year})"
                    )

                    merged = _benchmark_one_year(
                        site_id=site_id,
                        year=year,
                        product_id=product_id,
                        observed=observed,
                    )

                    record = _year_record(
                        site_id, product_id, year, merged
                    )
                    yearly_records.append(record)
                    combined_frames.append(merged.assign(Year=year))
                    successful_years.append(year)

                    print(
                        f"    ✓ {product_id:<12} N={len(merged):<4} "
                        f"RMSE={record['RMSE']:.3f} "
                        f"R={record['CORRELATION']:.3f}"
                    )

                except Exception as exc:
                    print(
                        f"    ✗ {product_id:<12} {year}: "
                        f"{type(exc).__name__}: {exc}"
                    )
                    failures.append({
                        "site": site_id,
                        "product": product_id,
                        "year": year,
                        "stage": "pipeline",
                        "error": f"{type(exc).__name__}: {exc}",
                    })

            # Replace the old common-year extraction with the complete
            # multi-year extraction for this site/product.
            if combined_frames:
                combined = pd.concat(
                    combined_frames,
                    ignore_index=True,
                )

                combined = combined.sort_values(
                    ["Date", "Year"]
                ).reset_index(drop=True)

                paths = ensure_product_result_dir(
                    site_id=site_id,
                    product_id=product_id,
                    results_root=results_root,
                )

                save_extraction(combined, paths)

                # Save pooled benchmark metadata for convenience.
                pooled = combined.dropna(
                    subset=["Observed_ET", "Satellite_ET"]
                )
                pooled_metrics = calculate_metrics(pooled)

                save_benchmark(
                    pooled_metrics,
                    paths,
                    site=site_id,
                    product=product_id,
                    start_date=pooled["Date"].min().strftime("%Y-%m-%d"),
                    end_date=(
                        pooled["Date"].max() + pd.Timedelta(days=1)
                    ).strftime("%Y-%m-%d"),
                    n=len(pooled),
                )

                print(
                    f"    ✓ pooled {product_id:<8} "
                    f"years={successful_years} N={len(pooled)}"
                )

    output.mkdir(parents=True, exist_ok=True)

    yearly = pd.DataFrame(yearly_records)

    if not yearly.empty:
        yearly["N"] = yearly["N"].astype(int)
        yearly["N_CATEGORY"] = yearly["N"].map(_classify_n)
        yearly["N_SUFFICIENT"] = yearly["N"] >= min_n
        yearly = yearly.sort_values(
            ["Product", "Site", "Year"]
        ).reset_index(drop=True)

    yearly_path = output / "yearly_benchmark.csv"
    report_path = output / "gee_multiyear_report.json"
    failure_path = output / "failures.json"

    yearly.to_csv(yearly_path, index=False)

    report = {
        "sprint": 7,
        "layer": "GEE_MULTI_YEAR",
        "sites": sites,
        "requested_years": years,
        "products": products,
        "yearly_records": int(len(yearly)),
        "primary_year_records": (
            int((yearly["N"] >= min_n).sum())
            if not yearly.empty else 0
        ),
        "failures": int(len(failures)),
        "available_site_years": {
            site: [
                y for y in years if (site, y) in available
            ]
            for site in sites
        },
    }

    report_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    if failures:
        failure_path.write_text(
            json.dumps(failures, indent=2),
            encoding="utf-8",
        )

    print("\nCreated:")
    print(f"  ✓ {yearly_path}")
    print(f"  ✓ {report_path}")
    if failures:
        print(f"  ⚠ {failure_path}")

    print("\nYear-level GEE coverage:")
    if yearly.empty:
        print("  No successful GEE benchmarks.")
    else:
        print(
            yearly.groupby(["Product", "Year"])
            .size()
            .rename("Site_Combinations")
            .reset_index()
            .to_string(index=False)
        )

    expected = sum(
        1 for site in sites
        for year in years
        if (site, year) in available
    ) * len(products)

    passed = len(yearly)
    failed = expected - passed

    print("\n" + "=" * 72)
    print(
        f"Sprint 7 GEE extension result: "
        f"{passed}/{expected} site-product-year combinations passed"
    )
    print(f"Failed: {failed}/{expected}")
    print("=" * 72)

    return 0 if failed == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("--sites", nargs="+", default=None)
    parser.add_argument("--all-sites", action="store_true")
    parser.add_argument("--products", nargs="+", default=DEFAULT_PRODUCTS)
    parser.add_argument("--years", nargs="+", type=int, default=DEFAULT_YEARS)
    parser.add_argument("--min-n", type=int, default=10)
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=DEFAULT_PROCESSED_DIR,
    )
    parser.add_argument(
        "--results-root",
        type=Path,
        default=DEFAULT_RESULTS_ROOT,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )

    args = parser.parse_args()

    if not args.all_sites and not args.sites:
        parser.error("Use either --all-sites or --sites SITE [SITE ...].")

    if args.min_n < 1:
        parser.error("--min-n must be >= 1")

    return run(
        sites=args.sites,
        products=args.products,
        years=args.years,
        processed_dir=args.processed_dir,
        results_root=args.results_root,
        output=args.output,
        all_sites=args.all_sites,
        min_n=args.min_n,
    )


if __name__ == "__main__":
    raise SystemExit(main())
