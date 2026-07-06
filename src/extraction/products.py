"""
OpenETBench
-----------

Earth Engine ET product registry.

Responsibilities
----------------
- Store metadata for all ET products
- Provide a single lookup interface

Author: Adarsh Jha
"""

from dataclasses import dataclass


# ============================================================
# ET Product Metadata
# ============================================================

@dataclass(frozen=True)
class ETProduct:
    """
    Metadata describing an ET product.

    Attributes
    ----------
    name : str
        Product name.

    collection : str
        Earth Engine ImageCollection ID.

    band : str
        Band containing evapotranspiration.

    scale : int
        Native spatial resolution (meters).

    temporal_resolution : str
        Native temporal resolution.

    units : str
        Units of the ET band.

    provider : str
        Dataset provider.
    """

    name: str
    collection: str
    band: str
    scale: int
    temporal_resolution: str
    units: str
    provider: str


# ============================================================
# ET Product Registry
# ============================================================

ET_PRODUCTS: dict[str, ETProduct] = {

    # --------------------------------------------------------
    # MOD16A2GF
    # --------------------------------------------------------
    "MOD16A2GF": ETProduct(
        name="MOD16A2GF",
        collection="MODIS/061/MOD16A2GF",
        band="ET",
        scale=500,
        temporal_resolution="8-day",
        units="kg m-2 / 8-day",
        provider="NASA",
    ),

    # --------------------------------------------------------
    # SSEBop
    # --------------------------------------------------------
    "SSEBop": ETProduct(
        name="SSEBop",
        collection="OpenET/SSEBOP/CONUS/GRIDMET/MONTHLY/v2_0",
        band="et",
        scale=1000,
        temporal_resolution="monthly",
        units="mm",
        provider="OpenET",
    ),

    # --------------------------------------------------------
    # ERA5-Land
    # --------------------------------------------------------
    "ERA5-Land": ETProduct(
        name="ERA5-Land",
        collection="ECMWF/ERA5_LAND/DAILY_AGGR",
        band="total_evaporation_sum",
        scale=11132,
        temporal_resolution="daily",
        units="m",
        provider="ECMWF",
    ),

}

# ============================================================
# Product Lookup
# ============================================================

def get_product(
    name: str,
) -> ETProduct:
    """
    Return metadata for an ET product.

    Parameters
    ----------
    name : str
        Product name.

    Returns
    -------
    ETProduct
    """

    if name not in ET_PRODUCTS:
        raise ValueError(
            f"Unknown ET product: {name}"
        )

    return ET_PRODUCTS[name]