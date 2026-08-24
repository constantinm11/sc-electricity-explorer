"""Pure selection helpers used by the dashboard and tests."""

from __future__ import annotations

import pandas as pd

from src.config import MISSING_LABEL


def relationships_for_county(lookup: pd.DataFrame, county_name: str) -> pd.DataFrame:
    """Return all sourced, non-exclusive provider relationships for one county."""
    return lookup.loc[lookup["county_name"].eq(county_name)].sort_values(
        ["provider_type", "provider_name", "relationship_type"]
    ).reset_index(drop=True)


def resolve_forecast_provider(providers: pd.DataFrame, provider_id: str) -> str:
    """Resolve a local retail entity to its documented planning/forecast entity."""
    match = providers.loc[providers["provider_id"].eq(provider_id), "forecast_provider_id"]
    if match.empty or not str(match.iloc[0]).strip():
        return provider_id
    return str(match.iloc[0])


def forecasts_for_provider(
    forecasts: pd.DataFrame, providers: pd.DataFrame, provider_id: str
) -> tuple[str, pd.DataFrame]:
    forecast_provider_id = resolve_forecast_provider(providers, provider_id)
    rows = forecasts.loc[forecasts["provider_id"].eq(forecast_provider_id)].copy()
    return forecast_provider_id, rows


def display_or_missing(value: object) -> str:
    if value is None or pd.isna(value) or not str(value).strip():
        return MISSING_LABEL
    return str(value)


def county_has_modeled_demand(lookup: pd.DataFrame) -> bool:
    """Guardrail used by tests and UI: this lookup contains relationships, not demand."""
    forbidden = {"demand", "demand_mw", "demand_mwh", "allocated_demand", "share_of_demand"}
    return bool(forbidden.intersection(set(lookup.columns)))

