# ET Product Investigation & Development Log

## Purpose

This document records the investigation, implementation decisions, and current status of every evapotranspiration (ET) product considered in the OpenETBench project.

The goal is to maintain a transparent engineering log describing:

- Investigation process
- Availability in Google Earth Engine (GEE)
- Implementation decisions
- Reasons for inclusion or exclusion
- Future work

---

# Product Status Legend

| Status | Meaning |
|---------|---------|
| ✅ Completed | Fully integrated and tested in the extraction framework |
| ⏸ Deferred (External Dataset Integration) | Product requires external datasets, uploaded GEE assets, NetCDF, GeoTIFF or custom implementation |
| 🔍 Under Investigation | Investigation still ongoing |

---

# Project Development Strategy

The benchmark consists of **15 predefined ET products**.

We intentionally do **not** introduce additional ET products until these fifteen products have been completely investigated.

Target products:

1. MOD16A2GF
2. GLEAM
3. SSEBop ET
4. ERA5-Land
5. FLDAS Global
6. GLDAS
7. MERRA-2
8. PML-V2
9. ALEXI ET
10. DisALEXI
11. BESS
12. FLUXCOM-X (X-BASE ET)
13. GLASS ET
14. MuSyQ ET
15. SMAP-PM ET

---

# Current Status

| Product | Status |
|---------|--------|
| MOD16A2GF | ✅ Completed |
| GLEAM | ⏸ Deferred |
| SSEBop ET | ⏸ Deferred |
| ERA5-Land | ✅ Completed |
| FLDAS | ✅ Completed |
| GLDAS | ✅ Completed |
| MERRA-2 | ✅ Completed |
| PML-V2 | ✅ Completed |
| ALEXI ET | ⏸ Deferred |
| DisALEXI | ⏸ Deferred |
| BESS | ⏸ Deferred |
| FLUXCOM-X (X-BASE ET) | ⏸ Deferred |
| GLASS ET | ⏸ Deferred |
| MuSyQ ET | ⏸ Deferred |
| SMAP-PM ET | ⏸ Deferred |

---

# Investigation Log

---

## 1. MOD16A2GF

### Decision

Implemented.

### Findings

- Native public GEE dataset.
- Global coverage.
- Stable MODIS product.
- Native extraction supported.

### Status

✅ Completed

---

## 2. GLEAM

### Findings

- No official public ImageCollection available in GEE.
- Distributed primarily as NetCDF.

### Decision

Move to External Dataset Integration.

### Status

⏸ Deferred

---

## 3. SSEBop ET

### Findings

- OpenET implementation available only for CONUS.
- No public global ImageCollection.

### Decision

Move to External Dataset Integration.

### Status

⏸ Deferred

---

## 4. ERA5-Land

### Findings

- Native GEE support.
- Daily product.

### Status

✅ Completed

---

## 5. FLDAS Global

Successfully integrated.

### Status

✅ Completed

---

## 6. GLDAS

Successfully integrated.

### Status

✅ Completed

---

## 7. MERRA-2

### Engineering Notes

Originally an hourly product.

Framework enhancements introduced:

- Hourly → Daily aggregation
- Sampling strategy abstraction

### Status

✅ Completed

---

## 8. PML-V2

### Dataset

```
projects/pml_evapotranspiration/PML/OUTPUT/PML_V22a
```

### Findings

- ET band available.
- Scale factor = 0.01.
- Global coverage.
- 8-day temporal resolution.
- Buffer sampling supported.

### Engineering Notes

Framework updated to support:

- Buffer sampling strategy

### Status

✅ Completed

---

## 9. ALEXI ET

### Findings

Only OpenET CONUS implementation exists.

```
projects/openet/assets/disalexi/conus/gridmet/monthly_v2_1
```

Original ALEXI algorithm is global, but no global precomputed GEE dataset currently exists.

### Decision

Move to External Dataset Integration.

### Status

⏸ Deferred

---

## 10. DisALEXI

### Findings

Same situation as ALEXI.

Only OpenET CONUS implementation exists.

### Decision

Move to External Dataset Integration.

### Status

⏸ Deferred

---

## 11. BESS

### Public Dataset

```
SNU/ESL/BESS/Rad/v1
```

### Findings

Contains only radiation variables.

No ET product is publicly available in GEE.

### Decision

Move to External Dataset Integration.

### Status

⏸ Deferred

---

## 12. FLUXCOM-X (X-BASE ET)

### Findings

- Final ET products are distributed through the ICOS Carbon Portal.
- No official public GEE ImageCollection exists.
- GEE is used only for processing some input datasets.

### Decision

Move to External Dataset Integration.

### Status

⏸ Deferred

---

## 13. GLASS ET

### Findings

No official public GEE ImageCollection available.

Distributed externally.

### Decision

Move to External Dataset Integration.

### Status

⏸ Deferred

---

## 14. MuSyQ ET

### Findings

- Not available in the public GEE catalog.
- Distributed as external raster products.
- Primarily covers the China–ASEAN region.
- Can be uploaded manually into GEE if required.

### Decision

Move to External Dataset Integration.

### Status

⏸ Deferred

---

## 15. SMAP-PM ET

### Findings

Public GEE provides:

```
NASA/SMAP/SPL4SMGP/008
```

This is the SMAP Level-4 land surface model product, **not** the published SMAP-PM ET benchmark dataset.

Although it contains:

```
land_evapotranspiration_flux
```

this variable is **not equivalent** to the published SMAP-PM ET product intended for benchmarking.

### Decision

To preserve scientific consistency, SMAP-PM will not be substituted with the Level-4 evapotranspiration flux variable.

Move to External Dataset Integration.

### Status

⏸ Deferred

---

# Engineering Decisions

## Phase 1 — Native GEE Products

Implemented directly through public Google Earth Engine datasets.

Completed products:

- MOD16A2GF
- ERA5-Land
- FLDAS
- GLDAS
- MERRA-2
- PML-V2

---

## Phase 2 — External Dataset Integration

Products requiring one of:

- NetCDF
- GeoTIFF
- Uploaded GEE Assets
- Custom Earth Engine Assets
- Local preprocessing pipelines

Products:

- GLEAM
- SSEBop
- ALEXI
- DisALEXI
- BESS
- FLUXCOM-X
- GLASS
- MuSyQ
- SMAP-PM

---

# Framework Enhancements During Development

During implementation the extraction framework evolved to support:

- Product abstraction
- Aggregation strategies
- Sampling strategies
- Hourly → Daily aggregation
- Buffer sampling
- Scale factor handling
- Modular product configuration

---

# Current Progress

## Native GEE Products

**6 / 15 completed**

## External Dataset Integration

**9 / 15 deferred**

These deferred products remain scientifically valid targets and will be implemented during the second development phase using external datasets or uploaded Earth Engine assets.

---

# Future Notes

This document should be updated after every product investigation.

Each new investigation should document:

- Dataset availability
- GEE Collection ID
- ET band
- Scale factor
- Spatial resolution
- Temporal resolution
- Sampling strategy
- Aggregation strategy
- Engineering decisions
- Implementation status