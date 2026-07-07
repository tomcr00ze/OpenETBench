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

    product_type : str
        ET product category.

    gee_collection : str
        Earth Engine ImageCollection ID.

    band : str
        Band containing evapotranspiration.

    scale : int
        Native spatial resolution (meters).

    temporal_resolution : str
        Native temporal resolution.

    scale_factor : float
        Multiplicative scale factor applied to the raw band values.

    units : str
        Native units of the ET band.

    provider : str
        Dataset provider.
    """

    name: str
    product_type: str
    gee_collection: str
    band: str
    scale: int
    temporal_resolution: str
    scale_factor: float
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
        product_type="Remote Sensing",
        gee_collection="MODIS/061/MOD16A2GF",
        band="ET",
        scale=500,
        temporal_resolution="8-day",
        scale_factor=0.1,
        units="kg m-2 / 8-day",
        provider="NASA",
    ),

    # --------------------------------------------------------
    # SSEBop
    # --------------------------------------------------------
    "SSEBOP": ETProduct(
        name="SSEBop",
        product_type="Remote Sensing",
        gee_collection="OpenET/SSEBOP/CONUS/GRIDMET/MONTHLY/v2_0",
        band="et",
        scale=1000,
        temporal_resolution="monthly",
        scale_factor=1.0,
        units="mm",
        provider="OpenET",
    ),

    # --------------------------------------------------------
    # ERA5-Land
    # --------------------------------------------------------
    "ERA5-LAND": ETProduct(
        name="ERA5-Land",
        product_type="Reanalysis",
        gee_collection="ECMWF/ERA5_LAND/DAILY_AGGR",
        band="total_evaporation_sum",
        scale=11132,
        temporal_resolution="daily",
        scale_factor=1.0,
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

    try:
        return ET_PRODUCTS[name.upper()]

    except KeyError as exc:

        raise ValueError(
            f"Unknown ET product: {name}"
        ) from exc


# ============================================================
# Helper Functions
# ============================================================

def list_products() -> list[str]:
    """
    Return the names of all registered ET products.

    Returns
    -------
    list[str]
    """

    return sorted(ET_PRODUCTS.keys())