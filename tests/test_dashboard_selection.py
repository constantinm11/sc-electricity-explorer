"""Tests for dashboard filtering and interpretation guardrails."""

import pandas as pd

from src.data_loaders import load_dashboard_data
from src.selection import (
    county_has_modeled_demand,
    display_or_missing,
    forecasts_for_provider,
    relationships_for_county,
)


def test_every_county_has_dashboard_relationship_selection() -> None:
    data = load_dashboard_data()
    for county in data.counties["county_name"]:
        assert not relationships_for_county(data.county_lookup, county).empty


def test_member_cooperative_resolves_to_central_forecast() -> None:
    data = load_dashboard_data()
    provider_id, rows = forecasts_for_provider(
        data.forecasts, data.providers, "aiken_electric_coop_inc"
    )
    assert provider_id == "central_electric"
    assert not rows.empty
    assert set(rows["geography_scope"]) == {"Central cooperative wholesale system"}


def test_county_lookup_has_no_demand_allocation() -> None:
    data = load_dashboard_data()
    assert county_has_modeled_demand(data.county_lookup) is False


def test_missing_display_is_not_zero() -> None:
    assert display_or_missing(None) == "Not publicly disclosed"
    assert display_or_missing(float("nan")) == "Not publicly disclosed"
    assert display_or_missing(0) == "0"


def test_dashboard_module_imports() -> None:
    import app

    assert callable(app.main)
