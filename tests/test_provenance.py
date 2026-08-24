from __future__ import annotations

import csv
import hashlib
import unittest
from pathlib import Path

import clean_data
import pandas as pd
from src.data_validation import assert_provenance_columns

RAW_SOURCES_AVAILABLE = clean_data.HISTORICAL_FILE.exists() and clean_data.FORECAST_FILE.exists()


class ProvenanceTests(unittest.TestCase):
    def test_immutable_source_manifest(self) -> None:
        manifest = clean_data.ROOT / "docs" / "sources" / "source_manifest.csv"
        with manifest.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 5)
        missing = [row for row in rows if not (clean_data.ROOT / row["path"]).exists()]
        if missing:
            self.assertEqual(
                len(missing),
                len(rows),
                "A public deployment should omit the complete private source set, not only part of it.",
            )
            return
        for row in rows:
            path = clean_data.ROOT / row["path"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), row["sha256"])
            self.assertEqual(path.stat().st_size, int(row["bytes"]))

    def test_processed_category_provenance(self) -> None:
        if RAW_SOURCES_AVAILABLE:
            _, _, historical_categories, _ = clean_data.clean_historical_demand()
            _, _, forecast_categories = clean_data.clean_forecast_demand()
        else:
            historical_categories = pd.read_csv(
                clean_data.ROOT / "data" / "processed" / "santee_historical_categories.csv"
            )
            forecast_categories = pd.read_csv(
                clean_data.ROOT / "data" / "processed" / "santee_forecast_categories.csv"
            )
        assert_provenance_columns(historical_categories)
        assert_provenance_columns(forecast_categories)
        self.assertFalse((forecast_categories["geography_scope"] == "South Carolina county").any())


if __name__ == "__main__":
    unittest.main()
