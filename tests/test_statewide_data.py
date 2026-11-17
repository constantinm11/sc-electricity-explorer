from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from src.data_validation import assert_complete_sc_counties, assert_no_county_demand_allocation, assert_provenance_columns

ROOT = Path(__file__).resolve().parents[1]


class StatewideDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.counties = pd.read_csv(ROOT / "data" / "sc_counties.csv", dtype={"fips": str})
        cls.providers = pd.read_csv(ROOT / "data" / "processed" / "providers.csv")
        cls.forecasts = pd.concat(
            [
                pd.read_csv(ROOT / "data" / "processed" / "provider_forecasts.csv"),
                pd.read_csv(ROOT / "data" / "processed" / "provider_forecasts_2026.csv"),
            ],
            ignore_index=True,
        )
        cls.availability = pd.read_csv(ROOT / "data" / "processed" / "data_availability.csv")
        cls.sources = pd.read_csv(ROOT / "data" / "processed" / "source_metadata.csv")
        cls.quality = pd.read_csv(ROOT / "data" / "processed" / "data_quality_events.csv")
        cls.lookup = pd.read_csv(ROOT / "data" / "reference" / "county_provider_lookup.csv", dtype={"county_fips": str})
        cls.projects = pd.read_csv(ROOT / "data" / "reference" / "large_load_projects.csv", dtype={"county_fips": str})

    def test_all_counties_have_sourced_presence(self) -> None:
        assert_complete_sc_counties(self.counties)
        self.assertEqual(set(self.lookup["county_fips"].str.zfill(5)), set(self.counties["fips"].str.zfill(5)))
        self.assertTrue(self.lookup["non_exhaustive"].all())
        self.assertFalse({"exclusive", "percent_coverage", "county_demand"} & set(self.lookup.columns))

    def test_forecast_provenance_and_no_county_allocation(self) -> None:
        assert_provenance_columns(self.forecasts)
        assert_no_county_demand_allocation(self.forecasts)
        self.assertTrue((self.forecasts["availability_status"] == "Publicly disclosed").all())
        self.assertTrue(set(self.forecasts["source_id"]).issubset(set(self.sources["source_id"])))
        self.assertTrue(set(self.lookup["source_id"]).issubset(set(self.sources["source_id"])))

    def test_required_geography_labels(self) -> None:
        duke = self.forecasts[self.forecasts["provider_id"] == "duke_dec_dep_combined"]
        self.assertTrue(duke["geography_scope"].str.contains("Carolinas-wide").all())
        dominion = self.forecasts[self.forecasts["provider_id"] == "dominion_sc"]
        self.assertTrue((dominion["geography_scope"] == "Dominion Energy South Carolina system").all())
        central = self.forecasts[self.forecasts["provider_id"] == "central_electric"]
        self.assertTrue((central["geography_scope"] == "Central cooperative wholesale system").all())

    def test_provider_methodological_rules(self) -> None:
        santee = self.forecasts[self.forecasts["provider_id"] == "santee_cooper"]
        self.assertIn("direct_residential_commercial_combined", set(santee["category"]))
        self.assertNotIn("residential", set(santee["category"]))
        bridge = self.forecasts[self.forecasts["metric"] == "winter_peak_change_vs_2025_forecast"]
        self.assertTrue((bridge["reported_or_modeled"] == "reported_change").all())
        self.assertTrue(bridge["notes"].str.contains("not absolute", case=False).all())
        accounts = self.forecasts[self.forecasts["metric"] == "customer_accounts"]
        self.assertTrue((accounts["unit"] == "accounts").all())
        overlapping = self.forecasts[self.forecasts["provider_id"].isin(["santee_cooper", "central_electric", "duke_dec_dep_combined"])]
        self.assertTrue(overlapping["do_not_sum_group"].notna().all())

    def test_2026_forecast_vintages_are_available(self) -> None:
        santee = self.forecasts[
            (self.forecasts["provider_id"] == "santee_cooper")
            & (self.forecasts["forecast_vintage"] == "Santee Cooper 2026 Triennial IRP")
        ]
        self.assertFalse(santee.empty)
        santee_2040 = santee[
            (santee["year"] == 2040)
            & (santee["metric"] == "winter_peak")
            & (santee["category"] == "total_system")
            & (santee["scenario"] == "base")
        ]
        self.assertEqual(float(santee_2040.iloc[0]["value"]), 7246.0)

        duke = self.forecasts[
            (self.forecasts["provider_id"] == "duke_dec_dep_combined")
            & (self.forecasts["forecast_vintage"] == "Duke 2026 Carolinas Resource Plan")
        ]
        self.assertFalse(duke.empty)
        self.assertTrue(duke["geography_scope"].str.contains("Carolinas-wide").all())

    def test_unavailable_categories_are_explicit(self) -> None:
        unavailable = self.availability[~self.availability["available"]]
        self.assertGreater(len(unavailable), 0)
        self.assertTrue((unavailable["display_status"] == "Not publicly disclosed").all())

    def test_large_load_records_do_not_infer_mw(self) -> None:
        no_mw = self.projects[self.projects["company"].isin(["Google", "Meta", "QTS", "NorthMark Strategies / Valara Holdings"])]
        self.assertTrue(no_mw["announced_mw"].isna().all())
        cielo = self.projects[self.projects["company"] == "Cielo Digital Infrastructure"].iloc[0]
        self.assertEqual(cielo["announced_mw"], 300)
        self.assertEqual(cielo["mw_source_type"], "public_report_context")
        self.assertIn("not a utility-accepted forecast", cielo["notes"])
        self.assertTrue(self.projects["context_only"].all())

    def test_quality_events_document_quarantine(self) -> None:
        quarantine = self.quality[self.quality["status"] == "quarantined"]
        self.assertEqual(set(quarantine["event_id"]), {"FORECAST_QUARANTINE_001", "HIST_UTIL_QUARANTINE_001"})


if __name__ == "__main__":
    unittest.main()
