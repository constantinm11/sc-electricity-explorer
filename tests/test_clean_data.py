from __future__ import annotations

import unittest

import pandas as pd
from openpyxl import load_workbook

import clean_data
from src.data_validation import assert_complete_sc_counties, assert_no_county_demand_allocation

RAW_SOURCES_AVAILABLE = clean_data.HISTORICAL_FILE.exists() and clean_data.FORECAST_FILE.exists()


class CleanDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if RAW_SOURCES_AVAILABLE:
            cls.monthly, cls.historical, cls.historical_categories, cls.events = clean_data.clean_historical_demand()
            cls.forecast_wide, cls.forecast, cls.forecast_categories = clean_data.clean_forecast_demand()
        else:
            processed = clean_data.ROOT / "data" / "processed"
            cls.monthly = pd.read_csv(processed / "santee_historical_monthly.csv")
            cls.historical = pd.read_csv(clean_data.OUTPUT_DIR / "santee_historical_demand_clean.csv")
            cls.historical_categories = pd.read_csv(processed / "santee_historical_categories.csv")
            cls.events = pd.read_csv(processed / "santee_correction_events.csv")
            cls.forecast_wide = pd.read_csv(processed / "santee_forecast_wide.csv")
            cls.forecast = pd.read_csv(processed / "santee_forecast_scenarios.csv")
            cls.forecast_categories = pd.read_csv(processed / "santee_forecast_categories.csv")

    def test_sc_counties_complete(self) -> None:
        counties = pd.read_csv(clean_data.ROOT / "data" / "sc_counties.csv", dtype={"fips": str})
        assert_complete_sc_counties(counties)

    @unittest.skipUnless(
        RAW_SOURCES_AVAILABLE,
        "Raw mentor workbooks are intentionally omitted from the public deployment branch.",
    )
    def test_provisional_swaps_and_ncp_untouched(self) -> None:
        wb = load_workbook(clean_data.HISTORICAL_FILE, data_only=True, read_only=True)
        ws = wb["Historical Load"]
        for row in self.monthly.itertuples(index=False):
            raw_row = int(row.source_row)
            raw_energy_central = float(ws.cell(raw_row, 6).value)
            raw_energy_losses = float(ws.cell(raw_row, 9).value)
            raw_ncp_central = float(ws.cell(raw_row, 13).value)
            raw_cp_central = float(ws.cell(raw_row, 18).value)
            raw_cp_losses = float(ws.cell(raw_row, 21).value)
            if row.year in clean_data.CORRECTION_YEARS:
                self.assertEqual(row.energy_central_mwh, raw_energy_losses)
                self.assertEqual(row.energy_transformer_losses_other_mwh, raw_energy_central)
                self.assertEqual(row.cp_central_mw, raw_cp_losses)
                self.assertEqual(row.cp_transformer_losses_other_mw, raw_cp_central)
                self.assertTrue(row.correction_applied)
            else:
                self.assertEqual(row.energy_central_mwh, raw_energy_central)
                self.assertEqual(row.cp_central_mw, raw_cp_central)
                self.assertFalse(row.correction_applied)
            self.assertEqual(row.ncp_central_mw, raw_ncp_central)
        wb.close()

    def test_forecast_category_reconciliation(self) -> None:
        peak_components = [
            "winter_peak_res_com_mw",
            "winter_peak_industrial_mw",
            "winter_peak_municipal_off_system_mw",
            "winter_peak_central_mw",
            "winter_peak_pll_mw",
        ]
        energy_components = [
            "annual_energy_res_com_gwh",
            "annual_energy_industrial_gwh",
            "annual_energy_municipal_off_system_gwh",
            "annual_energy_central_gwh",
            "annual_energy_pll_gwh",
        ]
        self.assertTrue(
            ((self.forecast_wide[peak_components].sum(axis=1) - self.forecast_wide["winter_peak_total_mw"]).abs() < 1e-6).all()
        )
        self.assertTrue(
            ((self.forecast_wide[energy_components].sum(axis=1) - self.forecast_wide["annual_energy_total_gwh"]).abs() < 1e-6).all()
        )

    def test_primary_forecast_and_combined_category(self) -> None:
        self.assertTrue((self.forecast["source_file"] == clean_data.FORECAST_FILE.name).all())
        categories = set(self.forecast_categories["category"])
        self.assertIn("direct_residential_commercial_combined", categories)
        self.assertNotIn("residential", categories)
        self.assertNotIn("commercial", categories)

    def test_no_county_demand_allocation(self) -> None:
        assert_no_county_demand_allocation(self.forecast_categories)
        self.assertTrue((self.forecast["geography_type"] == "utility_system").all())

    def test_correction_events_are_complete(self) -> None:
        self.assertEqual(set(self.events["year"]), clean_data.CORRECTION_YEARS)
        self.assertTrue((self.events["status"] == "provisional").all())
        self.assertTrue((self.events["confirmation_status"] == "pending_source_confirmation").all())


if __name__ == "__main__":
    unittest.main()
