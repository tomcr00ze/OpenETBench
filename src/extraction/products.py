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

    spatial_resolution : int
        Native spatial resolution (meters).

    temporal_resolution : str
        Native temporal resolution.

    scale_factor : float
        Multiplicative scale factor applied to the raw band values.

    units : str
        Native units of the ET band.

    provider : str
        Dataset provider.

    coverage : str
        Geographic coverage of the dataset. Examples: CONUS, Global.
    """

    # Basic
    name: str
    collection: str
    band: str

    # Scaling
    scale_factor: float

    # Spatial / Temporal
    spatial_resolution: int
    temporal_resolution: str

    # Metadata
    units: str
    provider: str
    coverage: str
    product_type: str
    
    aggregation: str = "native"
    sampling: str = "mean"


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

        # MODIS stores ET ×10
        scale_factor=0.1,

        spatial_resolution=500,
        temporal_resolution="8-day",

        units="mm/8-day",
        provider="NASA",
        coverage="Global",
        product_type="Remote Sensing",
        
        sampling="mean", 
    ),

    # --------------------------------------------------------
    # SSEBop (OpenET)
    # --------------------------------------------------------
    "SSEBOP": ETProduct(
        name="SSEBop",
        collection="OpenET/SSEBOP/CONUS/GRIDMET/MONTHLY/v2_0",
        band="et",

        scale_factor=1.0,

        spatial_resolution=1000,
        temporal_resolution="Monthly",

        units="mm",
        provider="OpenET",
        coverage="CONUS",
        product_type="Remote Sensing",

        sampling="mean", 
    ),

    # --------------------------------------------------------
    # ERA5-Land
    # --------------------------------------------------------
    "ERA5-LAND": ETProduct(
        name="ERA5-Land",
        collection="ECMWF/ERA5_LAND/DAILY_AGGR",
        band="total_evaporation_sum",

        # meters -> millimeters
        # sign convention:
        # evaporation is negative
        scale_factor=-1000.0,

        spatial_resolution=11132,
        temporal_resolution="Daily",

        units="mm/day",
        provider="ECMWF",
        coverage="Global",
        product_type="Reanalysis",
    ),

    # --------------------------------------------------------
    # GLDAS
    # --------------------------------------------------------

    "GLDAS": ETProduct(
        name="GLDAS",
        collection="NASA/GLDAS/V022/CLSM/G025/DA1D",
        band="Evap_tavg",

        # kg m-2 s-1 -> mm/day
        scale_factor=86400.0,

        spatial_resolution=27830,
        temporal_resolution="Daily",

        units="mm/day",
        provider="NASA",
        coverage="Global",
        product_type="Land Surface Model",
    ),

    # --------------------------------------------------------
    # FLDAS
    # --------------------------------------------------------
    "FLDAS": ETProduct(
        name="FLDAS",
        collection="NASA/FLDAS/NOAH01/C/GL/M/V001",
        band="Evap_tavg",

        # kg m-2 s-1 -> mm/day
        scale_factor=86400.0,
        spatial_resolution=11100,
        temporal_resolution="Monthly",
        units="mm/day",
        provider="NASA",
        coverage="Global",
        product_type="Land Surface Model",
    ),
    # --------------------------------------------------------
    # MERRA2
    # --------------------------------------------------------
    "MERRA2": ETProduct(
        name="MERRA2",
        collection="NASA/GSFC/MERRA/lnd/2",
        band="EVLAND",

        # kg m^-2 hour^-1 → mm/day
        scale_factor=3600.0,
        spatial_resolution=55000,

        # Native temporal resolution
        temporal_resolution="Hourly",
        units="mm/day",
        provider="NASA",
        coverage="Global",
        # MERRA-2 is a reanalysis product
        product_type="Reanalysis",
        aggregation="daily_sum",
        sampling="point",
    ),

    # --------------------------------------------------------
    # PMLV2
    # --------------------------------------------------------
    "PMLV2": ETProduct(
        name="PML-V2",
        collection="projects/pml_evapotranspiration/PML/OUTPUT/PML_V22a",
        band="ET",

        # Stored as scaled integers
        scale_factor=0.01,
        spatial_resolution=500,
        temporal_resolution="8-day",
        units="mm/8-day",

        provider="PML",
        coverage="Global",
        product_type="Remote Sensing",

        aggregation="native",
        sampling="buffer",
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

    key = name.upper()

    try:
        return ET_PRODUCTS[key]

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