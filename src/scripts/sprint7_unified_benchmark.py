"""
OpenETBench Sprint 7 — Unified multi-year benchmark.

Combines:
1. Existing GEE Sprint-4 benchmark rows
   results/summary/multisite_benchmark.csv
2. External-product year-level benchmark rows (currently SSEBop V6.1)
   results/summary/sprint7_ssebop/yearly_benchmark.csv

Then produces:
- Product × Site × Year benchmark
- Year-level QC
- Product × Site pooled multi-year benchmark
- Product-level multi-year comparison
- Product/site/year coverage matrix

Important:
The pooled multi-year metrics are calculated from the underlying extraction
files when available, rather than averaging yearly RMSE/MAE values.

Current project structure:
    results/<SITE>/<PRODUCT>/extraction.csv

For GEE products, the Sprint-7 GEE extension produces the available 2014–2018
site-year benchmark layer. SSEBop extraction files contain the available
2014–2018 monthly observations. Therefore the script reports actual year
coverage explicitly; it does not pretend that every product has the same
multi-year coverage.

Usage:
    python src/scripts/sprint7_unified_benchmark.py --min-n 10

Optional:
    --gee-benchmark PATH
    --ssebop-benchmark PATH
    --results-root PATH
    --output PATH
    --min-n INTEGER

The script is intentionally conservative:
- N=0/no-overlap rows are retained in the year-level table.
- Primary multi-year comparisons require pooled N >= min-N.
- Products with different temporal coverage remain labelled with their
  actual available years.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_RESULTS_ROOT = PROJECT_ROOT / "results"
DEFAULT_GEE_BENCHMARK = (
    DEFAULT_RESULTS_ROOT / "summary" / "sprint7_gee" / "yearly_benchmark.csv"
)
DEFAULT_SSEBOP_BENCHMARK = (
    DEFAULT_RESULTS_ROOT / "summary" / "sprint7_ssebop" / "yearly_benchmark.csv"
)
DEFAULT_OUTPUT = (
    DEFAULT_RESULTS_ROOT / "summary" / "sprint7_unified"
)

REQUIRED_YEARLY = {
    "Site", "Product", "Year", "N", "RMSE", "MAE",
    "BIAS", "CORRELATION", "R2"
}

METRICS = ["RMSE", "MAE", "ABS_BIAS", "CORRELATION", "R2"]


def classify_n(n: int) -> str:
    """Use the project's Sprint-5 convention."""
    if n < 5:
        return "INSUFFICIENT"
    if n < 10:
        return "LIMITED"
    if n < 30:
        return "ADEQUATE"
    return "STRONG"


def load_yearly(path: Path, source_layer: str) -> pd.DataFrame:
    """Load and normalize one year-level benchmark table."""
    if not path.exists():
        raise FileNotFoundError(f"Benchmark CSV not found: {path}")

    df = pd.read_csv(path)

    missing = REQUIRED_YEARLY - set(df.columns)
    if missing:
        raise ValueError(
            f"{path} is missing required columns: {sorted(missing)}"
        )

    df = df.copy()
    df["Site"] = df["Site"].astype(str).str.upper()
    df["Product"] = df["Product"].astype(str).str.upper()

    for c in ["Year", "N", "RMSE", "MAE", "BIAS", "CORRELATION", "R2"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["Year"] = df["Year"].astype("Int64")
    df["N"] = df["N"].fillna(0).astype(int)

    df["ABS_BIAS"] = df["BIAS"].abs()
    df["N_CATEGORY"] = df["N"].map(classify_n)
    df["N_SUFFICIENT"] = df["N"] >= 10
    df["SOURCE_LAYER"] = source_layer

    if "STATUS" not in df.columns:
        df["STATUS"] = np.where(
            df["N"] > 0,
            "BENCHMARKED",
            "NO_VALID_OVERLAP",
        )

    return df


def load_raw_extractions(
    results_root: Path,
) -> pd.DataFrame:
    """
    Discover raw extraction.csv files and concatenate them.

    Expected columns:
        Date, Observed_ET, Satellite_ET

    Site/Product are inferred from:
        results/<SITE>/<PRODUCT>/extraction.csv
    """
    rows = []

    for path in results_root.glob("*/*/extraction.csv"):
        if path.parent.parent.name == "summary":
            continue

        site = path.parent.parent.name.upper()
        product = path.parent.name.upper()

        try:
            df = pd.read_csv(path)
        except Exception:
            continue

        if not {"Date", "Observed_ET", "Satellite_ET"}.issubset(df.columns):
            continue

        x = df[["Date", "Observed_ET", "Satellite_ET"]].copy()
        x["Date"] = pd.to_datetime(x["Date"], errors="coerce")
        x["Observed_ET"] = pd.to_numeric(
            x["Observed_ET"], errors="coerce"
        )
        x["Satellite_ET"] = pd.to_numeric(
            x["Satellite_ET"], errors="coerce"
        )
        x["Site"] = site
        x["Product"] = product

        x = x.dropna(
            subset=["Date", "Observed_ET", "Satellite_ET"]
        )

        if not x.empty:
            x["Year"] = x["Date"].dt.year.astype(int)
            rows.append(x)

    if not rows:
        return pd.DataFrame(
            columns=[
                "Site", "Product", "Year", "Date",
                "Observed_ET", "Satellite_ET"
            ]
        )

    return (
        pd.concat(rows, ignore_index=True)
        .drop_duplicates(
            subset=["Site", "Product", "Date"]
        )
        .sort_values(["Site", "Product", "Date"])
        .reset_index(drop=True)
    )


def calculate_metrics_from_raw(group: pd.DataFrame) -> dict:
    """Calculate metrics from pooled observation/product pairs."""
    x = group.dropna(
        subset=["Observed_ET", "Satellite_ET"]
    )

    n = len(x)

    if n == 0:
        return {
            "N": 0,
            "RMSE": np.nan,
            "MAE": np.nan,
            "BIAS": np.nan,
            "CORRELATION": np.nan,
            "R2": np.nan,
        }

    observed = x["Observed_ET"].to_numpy(dtype=float)
    product = x["Satellite_ET"].to_numpy(dtype=float)
    error = product - observed

    rmse = float(np.sqrt(np.mean(error ** 2)))
    mae = float(np.mean(np.abs(error)))
    bias = float(np.mean(error))

    if n < 2 or np.std(observed) == 0 or np.std(product) == 0:
        correlation = np.nan
    else:
        correlation = float(np.corrcoef(observed, product)[0, 1])

    r2 = np.nan if pd.isna(correlation) else float(correlation ** 2)

    return {
        "N": n,
        "RMSE": rmse,
        "MAE": mae,
        "BIAS": bias,
        "CORRELATION": correlation,
        "R2": r2,
    }


def build_multiyear_from_raw(
    raw: pd.DataFrame,
) -> pd.DataFrame:
    """Build pooled Site × Product multi-year benchmark."""
    rows = []

    if raw.empty:
        return pd.DataFrame()

    for (site, product), g in raw.groupby(
        ["Site", "Product"], sort=True
    ):
        metrics = calculate_metrics_from_raw(g)
        years = sorted(g["Year"].unique().tolist())

        rows.append({
            "Site": site,
            "Product": product,
            "Years": ",".join(str(int(y)) for y in years),
            "Year_Count": len(years),
            "N": metrics["N"],
            "N_CATEGORY": classify_n(metrics["N"]),
            "N_SUFFICIENT": metrics["N"] >= 10,
            "Start": g["Date"].min().strftime("%Y-%m-%d"),
            "End": g["Date"].max().strftime("%Y-%m-%d"),
            "RMSE": metrics["RMSE"],
            "MAE": metrics["MAE"],
            "BIAS": metrics["BIAS"],
            "ABS_BIAS": (
                abs(metrics["BIAS"])
                if pd.notna(metrics["BIAS"])
                else np.nan
            ),
            "CORRELATION": metrics["CORRELATION"],
            "R2": metrics["R2"],
        })

    return pd.DataFrame(rows)


def build_product_summary(
    multiyear: pd.DataFrame,
    min_n: int,
) -> pd.DataFrame:
    """
    Product-level pooled comparison.

    Ranking uses equal-weight mean of metric ranks:
      lower is better: RMSE, MAE, absolute bias
      higher is better: correlation, R2
    """
    if multiyear.empty:
        return pd.DataFrame()

    primary = multiyear[
        (multiyear["N"] >= min_n)
    ].dropna(
        subset=METRICS
    ).copy()

    if primary.empty:
        return pd.DataFrame()

    s = primary.groupby("Product").agg(
        sites=("Site", "nunique"),
        combinations=("Product", "size"),
        total_N=("N", "sum"),
        median_N=("N", "median"),
        min_N=("N", "min"),
        max_N=("N", "max"),
        year_min=("Years", "min"),
        median_RMSE=("RMSE", "median"),
        median_MAE=("MAE", "median"),
        median_ABS_BIAS=("ABS_BIAS", "median"),
        median_CORRELATION=("CORRELATION", "median"),
        median_R2=("R2", "median"),
        mean_RMSE=("RMSE", "mean"),
        mean_MAE=("MAE", "mean"),
        mean_ABS_BIAS=("ABS_BIAS", "mean"),
        mean_CORRELATION=("CORRELATION", "mean"),
        mean_R2=("R2", "mean"),
    ).reset_index()

    rank_specs = [
        ("RMSE", True),
        ("MAE", True),
        ("ABS_BIAS", True),
        ("CORRELATION", False),
        ("R2", False),
    ]

    for metric, ascending in rank_specs:
        s[f"RANK_{metric}"] = s[
            f"median_{metric}"
        ].rank(
            method="min",
            ascending=ascending,
        )

    rank_cols = [f"RANK_{m}" for m, _ in rank_specs]
    s["MEAN_RANK"] = s[rank_cols].mean(axis=1)
    s["OVERALL_RANK"] = s["MEAN_RANK"].rank(
        method="min"
    )

    # Coverage of the actual multi-year benchmark period.
    s["SITE_COVERAGE"] = s["sites"]

    return s.sort_values(
        ["OVERALL_RANK", "MEAN_RANK", "median_RMSE"]
    ).reset_index(drop=True)


def build_coverage_matrix(
    yearly: pd.DataFrame,
) -> pd.DataFrame:
    """Create Product × Site × Year coverage/status matrix."""
    if yearly.empty:
        return pd.DataFrame()

    x = yearly[
        ["Product", "Site", "Year", "N", "N_CATEGORY", "STATUS"]
    ].copy()

    x["Year"] = x["Year"].astype(int)

    return x.sort_values(
        ["Product", "Site", "Year"]
    ).reset_index(drop=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__
    )

    parser.add_argument(
        "--gee-benchmark",
        type=Path,
        default=DEFAULT_GEE_BENCHMARK,
    )
    parser.add_argument(
        "--ssebop-benchmark",
        type=Path,
        default=DEFAULT_SSEBOP_BENCHMARK,
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
    parser.add_argument(
        "--min-n",
        type=int,
        default=10,
    )

    args = parser.parse_args()

    if args.min_n < 1:
        raise ValueError("--min-n must be >= 1")

    print("=" * 72)
    print("SPRINT 7 — UNIFIED MULTI-YEAR BENCHMARK")
    print("=" * 72)
    print(f"Minimum N: {args.min_n}")
    print()

    gee = load_yearly(
        args.gee_benchmark,
        "GEE_COMMON_YEAR",
    )

    ssebop = load_yearly(
        args.ssebop_benchmark,
        "EXTERNAL_SSEBOP",
    )

    # Avoid accidental duplicate site/product/year records.
    yearly = pd.concat(
        [gee, ssebop],
        ignore_index=True,
    )

    yearly = yearly.sort_values(
        ["Product", "Site", "Year"]
    )

    duplicate_mask = yearly.duplicated(
        subset=["Site", "Product", "Year"],
        keep=False,
    )

    if duplicate_mask.any():
        duplicates = yearly.loc[
            duplicate_mask,
            ["Site", "Product", "Year", "SOURCE_LAYER"],
        ]
        raise ValueError(
            "Duplicate Site × Product × Year records detected:\n"
            + duplicates.to_string(index=False)
        )

    # Year-level primary eligibility.
    yearly["N_SUFFICIENT"] = (
        yearly["N"] >= args.min_n
    )
    yearly["INTERPRETATION"] = yearly[
        "N_SUFFICIENT"
    ].map({
        True: "ELIGIBLE_FOR_PRIMARY_COMPARISON",
        False: "REFERENCE_ONLY",
    })

    # Actual raw observation pairs.
    raw = load_raw_extractions(
        args.results_root
    )

    print(
        f"Year-level records: {len(yearly)}"
    )
    print(
        f"Raw extraction pairs discovered: {len(raw)}"
    )

    # Pooled multi-year metrics from raw pairs.
    multiyear = build_multiyear_from_raw(
        raw
    )

    # If a product has no raw extraction file, retain a fallback
    # multi-year record based on its year-level rows. This is deliberately
    # labelled as a summary fallback and is not used to fabricate pooled
    # RMSE/MAE values.
    if not multiyear.empty:
        known = set(
            zip(
                multiyear["Site"],
                multiyear["Product"],
            )
        )
    else:
        known = set()

    fallback_rows = []

    for (site, product), g in yearly.groupby(
        ["Site", "Product"], sort=True
    ):
        key = (site, product)

        if key in known:
            continue

        valid = g[
            (g["N"] > 0)
        ].copy()

        if valid.empty:
            continue

        # Do not average errors into a false pooled benchmark.
        # Provide coverage/N information only.
        fallback_rows.append({
            "Site": site,
            "Product": product,
            "Years": ",".join(
                str(int(y))
                for y in sorted(valid["Year"].unique())
            ),
            "Year_Count": len(valid),
            "N": int(valid["N"].sum()),
            "N_CATEGORY": classify_n(
                int(valid["N"].sum())
            ),
            "N_SUFFICIENT": int(
                valid["N"].sum()
            ) >= args.min_n,
            "Start": (
                valid["Start"].dropna().min()
                if "Start" in valid
                else None
            ),
            "End": (
                valid["End"].dropna().max()
                if "End" in valid
                else None
            ),
            "RMSE": np.nan,
            "MAE": np.nan,
            "BIAS": np.nan,
            "ABS_BIAS": np.nan,
            "CORRELATION": np.nan,
            "R2": np.nan,
            "METRIC_SOURCE": "YEARLY_ONLY_NO_POOLED_RAW",
        })

    if not multiyear.empty:
        multiyear["METRIC_SOURCE"] = (
            "POOLED_RAW_EXTRACTIONS"
        )

    if fallback_rows:
        multiyear = pd.concat(
            [
                multiyear,
                pd.DataFrame(fallback_rows),
            ],
            ignore_index=True,
        )

    if not multiyear.empty:
        multiyear["N_SUFFICIENT"] = (
            multiyear["N"] >= args.min_n
        )
        multiyear["N_CATEGORY"] = (
            multiyear["N"].map(classify_n)
        )

    product_summary = build_product_summary(
        multiyear,
        args.min_n,
    )

    coverage = build_coverage_matrix(
        yearly
    )

    # Multi-year QC.
    if not multiyear.empty:
        qc = multiyear.copy()
        qc["QC_STATUS"] = qc[
            "N_SUFFICIENT"
        ].map({
            True: "PRIMARY",
            False: "REFERENCE_ONLY",
        })
    else:
        qc = pd.DataFrame()

    args.output.mkdir(
        parents=True,
        exist_ok=True,
    )

    yearly_path = (
        args.output / "product_site_year.csv"
    )
    multi_path = (
        args.output / "product_site_multiyear.csv"
    )
    summary_path = (
        args.output / "product_multiyear_summary.csv"
    )
    qc_path = (
        args.output / "multiyear_qc.csv"
    )
    coverage_path = (
        args.output / "coverage_matrix.csv"
    )
    report_path = (
        args.output / "unified_benchmark.json"
    )

    yearly.to_csv(
        yearly_path,
        index=False,
    )
    multiyear.to_csv(
        multi_path,
        index=False,
    )
    product_summary.to_csv(
        summary_path,
        index=False,
    )
    qc.to_csv(
        qc_path,
        index=False,
    )
    coverage.to_csv(
        coverage_path,
        index=False,
    )

    report = {
        "sprint": 7,
        "minimum_n": args.min_n,
        "year_level": {
            "records": int(len(yearly)),
            "sites": sorted(
                yearly["Site"].dropna().unique().tolist()
            ),
            "products": sorted(
                yearly["Product"].dropna().unique().tolist()
            ),
            "years": sorted(
                int(y)
                for y in yearly["Year"].dropna().unique()
            ),
        },
        "multi_year": {
            "site_product_records": int(
                len(multiyear)
            ),
            "primary_records": int(
                (multiyear["N"] >= args.min_n).sum()
            ) if not multiyear.empty else 0,
            "reference_only_records": int(
                (multiyear["N"] < args.min_n).sum()
            ) if not multiyear.empty else 0,
        },
        "methodology": {
            "year_level_qc": (
                f"N >= {args.min_n} is eligible for primary comparison"
            ),
            "n_categories": {
                "INSUFFICIENT": "N < 5",
                "LIMITED": "5 <= N < 10",
                "ADEQUATE": "10 <= N < 30",
                "STRONG": "N >= 30",
            },
            "multi_year_metrics": (
                "Calculated from pooled raw observation/product "
                "pairs when extraction.csv is available."
            ),
            "product_ranking": (
                "Equal-weight mean rank of median RMSE, median MAE, "
                "median absolute bias, median correlation and median R2 "
                "across qualifying Site × Product pooled records."
            ),
            "coverage_rule": (
                "Products retain their actual available years; "
                "missing product years are not imputed."
            ),
        },
        "limitations": [
            "The GEE layer uses the available BharatFlux site-years from 2014–2018.",
            "SSEBop contributes its available 2014–2018 year-level benchmark.",
            "Products retain asymmetric coverage where BharatFlux site-years "
            "or product observations are unavailable.",
        ],
    }

    report_path.write_text(
        json.dumps(
            report,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\nYear-level coverage:")
    print(
        coverage.groupby(
            ["Product", "Year"]
        ).size().rename(
            "Site_Combinations"
        ).reset_index().to_string(
            index=False
        )
    )

    print("\nMulti-year QC:")
    if qc.empty:
        print("No multi-year records available.")
    else:
        print(
            qc[
                [
                    "Site",
                    "Product",
                    "Years",
                    "N",
                    "N_CATEGORY",
                    "QC_STATUS",
                ]
            ].to_string(index=False)
        )

    print("\nProduct-level multi-year comparison:")
    if product_summary.empty:
        print("No products satisfy the primary multi-year criteria.")
    else:
        cols = [
            "OVERALL_RANK",
            "Product",
            "sites",
            "combinations",
            "median_N",
            "median_RMSE",
            "median_MAE",
            "median_ABS_BIAS",
            "median_CORRELATION",
            "median_R2",
            "MEAN_RANK",
        ]
        print(
            product_summary[
                [c for c in cols if c in product_summary]
            ].to_string(index=False)
        )

    print("\nCreated:")
    for path in [
        yearly_path,
        multi_path,
        summary_path,
        qc_path,
        coverage_path,
        report_path,
    ]:
        print(f"  ✓ {path}")

    print("\n" + "=" * 72)
    print(
        "Sprint 7 unified benchmark completed successfully."
    )
    print("=" * 72)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
