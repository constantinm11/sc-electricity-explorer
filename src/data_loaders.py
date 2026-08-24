"""Typed loading of committed dashboard datasets."""

from __future__ import annotations

import json
from dataclasses import dataclass

import pandas as pd

from src import config


@dataclass(frozen=True)
class DashboardData:
    counties: pd.DataFrame
    county_lookup: pd.DataFrame
    providers: pd.DataFrame
    profiles: pd.DataFrame
    forecasts: pd.DataFrame
    availability: pd.DataFrame
    large_loads: pd.DataFrame
    sources: pd.DataFrame
    quality_events: pd.DataFrame
    santee_demand: pd.DataFrame
    santee_historical: pd.DataFrame
    geojson: dict


def _read_csv(path, **kwargs) -> pd.DataFrame:
    return pd.read_csv(path, keep_default_na=False, **kwargs)


def load_dashboard_data() -> DashboardData:
    """Load all generated datasets without transforming their substantive values."""
    counties = _read_csv(config.COUNTY_CSV, dtype={"fips": str})
    lookup = _read_csv(config.COUNTY_LOOKUP_CSV, dtype={"county_fips": str})
    projects = _read_csv(config.LARGE_LOAD_CSV, dtype={"county_fips": str})
    forecasts = _read_csv(config.FORECASTS_CSV)
    santee = _read_csv(config.SANTEE_DEMAND_CSV)
    historical = _read_csv(config.SANTEE_HISTORICAL_CSV)

    for frame in (forecasts, projects, santee, historical):
        if "value" in frame:
            frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
        if "year" in frame:
            frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    projects["announced_mw"] = pd.to_numeric(projects["announced_mw"], errors="coerce")

    with config.COUNTY_GEOJSON.open(encoding="utf-8") as handle:
        geojson = json.load(handle)

    return DashboardData(
        counties=counties,
        county_lookup=lookup,
        providers=_read_csv(config.PROVIDERS_CSV),
        profiles=_read_csv(config.PROFILES_CSV),
        forecasts=forecasts,
        availability=_read_csv(config.AVAILABILITY_CSV),
        large_loads=projects,
        sources=_read_csv(config.SOURCES_CSV),
        quality_events=_read_csv(config.QUALITY_EVENTS_CSV),
        santee_demand=santee,
        santee_historical=historical,
        geojson=geojson,
    )

