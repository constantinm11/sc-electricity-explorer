"""Build auditable Santee Cooper processed data for the dashboard.

Raw mentor workbooks are immutable. The only release correction is the
provisional SANTEE_HIST_001 category swap applied to processed historical data.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "data" / "raw" / "mentor"
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUT_DIR = ROOT / "outputs"

HISTORICAL_FILE = RAW_DIR / "Historical data provided by santee cooper.xlsx"
FORECAST_FILE = RAW_DIR / "Load Forecast Details - no link.xlsx"
QUARANTINED_FORECAST_FILE = RAW_DIR / "forecasts in peak load with_without PPL.xlsx"

CORRECTION_RULE_ID = "SANTEE_HIST_001"
CORRECTION_YEARS = {2018, 2019, 2022}
CORRECTION_STATUS = "provisional_pending_source_confirmation"


def _safe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _provenance(
    *,
    source_file: str,
    source_sheet: str,
    source_table: str,
    vintage: str,
    geography_scope: str = "Santee Cooper utility system",
) -> dict[str, str]:
    return {
        "source_file": source_file,
        "source_sheet": source_sheet,
        "source_table": source_table,
        "source_page": "Not applicable - workbook table",
        "forecast_vintage": vintage,
        "geography_scope": geography_scope,
        "reported_or_modeled": "reported",
    }


def clean_historical_demand() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return corrected monthly data, annual totals, annual categories, and events."""
    wb = load_workbook(HISTORICAL_FILE, data_only=True, read_only=True)
    ws = wb["Historical Load"]
    records: list[dict[str, Any]] = []

    for row in range(4, ws.max_row + 1):
        raw_date = ws.cell(row, 2).value
        if raw_date is None:
            continue
        date = pd.to_datetime(raw_date)
        year = int(date.year)
        correction_applied = year in CORRECTION_YEARS

        energy_central_raw = _safe_float(ws.cell(row, 6).value)
        energy_losses_raw = _safe_float(ws.cell(row, 9).value)
        cp_central_raw = _safe_float(ws.cell(row, 18).value)
        cp_losses_raw = _safe_float(ws.cell(row, 21).value)

        energy_central = energy_losses_raw if correction_applied else energy_central_raw
        energy_losses = energy_central_raw if correction_applied else energy_losses_raw
        cp_central = cp_losses_raw if correction_applied else cp_central_raw
        cp_losses = cp_central_raw if correction_applied else cp_losses_raw

        records.append(
            {
                "date": date,
                "year": year,
                "month": int(date.month),
                "energy_res_com_mwh": _safe_float(ws.cell(row, 5).value),
                "energy_central_mwh_raw": energy_central_raw,
                "energy_central_mwh": energy_central,
                "energy_industrial_mwh": _safe_float(ws.cell(row, 7).value),
                "energy_municipal_mwh": _safe_float(ws.cell(row, 8).value),
                "energy_transformer_losses_other_mwh_raw": energy_losses_raw,
                "energy_transformer_losses_other_mwh": energy_losses,
                "energy_total_territorial_load_mwh": _safe_float(ws.cell(row, 10).value),
                "ncp_central_mw": _safe_float(ws.cell(row, 13).value),
                "cp_res_com_mw": _safe_float(ws.cell(row, 17).value),
                "cp_central_mw_raw": cp_central_raw,
                "cp_central_mw": cp_central,
                "cp_industrial_mw": _safe_float(ws.cell(row, 19).value),
                "cp_municipal_mw": _safe_float(ws.cell(row, 20).value),
                "cp_transformer_losses_other_mw_raw": cp_losses_raw,
                "cp_transformer_losses_other_mw": cp_losses,
                "cp_total_territorial_load_mw": _safe_float(ws.cell(row, 22).value),
                "correction_applied": correction_applied,
                "correction_rule_id": CORRECTION_RULE_ID if correction_applied else "",
                "correction_status": CORRECTION_STATUS if correction_applied else "not_applicable",
                "source_file": HISTORICAL_FILE.name,
                "source_sheet": "Historical Load",
                "source_table": "Monthly historical load",
                "source_row": row,
                "reported_or_modeled": "reported_with_provisional_processed_correction"
                if correction_applied
                else "reported",
            }
        )

    wb.close()
    monthly = pd.DataFrame(records).sort_values("date").reset_index(drop=True)

    annual_wide = (
        monthly.groupby("year", as_index=False)
        .agg(
            annual_energy_mwh=("energy_total_territorial_load_mwh", "sum"),
            annual_energy_gwh=("energy_total_territorial_load_mwh", lambda x: x.sum() / 1000),
            annual_max_cp_mw=("cp_total_territorial_load_mw", "max"),
            energy_res_com_mwh=("energy_res_com_mwh", "sum"),
            energy_central_mwh=("energy_central_mwh", "sum"),
            energy_industrial_mwh=("energy_industrial_mwh", "sum"),
            energy_municipal_mwh=("energy_municipal_mwh", "sum"),
            energy_transformer_losses_other_mwh=("energy_transformer_losses_other_mwh", "sum"),
        )
        .sort_values("year")
    )

    annual_long_records: list[dict[str, Any]] = []
    category_records: list[dict[str, Any]] = []
    category_columns = {
        "direct_residential_commercial_combined": "energy_res_com_mwh",
        "central": "energy_central_mwh",
        "direct_industrial": "energy_industrial_mwh",
        "municipal": "energy_municipal_mwh",
        "transformer_losses_other": "energy_transformer_losses_other_mwh",
    }
    provenance = _provenance(
        source_file=HISTORICAL_FILE.name,
        source_sheet="Historical Load",
        source_table="Monthly historical load",
        vintage="Historical 2016-2025",
    )

    for row in annual_wide.itertuples(index=False):
        correction_status = CORRECTION_STATUS if row.year in CORRECTION_YEARS else "not_applicable"
        for metric_key, metric_label, value, unit in (
            ("annual_energy_gwh", "Annual total territorial energy", row.annual_energy_gwh, "GWh"),
            ("annual_peak_cp_mw", "Annual max coincident peak demand", row.annual_max_cp_mw, "MW"),
        ):
            annual_long_records.append(
                {
                    "year": int(row.year),
                    "dataset": "historical",
                    "metric_key": metric_key,
                    "metric_label": metric_label,
                    "category": "total_system",
                    "scenario_key": "actual",
                    "scenario_label": "Actual historical",
                    "value": value,
                    "unit": unit,
                    "geography_type": "utility_system",
                    "geography_name": "Santee Cooper",
                    "correction_status": correction_status,
                    **provenance,
                    "notes": "Santee Cooper system total; not county-specific demand.",
                }
            )

        for category, column in category_columns.items():
            category_records.append(
                {
                    "provider_id": "santee_cooper",
                    "year": int(row.year),
                    "metric": "annual_energy",
                    "category": category,
                    "scenario": "actual",
                    "value": getattr(row, column) / 1000,
                    "unit": "GWh",
                    "geography_scope": "Santee Cooper utility system",
                    "forecast_vintage": "Historical 2016-2025",
                    "reported_or_modeled": "reported_with_provisional_processed_correction"
                    if row.year in CORRECTION_YEARS and category in {"central", "transformer_losses_other"}
                    else "reported",
                    "correction_status": correction_status,
                    "source_document": HISTORICAL_FILE.name,
                    "source_sheet": "Historical Load",
                    "source_table": "Monthly historical load",
                    "source_page": "Not applicable - workbook table",
                    "notes": "Residential and commercial are combined in the source."
                    if category == "direct_residential_commercial_combined"
                    else "",
                }
            )

    events = pd.DataFrame(
        [
            {
                "event_id": f"{CORRECTION_RULE_ID}_{year}",
                "provider_id": "santee_cooper",
                "year": year,
                "event_type": "provisional_processed_category_swap",
                "correction_rule_id": CORRECTION_RULE_ID,
                "affected_fields": "energy_central_mwh|energy_transformer_losses_other_mwh|cp_central_mw|cp_transformer_losses_other_mw",
                "untouched_fields": "ncp_central_mw|system_totals",
                "status": "provisional",
                "confirmation_status": "pending_source_confirmation",
                "reason": "Central and Transformer Losses/Other values are reversed relative to labels and surrounding-year patterns.",
                "source_document": HISTORICAL_FILE.name,
                "source_sheet": "Historical Load",
                "notes": "Raw workbook unchanged; swap exists only in processed data.",
            }
            for year in sorted(CORRECTION_YEARS)
        ]
    )
    return monthly, pd.DataFrame(annual_long_records), pd.DataFrame(category_records), events


def clean_forecast_demand() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return the primary Santee forecast as wide, scenario, and category tables."""
    wb = load_workbook(FORECAST_FILE, data_only=True, read_only=True)
    ws = wb["Energy and Demand"]
    wide_records: list[dict[str, Any]] = []

    for row in range(4, ws.max_row + 1):
        raw_year = ws.cell(row, 1).value
        if raw_year is None:
            continue
        year = int(raw_year)
        peak_pll = _safe_float(ws.cell(row, 6).value) or 0.0
        peak_total = _safe_float(ws.cell(row, 7).value)
        energy_pll = _safe_float(ws.cell(row, 16).value) or 0.0
        energy_total = _safe_float(ws.cell(row, 17).value)
        if peak_total is None or energy_total is None:
            continue

        wide_records.append(
            {
                "year": year,
                "winter_peak_res_com_mw": _safe_float(ws.cell(row, 2).value),
                "winter_peak_industrial_mw": _safe_float(ws.cell(row, 3).value),
                "winter_peak_municipal_off_system_mw": _safe_float(ws.cell(row, 4).value),
                "winter_peak_central_mw": _safe_float(ws.cell(row, 5).value),
                "winter_peak_pll_mw": peak_pll,
                "winter_peak_total_mw": peak_total,
                "winter_peak_excluding_pll_mw": peak_total - peak_pll,
                "winter_peak_high_case_mw": _safe_float(ws.cell(row, 8).value),
                "winter_peak_low_case_mw": _safe_float(ws.cell(row, 9).value),
                "annual_energy_res_com_gwh": _safe_float(ws.cell(row, 12).value),
                "annual_energy_industrial_gwh": _safe_float(ws.cell(row, 13).value),
                "annual_energy_municipal_off_system_gwh": _safe_float(ws.cell(row, 14).value),
                "annual_energy_central_gwh": _safe_float(ws.cell(row, 15).value),
                "annual_energy_pll_gwh": energy_pll,
                "annual_energy_total_gwh": energy_total,
                "annual_energy_excluding_pll_gwh": energy_total - energy_pll,
                "annual_energy_high_case_gwh": _safe_float(ws.cell(row, 18).value),
                "annual_energy_low_case_gwh": _safe_float(ws.cell(row, 19).value),
                "source_file": FORECAST_FILE.name,
                "source_sheet": "Energy and Demand",
                "source_table": "Tables 6-7: Forecasted system peak demand and energy sales",
                "source_row": row,
            }
        )

    wb.close()
    wide = pd.DataFrame(wide_records).sort_values("year").reset_index(drop=True)
    scenario_defs = [
        ("including_pll", "Including PLL / full forecast", "total"),
        ("excluding_pll", "Excluding PLL", "excluding_pll"),
        ("pll_only", "Potential Large Load only", "pll"),
        ("high_case", "High case", "high_case"),
        ("low_case", "Low case", "low_case"),
    ]
    scenario_records: list[dict[str, Any]] = []
    category_records: list[dict[str, Any]] = []
    provenance = _provenance(
        source_file=FORECAST_FILE.name,
        source_sheet="Energy and Demand",
        source_table="Tables 6-7: Forecasted system peak demand and energy sales",
        vintage="Santee Cooper 2025 load forecast",
    )

    category_map = {
        "direct_residential_commercial_combined": ("res_com", "Residential and commercial are combined in the source."),
        "direct_industrial": ("industrial", ""),
        "municipal_off_system": ("municipal_off_system", "Wholesale/off-system relationship; not an end-use class."),
        "central": ("central", "Wholesale cooperative relationship; avoid double counting with Central totals."),
        "potential_large_load": ("pll", "Explicit Santee Potential Large Load forecast category."),
    }

    for row in wide.itertuples(index=False):
        year = int(row.year)
        for scenario_key, scenario_label, suffix in scenario_defs:
            for metric_key, metric_label, unit, column in (
                ("winter_peak_mw", "Forecasted winter peak demand", "MW", f"winter_peak_{suffix}_mw"),
                ("annual_energy_gwh", "Forecasted annual energy sales", "GWh", f"annual_energy_{suffix}_gwh"),
            ):
                value = getattr(row, column)
                if pd.isna(value):
                    continue
                scenario_records.append(
                    {
                        "year": year,
                        "dataset": "forecast",
                        "metric_key": metric_key,
                        "metric_label": metric_label,
                        "category": "total_system" if scenario_key != "pll_only" else "potential_large_load",
                        "scenario_key": scenario_key,
                        "scenario_label": scenario_label,
                        "value": value,
                        "unit": unit,
                        "geography_type": "utility_system",
                        "geography_name": "Santee Cooper",
                        "correction_status": "not_applicable",
                        **provenance,
                        "notes": "Santee Cooper system forecast; not county-specific demand.",
                    }
                )

        for category, (suffix, note) in category_map.items():
            for metric, unit, column in (
                ("winter_peak", "MW", f"winter_peak_{suffix}_mw"),
                ("annual_energy", "GWh", f"annual_energy_{suffix}_gwh"),
            ):
                category_records.append(
                    {
                        "provider_id": "santee_cooper",
                        "year": year,
                        "metric": metric,
                        "category": category,
                        "scenario": "base",
                        "value": getattr(row, column),
                        "unit": unit,
                        "geography_scope": "Santee Cooper utility system",
                        "forecast_vintage": "Santee Cooper 2025 load forecast",
                        "reported_or_modeled": "reported",
                        "correction_status": "not_applicable",
                        "source_document": FORECAST_FILE.name,
                        "source_sheet": "Energy and Demand",
                        "source_table": "Tables 6-7: Forecasted system peak demand and energy sales",
                        "source_page": "Not applicable - workbook table",
                        "notes": note,
                    }
                )

    return wide, pd.DataFrame(scenario_records), pd.DataFrame(category_records)


def write_service_counties() -> pd.DataFrame:
    """Legacy Santee geography retained for the deep-dive view."""
    source = "https://www.santeecooper.com/Residential/Start-Move-Stop-Service/Start-Service/"
    return pd.DataFrame(
        [
            {
                "county_name": county,
                "fips": fips,
                "utility": "Santee Cooper",
                "service_type": "Direct retail presence",
                "service_note": "Santee Cooper serves portions of this county; county highlighting does not imply full-county coverage.",
                "source_url": source,
            }
            for county, fips in (("Berkeley", "45015"), ("Georgetown", "45043"), ("Horry", "45051"))
        ]
    )


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    monthly, historical_totals, historical_categories, correction_events = clean_historical_demand()
    forecast_wide, forecast_scenarios, forecast_categories = clean_forecast_demand()
    service_counties = write_service_counties()

    monthly.to_csv(OUTPUT_DIR / "santee_historical_monthly_clean.csv", index=False)
    historical_totals.to_csv(OUTPUT_DIR / "santee_historical_demand_clean.csv", index=False)
    forecast_wide.to_csv(OUTPUT_DIR / "santee_forecast_demand_wide.csv", index=False)
    forecast_scenarios.to_csv(OUTPUT_DIR / "santee_forecast_demand_clean.csv", index=False)
    service_counties.to_csv(OUTPUT_DIR / "santee_service_counties.csv", index=False)
    correction_events.to_csv(OUTPUT_DIR / "data_quality_notes.csv", index=False)
    combined = pd.concat([historical_totals, forecast_scenarios], ignore_index=True)
    combined.to_csv(OUTPUT_DIR / "santee_demand_combined_long.csv", index=False)

    monthly.to_csv(PROCESSED_DIR / "santee_historical_monthly.csv", index=False)
    historical_categories.to_csv(PROCESSED_DIR / "santee_historical_categories.csv", index=False)
    forecast_wide.to_csv(PROCESSED_DIR / "santee_forecast_wide.csv", index=False)
    forecast_scenarios.to_csv(PROCESSED_DIR / "santee_forecast_scenarios.csv", index=False)
    forecast_categories.to_csv(PROCESSED_DIR / "santee_forecast_categories.csv", index=False)
    correction_events.to_csv(PROCESSED_DIR / "santee_correction_events.csv", index=False)

    print("Primary historical source:", HISTORICAL_FILE.name)
    print("Primary forecast source:", FORECAST_FILE.name)
    print("Quarantined forecast source:", QUARANTINED_FORECAST_FILE.name)
    print("Historical monthly rows:", len(monthly))
    print("Historical total rows:", len(historical_totals))
    print("Forecast scenario rows:", len(forecast_scenarios))
    print("Provisional correction events:", len(correction_events))


if __name__ == "__main__":
    main()
