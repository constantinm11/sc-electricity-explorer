"""Presentation-only label, unit, theme, and map tests."""

from pathlib import Path
import tomllib

import pandas as pd

from src.chart_builder import provider_forecast_chart
from src.data_loaders import load_dashboard_data
from src.display import display_value, format_value, humanize
from src.map_builder import build_statewide_relationship_map


ROOT = Path(__file__).resolve().parents[1]


def test_required_human_readable_labels() -> None:
    expected = {
        "annual_energy": "Annual energy",
        "winter_peak": "Winter peak demand",
        "customer_accounts": "Customer accounts",
        "base": "Base forecast",
        "total_system": "Total system",
        "direct_residential_commercial_combined": "Residential and commercial, combined",
        "potential_large_load": "Potential large load",
        "central_electric": "Central Electric Power Cooperative",
        "county_presence_only": "County presence only",
    }
    assert {key: humanize(key) for key in expected} == expected


def test_mwh_is_converted_to_gwh_for_display_only() -> None:
    value, unit = display_value(20_955_156, "MWh", "annual_energy")
    assert value == 20_955.156
    assert unit == "GWh"
    assert format_value(20_955_156, "MWh", "annual_energy") == "20,955.2 GWh"


def test_provider_chart_uses_readable_units_and_light_template() -> None:
    data = load_dashboard_data()
    rows = data.forecasts.loc[data.forecasts["provider_id"].eq("central_electric")]
    figure = provider_forecast_chart(rows, "annual_energy", "Central 2023 IRP", "base")
    assert figure is not None
    assert figure.layout.yaxis.title.text == "Annual energy (GWh)"
    assert figure.layout.paper_bgcolor == "#FFFFFF"
    assert max(float(value) for trace in figure.data for value in trace.y) < 50_000


def test_statewide_map_has_selected_county_outline() -> None:
    data = load_dashboard_data()
    figure = build_statewide_relationship_map(
        data.counties, data.county_lookup, "Richland", data.geojson
    )
    assert len(figure.data) == 2
    assert list(figure.data[1].locations) == ["45079"]
    assert figure.data[1].marker.line.width == 3.2
    assert "demand" not in figure.data[0].hovertemplate.lower()


def test_streamlit_theme_is_deterministic_light() -> None:
    with (ROOT / ".streamlit" / "config.toml").open("rb") as handle:
        config = tomllib.load(handle)
    assert config["theme"] == {
        "base": "light",
        "primaryColor": "#73000A",
        "backgroundColor": "#F7F5F2",
        "secondaryBackgroundColor": "#FFFFFF",
        "textColor": "#1F2933",
        "font": "sans-serif",
    }
