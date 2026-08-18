import argparse, json
from pathlib import Path
import pandas as pd

REQ={"Site","Product","Year","N","Start","End","RMSE","MAE","BIAS","CORRELATION","R2"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--min-n",type=int,default=10)
    ap.add_argument("--results-root",default="results")
    a=ap.parse_args()
    root=Path(a.results_root); src=root/"summary"/"multisite_benchmark.csv"
    if not src.exists(): raise FileNotFoundError(src)
    df=pd.read_csv(src)
    miss=REQ-set(df.columns)
    if miss: raise ValueError(f"Missing columns: {sorted(miss)}")
    nums=["N","RMSE","MAE","BIAS","CORRELATION","R2"]
    for c in nums: df[c]=pd.to_numeric(df[c],errors="coerce")
    df["ABS_BIAS"]=df["BIAS"].abs()
    valid=df.dropna(subset=["Site","Product","N","RMSE","MAE","ABS_BIAS","CORRELATION","R2"]).copy()
    primary=valid[valid.N>=a.min_n].copy()
    low=valid[valid.N<a.min_n].copy()
    if primary.empty: raise ValueError("No combinations satisfy minimum N")
    s=primary.groupby("Product").agg(
        sites=("Site","nunique"), combinations=("Product","size"),
        total_N=("N","sum"), median_N=("N","median"), min_N=("N","min"), max_N=("N","max"),
        mean_RMSE=("RMSE","mean"),median_RMSE=("RMSE","median"),std_RMSE=("RMSE","std"),
        mean_MAE=("MAE","mean"),median_MAE=("MAE","median"),std_MAE=("MAE","std"),
        mean_BIAS=("BIAS","mean"),median_BIAS=("BIAS","median"),
        mean_ABS_BIAS=("ABS_BIAS","mean"),median_ABS_BIAS=("ABS_BIAS","median"),std_ABS_BIAS=("ABS_BIAS","std"),
        mean_CORRELATION=("CORRELATION","mean"),median_CORRELATION=("CORRELATION","median"),std_CORRELATION=("CORRELATION","std"),
        mean_R2=("R2","mean"),median_R2=("R2","median"),std_R2=("R2","std")
    ).reset_index()
    rank_specs=[("RMSE",True),("MAE",True),("ABS_BIAS",True),("CORRELATION",False),("R2",False)]
    for m,asc in rank_specs: s["RANK_"+m]=s["median_"+m].rank(method="min",ascending=asc)
    rc=["RANK_"+m for m,_ in rank_specs]
    s["MEAN_RANK"]=s[rc].mean(axis=1)
    s["OVERALL_RANK"]=s.MEAN_RANK.rank(method="min")
    wins=[]
    for site,g in primary.groupby("Site"):
        for m,asc in rank_specs:
            idx=g[m].idxmin() if asc else g[m].idxmax()
            wins.append({"Site":site,"Metric":m,"Winner":g.loc[idx,"Product"],"Value":float(g.loc[idx,m])})
    winners=pd.DataFrame(wins)
    wc=winners.groupby("Winner").size().rename("site_metric_wins").reset_index().rename(columns={"Winner":"Product"})
    s=s.merge(wc,on="Product",how="left"); s["site_metric_wins"]=s.site_metric_wins.fillna(0).astype(int)
    total_sites=primary.Site.nunique(); s["site_coverage_pct"]=100*s.sites/total_sites
    # Per-site equal-weight rank, useful for consistency.
    sr=[]
    for site,g in primary.groupby("Site"):
        x=g.copy()
        for m,asc in rank_specs: x["r_"+m]=x[m].rank(method="min",ascending=asc)
        x["SITE_MEAN_RANK"]=x[["r_"+m for m,_ in rank_specs]].mean(axis=1)
        sr += [{"Site":site,"Product":r.Product,"SITE_MEAN_RANK":float(r.SITE_MEAN_RANK)} for r in x.itertuples()]
    site_ranks=pd.DataFrame(sr)
    stab=site_ranks.groupby("Product").SITE_MEAN_RANK.agg(
        mean_site_rank="mean",std_site_rank="std",best_site_rank="min",worst_site_rank="max"
    ).reset_index()
    s=s.merge(stab,on="Product",how="left").sort_values(["OVERALL_RANK","MEAN_RANK","median_RMSE"])
    out=root/"summary"/"sprint6"; out.mkdir(parents=True,exist_ok=True)
    summary_cols=["OVERALL_RANK","Product","sites","site_coverage_pct","combinations","total_N","median_N","min_N","max_N",
                  "median_RMSE","median_MAE","median_ABS_BIAS","median_CORRELATION","median_R2",
                  "mean_RMSE","mean_MAE","mean_ABS_BIAS","mean_CORRELATION","mean_R2",
                  "std_RMSE","std_MAE","std_ABS_BIAS","std_CORRELATION","std_R2","MEAN_RANK",
                  "RANK_RMSE","RANK_MAE","RANK_ABS_BIAS","RANK_CORRELATION","RANK_R2",
                  "site_metric_wins","mean_site_rank","std_site_rank","best_site_rank","worst_site_rank"]
    s=s[[c for c in summary_cols if c in s]]
    s.to_csv(out/"product_summary.csv",index=False)
    winners.to_csv(out/"site_winners.csv",index=False)
    site_ranks.to_csv(out/"site_product_ranks.csv",index=False)
    primary.to_csv(out/"primary_benchmark.csv",index=False)
    report={"minimum_n":a.min_n,"valid_combinations":len(valid),"primary_combinations":len(primary),
            "low_n_combinations":len(low),"sites":sorted(primary.Site.unique().tolist()),
            "products":sorted(primary.Product.unique().tolist()),
            "methodology":{"primary_rule":f"N >= {a.min_n}",
                           "aggregation":"median and mean across qualifying site-product combinations",
                           "overall_rank":"equal-weight mean of ranks for RMSE, MAE, absolute bias, correlation and R2",
                           "lower_better":["RMSE","MAE","absolute bias"],
                           "higher_better":["correlation","R2"],
                           "low_n":"excluded from primary ranking but retained in source benchmark"}}
    (out/"benchmark_interpretation.json").write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
    print("="*72); print("SPRINT 6 — CONSOLIDATED BENCHMARK INTERPRETATION"); print("="*72)
    print(f"Minimum N: {a.min_n} | Primary combinations: {len(primary)} | Low-N: {len(low)}")
    print("\nProduct-level benchmark:")
    print(s[["OVERALL_RANK","Product","sites","combinations","median_N","median_RMSE","median_MAE","median_ABS_BIAS","median_CORRELATION","median_R2","MEAN_RANK","site_metric_wins"]].to_string(index=False))
    print("\nSite-wise metric winners:")
    print(winners.to_string(index=False))
    print("\nCreated:")
    for f in ["product_summary.csv","site_winners.csv","site_product_ranks.csv","primary_benchmark.csv","benchmark_interpretation.json"]: print("  ✓",out/f)
    print("\n"+"="*72); print("Sprint 6 benchmark interpretation completed successfully."); print("="*72)

if __name__=="__main__": main()
