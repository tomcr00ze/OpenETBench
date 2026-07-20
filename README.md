# 🌍 OpenETBench

> An open-source benchmarking toolkit for evaluating satellite, reanalysis, and machine-learning based Evapotranspiration (ET) products against Flux Tower observations.

---

## Overview

OpenETBench is a modular Python toolkit designed to benchmark global and regional Evapotranspiration (ET) datasets against in-situ Flux Tower observations.

The toolkit aims to provide a reproducible pipeline for

- preprocessing flux tower observations,
- extracting satellite ET products,
- harmonizing spatial and temporal resolutions,
- benchmarking ET products using standard metrics,
- generating publication-quality visualizations.

Although initially developed using the BharatFlux network, the architecture is designed to support other Flux Tower networks (e.g., FLUXNET) with minimal changes.

The framework now supports both native daily ET products and
high-frequency datasets requiring temporal aggregation (e.g. MERRA-2).

---

# Current Project Status

## ✅ Milestone 1 — BharatFlux Preprocessing (Completed)

Implemented a complete preprocessing pipeline for BharatFlux observations.

### Features

- Automatic dataset loading
- Metadata preservation
- Column standardization
- Missing value handling
- Numeric type conversion
- LE/ET split file merging
- Validation reports
- Processed dataset persistence

### Output

```
Raw BharatFlux CSV
        │
        ▼
Preprocessing
        │
        ▼
Clean BharatFlux Dataset
        │
        ├── parquet
        └── metadata.json
```

---

## ✅ Milestone 2 — Earth Engine Setup (Completed)

Implemented Google Earth Engine integration.

### Features

- Earth Engine authentication
- Connection verification
- ET product registry
- BharatFlux site registry

Current supported product

- MOD16A2GF
- ERA5-Land
- GLDAS
- FLDAS
- MERRA-2

Current supported site

- BharatFlux towers

---

## ✅ Milestone 3 — Earth Engine ET Extraction Framework (Completed)

Implemented a modular Google Earth Engine extraction framework for
multiple ET products.

### Features

- Generic ET product registry
- Automatic ImageCollection loading
- Spatial reduction
- Temporal aggregation
- Product-specific scale factors
- Daily time-series generation
- Day-of-Year computation

Output

```
Date
DoY
Satellite_ET
```

---

## ✅ Extraction Framework Enhancements

Recent improvements include:

- Product-specific temporal aggregation strategies
- Hourly → Daily aggregation for MERRA-2
- Product-specific spatial sampling strategies
- Generic extraction pipeline reusable across ET products
- Support for coarse-resolution reanalysis datasets

--- 

## ✅ Milestone 4 — Harmonization (Completed)

Implemented temporal harmonization.

### Current

- Temporal alignment
- Common Day-of-Year filtering
- Observation/Satellite merging

Output

```
Observed ET
Satellite ET
Common Dates
```

---

## ✅ Milestone 5 — Benchmarking (Partial Completed)

Current Metrics
---------------
✔ RMSE
✔ MAE
✔ Bias
✔ Pearson Correlation
✔ R²

Upcoming Benchmarking
---------------------
• Spatial Pattern
• Seasonal Cycle
• Interannual Variability
• Distribution Comparison
• Uncertainty Analysis

---

## ✅ Milestone 6 — Visualization (Completed)

Current figures

- Scatter Plot
- Flux Tower Location Map

Example outputs

```
Observed vs Satellite Scatter

BharatFlux Tower Map
```

---

# Current Pipeline

```
Raw BharatFlux Data
        │
        ▼
Preprocessing
        │
        ▼
Processed BharatFlux
        │
        ▼
Google Earth Engine
        │
        ▼
ET Product Extraction
        │
        ▼
Temporal Aggregation
        │
        ▼
Spatial Reduction
        │
        ▼
Temporal Harmonization
        │
        ▼
Merged Dataset
        │
        ▼
Benchmark Metrics
        │
        ▼
Visualization

```
# Extraction Architecture

Each ET product is described through a metadata registry.

```

ETProduct
      │
      ▼
Load ImageCollection
      │
      ▼
Temporal Aggregation
      │
      ▼
Spatial Reduction
      │
      ▼
DataFrame Conversion

```

---

# Project Structure

```
OpenETBench/

data/
    raw/
    processed/
    intermediate/

docs/
figures/
results/

src/

    preprocessing/
        loader.py
        cleaner.py

    extraction/
        gee.py
        sites.py
        products.py
        extractor.py
        storage.py

    harmonization/
        temporal.py
        spatial.py
        merge.py

    benchmarking/
        metrics.py
        uncertainty.py
        ilamb.py

    visualization/
        scatter.py
        maps.py
        heatmap.py
        taylor.py

    utils/
```

---

# Roadmap

## Phase 1 (Completed)

- BharatFlux preprocessing
- Earth Engine setup
- MOD16 extraction
- Temporal harmonization
- Benchmark metrics
- Scatter plots
- Site maps

---

## Phase 2 (In Progress)

### Completed

- MOD16A2GF
- GLEAM
- SSEBop
- ERA5-Land
- GLDAS
- FLDAS
- MERRA-2

### Remaining

- PML-V2
- ETMonitor
- ALEXI
- DisALEXI
- BESS

---

## Phase 3

Spatial Harmonization

- Conservative Regridding (CDO)
- Resolution harmonization
- CRS harmonization

---

## Phase 4

Advanced Visualization

- Taylor Diagram
- Heatmaps
- Monthly climatology
- Time-series comparison
- Seasonal comparison

---

## Phase 5

ILAMB-style Evaluation

- Overall score
- Variable ranking
- Performance dashboard

---

## Phase 6

OpenETBench v1.0

Support benchmarking of

- BharatFlux
- FLUXNET

against

- Satellite ET Products
- Reanalysis Products
- Machine Learning ET Products

---

# Design Philosophy

OpenETBench follows a modular architecture.

Each module performs exactly one responsibility.

```
Preprocessing
        │
Extraction
        │
Harmonization
        │
Benchmarking
        │
Visualization
```

This allows

- easy testing
- reproducibility
- future extension
- cleaner codebase

---

# Future Goals

- Support multiple Flux Tower networks
- Support regional ET products
- Add uncertainty propagation
- Add automatic report generation
- Add command-line interface
- Add configuration files
- Publish as an open-source Python package

---

# Author

**Adarsh Jha**

M.S. Data Science

Defence Institute of Advanced Technology (DIAT), Pune

OpenETBench is being developed as part of research on benchmarking global Evapotranspiration products against Flux Tower observations.
