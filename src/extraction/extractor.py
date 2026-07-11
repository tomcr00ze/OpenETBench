"""
OpenETBench
-----------

Generic Google Earth Engine extractor.

Author: Adarsh Jha
"""

import ee
import pandas as pd

from extraction.sites import Site
from extraction.products import ETProduct

# ============================================================
# Region
# ============================================================

def _create_region(
    site: Site,
) -> ee.Geometry:
    """
    Create a circular extraction region around a flux tower.

    Parameters
    ----------
    site : Site

    Returns
    -------
    ee.Geometry
    """

    return ee.Geometry.Point(
        [
            site.longitude,
            site.latitude,
        ]
    ).buffer(site.buffer_m)

# ============================================================
# Image Collection
# ============================================================

def _load_collection(
    product: ETProduct,
    start_date: str,
    end_date: str,
) -> ee.ImageCollection:
    """
    Load an Earth Engine ImageCollection.

    Parameters
    ----------
    product : ETProduct

    start_date : str

    end_date : str

    Returns
    -------
    ee.ImageCollection
    """

    return (
        ee.ImageCollection(
            product.gee_collection
        )
        .filterDate(
            start_date,
            end_date,
        )
    )

# ============================================================
# Image Reduction
# ============================================================

def _reduce_image(
    image: ee.Image,
    region: ee.Geometry,
    product: ETProduct,
) -> ee.Feature:
    """
    Reduce one image over one site.

    Returns
    -------
    ee.Feature
    """

    value = image.select(
        product.band
    ).reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=product.spatial_resolution,
        maxPixels=1e9,
    )

    return ee.Feature(
        None,
        {
            "date": image.date().format(
                "YYYY-MM-dd"
            ),
            "ET": value.get(
                product.band
            ),
        },
    )

# ============================================================
# Collection Reduction
# ============================================================

def _extract_collection(
    collection: ee.ImageCollection,
    region: ee.Geometry,
    product: ETProduct,
) -> ee.FeatureCollection:
    """
    Reduce every image in a collection.

    Returns
    -------
    ee.FeatureCollection
    """

    return ee.FeatureCollection(
        collection.map(
            lambda image:
                _reduce_image(
                    image,
                    region,
                    product,
                )
        )
    )

# ============================================================
# DataFrame Conversion
# ============================================================

def _to_dataframe(
    features: ee.FeatureCollection,
    product: ETProduct,
) -> pd.DataFrame:
    """
    Convert FeatureCollection to pandas.

    Returns
    -------
    pandas.DataFrame
    """

    data = features.getInfo()

    rows = []

    for feature in data["features"]:

        properties = feature["properties"]

        rows.append(
            {
                "Date": properties["date"],
                "ET": (
                    float(properties["ET"]) * product.scale_factor
                    if properties["ET"] is not None
                    else None
                ),
            }
        )

    df = pd.DataFrame(rows)

    df = df.dropna(
        subset=["ET"]
    )

    df["Date"] = pd.to_datetime(
        df["Date"]
    )

    df = df.sort_values(
        "Date"
    ).reset_index(
        drop=True
    )

    df["DoY"] = (
        df["Date"]
        .dt.dayofyear
        .astype("int64")
    )

    return df[
        [
            "Date",
            "DoY",
            "ET",
        ]
    ]

# ============================================================
# Public API
# ============================================================

def extract_timeseries(
    site: Site,
    product: ETProduct,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """
    Extract an ET time series from Google Earth Engine.

    Parameters
    ----------
    site : Site

    product : ETProduct

    start_date : str

    end_date : str

    Returns
    -------
    pandas.DataFrame
    """

    region = _create_region(site)

    collection = _load_collection(
        product,
        start_date,
        end_date,
    )

    features = _extract_collection(
        collection,
        region,
        product,
    )

    return _to_dataframe(
        features,
        product,
    )