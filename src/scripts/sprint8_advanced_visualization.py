"""OpenETBench Sprint 8 — advanced evaluation and final visualizations.

Creates four research-facing outputs from the frozen Sprint-7 unified layer:
1. Taylor diagram
2. Seasonal-cycle comparison
3. Interannual-variability comparison
4. Site-wise spatial performance pattern

The script does not modify Sprint-7 benchmark tables. It reads:
    results/summary/sprint7_unified/multiyear_qc.csv
    results/*/*/extraction.csv

Usage:
    python src/scripts/sprint8_advanced_visualization.py --min-n 10
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from visualization.advanced import (
    build_interannual,
    build_seasonal_cycle,
    build_spatial_performance,
    plot_interannual,
    plot_seasonal_cycle,
    plot_spatial_performance,
)
from visualization.taylor import build_taylor_statistics, plot_taylor_diagram

DEFAULT_RESULTS_ROOT = PROJECT_ROOT / "results"
DEFAULT_INPUT = DEFAULT_RESULTS_ROOT / "summary" / "sprint7_unified"
DEFAULT_OUTPUT = DEFAULT_RESULTS_ROOT / "summary" / "sprint8"


def load_raw(results_root: Path) -> pd.DataFrame:
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
        required = {"Date", "Observed_ET", "Satellite_ET"}
        if not required.issubset(df.columns):
            continue
        x = df[list(required)].copy()
        x["Date"] = pd.to_datetime(x["Date"], errors="coerce")
        x["Observed_ET"] = pd.to_numeric(x["Observed_ET"], errors="coerce")
        x["Satellite_ET"] = pd.to_numeric(x["Satellite_ET"], errors="coerce")
        x["Site"] = site
        x["Product"] = product
        x = x.dropna(subset=["Date", "Observed_ET", "Satellite_ET"])
        if not x.empty:
            rows.append(x)
    if not rows:
        return pd.DataFrame(columns=["Date", "Observed_ET", "Satellite_ET", "Site", "Product"])
    return pd.concat(rows, ignore_index=True).drop_duplicates(
        subset=["Site", "Product", "Date"]
    ).sort_values(["Site", "Product", "Date"]).reset_index(drop=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--min-n", type=int, default=10)
    args = parser.parse_args()

    if args.min_n < 1:
        raise ValueError("--min-n must be >= 1")

    print("=" * 72)
    print("SPRINT 8 — ADVANCED EVALUATION & FINAL VISUALIZATIONS")
    print("=" * 72)
    print(f"Minimum N: {args.min_n}")

    qc_path = args.input / "multiyear_qc.csv"
    multi_path = args.input / "product_site_multiyear.csv"
    if not qc_path.exists():
        raise FileNotFoundError(f"Missing Sprint-7 QC file: {qc_path}")
    if not multi_path.exists():
        raise FileNotFoundError(f"Missing Sprint-7 multi-year file: {multi_path}")

    qc = pd.read_csv(qc_path)
    multiyear = pd.read_csv(multi_path)
    primary = qc[qc["N"] >= args.min_n].copy()
    raw = load_raw(args.results_root)

    if raw.empty:
        raise RuntimeError("No raw extraction.csv files were found.")

    args.output.mkdir(parents=True, exist_ok=True)
    data_dir = args.output / "data"
    fig_dir = args.output / "figures"
    data_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    print(f"Primary Site × Product records: {len(primary)}")
    print(f"Raw extraction pairs: {len(raw)}")

    # 1. Taylor diagram
    taylor = build_taylor_statistics(raw, primary)
    taylor_csv = data_dir / "taylor_statistics.csv"
    taylor.to_csv(taylor_csv, index=False)
    taylor_png = plot_taylor_diagram(taylor, fig_dir / "taylor_diagram.png")
    print(f"✓ Taylor diagram: {taylor_png}")

    # 2. Seasonal cycle
    seasonal = build_seasonal_cycle(raw, primary)
    seasonal_csv = data_dir / "seasonal_cycle.csv"
    seasonal.to_csv(seasonal_csv, index=False)
    seasonal_png = plot_seasonal_cycle(seasonal, fig_dir / "seasonal_cycle.png")
    print(f"✓ Seasonal cycle: {seasonal_png}")

    # 3. Interannual variability
    annual = build_interannual(raw, primary)
    annual_csv = data_dir / "interannual_variability.csv"
    annual.to_csv(annual_csv, index=False)
    annual_png = plot_interannual(annual, fig_dir / "interannual_variability.png")
    print(f"✓ Interannual variability: {annual_png}")

    # 4. Spatial performance pattern
    spatial = build_spatial_performance(multiyear, args.min_n)
    spatial_csv = data_dir / "spatial_performance.csv"
    spatial.to_csv(spatial_csv, index=False)
    spatial_png = plot_spatial_performance(spatial, fig_dir / "spatial_performance.png")
    print(f"✓ Spatial performance: {spatial_png}")

    report = {
        "sprint": 8,
        "minimum_n": args.min_n,
        "primary_site_product_records": int(len(primary)),
        "raw_extraction_pairs": int(len(raw)),
        "outputs": {
            "taylor": str(taylor_png),
            "seasonal_cycle": str(seasonal_png),
            "interannual_variability": str(annual_png),
            "spatial_performance": str(spatial_png),
        },
        "interpretation_notes": [
            "Taylor statistics use site-level normalized standard deviation ratios and correlations, summarized by product using medians.",
            "Seasonal-cycle curves are standardized within each Site × Product pair before pooling, so the figure compares timing and shape rather than raw magnitude across native temporal resolutions.",
            "Interannual variability is shown as standardized annual anomalies because available years and native sampling differ among products.",
            "The spatial panel is a site-wise performance map (RMSE), not a gridded ET spatial-pattern evaluation; gridded spatial validation is outside the current site-based benchmark design.",
        ],
    }
    report_path = args.output / "sprint8_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\nCreated:")
    for p in [taylor_csv, seasonal_csv, annual_csv, spatial_csv, report_path]:
        print(f"  ✓ {p}")
    print("\n" + "=" * 72)
    print("Sprint 8 completed successfully.")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
