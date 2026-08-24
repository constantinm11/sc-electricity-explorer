# Architecture and Data Flow

## Flow

```text
immutable mentor XLSX files ──> clean_data.py ──> Santee processed CSVs ─┐
                                                                        │
official EIA-861 XLSX ─┐                                                ├─> app.py
supplied statewide DOCX ├─> scripts/build_statewide_data.py ─> CSVs ───┤   Streamlit
public source records ──┘                                                │
county GeoJSON/CSV ──────────────────────────────────────────────────────┘
```

The app reads committed CSVs; it does not parse workbooks at runtime. This keeps interaction deterministic and makes the source-to-display boundary auditable.

## Application modules

- `app.py`: page composition, user controls, interpretation warnings, and Streamlit entry point.
- `src/config.py`: relative repository paths, labels, and visual constants.
- `src/data_loaders.py`: typed loading of committed datasets and county geometry.
- `src/selection.py`: pure county/provider and planning-entity resolution logic.
- `src/map_builder.py`: county presence maps that never accept demand values.
- `src/chart_builder.py`: provider and Santee charts with geography and vintage in titles.
- `src/data_validation.py`: reusable completeness, provenance, and allocation guardrails.

## Pipelines

`clean_data.py` reads the two authoritative Santee workbooks with `openpyxl`, applies the provisional correction only in memory/processed outputs, and writes compatibility files to `outputs/` plus normalized Santee files to `data/processed/`.

`scripts/build_statewide_data.py` accepts an explicit EIA-861 workbook path, validates all 46 counties, normalizes provider and county relationships, and combines those with provider records extracted from the supplied statewide report. It never modifies source files or performs an implicit download.

`export_static_demo.py` creates a local HTML review artifact with the statewide relationship map and a separate Santee system forecast chart. It does not place a provider total in county hover data.

## Verification boundary

Tests cover raw source hashes, correction behavior, category reconciliation, provenance, geography labels, availability wording, county/FIPS completeness, large-load MW guardrails, selection logic, and noninteractive rendering of every dashboard section.
