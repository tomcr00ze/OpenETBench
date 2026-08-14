# 🌍 OpenETBench

> **A modular and reproducible framework for benchmarking Evapotranspiration (ET) products against Flux Tower observations.**

OpenETBench is an open-source Python framework for evaluating satellite, reanalysis, and data-driven Evapotranspiration (ET) products using in-situ Flux Tower observations as the reference.

The framework is built around a common pipeline: observations are preprocessed into a standardized representation, ET products are extracted or ingested through product-specific adapters, observations and products are temporally harmonized, statistical metrics are computed consistently, and standardized visualizations and benchmark artifacts are produced.

The current implementation has been developed and validated using **BharatFlux** observations and **Google Earth Engine (GEE)**-accessible ET products.

---

## Table of Contents

- [Why OpenETBench?](#why-openetbench)
- [What is being benchmarked?](#what-is-being-benchmarked)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Benchmarking Workflow](#benchmarking-workflow)
- [Supported ET Products](#supported-et-products)
- [Reference Observations](#reference-observations)
- [Temporal Harmonization](#temporal-harmonization)
- [Benchmark Metrics](#benchmark-metrics)
- [Visualization](#visualization)
- [Output Structure](#output-structure)
- [Project Structure](#project-structure)
- [Development Status](#development-status)
- [Extensibility](#extensibility)
- [GEE and External Product Integration](#gee-and-external-product-integration)
- [Roadmap](#roadmap)
- [Design Principles](#design-principles)
- [Installation](#installation)
- [Current Usage](#current-usage)
- [Research Context](#research-context)
- [Author](#author)

---

# Why OpenETBench?

Evapotranspiration is a fundamental component of the terrestrial water and energy cycles and is widely used in hydrology, agriculture, climate studies, drought monitoring, and land-surface modelling.

A large number of ET products are available from different sources. These products can differ substantially in:

- spatial resolution,
- temporal resolution,
- input data,
- physical assumptions,
- estimation methodology,
- spatial and temporal coverage,
- units and aggregation conventions.

Consequently, comparing ET products requires more than simply placing two time series side by side.

OpenETBench provides a **consistent evaluation framework** in which different products can be processed through the same downstream benchmarking and visualization pipeline.

---

# What is being benchmarked?

At its core, OpenETBench compares a Flux Tower reference ET series with one or more independently produced ET estimates.

```text
                  Flux Tower ET
                    Reference
                       │
                       ▼
              ┌─────────────────┐
              │   OpenETBench   │
              └────────┬────────┘
                       ▲
                       │
          ┌────────────┼────────────┐
          │            │            │
       Satellite   Reanalysis   Data-driven
           ET           ET           ET
```

The current implementation uses **BharatFlux** observations as the reference. The evaluated products currently include satellite and reanalysis/data-driven products available through the common GEE workflow.

The architecture is intentionally not tied to one ET product or one observation network.

---

# Key Features

## 🛰️ Multi-Product ET Evaluation

A common product abstraction allows different ET products to be evaluated through the same extraction, harmonization, benchmarking, and visualization interfaces.

Product-specific properties such as the GEE collection, ET band, scale factor, spatial resolution, temporal resolution, units, and aggregation strategy are represented as product metadata.

## 🌱 Flux Tower Reference Data

The preprocessing layer converts raw BharatFlux observations into standardized datasets suitable for benchmarking.

Current preprocessing capabilities include:

- dataset discovery and loading,
- metadata preservation,
- column standardization,
- missing-value handling,
- numeric conversion,
- LE/ET data handling,
- validation,
- processed-data persistence.

Processed datasets are stored in machine-readable formats such as Parquet together with metadata JSON files.

## ☁️ Google Earth Engine Integration

The extraction layer provides a common interface for GEE-hosted ET products, including:

- Earth Engine initialization,
- product registration,
- ImageCollection access,
- spatial reduction around Flux Tower sites,
- product-specific scale factors,
- temporal aggregation,
- date filtering,
- conversion to standardized tabular data.

The downstream benchmark code therefore does not need a separate implementation for every GEE collection.

## ⏱️ Temporal Harmonization

Products are available at different temporal resolutions. OpenETBench performs product-aware temporal processing before comparison.

```text
8-day product   ───────────────► 8-day series
Daily product   ───────────────► Daily series
Monthly product ───────────────► Monthly series
Hourly product  ─► aggregation ─► Daily series
```

The current implementation includes higher-frequency handling for **MERRA-2**, where the source data are aggregated before comparison.

## 📊 Standard Benchmark Metrics

The current benchmark layer calculates:

- RMSE
- MAE
- Bias
- Pearson Correlation
- R²

## 📈 Standardized Visual Diagnostics

For each successful site/product benchmark, the visualization layer produces:

- observed-vs-product scatter plots,
- observed-vs-product time-series plots,
- Flux Tower site-location maps.

## 💾 Reproducible Result Artifacts

Each benchmark stores both numerical and visual outputs together, making a site/product evaluation self-contained and easy to inspect or archive.

---

# Architecture

OpenETBench follows a modular architecture in which each layer has a focused responsibility.

```text
┌─────────────────────────────┐
│        Preprocessing        │
│   Flux Tower observations   │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│         Extraction          │
│  GEE products / ingestion   │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│       Harmonization         │
│ Temporal / spatial alignment│
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│        Benchmarking         │
│   Metrics and evaluation    │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│       Visualization         │
│  Scatter / Time Series / Map│
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│           Export            │
│      CSV / JSON / PNG       │
└─────────────────────────────┘
```

This separation allows product-specific extraction logic to remain independent from common benchmarking logic.

---

# Benchmarking Workflow

The current end-to-end workflow is:

```text
Raw BharatFlux Data
        │
        ▼
Observation Preprocessing
        │
        ▼
Processed BharatFlux Dataset
        │
        ├─────────────────────────┐
        │                         │
        ▼                         ▼
Reference ET                ET Product Registry
                                  │
                                  ▼
                           GEE Product Extraction
                                  │
                                  ▼
                           Temporal Aggregation
                                  │
                                  ▼
                           Temporal Harmonization
                                  │
                ┌─────────────────┴─────────────────┐
                │                                   │
                ▼                                   ▼
          Observed ET                         Product ET
                │                                   │
                └─────────────────┬─────────────────┘
                                  │
                                  ▼
                           Benchmark Metrics
                                  │
                                  ▼
                         Visual Diagnostics
                                  │
                                  ▼
                           Result Artifacts
```

The intended result is a standardized comparison for each **site × product × time period** combination.

---

# Supported ET Products

The following products are currently validated through the GEE extraction workflow.

| Product | Category | Temporal Resolution | Status |
|---|---|---:|---|
| **MOD16A2GF** | Satellite | 8-day | ✅ Validated |
| **ERA5-Land** | Reanalysis | Daily | ✅ Validated |
| **FLDAS** | Land-surface / reanalysis | Monthly | ✅ Validated |
| **GLDAS** | Land-surface / reanalysis | Daily | ✅ Validated |
| **MERRA-2** | Reanalysis | Hourly → Daily | ✅ Validated |
| **PML-V2** | Data-driven / satellite-based | 8-day | ✅ Validated |

### Product abstraction

Products are represented through a common `ETProduct` abstraction containing metadata such as:

```text
ETProduct
├── name
├── collection
├── band
├── scale_factor
├── spatial_resolution
├── temporal_resolution
├── units
├── provider
├── coverage
└── aggregation information
```

The metadata-driven design keeps product-specific behavior separate from the shared benchmarking pipeline.

---

# Reference Observations

The current reference dataset is **BharatFlux**.

Processed observations use a standardized tabular representation containing fields such as:

```text
DoY
LE
ET
```

For benchmarking, the ET observation series is aligned with the corresponding product time series using common dates before statistical evaluation.

The preprocessing layer also supports the associated data-cleaning and LE/ET preparation required to turn raw tower files into benchmark-ready data.

---

# Temporal Harmonization

ET products do not share a common temporal resolution. OpenETBench therefore treats temporal resolution as part of the product definition rather than assuming that all datasets are daily.

The harmonization layer provides:

- temporal alignment,
- common-date filtering,
- Day-of-Year handling,
- product-specific temporal aggregation,
- observation/product merging.

For example, the current products include 8-day, daily, monthly, and hourly source data. MERRA-2 is handled by aggregating its higher-frequency data before the final comparison.

The output is a common benchmark dataframe containing fields such as:

```text
Date
DoY
Observed_LE
Observed_ET
Satellite_ET
```

where the final product column represents the evaluated ET product.

---

# Benchmark Metrics

OpenETBench currently calculates five core metrics.

| Metric | Purpose |
|---|---|
| **RMSE** | Measures the magnitude of prediction error, giving larger errors greater weight. |
| **MAE** | Measures average absolute error. |
| **Bias** | Quantifies systematic overestimation or underestimation. |
| **Pearson Correlation** | Measures linear association between observed and product ET. |
| **R²** | Measures the variance explained by the fitted relationship. |

The metrics are stored in `benchmark.json` for every benchmark.

Example:

```json
{
    "rmse": 13.17177895120969,
    "mae": 8.924795656628286,
    "bias": 7.6163704169232735,
    "correlation": 0.7880338078657112,
    "r2": 0.6209972823393326
}
```

---

# Visualization

OpenETBench provides three standardized visual diagnostics.

## Scatter Plot

The scatter plot compares observed ET against the evaluated product ET and provides a direct view of agreement, dispersion, and systematic differences.

**Output:** `scatter.png`

## Time-Series Plot

The time-series plot compares observed and product ET over the common temporal period. It is useful for assessing temporal tracking, seasonal behavior, offsets, and variability.

**Output:** `timeseries.png`

## Benchmark Site Map

The map displays the geographic location of the Flux Tower used in the benchmark.

**Output:** `map.png`

> **Note:** The current `map.png` is a **site-location map**, not a spatial ET field or product-specific raster map. Therefore, maps for different products evaluated at the same Flux Tower site are expected to look the same. Product-specific differences are represented by the scatter plot, time series, and benchmark statistics.

---

# Output Structure

Benchmark artifacts are organized by site and product:

```text
results/
└── BFT/
    ├── MOD16A2GF/
    │   ├── extraction.csv
    │   ├── benchmark.json
    │   ├── scatter.png
    │   ├── timeseries.png
    │   └── map.png
    │
    ├── ERA5-LAND/
    │   ├── extraction.csv
    │   ├── benchmark.json
    │   ├── scatter.png
    │   ├── timeseries.png
    │   └── map.png
    │
    ├── FLDAS/
    ├── GLDAS/
    ├── MERRA2/
    └── PMLV2/
```

### `extraction.csv`

Contains the aligned observation/product data used for benchmarking.

### `benchmark.json`

Contains the numerical benchmark metrics.

### PNG files

Contain the standardized visual diagnostics for the benchmark.

Keeping these artifacts together provides a reproducible record of each site/product evaluation.

---

# Project Structure

```text
OpenETBench/
│
├── data/
│   ├── raw/
│   ├── intermediate/
│   └── processed/
│       └── bharatflux/
│
├── docs/
├── figures/
├── notebooks/
│   ├── experiments/
│   └── workflows/
│
├── results/
│   └── <SITE>/<PRODUCT>/
│
├── src/
│   ├── preprocessing/
│   │   ├── loader.py
│   │   ├── cleaner.py
│   │   ├── converter.py
│   │   ├── exporter.py
│   │   ├── merger.py
│   │   ├── metadata.py
│   │   └── qc.py
│   │
│   ├── extraction/
│   │   ├── gee.py
│   │   ├── sites.py
│   │   ├── products.py
│   │   ├── extractor.py
│   │   └── storage.py
│   │
│   ├── harmonization/
│   │   ├── temporal.py
│   │   ├── spatial.py
│   │   ├── standardize.py
│   │   └── merge.py
│   │
│   ├── benchmarking/
│   │   ├── metrics.py
│   │   ├── statistics.py
│   │   ├── comparison.py
│   │   ├── uncertainty.py
│   │   └── ilamb.py
│   │
│   ├── visualization/
│   │   ├── scatter.py
│   │   ├── timeseries.py
│   │   ├── maps.py
│   │   ├── heatmap.py
│   │   └── taylor.py
│   │
│   ├── utils/
│   │   ├── config.py
│   │   ├── constants.py
│   │   └── io.py
│   │
│   └── scripts/
│       └── sprint3_visualization.py
│
├── tests/
│   ├── test_loader.py
│   ├── test_converter.py
│   └── test_metrics.py
│
├── CITATION.cff
├── CONTRIBUTING.md
├── environment.yml
├── LICENSE
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

# Notebook Organization

OpenETBench separates exploratory experimentation from systematic workflow notebooks.

### `notebooks/experiments/`

Used for exploratory analysis, prototyping, debugging, and investigation.

### `notebooks/workflows/`

Used for systematic demonstrations of the reusable OpenETBench pipeline. These notebooks are intended to call the common modules under `src/` rather than duplicating the core implementation.

This separation keeps exploratory work flexible without allowing experimental notebook code to become the canonical pipeline implementation.

---

# Development Status

The current implementation has been validated through three major stages.

### Core single-product benchmark

A real BharatFlux dataset was successfully evaluated against MOD16A2GF, including:

- observation loading,
- GEE extraction,
- temporal alignment,
- benchmark dataframe creation,
- metric calculation,
- CSV/JSON export.

### Multi-product validation

The common pipeline successfully evaluated all six current GEE-backed products:

```text
MOD16A2GF   ✓
ERA5-Land   ✓
FLDAS       ✓
GLDAS       ✓
MERRA-2     ✓
PML-V2      ✓
```

### Visualization validation

For all six products, the visualization pipeline successfully generated:

```text
scatter.png
 timeseries.png
 map.png
```

alongside the corresponding extraction and benchmark outputs.

The current validated scope therefore represents a working **single-site, multi-product GEE benchmarking pipeline**.

---

# Extensibility

The architecture is designed so that adding a new product should primarily require defining how that product is accessed and transformed into the common ET representation.

```text
New Product
     │
     ▼
Product Metadata / Adapter
     │
     ▼
Common Extraction / Ingestion
     │
     ▼
Common Harmonization
     │
     ▼
Common Benchmarking
     │
     ▼
Common Visualization
     │
     ▼
Standardized Results
```

The same philosophy can be applied to additional Flux Tower networks through observation-specific preprocessing adapters.

---

# GEE and External Product Integration

OpenETBench distinguishes between products that can be accessed directly through Google Earth Engine and products requiring external ingestion.

## Current GEE-backed scope

```text
MOD16A2GF
ERA5-Land
FLDAS
GLDAS
MERRA-2
PML-V2
```

## External products

Products currently tracked for future external integration include:

```text
GLEAM
SSEBop
BESS
GLASS ET
FLUXCOM-X / X-BASE ET
ALEXI
DisALEXI
MuSyQ ET
SMAP-PM ET
```

The intended external-data architecture is:

```text
External Product
      │
      ▼
Ingestion / Conversion
      │
      ▼
Standardized ET Series
      │
      ▼
Harmonization
      │
      ▼
Benchmarking
      │
      ▼
Visualization
```

This keeps the downstream evaluation process independent of the original data-distribution mechanism.

---

# Roadmap

## Multi-Site Evaluation

Extend the validated workflow from the current single-site benchmark to additional BharatFlux sites and years.

```text
Single Site
     │
     ▼
Multiple Sites
     │
     ▼
Multiple Years
     │
     ▼
Product × Site × Time Evaluation
```

## Expanded Product Coverage

Integrate additional ET products, particularly products that are not directly accessible through the current GEE workflow.

## Advanced Evaluation

Future benchmarking capabilities may include:

- spatial pattern evaluation,
- seasonal-cycle evaluation,
- interannual variability,
- distribution comparison,
- uncertainty analysis,
- Taylor diagrams,
- heatmaps,
- monthly climatology,
- consolidated product ranking,
- ILAMB-style evaluation.

## Broader Observation Networks

Extend the reference-data layer to additional Flux Tower networks, including FLUXNET-compatible observations.

---

# Design Principles

### Common interfaces

Different ET products should be evaluated through consistent interfaces wherever possible.

### Product-specific metadata

Product-specific behavior should be expressed through product metadata or adapters rather than duplicated throughout the pipeline.

### Separation of concerns

Preprocessing, extraction, harmonization, benchmarking, visualization, and export remain separate responsibilities.

### Reproducibility

Each benchmark should retain the aligned data, numerical metrics, and visual diagnostics required to inspect the evaluation.

### Extensibility

New products, sites, observation networks, and evaluation methods should be addable without redesigning the complete framework.

### Clean experimentation

Exploratory notebooks remain separate from the reusable implementation and systematic workflow notebooks.

---

# Installation

Clone the repository and install the project dependencies.

```bash
git clone <repository-url>
cd OpenETBench
pip install -r requirements.txt
```

Alternatively, use the provided Conda environment:

```bash
conda env create -f environment.yml
```

The GEE extraction workflow additionally requires a configured Google Earth Engine account/environment.

---

# Current Usage

The current validated visualization entry point can be executed from the project root.

For a single product:

```bash
python src/scripts/sprint3_visualization.py --site BFT --products MOD16A2GF
```

For multiple products:

```bash
python src/scripts/sprint3_visualization.py --site BFT --products ERA5-LAND FLDAS GLDAS MERRA2 PMLV2
```

The visualization pipeline reads the corresponding benchmark results and generates standardized artifacts under:

```text
results/<SITE>/<PRODUCT>/
```

The extraction, preprocessing, harmonization, benchmarking, and visualization logic is implemented through the reusable modules under `src/`.

---

# Research Context

OpenETBench is being developed to support systematic evaluation of ET products against ground-based observations.

The long-term objective is to move beyond isolated pairwise comparisons and establish a reusable framework in which ET products from different methodological families can be evaluated using consistent:

- reference observations,
- temporal alignment,
- statistical metrics,
- visual diagnostics,
- data structures,
- result formats.

The resulting framework can support larger-scale comparisons across sites, temporal periods, and ET product families.

---

# Author

**Adarsh Jha**  
M.S. Data Science  
Defence Institute of Advanced Technology (DIAT), Pune

OpenETBench is being developed as part of research on benchmarking global Evapotranspiration products against Flux Tower observations.
