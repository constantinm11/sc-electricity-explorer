"""Presentation-only labels and unit conversion helpers.

Stored data remains unchanged. These functions are the single display layer for
technical identifiers, units, and table headings used by the dashboard.
"""

from __future__ import annotations

import re
from typing import Iterable

import pandas as pd

from src.config import MISSING_LABEL


DISPLAY_LABELS = {
    # Metrics
    "annual_energy": "Annual energy",
    "annual_energy_gwh": "Annual energy",
    "annual_energy_and_peaks": "Annual energy and peak demand",
    "annual_peak_cp_mw": "Annual maximum coincident peak demand",
    "winter_peak": "Winter peak demand",
    "winter_peak_mw": "Winter peak demand",
    "summer_peak": "Summer peak demand",
    "peak_demand": "Peak demand",
    "peak_and_energy": "Peak demand and annual energy",
    "winter_peak_and_annual_energy": "Winter peak and annual energy",
    "winter_peak_change_vs_2025_forecast": "Winter peak change from the 2025 forecast",
    "customer_accounts": "Customer accounts",
    "retail_sales": "Retail electricity sales",
    "large_load_full_load_peak": "Large-load full-load peak",
    "large_load_project_count": "Large-load project count",
    "absolute_class_forecast": "Absolute customer-class forecast",
    "class_demand": "Customer-class demand",
    "class_demand_forecast": "Customer-class demand forecast",
    "current_2025_class_forecast": "Current 2025 customer-class forecast",
    "detailed_demand_forecast": "Detailed demand forecast",
    "separate_forecast": "Separate forecast",
    # Scenarios
    "base": "Base forecast",
    "reference": "Reference forecast",
    "actual": "Reported historical",
    "including_pll": "Including potential large load",
    "excluding_pll": "Excluding potential large load",
    "pll_only": "Potential large load only",
    "high": "High forecast",
    "high_case": "High forecast",
    "low": "Low forecast",
    "low_case": "Low forecast",
    "forecast_bridge": "Change from prior forecast",
    "advanced_development_projects": "Advanced development projects",
    # Categories
    "total_system": "Total system",
    "combined_total": "Combined total",
    "combined_retail": "Combined retail",
    "direct_residential_commercial_combined": "Residential and commercial, combined",
    "direct_industrial": "Direct-served industrial",
    "potential_large_load": "Potential large load",
    "municipal_off_system": "Municipal and off-system",
    "transformer_losses_other": "Transformer losses and other",
    "central": "Central wholesale load",
    "residential_commercial": "Residential and commercial",
    "residential_commercial_industrial": "Residential, commercial, and industrial",
    "all_categories": "All categories",
    "advanced_projects_total": "Advanced projects total",
    "executed_energy_service_agreements": "Executed energy-service agreements",
    "late_stage_projects": "Late-stage projects",
    "letter_agreements": "Letter agreements",
    "demand_side_management": "Demand-side management",
    "electric_vehicles": "Electric vehicles",
    "large_commercial": "Large commercial",
    "small_commercial": "Small commercial",
    # Relationships and coverage
    "distribution_equipment_presence": "Distribution presence",
    "documented_municipal_wholesale_supplier": "Documented municipal wholesale supplier",
    "county_presence_only": "County presence only",
    "supplier_relationship_not_retail_boundary": "Supplier relationship; not a retail boundary",
    # Providers and planning systems
    "central_electric": "Central Electric Power Cooperative",
    "duke_dec_dep_combined": "Duke Energy Carolinas and Duke Energy Progress",
    "duke_energy_carolinas": "Duke Energy Carolinas",
    "duke_energy_progress": "Duke Energy Progress",
    "dominion_sc": "Dominion Energy South Carolina",
    "santee_cooper": "Santee Cooper",
    "lockhart_power": "Lockhart Power",
    "pmpa": "Piedmont Municipal Power Agency",
    "carolina_power_partners": "Carolina Power Partners",
    "municipal_utilities": "Municipal utilities",
    # Statuses
    "reported": "Reported by source",
    "reported_change": "Reported change from prior forecast",
    "provisional": "Provisional",
    "quarantined": "Quarantined",
    "active_warning": "Active warning",
    "pending_source_confirmation": "Pending source confirmation",
    "confirmed_release_rule": "Confirmed release rule",
    "regeneration_required": "Regeneration required",
    "documented": "Documented",
    "geography_scope_warning": "Geography scope warning",
    "provisional_processed_category_swap": "Provisional processed-data category swap",
    "source_quarantine": "Source quarantine",
}

ACRONYMS = {"eia": "EIA", "fips": "FIPS", "irp": "IRP", "mw": "MW", "mwh": "MWh", "gwh": "GWh", "pll": "PLL", "sc": "SC"}


def humanize(value: object) -> str:
    """Return a stable plain-language label for a stored identifier."""
    if value is None or pd.isna(value) or not str(value).strip():
        return MISSING_LABEL
    text = str(value).strip()
    if text in DISPLAY_LABELS:
        return DISPLAY_LABELS[text]
    words = re.split(r"[_|]+", text)
    return " ".join(ACRONYMS.get(word.lower(), word.capitalize()) for word in words)


def option_map(values: Iterable[object]) -> dict[str, object]:
    """Map human-readable control labels back to stored values."""
    result: dict[str, object] = {}
    for value in values:
        label = humanize(value)
        if label in result and result[label] != value:
            label = f"{label} ({value})"
        result[label] = value
    return result


def display_value(value: float, unit: str, metric: str = "") -> tuple[float, str]:
    """Convert units for display only; source values are never mutated."""
    numeric = float(value)
    if unit == "MWh":
        return numeric / 1_000.0, "GWh"
    return numeric, unit


def format_value(value: float, unit: str, metric: str = "") -> str:
    if pd.isna(value):
        return MISSING_LABEL
    numeric, shown_unit = display_value(value, unit, metric)
    decimals = 0 if shown_unit in {"MW", "accounts", "projects"} else 1
    suffix = {"accounts": "accounts", "projects": "projects"}.get(shown_unit, shown_unit)
    return f"{numeric:,.{decimals}f} {suffix}"


def axis_label(metric: str, unit: str) -> str:
    _, shown_unit = display_value(0, unit, metric)
    if shown_unit == "MW":
        return "Peak power (MW)"
    if shown_unit == "GWh":
        return "Annual energy (GWh)"
    if shown_unit == "accounts":
        return "Customer accounts"
    if shown_unit == "projects":
        return "Projects"
    return shown_unit


def humanize_table(frame: pd.DataFrame, identifier_columns: Iterable[str]) -> pd.DataFrame:
    """Return a presentation copy with identifiers and headings humanized."""
    result = frame.copy()
    for column in identifier_columns:
        if column in result:
            result[column] = result[column].map(humanize)
    result = result.rename(columns={column: humanize(column) for column in result.columns})
    return result
