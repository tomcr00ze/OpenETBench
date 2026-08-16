"""OpenETBench Sprint 5: quality control and minimum-N analysis.

Reads results/summary/multisite_benchmark.csv and produces QC tables under
results/summary/sprint5/. Default minimum N for primary comparison is 10.

Usage:
    python src/scripts/sprint5_quality_control.py
    python src/scripts/sprint5_quality_control.py --min-n 10
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BENCHMARK = PROJECT_ROOT / "results" / "summary" / "multisite_benchmark.csv"
DEFAULT_FAILURES = PROJECT_ROOT / "results" / "summary" / "multisite_failures.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "results" / "summary" / "sprint5"


def classify_n(n: int) -> str:
    if n < 5:
        return "INSUFFICIENT"
    if n < 10:
        return "LIMITED"
    if n < 20:
        return "ADEQUATE"
    return "STRONG"


def load_benchmark(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Benchmark CSV not found: {path}")
    df = pd.read_csv(path)
    required = {"Site", "Product", "Year", "N", "Start", "End", "RMSE", "MAE", "BIAS", "CORRELATION", "R2"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError("Missing columns: " + ", ".join(sorted(missing)))
    for c in ["Year", "N", "RMSE", "MAE", "BIAS", "CORRELATION", "R2"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if df["N"].isna().any() or (df["N"] <= 0).any():
        raise ValueError("Benchmark contains invalid N values.")
    df["N"] = df["N"].astype(int)
    return df


def add_qc(df: pd.DataFrame, min_n: int) -> pd.DataFrame:
    out = df.copy()
    out["N_CATEGORY"] = out["N"].map(classify_n)
    out["MIN_N_THRESHOLD"] = min_n
    out["N_SUFFICIENT"] = out["N"] >= min_n
    out["INTERPRETATION"] = out["N_SUFFICIENT"].map({
        True: "ELIGIBLE_FOR_PRIMARY_COMPARISON",
        False: "RETAINED_FOR_REFERENCE_ONLY",
    })
    return out


def grouped_summary(df: pd.DataFrame, key: str, min_n: int) -> pd.DataFrame:
    rows = []
    for name, g in df.groupby(key, sort=True):
        e = g[g.N >= min_n]
        rows.append({
            key: name,
            "Site_Product_Combinations": len(g),
            "Eligible_Combinations": len(e),
            "Eligibility_Rate": len(e) / len(g),
            "Min_N": int(g.N.min()),
            "Median_N": float(g.N.median()),
            "Max_N": int(g.N.max()),
            "N_lt_5": int((g.N < 5).sum()),
            "N_5_to_9": int(((g.N >= 5) & (g.N < 10)).sum()),
            "N_10_to_19": int(((g.N >= 10) & (g.N < 20)).sum()),
            "N_ge_20": int((g.N >= 20).sum()),
            "Median_RMSE_Eligible": None if e.empty else float(e.RMSE.median()),
            "Median_MAE_Eligible": None if e.empty else float(e.MAE.median()),
            "Median_Abs_BIAS_Eligible": None if e.empty else float(e.BIAS.abs().median()),
            "Median_CORRELATION_Eligible": None if e.empty else float(e.CORRELATION.median()),
            "Median_R2_Eligible": None if e.empty else float(e.R2.median()),
        })
    return pd.DataFrame(rows)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    p.add_argument("--failures", type=Path, default=DEFAULT_FAILURES)
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    p.add_argument("--min-n", type=int, default=10)
    args = p.parse_args()
    if args.min_n < 1:
        raise ValueError("--min-n must be >= 1")

    print("=" * 72)
    print("SPRINT 5 — QUALITY CONTROL & MINIMUM-N ANALYSIS")
    print("=" * 72)
    print(f"Benchmark: {args.benchmark}")
    print(f"Minimum N: {args.min_n}")

    df = add_qc(load_benchmark(args.benchmark), args.min_n)
    filtered = df[df.N >= args.min_n].copy()
    args.output.mkdir(parents=True, exist_ok=True)

    n_dist = (df.N.map(classify_n).value_counts()
              .reindex(["INSUFFICIENT", "LIMITED", "ADEQUATE", "STRONG"], fill_value=0)
              .rename_axis("N_CATEGORY").reset_index(name="Combinations"))
    n_dist["Percentage"] = n_dist.Combinations / len(df)

    product = grouped_summary(df, "Product", args.min_n)
    site = grouped_summary(df, "Site", args.min_n)

    failures = []
    if args.failures.exists():
        try:
            failures = json.loads(args.failures.read_text(encoding="utf-8"))
        except Exception:
            failures = []

    report = {
        "sprint": 5,
        "minimum_n_threshold": args.min_n,
        "minimum_n_is_operational_qc": True,
        "successful_combinations": int(len(df)),
        "eligible_combinations": int(len(filtered)),
        "below_minimum_n": int(len(df) - len(filtered)),
        "eligibility_rate": float(len(filtered) / len(df)),
        "n_min": int(df.N.min()), "n_median": float(df.N.median()),
        "n_mean": float(df.N.mean()), "n_max": int(df.N.max()),
        "n_lt_5": int((df.N < 5).sum()),
        "n_5_to_9": int(((df.N >= 5) & (df.N < 10)).sum()),
        "n_10_to_19": int(((df.N >= 10) & (df.N < 20)).sum()),
        "n_ge_20": int((df.N >= 20).sum()),
        "sprint4_failures": failures,
    }

    files = {
        "qc_benchmark.csv": df,
        "qc_filtered_benchmark.csv": filtered,
        "product_summary.csv": product,
        "site_summary.csv": site,
        "n_distribution.csv": n_dist,
    }
    for name, table in files.items():
        table.to_csv(args.output / name, index=False)
    (args.output / "qc_report.json").write_text(json.dumps(report, indent=4), encoding="utf-8")

    print("\nN distribution:")
    print(n_dist.to_string(index=False))
    print("\nOverall QC:")
    print(f"  Successful combinations : {len(df)}")
    print(f"  N >= {args.min_n}           : {len(filtered)}")
    print(f"  N < {args.min_n}            : {len(df) - len(filtered)}")
    print(f"  Eligibility rate         : {len(filtered) / len(df) * 100:.2f}%")
    print(f"  Sprint 4 logged failures : {len(failures)}")
    print("\nCreated:")
    for name in [*files, "qc_report.json"]:
        print(f"  ✓ {args.output / name}")
    print("\n" + "=" * 72)
    print("Sprint 5 QC completed successfully.")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
