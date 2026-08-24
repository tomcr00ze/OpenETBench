"""Finalize OpenETBench: documentation, reproducibility, and research-ready tables."""
from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


def _git(cmd, root):
    try:
        return subprocess.check_output(["git", *cmd], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "unavailable"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    p.add_argument("--min-n", type=int, default=10)
    args = p.parse_args()
    root = args.project_root.resolve()
    summary = root / "results" / "summary"
    unified = summary / "sprint7_unified"
    s8 = summary / "sprint8"
    final = summary / "final"
    tables = final / "benchmark_tables"
    final.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)

    required = [
        unified / "product_site_year.csv",
        unified / "product_site_multiyear.csv",
        unified / "product_multiyear_summary.csv",
        unified / "multiyear_qc.csv",
        unified / "coverage_matrix.csv",
        unified / "unified_benchmark.json",
        s8 / "sprint8_report.json",
    ]
    missing = [str(x) for x in required if not x.exists()]
    if missing:
        raise FileNotFoundError("Missing required outputs:\n" + "\n".join(missing))

    # Research-ready tables: keep source fields intact, add explicit selection flags.
    year = pd.read_csv(required[0])
    multi = pd.read_csv(required[1])
    products = pd.read_csv(required[2])
    qc = pd.read_csv(required[3])
    coverage = pd.read_csv(required[4])

    qc["PRIMARY"] = qc["N"] >= args.min_n
    qc.to_csv(tables / "site_product_multiyear_qc.csv", index=False)
    year.to_csv(tables / "site_product_year_benchmark.csv", index=False)
    multi.to_csv(tables / "site_product_multiyear_benchmark.csv", index=False)
    products.to_csv(tables / "product_multiyear_ranking.csv", index=False)
    coverage.to_csv(tables / "product_year_site_coverage.csv", index=False)

    primary_products = products.copy()
    primary_products["MIN_N"] = args.min_n
    primary_products["PRIMARY_SITE_PRODUCT_COUNT"] = [
        int(((qc["Product"] == prod) & (qc["PRIMARY"])).sum()) for prod in primary_products["Product"]
    ]
    primary_products.to_csv(tables / "product_multiyear_ranking_with_qc.csv", index=False)

    # Copy Sprint 8 data for a single final handoff location.
    if (s8 / "data").exists():
        dst = final / "sprint8_diagnostics"
        dst.mkdir(exist_ok=True)
        for f in (s8 / "data").glob("*.csv"):
            shutil.copy2(f, dst / f.name)

    unified_json = json.loads((unified / "unified_benchmark.json").read_text(encoding="utf-8"))
    s8_json = json.loads((s8 / "sprint8_report.json").read_text(encoding="utf-8"))

    # Reproducibility manifest.
    manifest = {
        "project": "OpenETBench",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "minimum_n_primary": args.min_n,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "git_commit": _git(["rev-parse", "HEAD"], root),
        "git_branch": _git(["branch", "--show-current"], root),
        "sprint7_unified": str(unified_json.get("sprint", "unknown")),
        "sprint8": str(s8_json.get("sprint", "unknown")),
        "bharatflux_years": "2014-2018 (site-dependent coverage)",
        "products": sorted(qc["Product"].dropna().unique().tolist()),
        "outputs": {
            "year_benchmark": "benchmark_tables/site_product_year_benchmark.csv",
            "multiyear_benchmark": "benchmark_tables/site_product_multiyear_benchmark.csv",
            "multiyear_qc": "benchmark_tables/site_product_multiyear_qc.csv",
            "product_ranking": "benchmark_tables/product_multiyear_ranking.csv",
            "coverage": "benchmark_tables/product_year_site_coverage.csv",
            "sprint8_diagnostics": "sprint8_diagnostics/",
        },
    }
    (final / "reproducibility_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Concise research handoff document. Avoid interpreting metrics beyond what the benchmark computes.
    product_lines = []
    for _, r in products.sort_values("OVERALL_RANK").iterrows():
        product_lines.append(
            f"| {r['OVERALL_RANK']:.0f} | {r['Product']} | {int(r['sites'])} | {int(r['combinations'])} | "
            f"{r['median_N']:.0f} | {r['median_RMSE']:.3f} | {r['median_MAE']:.3f} | "
            f"{r['median_ABS_BIAS']:.3f} | {r['median_CORRELATION']:.3f} | {r['median_R2']:.3f} |"
        )

    readme = f"""# OpenETBench — Final Research Handoff\n\n"
    readme += "OpenETBench is a site-based evapotranspiration benchmark using BharatFlux eddy-covariance observations. The final pipeline combines the common-year baseline with site-dependent 2014–2018 multi-year coverage, GEE products, and the externally integrated SSEBop V6.1 product.\n\n"
    readme += "## Final benchmark design\n\n"
    readme += f"- Primary multi-year threshold: **N ≥ {args.min_n} paired observations**.\n"
    readme += "- Year-level analysis: Product × Site × Year.\n"
    readme += "- Multi-year analysis: pooled Product × Site records over the years actually available for that site.\n"
    readme += "- Sprint 8 diagnostics: Taylor diagram, seasonal cycle, interannual variability, and site-wise spatial performance.\n"
    readme += "- SSEBop V6.1 is retained as an external non-GEE comparison product; it has substantially less site coverage than the six GEE products.\n\n"
    readme += "## Research-ready product summary\n\n"
    readme += "| Rank | Product | Sites | Combinations | Median N | Median RMSE | Median MAE | Median |Bias| | Median R | Median R² |\n"
    readme += "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|\n"
    readme += "\n".join(product_lines) + "\n\n"
    readme += "## Important interpretation rule\n\n"
    readme += "Product rankings should be interpreted together with coverage and QC. A product with fewer valid site-years or lower temporal sampling is not directly equivalent to a product with broad daily coverage. The ranking is therefore a benchmark summary, not a universal statement of product superiority.\n\n"
    readme += "## Reproducibility\n\n"
    readme += "The final directory contains frozen benchmark tables, QC flags, coverage tables, Sprint 8 diagnostic data, and a machine-readable reproducibility manifest. Raw data and generated figures remain in their existing project locations.\n\n"
    readme += "### Core outputs\n\n"
    readme += "- `benchmark_tables/site_product_year_benchmark.csv`\n"
    readme += "- `benchmark_tables/site_product_multiyear_benchmark.csv`\n"
    readme += "- `benchmark_tables/site_product_multiyear_qc.csv`\n"
    readme += "- `benchmark_tables/product_multiyear_ranking.csv`\n"
    readme += "- `benchmark_tables/product_year_site_coverage.csv`\n"
    readme += "- `sprint8_diagnostics/`\n"
    readme += "- `reproducibility_manifest.json`\n"
    (final / "README_FINAL.md").write_text(readme, encoding="utf-8")

    # Project-level handoff note, without modifying existing README.
    project_note = root / "FINAL_OPENETBENCH.md"
    project_note.write_text("""# OpenETBench Final Handoff\n\nSee `results/summary/final/README_FINAL.md` for the frozen research-ready benchmark summary.\n\nRun the finalization script again after any intentional benchmark change:\n\n```powershell\npython src/scripts/finalize_openetbench.py --min-n 10\n```\n\nSprint 7 and Sprint 8 outputs should be treated as the computational source of truth; the `final/` directory is the organized research handoff layer.\n""", encoding="utf-8")

    print("=" * 72)
    print("OPENETBENCH — FINALIZATION")
    print("=" * 72)
    print(f"Primary threshold: N >= {args.min_n}")
    print(f"✓ Final tables: {tables}")
    print(f"✓ Final README: {final / 'README_FINAL.md'}")
    print(f"✓ Reproducibility manifest: {final / 'reproducibility_manifest.json'}")
    print("✓ Project handoff note: FINAL_OPENETBENCH.md")
    print("\nFinalization completed successfully.")


if __name__ == "__main__":
    main()
