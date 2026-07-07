"""
OpenETBench
------------

BharatFlux site registry.

This module contains metadata for all BharatFlux flux tower sites.
These coordinates are used for extracting ET products from
Google Earth Engine.

Author: Adarsh Jha
"""

# ============================================================
# BharatFlux Site Registry
# ============================================================

from dataclasses import dataclass


@dataclass(frozen=True)
class Site:
    """
    BharatFlux flux tower metadata.

    Parameters
    ----------
    id : str
        Site abbreviation.

    latitude : float
        Latitude (decimal degrees).

    longitude : float
        Longitude (decimal degrees).

    elevation : float | None
        Elevation above mean sea level (m).

    buffer_m : int
        Radius (m) used for satellite extraction.
    """

    id: str
    latitude: float
    longitude: float
    elevation: float | None = None
    buffer_m: int = 700


# ============================================================
# BharatFlux Sites
#
# Coordinates taken from:
#
# Deb Burman et al. (2025)
# Agricultural and Forest Meteorology
# Table 1
# ============================================================

SITES: dict[str, Site] = {

    "KNP": Site(
        id="KNP",
        latitude=26.58,
        longitude=93.10,
        elevation=80,
    ),

    "BFT": Site(
        id="BFT",
        latitude=21.86,
        longitude=77.42,
        elevation=507,
    ),

    "KKM": Site(
        id="KKM",
        latitude=29.38,
        longitude=79.37,
        elevation=1217,
    ),

    "DIT": Site(
        id="DIT",
        latitude=15.50,
        longitude=74.99,
        elevation=692,
    ),

    "BKC": Site(
        id="BKC",
        latitude=25.06,
        longitude=82.59,
        elevation=169,
    ),

    "BIT": Site(
        id="BIT",
        latitude=11.76,
        longitude=76.59,
        elevation=873,
    ),

    "NIT": Site(
        id="NIT",
        latitude=22.80,
        longitude=72.57,
        elevation=55,
    ),

    "SIT": Site(
        id="SIT",
        latitude=26.00,
        longitude=85.67,
        elevation=39,
    ),

    "JIT": Site(
        id="JIT",
        latitude=26.99,
        longitude=71.34,
        elevation=120,
    ),

    "UIT": Site(
        id="UIT",
        latitude=26.51,
        longitude=80.22,
        elevation=129,
    ),

    "PVM": Site(
        id="PVM",
        latitude=11.43,
        longitude=79.79,
        elevation=None,
    ),

    "SFT": Site(
        id="SFT",
        latitude=21.82,
        longitude=88.62,
        elevation=None,
    ),
}


# ============================================================
# Helper Functions
# ============================================================

def get_site(site_id: str) -> Site:
    """
    Return a BharatFlux site.

    Parameters
    ----------
    site_id : str
        Site abbreviation.

    Returns
    -------
    Site
    """

    try:
        return SITES[site_id.upper()]

    except KeyError as exc:

        raise KeyError(
            f"Unknown BharatFlux site: {site_id}"
        ) from exc


def list_sites() -> list[str]:
    """
    Return all available BharatFlux site IDs.
    """

    return sorted(SITES.keys())