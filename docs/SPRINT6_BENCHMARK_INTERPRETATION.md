# Sprint 6 --- Consolidated Benchmark Interpretation

## 1. Purpose of Sprint 6

Sprint 6 converts the quality-controlled benchmark produced by Sprint 5
into a **consolidated scientific comparison of ET products**.

Sprint 4 established multi-site benchmarking, while Sprint 5 determined
which site--product combinations have sufficient observational support.

Sprint 6 asks the next question:

> **Across the available sites, which ET products perform most
> consistently against the BharatFlux reference observations?**

The objective is not to identify a universally "best" ET product from a
single metric. Instead, Sprint 6 combines several complementary metrics
and summarizes performance at both:

-   **product level**, and
-   **site level**.

The primary analysis uses:

``` text
N >= 10
```

so that extremely sparse comparisons do not dominate the product
rankings.

------------------------------------------------------------------------

# 2. How Sprint 6 was accomplished

## Step 1 --- Select the primary benchmark

Sprint 6 uses the quality-controlled benchmark with:

``` text
N >= 10
```

This produced:

``` text
Primary combinations = 55
Low-N combinations   = 9
```

The low-N combinations remain available for diagnostic analysis but are
not used for the primary product ranking.

------------------------------------------------------------------------

## Step 2 --- Evaluate five complementary metrics

The benchmark considers:

### RMSE

Root Mean Square Error measures the magnitude of prediction errors while
giving greater weight to larger errors.

**Lower is better.**

### MAE

Mean Absolute Error measures the average magnitude of the absolute
errors.

**Lower is better.**

### Absolute Bias

Absolute bias measures the magnitude of systematic over- or
under-estimation without allowing positive and negative bias to cancel
during comparison.

**Lower is better.**

### Correlation

Correlation measures the degree to which temporal variations in the
product agree with the reference observations.

**Higher is better.**

### R²

R² measures the proportion of variance explained by the product relative
to the reference observations.

**Higher is better.**

These metrics capture different aspects of ET-product performance, so no
single metric is treated as sufficient on its own.

------------------------------------------------------------------------

# 3. Product-level ranking methodology

Sprint 6 summarizes each product across its eligible site combinations
using:

-   median `N`;
-   median RMSE;
-   median MAE;
-   median absolute bias;
-   median correlation;
-   median R²;
-   mean metric rank;
-   number of site-level metric wins.

The overall product rank is based on the **mean rank across the five
evaluation metrics**.

This should be interpreted as a **multi-criteria benchmark ranking**,
rather than as a universal scientific ordering of ET products.

------------------------------------------------------------------------

# 4. Product-level results

The primary benchmark produced the following ranking:

  -------------------------------------------------------------------------------------------------------
    Overall Product           Sites Median N   Median   Median   Median    Bias         Median R   Median
       rank                                      RMSE      MAE                                         R²
  --------- --------------- ------- -------- -------- -------- -------- ------- ------- -------- --------
          1 **ERA5-LAND**        11      210    0.970    0.766    0.340   0.648   0.420      2.2       20

          2 **MERRA2**           11      210    1.198    0.985    0.409   0.657   0.432      2.8        9

          3 **FLDAS**             5       12    1.838    1.366    1.183   0.795   0.631      3.4        8

          4 **GLDAS**            11      210    1.127    0.903    0.471   0.604   0.365      3.8        6

          5 **PMLV2**             9       46    1.355    1.036    0.531   0.634   0.402      4.4       12

          5 **MOD16A2GF**         8       46   12.892    9.611    8.827   0.666   0.444      4.4        0
  -------------------------------------------------------------------------------------------------------

The tied fifth position results from the same mean rank reported by the
benchmark.

------------------------------------------------------------------------

# 5. Main interpretation

## 5.1 ERA5-LAND is the strongest overall product in this benchmark

ERA5-LAND obtains the best overall rank.

Its median performance is characterized by:

-   lowest median RMSE among the six products;
-   lowest median MAE;
-   lowest median absolute bias;
-   competitive correlation;
-   competitive R²;
-   highest number of site-level metric wins: **20**.

Its performance is also supported by coverage across **11 sites**.

Therefore, within the current benchmark configuration, **ERA5-LAND
provides the strongest overall and most consistent performance among the
evaluated products.**

This conclusion is specific to the present:

-   sites,
-   year,
-   reference dataset,
-   extraction configuration,
-   temporal matching procedure,
-   and metric/ranking methodology.

It should not be generalized into a universal claim that ERA5-LAND is
the best ET product everywhere.

------------------------------------------------------------------------

# 6. MERRA2 is the second strongest overall product

MERRA2 ranks second.

It has:

-   median RMSE = **1.198**;
-   median MAE = **0.985**;
-   median absolute bias = **0.409**;
-   median correlation = **0.657**;
-   median R² = **0.432**.

MERRA2 performs particularly well in correlation and R² at several
sites.

This indicates that its temporal variability can agree well with the
reference observations even when its absolute error is not always the
lowest.

MERRA2 also has strong coverage:

``` text
11 sites
11 primary combinations
median N = 210
```

Thus, its ranking is supported by broad observational coverage.

------------------------------------------------------------------------

# 7. FLDAS: strong performance, but limited coverage

FLDAS ranks third in the consolidated ranking.

Its median correlation and R² are actually the strongest among the six
products:

``` text
Median correlation = 0.795
Median R²           = 0.631
```

It also wins all five metrics at BFT and performs strongly at KKM.

However, only **5 sites** qualify for the primary analysis, and its
median N is only **12**.

Therefore, the correct interpretation is not simply:

> "FLDAS is the third-best ET product."

A more defensible interpretation is:

> **FLDAS demonstrates strong agreement at the sites where sufficient
> observations are available, but its smaller eligible site/sample
> coverage limits the strength of direct cross-product comparison.**

This distinction is important for the final scientific discussion.

------------------------------------------------------------------------

# 8. GLDAS: good error performance at several sites

GLDAS ranks fourth overall.

It has:

-   median RMSE = **1.127**;
-   median MAE = **0.903**;
-   median absolute bias = **0.471**;
-   median correlation = **0.604**;
-   median R² = **0.365**.

GLDAS performs particularly well at BKC, where it wins:

-   RMSE;
-   MAE;
-   absolute bias.

It also wins RMSE and MAE at SFT.

Thus, GLDAS demonstrates strong site-specific performance despite having
weaker overall correlation/R² statistics than ERA5-LAND, MERRA2 and
FLDAS.

------------------------------------------------------------------------

# 9. PMLV2: strong site-specific performance

PMLV2 ranks fifth, tied with MOD16A2GF by mean rank.

However, the interpretation of PMLV2 is quite different from MOD16A2GF.

PMLV2 has:

-   median RMSE = **1.355**;
-   median MAE = **1.036**;
-   median absolute bias = **0.531**;
-   median correlation = **0.634**;
-   median R² = **0.402**.

It records **12 site-level metric wins**, particularly at:

-   BIT;
-   JIT;
-   UIT.

At BIT and JIT, PMLV2 wins four of the five evaluated metrics.

Therefore, PMLV2 should not be viewed as uniformly weak. Rather, its
performance appears to be **more site-dependent** than ERA5-LAND.

------------------------------------------------------------------------

# 10. MOD16A2GF: weakest absolute-error performance

MOD16A2GF occupies the tied fifth position, but its performance is
substantially weaker in terms of absolute error:

-   median RMSE = **12.892**;
-   median MAE = **9.611**;
-   median absolute bias = **8.827**;
-   median correlation = **0.666**;
-   median R² = **0.444**;
-   site-level metric wins = **0**.

The important observation is that its temporal agreement is not
necessarily poor:

``` text
Median correlation = 0.666
Median R²          = 0.444
```

Yet its RMSE, MAE and bias are dramatically larger than those of the
other products.

This suggests a distinction between:

**temporal pattern agreement** and **absolute magnitude agreement**.

MOD16A2GF may capture some temporal variability while exhibiting
substantial magnitude disagreement with the reference observations under
the current benchmark configuration.

This result should be investigated and discussed rather than hidden.

------------------------------------------------------------------------

# 11. Site-level interpretation

The site-winner analysis provides an important complementary view.

Across the 55 primary site--product combinations and five metrics, the
number of metric wins is:

  Product           Site-level metric wins
  --------------- ------------------------
  **ERA5-LAND**                     **20**
  **PMLV2**                         **12**
  **MERRA2**                         **9**
  **FLDAS**                          **8**
  **GLDAS**                          **6**
  MOD16A2GF                          **0**

This demonstrates that the product-level ranking does not mean the same
product wins everywhere.

Different products dominate at different sites.

------------------------------------------------------------------------

# 12. Important site-specific findings

### BFT

FLDAS wins all five metrics:

-   RMSE = 2.480924
-   MAE = 2.099154
-   absolute bias = 2.054316
-   correlation = 0.838280
-   R² = 0.702713

This is the strongest example of FLDAS performing very well at an
individual site.

### BIT

PMLV2 wins:

-   RMSE;
-   MAE;
-   correlation;
-   R².

ERA5-LAND has the lowest absolute bias.

Thus, BIT illustrates how different products can excel at different
aspects of performance.

### BKC

GLDAS wins:

-   RMSE;
-   MAE;
-   absolute bias.

MERRA2 wins:

-   correlation;
-   R².

This is a clear example of the distinction between **absolute accuracy**
and **temporal agreement**.

### DIT

ERA5-LAND wins RMSE and MAE, while MERRA2 wins correlation and R².

Again, no single product dominates every metric.

### JIT

PMLV2 wins four metrics, while ERA5-LAND wins absolute bias.

### KKM

ERA5-LAND performs strongly on RMSE and MAE, while FLDAS wins
correlation and R² and PMLV2 obtains the lowest absolute bias.

### KNP

ERA5-LAND wins all five metrics.

This is one of the clearest site-level cases for ERA5-LAND.

### NIT

ERA5-LAND wins RMSE, MAE and absolute bias, while MERRA2 wins
correlation and R².

### SFT

GLDAS wins RMSE and MAE; PMLV2 has the lowest absolute bias; MERRA2 wins
correlation and R².

The very low correlation/R² values here also show that low temporal
agreement can coexist with relatively competitive absolute-error
metrics.

### SIT

ERA5-LAND wins RMSE, MAE, correlation and R², while MERRA2 has the
lowest absolute bias.

ERA5-LAND is particularly strong here, with:

``` text
Correlation = 0.977519
R²          = 0.955543
```

### UIT

ERA5-LAND wins RMSE and MAE, FLDAS wins absolute bias, and PMLV2 wins
correlation and R².

------------------------------------------------------------------------

# 13. Metric-level interpretation

The site-winner table shows that the products specialize in different
metrics.

### RMSE

-   ERA5-LAND: 6 wins
-   PMLV2: 2 wins
-   GLDAS: 2 wins
-   FLDAS: 1 win

### MAE

-   ERA5-LAND: 6 wins
-   PMLV2: 2 wins
-   GLDAS: 2 wins
-   FLDAS: 1 win

### Absolute Bias

-   ERA5-LAND: 4 wins
-   FLDAS: 2 wins
-   GLDAS: 2 wins
-   PMLV2: 2 wins
-   MERRA2: 1 win

### Correlation

-   MERRA2: 4 wins
-   PMLV2: 3 wins
-   ERA5-LAND: 2 wins
-   FLDAS: 2 wins

### R²

-   MERRA2: 4 wins
-   PMLV2: 3 wins
-   ERA5-LAND: 2 wins
-   FLDAS: 2 wins

This supports a key scientific interpretation:

> **Absolute-error metrics and temporal-agreement metrics do not
> necessarily identify the same winner.**

That is precisely why a multi-metric benchmark is more informative than
relying on RMSE or correlation alone.

------------------------------------------------------------------------

# 14. Important limitations

The Sprint 6 results should be interpreted within the scope of the
current benchmark.

### 14.1 Unequal site coverage

Products do not have the same number of eligible sites:

-   ERA5-LAND: 11
-   MERRA2: 11
-   GLDAS: 11
-   PMLV2: 9
-   MOD16A2GF: 8
-   FLDAS: 5

Therefore, products with fewer eligible sites have less evidence
supporting their product-level ranking.

### 14.2 Unequal sample sizes

Even after applying `N >= 10`, the median N differs substantially
between products.

### 14.3 Current benchmark period

The present analysis uses the configured benchmark period/year and
current BharatFlux observations. The results should therefore not be
generalized to all years or all climates without additional validation.

### 14.4 Ranking methodology

The overall rank is a composite rank across multiple metrics. It is
useful for summarization but does not replace detailed metric-level
analysis.

### 14.5 MOD16A2GF requires further investigation

The large absolute-error values warrant a dedicated review of scaling,
units, temporal aggregation and product/reference comparability before
making strong conclusions about its scientific quality.

------------------------------------------------------------------------

# 15. Scientific takeaway from Sprint 6

The current benchmark reveals three broad patterns:

### Pattern 1 --- ERA5-LAND is the most consistently strong product

ERA5-LAND provides the strongest overall balance across absolute error,
bias and temporal agreement, with the broadest site-level support among
the leading products.

### Pattern 2 --- MERRA2 is particularly strong for temporal agreement

MERRA2 frequently wins correlation and R² even when it does not have the
lowest absolute error.

### Pattern 3 --- Product performance is site-dependent

FLDAS, GLDAS and PMLV2 can outperform the overall leader at particular
sites and/or for particular metrics.

Therefore, the benchmark should be interpreted as:

> **There is no single product that dominates every site and every
> performance criterion. ERA5-LAND provides the strongest overall
> cross-site performance in the current primary benchmark, while other
> products exhibit important site- or metric-specific strengths.**

------------------------------------------------------------------------

# 16. Outputs produced

Sprint 6 generated:

``` text
results/summary/sprint6/product_summary.csv
results/summary/sprint6/site_winners.csv
results/summary/sprint6/site_product_ranks.csv
results/summary/sprint6/primary_benchmark.csv
results/summary/sprint6/benchmark_interpretation.json
```

The `site_winners.csv` contains **55 primary site × metric winners** and
was verified as having no duplicated site--metric rows.

------------------------------------------------------------------------

# 17. Sprint 6 status

**Status: COMPLETED**

Sprint 6 converts the quality-controlled multi-site benchmark into a
consolidated product-level and site-level interpretation framework.

The resulting benchmark provides the foundation for the next phase:
expanding OpenETBench beyond the current GEE products and adding richer
scientific evaluation and visualization.
