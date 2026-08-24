"""Build normalized statewide provider and relationship data.

The EIA input is the official 2024 final Service_Territory_2024.xlsx file from
https://www.eia.gov/electricity/data/eia861/. It is supplied as a command-line
argument so the repository does not silently download or mutate public data.
"""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
REFERENCE_DIR = ROOT / "data" / "reference"

EIA_SOURCE_URL = "https://www.eia.gov/electricity/data/eia861/"
EIA_ZIP_URL = "https://www.eia.gov/electricity/data/eia861/zip/f8612024.zip"
REPORT_NAME = "Not publicly distributed"

PROVIDER_ID_OVERRIDES = {
    "South Carolina Public Service Authority": "santee_cooper",
    "Dominion Energy South Carolina, Inc": "dominion_sc",
    "Duke Energy Carolinas, LLC": "duke_energy_carolinas",
    "Duke Energy Progress - (NC)": "duke_energy_progress",
    "Lockhart Power Co": "lockhart_power",
    "MPD Electric Cooperative": "mpd_electric_cooperative",
}


def slugify(value: str) -> str:
    value = value.lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", "_", value).strip("_")


def provider_type(name: str) -> str:
    lower = name.lower()
    if "coop" in lower or "member corp" in lower:
        return "Electric cooperative"
    if name == "South Carolina Public Service Authority":
        return "State-owned utility"
    if name in {
        "Dominion Energy South Carolina, Inc",
        "Duke Energy Carolinas, LLC",
        "Duke Energy Progress - (NC)",
        "Lockhart Power Co",
    }:
        return "Investor-owned utility"
    return "Municipal utility"


def build_eia_relationships(eia_path: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    eia = pd.read_excel(eia_path, sheet_name="Counties_States")
    eia = eia[eia["State"] == "SC"].copy()
    counties = pd.read_csv(ROOT / "data" / "sc_counties.csv", dtype={"fips": str})
    fips_by_county = counties.set_index("county_name")["fips"].astype(str).str.zfill(5).to_dict()
    assert set(eia["County"]) == set(fips_by_county), "EIA county names do not reconcile to all 46 SC counties"

    providers: list[dict[str, Any]] = []
    profiles: list[dict[str, Any]] = []
    relationships: list[dict[str, Any]] = []

    for utility_name, group in eia.groupby("Utility Name", sort=True):
        utility_number = int(group["Utility Number"].iloc[0])
        provider_id = PROVIDER_ID_OVERRIDES.get(utility_name, slugify(utility_name.replace(" - (SC)", "")))
        kind = provider_type(utility_name)
        forecast_provider_id = provider_id
        if provider_id in {"duke_energy_carolinas", "duke_energy_progress"}:
            forecast_provider_id = "duke_dec_dep_combined"
        elif kind == "Electric cooperative":
            forecast_provider_id = "central_electric"

        providers.append(
            {
                "provider_id": provider_id,
                "provider_name": utility_name,
                "provider_type": kind,
                "planning_area": "South Carolina distribution presence",
                "state_scope": "South Carolina county presence",
                "forecast_provider_id": forecast_provider_id,
                "overlap_group": "central_member_cooperatives" if kind == "Electric cooperative" else "retail_distribution",
                "eia_utility_number": utility_number,
                "notes": "EIA-861 reports distribution equipment in one or more counties; it does not establish exclusivity or exact boundaries.",
            }
        )
        profiles.append(
            {
                "provider_id": provider_id,
                "display_name": utility_name,
                "provider_type": kind,
                "forecast_provider_id": forecast_provider_id,
                "geography_scope": "South Carolina county presence",
                "latest_forecast_vintage": "Not publicly disclosed",
                "forecast_summary": "Not publicly disclosed" if kind == "Municipal utility" else "See linked planning-system forecast where available.",
                "availability_summary": "County presence only; forecast availability varies by provider.",
                "overlap_warning": "Do not add retail, cooperative, municipal, and wholesale supplier totals together.",
                "notes": "Provider presence is non-exclusive and may cover only part of a county.",
            }
        )
        for row in group.itertuples(index=False):
            county = str(row.County)
            relationships.append(
                {
                    "county_fips": fips_by_county[county],
                    "county_name": county,
                    "provider_id": provider_id,
                    "provider_name": utility_name,
                    "provider_type": kind,
                    "relationship_type": "distribution_equipment_presence",
                    "coverage_type": "county_presence_only",
                    "confidence": "high",
                    "source_id": "eia_861_service_territory_2024",
                    "source_year": 2024,
                    "source_url": EIA_SOURCE_URL,
                    "non_exhaustive": True,
                    "notes": "EIA-861 county presence; not exclusive and not an exact subcounty service boundary.",
                }
            )

    supplemental = [
        ("central_electric", "Central Electric Power Cooperative", "Cooperative wholesale system", "Central cooperative planning area", "South Carolina cooperative wholesale system", "central_electric", "central_wholesale_system"),
        ("duke_dec_dep_combined", "Duke Energy Carolinas + Duke Energy Progress", "Planning-area aggregation", "DEC and DEP planning areas", "Carolinas-wide", "duke_dec_dep_combined", "duke_combined_planning_area"),
        ("pmpa", "Piedmont Municipal Power Agency", "Joint action agency / wholesale supplier", "Municipal wholesale supply", "Supplier relationship only", "pmpa", "municipal_wholesale"),
        ("carolina_power_partners", "Carolina Power Partners", "Wholesale supplier", "Municipal wholesale supply", "Supplier relationship only", "carolina_power_partners", "municipal_wholesale"),
    ]
    for provider_id, name, kind, planning_area, scope, forecast_id, overlap in supplemental:
        providers.append(
            {
                "provider_id": provider_id,
                "provider_name": name,
                "provider_type": kind,
                "planning_area": planning_area,
                "state_scope": scope,
                "forecast_provider_id": forecast_id,
                "overlap_group": overlap,
                "eia_utility_number": "Not applicable",
                "notes": "Added from the supplied statewide report; not an EIA retail-presence record.",
            }
        )
        profiles.append(
            {
                "provider_id": provider_id,
                "display_name": name,
                "provider_type": kind,
                "forecast_provider_id": forecast_id,
                "geography_scope": scope,
                "latest_forecast_vintage": "Not publicly disclosed",
                "forecast_summary": "Not publicly disclosed",
                "availability_summary": "See provider-specific records and supplier notes.",
                "overlap_warning": "Do not add wholesale and retail totals together.",
                "notes": "Planning or supplier relationship; not a county-demand assignment.",
            }
        )

    profile_overrides = {
        "santee_cooper": ("Santee Cooper utility system", "Santee Cooper 2025 load forecast", "Full category and scenario forecast available; direct residential and commercial are combined."),
        "duke_dec_dep_combined": ("Carolinas-wide DEC+DEP planning areas", "Duke 2025 SC IRP Update", "Current total forecast is Carolinas-wide; 2023 class series is older and separate."),
        "dominion_sc": ("Dominion Energy South Carolina system", "Dominion 2026 IRP", "Total energy and peaks available; class bridge values are changes, not absolute demand."),
        "central_electric": ("Central cooperative wholesale system", "Central 2023 IRP", "Total demand scenarios and class account counts available; class MW/GWh are not disclosed."),
        "lockhart_power": ("Lockhart distribution system", "Lockhart 2023 IRP", "Supplier relationship available; detailed demand forecast not publicly disclosed."),
    }
    for profile in profiles:
        if profile["provider_id"] in profile_overrides:
            scope, vintage, summary = profile_overrides[profile["provider_id"]]
            profile["geography_scope"] = scope
            profile["latest_forecast_vintage"] = vintage
            profile["forecast_summary"] = summary

    supplier_relationships = [
        ("Abbeville", "pmpa", "Piedmont Municipal Power Agency", "PMPA supply; city hydro and SEPA allocation also documented."),
        ("Bamberg", "santee_cooper", "Santee Cooper", "Wholesale supply through 2033; SEPA allocation also documented."),
        ("Marlboro", "mpd_electric_cooperative", "Marlboro-area electric cooperative", "Bennettsville wholesale supply documented through 2031."),
        ("Kershaw", "carolina_power_partners", "Carolina Power Partners", "Camden wholesale supply documented through 2041."),
        ("Laurens", "pmpa", "Piedmont Municipal Power Agency", "Clinton and Laurens municipal wholesale supply relationships documented."),
        ("Abbeville", "duke_energy_carolinas", "Duke Energy Carolinas, LLC", "Due West wholesale supply documented through 2028."),
        ("Pickens", "pmpa", "Piedmont Municipal Power Agency", "Easley wholesale supply documented through 2029."),
        ("Cherokee", "pmpa", "Piedmont Municipal Power Agency", "Gaffney wholesale supply documented through 2029."),
        ("Georgetown", "santee_cooper", "Santee Cooper", "City of Georgetown wholesale supply documented through November 2030."),
        ("Greenwood", "carolina_power_partners", "Carolina Power Partners", "Greenwood wholesale supply documented through 2038."),
        ("Greenville", "pmpa", "Piedmont Municipal Power Agency", "Greer wholesale supply documented through 2028."),
        ("McCormick", "carolina_power_partners", "Carolina Power Partners", "McCormick wholesale supply documented through 2038."),
        ("Newberry", "pmpa", "Piedmont Municipal Power Agency", "City of Newberry wholesale supply documented through 2029."),
        ("Orangeburg", "duke_dec_dep_combined", "Duke Energy", "Orangeburg wholesale supply documented through 2039; source does not specify DEC versus DEP."),
        ("Newberry", "newberry_electric_coop_inc", "Newberry Electric Cooperative", "Prosperity wholesale supply documented through 2030; cooperative planning is represented through Central."),
        ("York", "pmpa", "Piedmont Municipal Power Agency", "Rock Hill wholesale supply documented through 2028."),
        ("Oconee", "santee_cooper", "Santee Cooper", "Seneca wholesale supply documented through 2025; historical contract status may have changed."),
        ("Union", "lockhart_power", "Lockhart Power", "Union year-to-year supply relationship documented; PMPA agreements also noted."),
        ("Oconee", "pmpa", "Piedmont Municipal Power Agency", "Westminster wholesale supply documented through 2042."),
        ("Fairfield", "dominion_sc", "Dominion Energy South Carolina, Inc", "Winnsboro wholesale supply documented through 2026; current status may have changed."),
    ]
    for county, supplier_id, supplier_name, note in supplier_relationships:
        relationships.append(
            {
                "county_fips": fips_by_county[county],
                "county_name": county,
                "provider_id": supplier_id,
                "provider_name": supplier_name,
                "provider_type": "Wholesale supplier relationship",
                "relationship_type": "documented_municipal_wholesale_supplier",
                "coverage_type": "supplier_relationship_not_retail_boundary",
                "confidence": "high",
                "source_id": "statewide_provider_report",
                "source_year": 2026,
                "source_url": "docs/sources/" + REPORT_NAME,
                "non_exhaustive": True,
                "notes": note,
            }
        )

    providers_df = pd.DataFrame(providers).drop_duplicates("provider_id").sort_values(["provider_type", "provider_name"])
    profiles_df = pd.DataFrame(profiles).drop_duplicates("provider_id").sort_values("display_name")
    relationships_df = pd.DataFrame(relationships).drop_duplicates(
        ["county_fips", "provider_id", "relationship_type", "notes"]
    ).sort_values(["county_name", "relationship_type", "provider_name"])
    return providers_df, profiles_df, relationships_df


def forecast_record(
    provider_id: str,
    provider_name: str,
    vintage: str,
    source_id: str,
    page: str,
    table: str,
    geography: str,
    year: int | None,
    metric: str,
    category: str,
    scenario: str,
    value: float,
    unit: str,
    *,
    status: str = "reported",
    horizon: str = "calendar_year",
    notes: str = "",
    overlap: str = "",
) -> dict[str, Any]:
    return {
        "provider_id": provider_id,
        "provider_name": provider_name,
        "forecast_vintage": vintage,
        "source_id": source_id,
        "source_document": REPORT_NAME if source_id != "santee_primary_forecast_workbook" else "Load Forecast Details - no link.xlsx",
        "source_page": page,
        "source_table": table,
        "geography_scope": geography,
        "year": year,
        "time_horizon": horizon,
        "metric": metric,
        "category": category,
        "scenario": scenario,
        "value": value,
        "unit": unit,
        "reported_or_modeled": status,
        "availability_status": "Publicly disclosed",
        "notes": notes,
        "do_not_sum_group": overlap,
    }


def build_provider_forecasts() -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    santee_categories = pd.read_csv(PROCESSED_DIR / "santee_forecast_categories.csv")
    for row in santee_categories.itertuples(index=False):
        records.append(
            forecast_record(
                "santee_cooper",
                "Santee Cooper",
                row.forecast_vintage,
                "santee_primary_forecast_workbook",
                row.source_page,
                row.source_table,
                row.geography_scope,
                int(row.year),
                row.metric,
                row.category,
                row.scenario,
                float(row.value),
                row.unit,
                notes=row.notes if isinstance(row.notes, str) else "",
                overlap="santee_central_wholesale_overlap",
            )
        )
    santee_scenarios = pd.read_csv(PROCESSED_DIR / "santee_forecast_scenarios.csv")
    for row in santee_scenarios.itertuples(index=False):
        records.append(
            forecast_record(
                "santee_cooper",
                "Santee Cooper",
                row.forecast_vintage,
                "santee_primary_forecast_workbook",
                row.source_page,
                row.source_table,
                row.geography_scope,
                int(row.year),
                "winter_peak" if row.metric_key == "winter_peak_mw" else "annual_energy",
                row.category,
                row.scenario_key,
                float(row.value),
                row.unit,
                notes=row.notes,
                overlap="santee_central_wholesale_overlap",
            )
        )

    duke_total = [
        (2026,18866,99973,14312,65027),(2027,18636,103476,14596,69062),(2028,19403,110959,14854,71011),
        (2029,20113,117633,15119,73822),(2030,20747,123670,15322,76322),(2031,21139,126695,15449,77487),
        (2032,21560,130048,15605,78540),(2033,22123,135711,15770,79545),(2034,22542,139794,15857,80611),
        (2035,23115,143751,15979,81835),(2036,23391,146058,16179,83228),(2037,23893,148319,16447,84621),
        (2038,24156,150571,16616,86049),(2039,24520,152746,16876,87403),(2040,24775,155256,16978,88634),
    ]
    for year, dec_peak, dec_energy, dep_peak, dep_energy in duke_total:
        for category, peak, energy in (
            ("duke_energy_carolinas", dec_peak, dec_energy),
            ("duke_energy_progress", dep_peak, dep_energy),
            ("combined_total", dec_peak + dep_peak, dec_energy + dep_energy),
        ):
            for metric, value, unit in (("peak_demand", peak, "MW"), ("annual_energy", energy, "GWh")):
                records.append(forecast_record("duke_dec_dep_combined", "Duke Energy Carolinas + Duke Energy Progress", "Duke 2025 SC IRP Update", "duke_2025_update", "24-25", "Tables 5-6", "Carolinas-wide DEC+DEP planning areas", year, metric, category, "base", value, unit, notes="Not South Carolina-only; do not allocate to counties.", overlap="duke_planning_area"))

    duke_classes = [
        (2024,49701,43971,31618,1806,127096),(2025,49338,43854,32609,1801,127602),(2026,49121,43706,33469,1797,128092),
        (2027,49180,44067,34455,1791,129491),(2028,49755,44810,35483,1788,131836),(2029,50413,45812,36251,1784,134261),
        (2030,51082,46619,37052,1784,136538),(2031,51878,47428,37669,1782,138756),(2032,52858,48281,38141,1780,141060),
        (2033,53961,49215,38658,1779,143612),(2034,55263,49506,39191,1777,145736),(2035,56765,49897,39746,1776,148184),
        (2036,58394,50359,40300,1774,150828),(2037,59997,50749,40847,1772,153365),(2038,61813,51247,41475,1772,156307),
    ]
    for year, residential, commercial, industrial, other, total in duke_classes:
        for category, value in (("residential",residential),("commercial",commercial),("industrial",industrial),("other",other),("combined_retail",total)):
            records.append(forecast_record("duke_dec_dep_combined", "Duke Energy Carolinas + Duke Energy Progress", "Duke 2023 Appendix D", "duke_2023_appendix_d", "24-25", "Tables D-19 and D-20", "Carolinas-wide DEC+DEP planning areas", year, "retail_sales", category, "base", value, "GWh", notes="Older class-series vintage; keep separate from Duke 2025 totals.", overlap="duke_planning_area"))

    for category, count, mw in (("executed_energy_service_agreements",16,4337),("letter_agreements",24,3259),("late_stage_projects",3,350),("advanced_projects_total",43,7946)):
        records.append(forecast_record("duke_dec_dep_combined", "Duke Energy Carolinas + Duke Energy Progress", "Spring 2026 large-load report", "duke_large_load_spring_2026", "3", "Table 1", "Carolinas-wide DEC+DEP planning areas", None, "large_load_project_count", category, "advanced_development_projects", count, "projects", horizon="tenth_forecast_year", notes="Development-pipeline record; separate from the 2025 total forecast.", overlap="duke_large_load_pipeline"))
        records.append(forecast_record("duke_dec_dep_combined", "Duke Energy Carolinas + Duke Energy Progress", "Spring 2026 large-load report", "duke_large_load_spring_2026", "3", "Table 1", "Carolinas-wide DEC+DEP planning areas", None, "large_load_full_load_peak", category, "advanced_development_projects", mw, "MW", horizon="tenth_forecast_year", notes="Full-load pipeline value; not county-assigned demand.", overlap="duke_large_load_pipeline"))

    dominion = [
        (2026,23555,4742,4710),(2027,24117,4805,4832),(2028,25011,4935,4980),(2029,25490,5005,5094),
        (2030,25939,5072,5190),(2031,26435,5143,5290),(2032,26804,5217,5388),(2033,27005,5265,5439),
        (2034,27214,5305,5509),(2035,27447,5348,5569),(2036,27673,5386,5626),(2037,27872,5424,5679),
        (2038,28088,5465,5718),(2039,28292,5499,5769),(2040,28487,5534,5832),(2041,28771,5589,5899),
        (2042,29039,5643,5970),(2043,29319,5694,6034),(2044,29581,5747,6078),(2045,29826,5796,6137),
    ]
    for year, energy, summer, winter in dominion:
        for metric, value, unit in (("annual_energy",energy,"GWh"),("summer_peak",summer,"MW"),("winter_peak",winter,"MW")):
            records.append(forecast_record("dominion_sc", "Dominion Energy South Carolina", "Dominion 2026 IRP", "dominion_2026_irp", "36", "Table 8", "Dominion Energy South Carolina system", year, metric, "total_system", "reference", value, unit, overlap="dominion_system"))
    for category, value in (("residential",-35),("commercial",-94),("industrial",23),("electric_vehicles",-92),("electrification",406),("demand_side_management",22)):
        records.append(forecast_record("dominion_sc", "Dominion Energy South Carolina", "Dominion 2026 IRP", "dominion_2026_irp", "37", "Figure 10", "Dominion Energy South Carolina system", 2040, "winter_peak_change_vs_2025_forecast", category, "forecast_bridge", value, "MW change", status="reported_change", notes="Difference from the prior forecast; not absolute category demand.", overlap="dominion_system"))

    central_base = [
        (2023,4150,4539,20955156),(2024,4232,4650,21646804),(2025,4319,4722,22189749),(2026,4394,4800,22905930),
        (2027,4646,4980,24735750),(2028,4814,5200,26169508),(2029,4974,5347,27345836),(2030,5046,5468,27858368),
        (2031,5089,5507,27948965),(2032,5125,5546,28213144),(2033,5166,5574,28319729),(2034,5203,5606,28413254),
        (2035,5244,5642,28579221),(2036,5288,5687,28874061),(2037,5342,5727,29032087),(2038,5395,5773,29185151),
        (2039,5450,5821,29407286),(2040,5502,5871,29738179),(2041,5552,5913,29835300),(2042,5609,5962,30002234),(2043,5666,6009,30266304),
    ]
    for year, summer, winter, energy in central_base:
        for metric, value, unit in (("summer_peak",summer,"MW"),("winter_peak",winter,"MW"),("annual_energy",energy,"MWh")):
            records.append(forecast_record("central_electric", "Central Electric Power Cooperative", "Central 2023 IRP", "central_2023_irp", "62", "Table 5-3", "Central cooperative wholesale system", year, metric, "total_system", "base", value, unit, overlap="santee_central_wholesale_overlap"))

    central_accounts = [
        (2023,786335,89333,396),(2024,800985,90649,398),(2025,814659,91933,400),(2026,827129,93179,401),
        (2027,838633,94405,401),(2028,849717,95587,401),(2029,860342,96725,401),(2030,870838,97850,401),
        (2031,881317,98982,401),(2032,891803,100119,401),(2033,902276,101240,401),(2034,912723,102357,401),
        (2035,922981,103445,401),(2036,933046,104497,401),(2037,943046,105533,401),(2038,953060,106565,401),
        (2039,963136,107603,401),(2040,973347,108649,401),(2041,983681,109679,401),(2042,993940,110693,401),(2043,1004306,111716,401),
    ]
    for year, residential, small_commercial, large_commercial in central_accounts:
        for category, value in (("residential",residential),("small_commercial",small_commercial),("large_commercial",large_commercial)):
            records.append(forecast_record("central_electric", "Central Electric Power Cooperative", "Central 2023 IRP", "central_2023_irp", "61-62", "Table 5-2", "Central cooperative wholesale system", year, "customer_accounts", category, "base", value, "accounts", notes="Customer accounts, not MW or energy.", overlap="central_member_accounts"))

    central_scenarios = [
        ("low",2023,4128,4523,20850589),("low",2030,4895,5299,27129166),("low",2040,5122,5449,28008314),("low",2043,5209,5507,28228355),
        ("base",2023,4150,4539,20955156),("base",2030,5046,5468,27858368),("base",2040,5502,5871,29738179),("base",2043,5666,6009,30266304),
        ("high",2023,4194,4615,21095324),("high",2030,6179,6586,34308608),("high",2040,7018,7404,38258509),("high",2043,7332,7677,39553320),
    ]
    for scenario, year, summer, winter, energy in central_scenarios:
        for metric, value, unit in (("summer_peak",summer,"MW"),("winter_peak",winter,"MW"),("annual_energy",energy,"MWh")):
            records.append(forecast_record("central_electric", "Central Electric Power Cooperative", "Central 2023 IRP", "central_2023_irp", "62, 67-68", "Tables 5-3 through 5-5", "Central cooperative wholesale system", year, metric, "total_system", scenario, value, unit, notes="High case includes prospective industrial/high-load-factor growth; it is not labeled data-center demand.", overlap="santee_central_wholesale_overlap"))

    return pd.DataFrame(records).sort_values(["provider_id", "forecast_vintage", "metric", "category", "scenario", "year"], na_position="last")


def build_availability() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    def add(provider_id: str, category: str, metric: str, available: bool, vintage: str, geography: str, notes: str) -> None:
        rows.append({"provider_id":provider_id,"category":category,"metric":metric,"available":available,"display_status":"Publicly disclosed" if available else "Not publicly disclosed","forecast_vintage":vintage,"geography_scope":geography,"notes":notes})

    for category in ("direct_residential_commercial_combined","direct_industrial","municipal_off_system","central","potential_large_load","total_system"):
        add("santee_cooper",category,"winter_peak_and_annual_energy",True,"Santee Cooper 2025 load forecast","Santee Cooper utility system","Residential and commercial are combined." if "residential" in category else "")
    for category in ("residential","commercial"):
        add("santee_cooper",category,"separate_forecast",False,"Santee Cooper 2025 load forecast","Santee Cooper utility system","Source publishes a combined direct residential/commercial category.")
    add("duke_dec_dep_combined","total_system","peak_and_energy",True,"Duke 2025 SC IRP Update","Carolinas-wide DEC+DEP planning areas","Current totals are not South Carolina-only.")
    add("duke_dec_dep_combined","residential_commercial_industrial","retail_sales",True,"Duke 2023 Appendix D","Carolinas-wide DEC+DEP planning areas","Older class-series vintage kept separate from current totals.")
    add("duke_dec_dep_combined","residential_commercial_industrial","current_2025_class_forecast",False,"Duke 2025 SC IRP Update","Carolinas-wide DEC+DEP planning areas","No replacement numeric class table in the public update.")
    add("dominion_sc","total_system","annual_energy_and_peaks",True,"Dominion 2026 IRP","Dominion Energy South Carolina system","")
    add("dominion_sc","residential_commercial_industrial","absolute_class_forecast",False,"Dominion 2026 IRP","Dominion Energy South Carolina system","Bridge values are changes versus a prior forecast, not absolute category demand.")
    add("central_electric","total_system","annual_energy_and_peaks",True,"Central 2023 IRP","Central cooperative wholesale system","")
    add("central_electric","residential_commercial","customer_accounts",True,"Central 2023 IRP","Central cooperative wholesale system","Counts are customer accounts, not MW or energy.")
    add("central_electric","residential_commercial_industrial","class_demand",False,"Central 2023 IRP","Central cooperative wholesale system","Class MW/GWh are not publicly disclosed.")
    add("lockhart_power","all_categories","detailed_demand_forecast",False,"Lockhart 2023 IRP","Lockhart distribution system","Supplier relationship is public; detailed class forecast is not.")
    add("municipal_utilities","all_categories","class_demand_forecast",False,"Municipal IRPs reviewed","Municipal retail systems","Supplier relationships are public; class forecasts are not.")
    return pd.DataFrame(rows)


def build_sources(eia_path: Path) -> pd.DataFrame:
    eia_sha256 = hashlib.sha256(eia_path.read_bytes()).hexdigest()
    return pd.DataFrame(
        [
            {"source_id":"eia_861_service_territory_2024","title":"Form EIA-861 2024 final Service Territory","publisher":"U.S. Energy Information Administration","source_type":"official_public_dataset","vintage":"2024 final","url":EIA_SOURCE_URL,"local_path":"Not committed; official input supplied to build script","sha256":eia_sha256,"source_page_table":"Service_Territory_2024.xlsx / Counties_States","geography_scope":"Utility county presence","authoritative_status":"primary","notes":"County presence indicates distribution equipment; not exclusivity or exact boundaries."},
            {"source_id":"santee_primary_forecast_workbook","title":"Load Forecast Details - no link.xlsx","publisher":"Santee Cooper / mentor supplied","source_type":"mentor_raw_workbook","vintage":"Santee Cooper 2025 load forecast","url":"Not publicly linked in workbook","local_path":"data/raw/mentor/Load Forecast Details - no link.xlsx","sha256":"c7d9d6de5d60db40100915c18a9cf7292671bf9f4615b14879244aed5c700792","source_page_table":"Energy and Demand, Tables 6-7","geography_scope":"Santee Cooper utility system","authoritative_status":"primary","notes":"Primary Santee forecast source."},
            {"source_id":"santee_historical_workbook","title":"Historical data provided by santee cooper.xlsx","publisher":"Santee Cooper / mentor supplied","source_type":"mentor_raw_workbook","vintage":"Historical 2016-2025","url":"Not publicly linked in workbook","local_path":"data/raw/mentor/Historical data provided by santee cooper.xlsx","sha256":"e60a6c5672476084df0d9fc6fa047c6202225ca0b3093d53fe5d66d111945b42","source_page_table":"Historical Load","geography_scope":"Santee Cooper utility system","authoritative_status":"primary_with_provisional_processed_correction","notes":"Raw source unchanged."},
            {"source_id":"statewide_provider_report","title":"South Carolina Electricity Provider IRP Demand Forecast Review","publisher":"Sarah Carroll","source_type":"mentor_statewide_synthesis","vintage":"2026 synthesis","url":"Not applicable","local_path":"docs/sources/"+REPORT_NAME,"sha256":"","source_page_table":"Tables 1-16 and source index","geography_scope":"Provider-specific; varies by record","authoritative_status":"curated_reference","notes":"Carries original-source page/table references."},
            {"source_id":"duke_2025_update","title":"Duke 2025 South Carolina IRP Update","publisher":"Duke Energy","source_type":"official_utility_filing","vintage":"2025 update","url":"https://dms.psc.sc.gov/Attachments/Matter/46686d94-5740-4840-9f43-d6164049d52b","local_path":"Not committed","sha256":"Not locally archived","source_page_table":"Tables 5-6, pages 24-25","geography_scope":"Carolinas-wide DEC+DEP planning areas","authoritative_status":"primary","notes":"Not South Carolina-only."},
            {"source_id":"duke_2023_appendix_d","title":"Duke 2023 Appendix D Load Forecast","publisher":"Duke Energy","source_type":"official_utility_filing","vintage":"2023 Appendix D","url":"https://dms.psc.sc.gov/Attachments/Matter/7b016a65-5ab4-47ec-8c9f-138c63646636","local_path":"Not committed","sha256":"Not locally archived","source_page_table":"Tables D-19 and D-20, pages 24-25","geography_scope":"Carolinas-wide DEC+DEP planning areas","authoritative_status":"primary_older_vintage","notes":"Class series kept separate from 2025 totals."},
            {"source_id":"duke_large_load_spring_2026","title":"Duke Semi-Annual Economic Development Report on Large Load Additions","publisher":"Duke Energy","source_type":"official_utility_filing","vintage":"Spring 2026","url":"https://dms.psc.sc.gov/Attachments/Matter/de0c7c13-0d78-48ab-ac99-0589702ddad9","local_path":"Not committed","sha256":"Not locally archived","source_page_table":"Table 1, page 3","geography_scope":"Carolinas-wide DEC+DEP planning areas","authoritative_status":"primary_pipeline_record","notes":"Separate from utility total forecast."},
            {"source_id":"dominion_2026_irp","title":"Dominion Energy South Carolina 2026 IRP","publisher":"Dominion Energy South Carolina","source_type":"official_utility_filing","vintage":"2026 IRP","url":"https://cdn-dominionenergy-prd-001.azureedge.net/-/media/content/about/our-company/irp/pdfs/integrated-resource-plan-desc.pdf","local_path":"Not committed","sha256":"Not locally archived","source_page_table":"Table 8 and Figure 10, pages 36-37","geography_scope":"Dominion Energy South Carolina system","authoritative_status":"primary","notes":"Driver bridge values are changes versus prior forecast."},
            {"source_id":"central_2023_irp","title":"Central Electric Power Cooperative 2023 IRP","publisher":"Central Electric Power Cooperative","source_type":"official_utility_filing","vintage":"2023 IRP","url":"https://energy.sc.gov/sites/energy/files/2023-12/2023%20Central%20Electric%20Power%20Cooperative%20IRP%C2%A0%28PDF%29.pdf","local_path":"Not committed","sha256":"Not locally archived","source_page_table":"Tables 5-2 through 5-5, pages 61-68","geography_scope":"Central cooperative wholesale system","authoritative_status":"primary","notes":"Class values are accounts unless explicitly reported otherwise."},
        ]
    )


def build_quality_events() -> pd.DataFrame:
    corrections = pd.read_csv(PROCESSED_DIR / "santee_correction_events.csv")
    rows = corrections.to_dict("records")
    rows.extend(
        [
            {"event_id":"FORECAST_QUARANTINE_001","provider_id":"santee_cooper","year":"Not applicable","event_type":"source_quarantine","correction_rule_id":"Not applicable","affected_fields":"entire_workbook","untouched_fields":"primary forecast workbook","status":"quarantined","confirmation_status":"confirmed_release_rule","reason":"Derived three-year workbook is rounded and has weaker provenance than the complete primary forecast workbook.","source_document":"forecasts in peak load with_without PPL.xlsx","source_sheet":"All sheets","notes":"No alleged 22/2200% correction manufactured; workbook excluded from authoritative ingestion."},
            {"event_id":"HIST_UTIL_QUARANTINE_001","provider_id":"santee_cooper","year":"2018|2019|2022","event_type":"source_quarantine","correction_rule_id":"SANTEE_HIST_001","affected_fields":"derived Central utilization metrics","untouched_fields":"raw workbook","status":"quarantined","confirmation_status":"regeneration_required","reason":"Derived utilization workbook inherits the historical category anomaly.","source_document":"historical utilization metrics.xlsx","source_sheet":"Utilization Metrics|Annual Summary","notes":"Regenerate later from corrected processed data."},
            {"event_id":"COUNTY_LOOKUP_SCOPE_001","provider_id":"all","year":2024,"event_type":"geography_scope_warning","correction_rule_id":"Not applicable","affected_fields":"county_provider_lookup","untouched_fields":"county geometries","status":"active_warning","confirmation_status":"documented","reason":"EIA-861 county presence is non-exclusive and does not provide exact subcounty boundaries.","source_document":"Service_Territory_2024.xlsx","source_sheet":"Counties_States","notes":"Lookup is explicitly non-exhaustive and must not be used to allocate demand."},
        ]
    )
    return pd.DataFrame(rows)


def build_large_load_projects() -> pd.DataFrame:
    projects = [
        ("google_berkeley","Google","Google Berkeley expansion","45015","Berkeley",None,"Not publicly disclosed","official_announcement","grid relationship not publicly disclosed","https://governor.sc.gov/news/2024-09/google-grows-south-carolina-footprint-new-dorchester-county-operations-expansion","Expansion announced; no MW disclosed."),
        ("google_dorchester","Google","Google Dorchester campuses","45035","Dorchester",None,"Not publicly disclosed","official_announcement","grid relationship not publicly disclosed","https://governor.sc.gov/news/2024-09/google-grows-south-carolina-footprint-new-dorchester-county-operations-expansion","Two campuses announced; no MW disclosed."),
        ("meta_aiken","Meta","Meta Aiken data center","45003","Aiken",None,"Not publicly disclosed","official_announcement","grid relationship not publicly disclosed","https://governor.sc.gov/news/2024-08/meta-selects-aiken-county-first-south-carolina-data-center","AI-optimized facility; no MW disclosed."),
        ("qts_york","QTS","QTS York County campus","45091","York",None,"Not publicly disclosed","official_announcement","grid relationship not publicly disclosed","https://governor.sc.gov/news/2023-09/qts-data-centers-establishing-first-south-carolina-operations-york-county","Hyperscale facility; no MW disclosed."),
        ("cielo_cherokee","Cielo Digital Infrastructure","Cielo Gaffney campus","45021","Cherokee",300.0,"Up to 300 MW","public_report_context","grid relationship not publicly disclosed","https://www.datacenterdynamics.com/en/news/cielo-digital-infrastructure-plans-300mw-data-center-campus-in-south-carolina/","Public-report context only; not a utility-accepted forecast."),
        ("northmark_spartanburg","NorthMark Strategies / Valara Holdings","NorthMark high-performance computing center","45083","Spartanburg",None,"Not publicly disclosed","official_announcement","reported on-site generation","https://governor.sc.gov/news/2025-04/northmark-strategies-selects-spartanburg-county-establish-first-south-carolina","Announcement reports on-site generation; no grid-load MW disclosed."),
    ]
    rows=[]
    for project_id,company,name,fips,county,mw,mw_label,mw_source,grid,source,notes in projects:
        rows.append({"project_id":project_id,"company":company,"project_name":name,"county_fips":fips,"county_name":county,"provider_id_if_known":"Not publicly disclosed","status":"public_announcement_context","announced_mw":mw,"mw_display":mw_label,"mw_source_type":mw_source,"grid_or_onsite":grid,"utility_forecast_link_status":"Not publicly disclosed","context_only":True,"source_url":source,"notes":notes})
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eia-service-territory", required=True, type=Path)
    args = parser.parse_args()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)

    providers, profiles, lookup = build_eia_relationships(args.eia_service_territory)
    forecasts = build_provider_forecasts()
    availability = build_availability()
    sources = build_sources(args.eia_service_territory)
    quality = build_quality_events()
    projects = build_large_load_projects()

    providers.to_csv(PROCESSED_DIR / "providers.csv", index=False)
    forecasts.to_csv(PROCESSED_DIR / "provider_forecasts.csv", index=False)
    profiles.to_csv(PROCESSED_DIR / "provider_profiles.csv", index=False)
    availability.to_csv(PROCESSED_DIR / "data_availability.csv", index=False)
    sources.to_csv(PROCESSED_DIR / "source_metadata.csv", index=False)
    quality.to_csv(PROCESSED_DIR / "data_quality_events.csv", index=False)
    lookup.to_csv(REFERENCE_DIR / "county_provider_lookup.csv", index=False)
    projects.to_csv(REFERENCE_DIR / "large_load_projects.csv", index=False)

    print("Providers:", len(providers))
    print("Provider forecast records:", len(forecasts))
    print("County/provider relationship records:", len(lookup))
    print("Counties represented:", lookup["county_fips"].nunique())
    print("Large-load context records:", len(projects))


if __name__ == "__main__":
    main()
