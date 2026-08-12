"""Project-wide configuration."""

from pathlib import Path


# OpenETBench project root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Google Earth Engine cloud project.
GEE_PROJECT = "openetbench"

# Canonical result root used by the benchmarking pipeline.
RESULTS_DIR = PROJECT_ROOT / "results"
