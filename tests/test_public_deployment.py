"""Guards for the source-free Streamlit deployment branch."""

from src import config
from src.data_loaders import load_dashboard_data


def test_runtime_assets_are_committed_and_not_raw_sources() -> None:
    runtime_assets = [
        config.COUNTY_GEOJSON,
        config.COUNTY_CSV,
        config.COUNTY_LOOKUP_CSV,
        config.LARGE_LOAD_CSV,
        config.PROVIDERS_CSV,
        config.PROFILES_CSV,
        config.FORECASTS_CSV,
        config.FORECASTS_2026_CSV,
        config.AVAILABILITY_CSV,
        config.SOURCES_CSV,
        config.QUALITY_EVENTS_CSV,
        config.SANTEE_DEMAND_CSV,
        config.SANTEE_DEMAND_2026_CSV,
        config.SANTEE_HISTORICAL_CSV,
    ]
    assert all(path.is_file() for path in runtime_assets)
    assert all("data/raw" not in path.as_posix() for path in runtime_assets)
    assert all(path.suffix in {".csv", ".geojson"} for path in runtime_assets)


def test_dashboard_loads_without_private_archive() -> None:
    data = load_dashboard_data()
    assert len(data.counties) == 46
    assert not data.forecasts.empty
    assert not data.santee_demand.empty
