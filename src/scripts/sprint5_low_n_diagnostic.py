import argparse
import json
from pathlib import Path
import pandas as pd

EXPECTED = {
    "MOD16A2GF": "8-day",
    "PMLV2": "8-day",
    "FLDAS": "monthly/irregular",
    "ERA5-LAND": "daily",
    "GLDAS": "daily",
    "MERRA2": "daily",
}

def diagnose(product, n):
    expected = EXPECTED.get(product, "unknown")
    if n < 5:
        severity = "very low overlap"
    else:
        severity = "low overlap"
    if expected == "monthly/irregular":
        return f"{severity}; sparse temporal sampling is expected for {product}"
    if expected == "8-day":
        return f"{severity}; {product} has 8-day sampling, so N is naturally lower than daily products"
    if expected == "daily":
        return f"{severity}; daily product with few valid overlapping observations"
    return f"{severity}; inspect temporal overlap and missing values"

def category(n, threshold):
    if n < 5: return "INSUFFICIENT"
    if n < threshold: return "LIMITED"
    if n < 20: return "ADEQUATE"
    return "STRONG"

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--min-n", type=int, default=10)
    p.add_argument("--results-root", default="results")
    args = p.parse_args()

    root = Path(args.results_root)
    src = root / "summary" / "multisite_benchmark.csv"
    if not src.exists():
        raise FileNotFoundError(f"Benchmark CSV not found: {src}")

    df = pd.read_csv(src)
    required = {"Site","Product","Year","N","Start","End","RMSE","MAE","BIAS","CORRELATION","R2"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    df["N"] = pd.to_numeric(df["N"], errors="coerce")
    low = df[df["N"] < args.min_n].copy().sort_values(["N","Site","Product"])

    print("="*72)
    print("SPRINT 5.5 — LOW-N DIAGNOSTIC")
    print("="*72)
    print(f"Benchmark: {src}")
    print(f"Minimum N: {args.min_n}\n")

    if low.empty:
        print("No low-N combinations found.")
        return

    low["N_CATEGORY"] = low["N"].apply(lambda x: category(int(x), args.min_n))
    low["EXPECTED_TEMPORAL_SAMPLING"] = low["Product"].map(EXPECTED).fillna("unknown")
    low["DIAGNOSTIC"] = low.apply(lambda r: diagnose(r["Product"], int(r["N"])), axis=1)

    cols = ["Site","Product","Year","N","N_CATEGORY",
            "EXPECTED_TEMPORAL_SAMPLING","RMSE","MAE","BIAS",
            "CORRELATION","R2","DIAGNOSTIC"]

    print("Low-N combinations:")
    print(low[cols].to_string(index=False))
    print("\nLow-N count by product:")
    print(low.groupby("Product").size().sort_values(ascending=False).to_string())
    print("\nLow-N count by site:")
    print(low.groupby("Site").size().sort_values(ascending=False).to_string())

    # Compare benchmark N with product extraction files where available.
    checks = []
    for _, r in low.iterrows():
        f = root / str(r["Site"]) / str(r["Product"]) / "extraction.csv"
        total = valid = None
        if f.exists():
            try:
                ext = pd.read_csv(f)
                total = len(ext)
                if "ET" in ext.columns:
                    valid = int(ext["ET"].notna().sum())
            except Exception:
                pass
        checks.append({"Site":r["Site"],"Product":r["Product"],
                       "N":int(r["N"]),"extraction_rows":total,
                       "extraction_valid_ET":valid})

    out = root / "summary" / "sprint5"
    out.mkdir(parents=True, exist_ok=True)
    csv_out = out / "low_n_diagnostic.csv"
    json_out = out / "low_n_diagnostic.json"

    low[cols].to_csv(csv_out, index=False)
    report = {
        "minimum_n": args.min_n,
        "low_n_count": len(low),
        "low_n_combinations": low[cols].to_dict(orient="records"),
        "by_product": low.groupby("Product").size().astype(int).to_dict(),
        "by_site": low.groupby("Site").size().astype(int).to_dict(),
        "extraction_side_check": checks,
    }
    json_out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    print("\nCreated:")
    print(f"  ✓ {csv_out}")
    print(f"  ✓ {json_out}")
    print("\nSprint 5.5 diagnostic completed successfully.")

if __name__ == "__main__":
    main()
