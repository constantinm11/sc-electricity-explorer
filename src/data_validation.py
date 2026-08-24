"""Validation helpers shared by tests and release checks."""

from __future__ import annotations

import pandas as pd


REQUIRED_PROVENANCE_FIELDS = {
    "source_document",
    "source_table",
    "source_page",
    "forecast_vintage",
    "geography_scope",
    "metric",
    "category",
    "scenario",
    "unit",
    "reported_or_modeled",
}


def assert_complete_sc_counties(counties: pd.DataFrame) -> None:
    assert len(counties) == 46
    assert counties["fips"].astype(str).str.zfill(5).nunique() == 46
    assert set(counties["state"]) == {"SC"}


def assert_provenance_columns(frame: pd.DataFrame) -> None:
    missing = REQUIRED_PROVENANCE_FIELDS - set(frame.columns)
    assert not missing, f"Missing provenance fields: {sorted(missing)}"
    assert frame[list(REQUIRED_PROVENANCE_FIELDS)].notna().all().all()


def assert_no_county_demand_allocation(frame: pd.DataFrame) -> None:
    forbidden = {"county_demand", "measured_county_demand", "allocated_county_demand"}
    values = set(frame.get("geography_scope", pd.Series(dtype=str)).dropna().astype(str).str.lower())
    assert not (values & forbidden)
    assert "county_fips" not in frame.columns or frame["county_fips"].isna().all()
