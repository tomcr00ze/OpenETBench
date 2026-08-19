"""
Sprint 7 — SSEBop V6.1 extraction and integration.

Purpose
-------
Integrate the externally downloaded SSEBop V6.1 monthly Actual ET product
into OpenETBench without using Google Earth Engine.

Pipeline
--------
SSEBop GeoTIFFs
    -> site-pixel extraction
    -> monthly BharatFlux aggregation
    -> year-specific benchmark
    -> multi-year benchmark
    -> common metrics

The script deliberately does not overwrite the Sprint 4-6 GEE benchmark.

Example
-------
python src/scripts/sprint7_ssebop.py ^
    --ssebop-zips "data/external/ssebop/SSEBop_2014_2015.zip" ^
                   "data/external/ssebop/SSEBop_2016_2018.zip" ^
    --sites BFT BIT BKC ^
    --processed-dir data/processed/bharatflux

All processed site-years can be auto-discovered with ``--all-sites``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from benchmarking.metrics import calculate_metrics
from extraction.sites import get_site, list_sites
from extraction.ssebop import (
    extract_monthly_timeseries,
    site_covered_by_ssebop,
    validate_inventory,
)
from harmonization.monthly import (
    aggregate_observed_to_monthly,
    merge_monthly_observed_product,
)
from utils.io import load_bharatflux


DEFAULT_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "bharatflux"
DEFAULT_OUTPUT = PROJECT_ROOT / "results" / "summary" / "sprint7_ssebop"
PRODUCT_ID = "SSEBOP_V61"


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


def _prepare_monthly_observations(
    dataset,
    year: int,
    min_daily_coverage: float,
) -> pd.DataFrame:
    return aggregate_observed_to_monthly(
        dataset.data,
        year,
        min_daily_coverage=min_daily_coverage,
    )


def _benchmark_one_year(
    observed_monthly: pd.DataFrame,
    product_monthly: pd.DataFrame,
    *,
    site: str,
    year: int,
) -> tuple[pd.DataFrame, dict]:
    merged = merge_monthly_observed_product(
        observed_monthly,
        product_monthly,
    )

    merged = merged.dropna(
        subset=["Observed_ET", "Satellite_ET"]
    ).reset_index(drop=True)

    if merged.empty:
        raise ValueError(
            f"{site}/SSEBOP/{year}: no complete monthly ET pairs."
        )

    metrics = calculate_metrics(
        merged.rename(
            columns={
                "Observed_ET": "Observed_ET",
                "Satellite_ET": "Satellite_ET",
            }
        )
    )

    record = {
        "Site": site,
        "Product": PRODUCT_ID,
        "Year": year,
        "N": len(merged),
        "Start": merged["Date"].min().strftime("%Y-%m-%d"),
        "End": merged["Date"].max().strftime("%Y-%m-%d"),
        "RMSE": metrics.rmse,
        "MAE": metrics.mae,
        "BIAS": metrics.bias,
        "CORRELATION": metrics.correlation,
        "R2": metrics.r2,
    }

    return merged, record


def run(
    *,
    ssebop_zips: list[Path],
    processed_dir: Path,
    output_dir: Path,
    sites: list[str] | None,
    years: list[int] | None,
    min_daily_coverage: float,
) -> int:
    print("=" * 72)
    print("SPRINT 7 — SSEBOP V6.1 EXTRACTION & INTEGRATION")
    print("=" * 72)

    print("\nValidating SSEBop inventory...")
    inventory = validate_inventory(ssebop_zips)

    if inventory.empty:
        raise ValueError("No SSEBop actual-ET rasters were found.")

    print(f"  ✓ Monthly rasters found: {len(inventory)}")
    print(
        "  ✓ Coverage:",
        f"{inventory.Year.min()}–{inventory.Year.max()}",
    )
    print(
        "  ✓ Versions:",
        ", ".join(sorted(inventory.Version.unique())),
    )

    expected_periods = {
        (year, month)
        for year in range(2014, 2019)
        for month in range(1, 13)
    }
    available_periods = set(
        zip(inventory["Year"], inventory["Month"])
    )
    missing_periods = sorted(expected_periods - available_periods)

    if missing_periods:
        print(f"  ⚠ Missing expected 2014–2018 months: {missing_periods}")
    else:
        print("  ✓ All 60 expected 2014–2018 months are present.")

    datasets = load_bharatflux(processed_dir)

    if sites is None:
        site_ids = list_sites()
    else:
        site_ids = [site.upper() for site in sites]

    for site_id in site_ids:
        get_site(site_id)

    if years is None:
        year_ids = list(range(2014, 2019))
    else:
        year_ids = sorted(set(int(y) for y in years))

    output_dir.mkdir(parents=True, exist_ok=True)

    yearly_records: list[dict] = []
    site_multi_records: list[dict] = []

    print("\nExtraction/benchmark scope:")
    print(f"  Sites: {', '.join(site_ids)}")
    print(f"  Years: {', '.join(map(str, year_ids))}")
    print(f"  Daily coverage threshold: {min_daily_coverage:.0%}")

    for site_id in site_ids:
        print(f"\n[{site_id}]")
        site = get_site(site_id)

        if not site_covered_by_ssebop(site, ssebop_zips):
            print(
                "  ⚠ Site is outside the spatial extent of the supplied "
                "SSEBop raster window; skipped."
            )
            continue

        site_frames: list[pd.DataFrame] = []

        for year in year_ids:
            dataset = _find_site_year_dataset(
                datasets,
                site_id,
                year,
            )

            if dataset is None:
                continue

            observed_monthly = _prepare_monthly_observations(
                dataset,
                year,
                min_daily_coverage,
            )

            product_monthly = extract_monthly_timeseries(
                site,
                ssebop_zips,
                start_year=year,
                end_year=year,
            )

            merged, record = _benchmark_one_year(
                observed_monthly,
                product_monthly,
                site=site_id,
                year=year,
            )

            merged["Site"] = site_id
            merged["Product"] = PRODUCT_ID
            merged["Year"] = year
            site_frames.append(merged)
            yearly_records.append(record)

            print(
                f"  ✓ {year}: N={record['N']:<2} "
                f"RMSE={record['RMSE']:.3f} "
                f"MAE={record['MAE']:.3f} "
                f"R={record['CORRELATION']:.3f}"
            )

        if not site_frames:
            print("  ⚠ No BharatFlux site-years available.")
            continue

        site_all = pd.concat(
            site_frames,
            ignore_index=True,
        ).sort_values("Date")

        # Pooled multi-year benchmark for this site/product. The source
        # year-specific records remain available in yearly_benchmark.csv.
        pooled = calculate_metrics(
            site_all.rename(
                columns={
                    "Observed_ET": "Observed_ET",
                    "Satellite_ET": "Satellite_ET",
                }
            )
        )

        site_multi_records.append(
            {
                "Site": site_id,
                "Product": PRODUCT_ID,
                "Years": ",".join(
                    map(
                        str,
                        sorted(site_all["Year"].unique()),
                    )
                ),
                "N": len(site_all),
                "Start": site_all["Date"].min().strftime("%Y-%m-%d"),
                "End": site_all["Date"].max().strftime("%Y-%m-%d"),
                "RMSE": pooled.rmse,
                "MAE": pooled.mae,
                "BIAS": pooled.bias,
                "CORRELATION": pooled.correlation,
                "R2": pooled.r2,
            }
        )

        # Keep one canonical site/product extraction artifact.
        site_dir = PROJECT_ROOT / "results" / site_id / PRODUCT_ID
        site_dir.mkdir(parents=True, exist_ok=True)
        site_all.to_csv(
            site_dir / "extraction.csv",
            index=False,
        )

    yearly = pd.DataFrame(yearly_records)
    multi = pd.DataFrame(site_multi_records)

    yearly_path = output_dir / "yearly_benchmark.csv"
    multi_path = output_dir / "multiyear_benchmark.csv"
    inventory_path = output_dir / "inventory.csv"

    yearly.to_csv(yearly_path, index=False)
    multi.to_csv(multi_path, index=False)
    inventory.to_csv(inventory_path, index=False)

    print("\nCreated:")
    print(f"  ✓ {inventory_path}")
    print(f"  ✓ {yearly_path}")
    print(f"  ✓ {multi_path}")
    print("\n" + "=" * 72)
    print("SSEBop extraction and integration completed successfully.")
    print("=" * 72)

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--ssebop-zips",
        nargs="+",
        type=Path,
        required=True,
        help="One or more ZIP files containing SSEBop actual-mm GeoTIFFs.",
    )
    parser.add_argument(
        "--sites",
        nargs="+",
        default=None,
        help="BharatFlux site IDs. Defaults to all registered sites.",
    )
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=None,
        help="Inclusive benchmark years to process. Defaults to 2014–2018.",
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=DEFAULT_PROCESSED_DIR,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )
    parser.add_argument(
        "--min-daily-coverage",
        type=float,
        default=0.80,
        help="Minimum valid daily ET fraction required to form a monthly total.",
    )

    args = parser.parse_args()

    if not 0 < args.min_daily_coverage <= 1:
        raise ValueError("--min-daily-coverage must be in (0, 1].")

    return run(
        ssebop_zips=args.ssebop_zips,
        processed_dir=args.processed_dir,
        output_dir=args.output,
        sites=args.sites,
        years=args.years,
        min_daily_coverage=args.min_daily_coverage,
    )


if __name__ == "__main__":
    raise SystemExit(main())
