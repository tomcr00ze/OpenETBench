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
| 🔍 Pending Investigation | Investigation is ongoing |
| ⏸ Deferred | Planned for future implementation using external datasets (NetCDF, GeoTIFF, uploaded GEE assets, etc.) |

---

# Project Development Strategy

The benchmark consists of **15 target ET products**.

We intentionally do **not** add new products outside this list until all target products have been investigated.

The benchmark list is:

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
| FLUXCOM-X | 🔍 Pending Investigation |
| GLASS ET | ⏸ Deferred |
| MuSyQ ET | 🔍 Pending Investigation |
| SMAP-PM ET | 🔍 Pending Investigation |

---

# Investigation Log

---

## 1. MOD16A2GF

### Decision

Implemented.

### Reason

- Publicly available in GEE.
- Stable.
- Global coverage.
- Native extraction supported.

### Status

✅ Completed

---

## 2. GLEAM

### Investigation

Global ET product.

### Findings

- No official public ImageCollection in GEE.

### Decision

Implement later using NetCDF or uploaded assets.

### Status

⏸ Deferred

---

## 3. SSEBop ET

### Investigation

Global ET product exists.

### Findings

OpenET provides only CONUS implementation.

No public global GEE ImageCollection.

### Decision

Implement later using external dataset.

### Status

⏸ Deferred

---

## 4. ERA5-Land

Implemented successfully.

### Notes

- Daily product
- Native GEE support

### Status

✅ Completed

---

## 5. FLDAS

Implemented successfully.

### Status

✅ Completed

---

## 6. GLDAS

Implemented successfully.

### Status

✅ Completed

---

## 7. MERRA-2

### Investigation Summary

Originally produced hourly values.

### Engineering Changes

Implemented custom:

- hourly → daily aggregation
- point sampling

Added new framework concepts:

- aggregation strategy
- sampling strategy

### Status

✅ Completed

---

## 8. PML-V2

### Investigation Summary

Collection:

projects/pml_evapotranspiration/PML/OUTPUT/PML_V22a

### Findings

- ET band = ET
- Scale factor = 0.01
- 8-day product
- Global coverage
- Buffer sampling works

### Decision

Integrated directly.

### Status

✅ Completed

---

## 9. ALEXI ET

### Investigation

Only public GEE implementation found:

projects/openet/assets/disalexi/conus/gridmet/monthly_v2_1

### Findings

- OpenET implementation
- CONUS only
- Not applicable for BharatFlux sites

Original ALEXI algorithm is global but no public global precomputed GEE dataset currently exists.

### Decision

Implement later using external datasets or custom implementation.

### Status

⏸ Deferred

---

## 10. DisALEXI

Same findings as ALEXI.

### Status

⏸ Deferred

---

## 11. BESS

### Investigation

Public GEE dataset:

SNU/ESL/BESS/Rad/v1

### Findings

Only radiation variables available.

No ET product exists in public GEE.

### Decision

Implement later using external dataset.

### Status

⏸ Deferred

---

## 12. FLUXCOM-X

Investigation pending.

### Status

🔍 Pending Investigation

---

## 13. GLASS ET

### Investigation

No official public GEE dataset found.

### Decision

Implement later using external dataset.

### Status

⏸ Deferred

---

## 14. MuSyQ ET

Investigation pending.

### Status

🔍 Pending Investigation

---

## 15. SMAP-PM ET

Investigation pending.

### Status

🔍 Pending Investigation

---

# Engineering Decisions

## Phase 1

Implement all products that can be extracted directly from Google Earth Engine.

Current products:

- MOD16A2GF
- ERA5-Land
- FLDAS
- GLDAS
- MERRA-2
- PML-V2

---

## Phase 2

Support external datasets.

Planned input formats:

- NetCDF
- GeoTIFF
- Uploaded Earth Engine Assets
- Other research datasets

Products:

- GLEAM
- SSEBop
- BESS
- GLASS
- ALEXI
- DisALEXI

---

# Future Notes

This document should be updated after every product investigation.

Each new entry should include:

- Availability
- Collection ID
- Scale factor
- Temporal resolution
- Spatial resolution
- Sampling strategy
- Aggregation strategy
- Engineering decisions
- Implementation status