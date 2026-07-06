"""
OpenETBench
-----------

Google Earth Engine utilities.

Responsibilities
----------------
- Initialize Google Earth Engine
- Verify Earth Engine connection

Author: Adarsh Jha
"""

import ee
from utils.config import GEE_PROJECT


# ============================================================
# Initialize Earth Engine
# ============================================================

def initialize() -> None:
    """
    Initialize the Google Earth Engine API.

    Raises
    ------
    RuntimeError
        If Earth Engine has not been authenticated.

    Returns
    -------
    None
    """

    try:
        ee.Initialize(project=GEE_PROJECT)
        print("✓ Earth Engine initialized successfully.")

    except Exception as exc:
        raise RuntimeError(
            "\n"
            "Earth Engine is not authenticated.\n\n"
            "Run the following command once in your terminal:\n\n"
            "    earthengine authenticate\n\n"
            "or\n\n"
            "    python -m ee authenticate\n"
        ) from exc


# ============================================================
# Check Earth Engine Connection
# ============================================================

def check_connection() -> bool:
    """
    Verify that Earth Engine is working correctly.

    Returns
    -------
    bool
        True if the connection is successful.

    Raises
    ------
    RuntimeError
        If the connection test fails.
    """

    try:
        value = ee.Number(1).getInfo()

        if value != 1:
            raise RuntimeError(
                "Unexpected response from Earth Engine."
            )

        print("✓ Earth Engine connection verified.")

        return True

    except Exception as exc:
        raise RuntimeError(
            "Failed to communicate with Earth Engine."
        ) from exc