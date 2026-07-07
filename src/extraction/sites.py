"""
OpenETBench
------------

BharatFlux site registry.

This module contains metadata for all BharatFlux flux tower sites.
These coordinates are used for extracting ET products from
Google Earth Engine.

Author: Adarsh Jha
"""

from dataclasses import dataclass


# ============================================================
# BharatFlux Site
# ============================================================

@dataclass(frozen=True)
class FluxSite:
    """
    Metadata for one BharatFlux flux tower site.
    """

    id: str
    name: str
    latitude: float
    longitude: float


# ============================================================
# BharatFlux Site Registry
# ============================================================

BHARATFLUX_SITES = {

    "BFT": FluxSite(
        id="BFT",
        name="BFT",
        latitude=30.2756,
        longitude=79.7311,
    ),

    "BIT": FluxSite(
        id="BIT",
        name="BIT",
        latitude=13.5503,
        longitude=77.4250,
    ),

    "BKC": FluxSite(
        id="BKC",
        name="BKC",
        latitude=18.1186,
        longitude=74.4890,
    ),

    "DIT": FluxSite(
        id="DIT",
        name="DIT",
        latitude=30.3760,
        longitude=78.0783,
    ),

    "JIT": FluxSite(
        id="JIT",
        name="JIT",
        latitude=26.7490,
        longitude=94.2037,
    ),

    "KKM": FluxSite(
        id="KKM",
        name="KKM",
        latitude=10.7870,
        longitude=76.4490,
    ),

    "RAR": FluxSite(
        id="RAR",
        name="RAR",
        latitude=23.4270,
        longitude=87.2870,
    ),

    "RJP": FluxSite(
        id="RJP",
        name="RJP",
        latitude=26.0008,
        longitude=73.3499,
    ),

    "SKP": FluxSite(
        id="SKP",
        name="SKP",
        latitude=22.9570,
        longitude=88.5230,
    ),
}

# ============================================================
# Helper Functions
# ============================================================

def get_site(site_id: str) -> FluxSite:
    """
    Return metadata for a BharatFlux site.

    Parameters
    ----------
    site_id : str

    Returns
    -------
    FluxSite
    """

    if site_id not in BHARATFLUX_SITES:
        raise KeyError(
            f"Unknown BharatFlux site: {site_id}"
        )

    return BHARATFLUX_SITES[site_id]