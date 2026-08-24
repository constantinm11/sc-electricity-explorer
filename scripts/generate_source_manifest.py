"""Regenerate the SHA-256 manifest for immutable committed source artifacts."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "sources" / "source_manifest.csv"

SOURCES = [
    (
        "data/raw/mentor/Historical data provided by santee cooper.xlsx",
        "mentor_raw_historical",
        "authoritative_raw",
        "Immutable source; provisional category correction is applied only in processed data.",
    ),
    (
        "data/raw/mentor/Load Forecast Details - no link.xlsx",
        "mentor_raw_forecast",
        "authoritative_raw",
        "Primary Santee forecast source for this release.",
    ),
    (
        "data/raw/mentor/forecasts in peak load with_without PPL.xlsx",
        "mentor_derived_forecast",
        "quarantined",
        "Rounded three-year derivative with ambiguous provenance; not used for authoritative ingestion.",
    ),
    (
        "data/raw/mentor/historical utilization metrics.xlsx",
        "mentor_derived_historical",
        "quarantined",
        "Inherits the historical category anomaly; regenerate from corrected processed data before use.",
    ),
    (
        "docs/sources/Not publicly distributed",
        "mentor_statewide_synthesis",
        "authoritative_reference",
        "Provider-level synthesis with source page and table references; never treated as county-demand data.",
    ),
]


def main() -> None:
    rows = []
    for relative_path, role, status, notes in SOURCES:
        path = ROOT / relative_path
        content = path.read_bytes()
        rows.append(
            {
                "path": relative_path,
                "sha256": hashlib.sha256(content).hexdigest(),
                "bytes": len(content),
                "role": role,
                "ingestion_status": status,
                "notes": notes,
            }
        )
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {OUTPUT.relative_to(ROOT)} ({len(rows)} immutable sources)")


if __name__ == "__main__":
    main()
