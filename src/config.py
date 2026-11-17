"""Shared paths, labels, and visual constants for the dashboard."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
REFERENCE_DIR = DATA_DIR / "reference"
OUTPUT_DIR = ROOT / "outputs"

COUNTY_GEOJSON = DATA_DIR / "sc_counties.geojson"
COUNTY_CSV = DATA_DIR / "sc_counties.csv"
COUNTY_LOOKUP_CSV = REFERENCE_DIR / "county_provider_lookup.csv"
LARGE_LOAD_CSV = REFERENCE_DIR / "large_load_projects.csv"
PROVIDERS_CSV = PROCESSED_DIR / "providers.csv"
PROFILES_CSV = PROCESSED_DIR / "provider_profiles.csv"
FORECASTS_CSV = PROCESSED_DIR / "provider_forecasts.csv"
FORECASTS_2026_CSV = PROCESSED_DIR / "provider_forecasts_2026.csv"
AVAILABILITY_CSV = PROCESSED_DIR / "data_availability.csv"
SOURCES_CSV = PROCESSED_DIR / "source_metadata.csv"
QUALITY_EVENTS_CSV = PROCESSED_DIR / "data_quality_events.csv"
SANTEE_DEMAND_CSV = OUTPUT_DIR / "santee_demand_combined_long.csv"
SANTEE_DEMAND_2026_CSV = PROCESSED_DIR / "santee_demand_2026.csv"
SANTEE_HISTORICAL_CSV = PROCESSED_DIR / "santee_historical_categories.csv"

MISSING_LABEL = "Not publicly disclosed"
GARNET = "#73000A"
GARNET_DARK = "#4F0007"
INK = "#1F2933"
MUTED_INK = "#52606D"
SAND = "#F7F5F2"
WHITE = "#FFFFFF"
TEAL = "#167D8D"
GOLD = "#DFA928"
GRID = "#E7E2DC"

SECTIONS = (
    "Statewide Provider Explorer",
    "Santee Cooper Deep Dive",
    "Methodology and Data Quality",
)
