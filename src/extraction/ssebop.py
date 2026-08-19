"""
OpenETBench
-----------

External SSEBop V6.1 monthly Actual ET extractor.

This module is intentionally independent of Google Earth Engine. It reads the
monthly SSEBop ``*_actual_mm.tif`` rasters supplied by USGS/FEWS and extracts
the pixel containing a BharatFlux tower coordinate.

The extractor returns the same canonical product dataframe used by the GEE
extractor:

    Date | DoY | ET

SSEBop monthly values are totals in mm/month.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import re
from typing import Iterable

import pandas as pd
import rasterio
from rasterio.io import MemoryFile

from extraction.sites import Site


_FILENAME_RE = re.compile(
    r"m(?P<year>\d{4})(?P<month>\d{2})_viirsSSEBopETv(?P<version>[\d.]+)_actual_mm\.tif$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SSEBopRasterRef:
    """Reference to one monthly SSEBop raster."""

    year: int
    month: int
    version: str
    archive: Path
    member: str


def _discover_members(zip_paths: Iterable[Path]) -> list[SSEBopRasterRef]:
    """Discover all SSEBop actual-ET TIFF members in one or more ZIP archives."""

    refs: list[SSEBopRasterRef] = []

    for zip_path in zip_paths:
        zip_path = Path(zip_path)
        if not zip_path.exists():
            raise FileNotFoundError(f"SSEBop ZIP not found: {zip_path}")

        import zipfile

        with zipfile.ZipFile(zip_path) as archive:
            for member in archive.namelist():
                name = Path(member).name
                match = _FILENAME_RE.fullmatch(name)
                if not match:
                    continue

                refs.append(
                    SSEBopRasterRef(
                        year=int(match.group("year")),
                        month=int(match.group("month")),
                        version=(
                        "6.1"
                        if match.group("version") in {"61", "6.1"}
                        else match.group("version")
                    ),
                        archive=zip_path,
                        member=member,
                    )
                )

    refs.sort(key=lambda x: (x.year, x.month, str(x.archive), x.member))

    # One raster per year-month is required.
    by_period: dict[tuple[int, int], list[SSEBopRasterRef]] = {}
    for ref in refs:
        by_period.setdefault((ref.year, ref.month), []).append(ref)

    duplicates = {
        period: candidates
        for period, candidates in by_period.items()
        if len(candidates) > 1
    }
    if duplicates:
        details = {
            f"{year}-{month:02d}": [
                f"{r.archive.name}:{r.member}" for r in candidates
            ]
            for (year, month), candidates in duplicates.items()
        }
        raise ValueError(
            "Duplicate SSEBop actual-ET rasters found for one or more "
            f"months: {details}"
        )

    return [candidates[0] for candidates in by_period.values()]


def _read_point_from_zip(
    ref: SSEBopRasterRef,
    site: Site,
) -> float | None:
    """Read the SSEBop value at the BharatFlux site coordinate."""

    import zipfile

    with zipfile.ZipFile(ref.archive) as archive:
        raw = archive.read(ref.member)

    with MemoryFile(BytesIO(raw)) as memfile:
        with memfile.open() as dataset:
            if dataset.crs is None:
                raise ValueError(
                    f"{ref.member}: raster has no CRS."
                )

            if dataset.crs.to_string().upper() not in {
                "EPSG:4326",
                "OGC:CRS84",
            }:
                raise ValueError(
                    f"{ref.member}: expected geographic WGS84 raster, "
                    f"found {dataset.crs}."
                )

            sample = next(
                dataset.sample(
                    [(site.longitude, site.latitude)],
                    indexes=1,
                    masked=True,
                )
            )

            value = sample[0]

            if value is None:
                return None

            try:
                if bool(value.mask):
                    return None
            except AttributeError:
                pass

            value = float(value)
            if dataset.nodata is not None and value == float(dataset.nodata):
                return None

            return value


def site_covered_by_ssebop(
    site: Site,
    zip_paths: Iterable[Path],
) -> bool:
    """
    Check whether a BharatFlux site falls inside the supplied SSEBop raster
    coverage.

    The global SSEBop model is distributed through FEWS NET in regional
    raster windows. Therefore product-level global coverage does not imply
    that every downloaded regional raster contains every BharatFlux site.
    """
    refs = _discover_members(zip_paths)
    if not refs:
        return False

    import zipfile

    ref = refs[0]
    with zipfile.ZipFile(ref.archive) as archive:
        raw = archive.read(ref.member)

    with MemoryFile(BytesIO(raw)) as memfile:
        with memfile.open() as dataset:
            left, bottom, right, top = dataset.bounds
            return (
                left <= site.longitude <= right
                and bottom <= site.latitude <= top
            )


def extract_monthly_timeseries(
    site: Site,
    zip_paths: Iterable[Path],
    *,
    start_year: int | None = None,
    end_year: int | None = None,
) -> pd.DataFrame:
    """
    Extract monthly SSEBop Actual ET for one BharatFlux site.

    Parameters
    ----------
    site:
        BharatFlux site metadata.

    zip_paths:
        One or more ZIP archives containing ``*_actual_mm.tif`` files.

    start_year, end_year:
        Optional inclusive year bounds.

    Returns
    -------
    pandas.DataFrame
        Canonical product dataframe with columns:
        ``Date``, ``DoY``, ``ET``.
    """

    refs = _discover_members(zip_paths)

    if start_year is not None:
        refs = [r for r in refs if r.year >= start_year]
    if end_year is not None:
        refs = [r for r in refs if r.year <= end_year]

    if not refs:
        raise ValueError("No SSEBop actual-ET rasters found in requested period.")

    versions = sorted({r.version for r in refs})
    if len(versions) != 1:
        raise ValueError(
            f"Multiple SSEBop versions found: {versions}. "
            "Use one version for a benchmark run."
        )

    rows: list[dict] = []

    for ref in refs:
        value = _read_point_from_zip(ref, site)
        rows.append(
            {
                "Date": pd.Timestamp(ref.year, ref.month, 1),
                "ET": value,
                "SSEBop_Version": ref.version,
            }
        )

    df = pd.DataFrame(rows).sort_values("Date").reset_index(drop=True)

    # Preserve missing monthly rasters/pixels as NaN; downstream QC decides
    # whether a site-year has enough valid observations.
    df["DoY"] = df["Date"].dt.dayofyear.astype("int64")

    return df[["Date", "DoY", "ET", "SSEBop_Version"]]


def validate_inventory(
    zip_paths: Iterable[Path],
) -> pd.DataFrame:
    """
    Return a year-month inventory of SSEBop actual-ET rasters.

    This is useful before running the benchmark to verify that all 60
    required months are present.
    """

    refs = _discover_members(zip_paths)

    rows = [
        {
            "Year": ref.year,
            "Month": ref.month,
            "Version": ref.version,
            "Archive": str(ref.archive),
            "Member": ref.member,
        }
        for ref in refs
    ]

    return pd.DataFrame(rows).sort_values(
        ["Year", "Month"]
    ).reset_index(drop=True)
