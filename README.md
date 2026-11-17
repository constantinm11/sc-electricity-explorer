# South Carolina Electricity Provider Explorer

This local Streamlit dashboard was prepared for the University of South Carolina Provost Undergraduate AI Fellowship. It provides statewide provider/service context and provider-level planning forecasts while preserving a detailed Santee Cooper prototype.

The dashboard does **not** model or claim measured county electricity demand. County records are sourced, many-to-many provider relationships; utility totals remain at their reported system or planning-area geography.

## Public-release note

The live dashboard uses committed, normalized processed data. Raw mentor-supplied workbooks and the supplied source report are retained only in the private `main` branch and are intentionally omitted from this deployment branch. County records represent provider presence, not measured county electricity demand. Public project records remain a separate contextual layer and are not combined with utility forecasts.

## Dashboard sections

- **Statewide Provider Explorer** renders all 46 counties, shows non-exclusive provider/service relationships, connects retail entities to relevant planning-system forecasts, and preserves multiple forecast vintages where available. The newest vintage is selected by default while older vintages remain available for comparison. Public large-load announcements stay in a separate contextual layer.
- **Santee Cooper Deep Dive** preserves historical data plus both the 2025 load forecast and the 2026 Triennial IRP forecast. Users can switch forecast vintage and compare with-PLL, without-PLL, PLL-only, high, and low cases. Direct residential and commercial remain combined.
- **Methodology and Data Quality** exposes source metadata, availability gaps, overlap warnings, quarantined inputs, and provisional corrections.

## Run locally

Python 3.11 or newer is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
streamlit run app.py
```

Open the local URL printed by Streamlit, normally `http://localhost:8501`. No secrets or external services are required for the committed dashboard outputs.

To regenerate the static review artifact:

```bash
python export_static_demo.py
```

Then open `outputs/sc_energy_map_demo.html` locally.

## Statewide data rebuild

The committed normalized statewide CSVs are ready to use. To rebuild them, download the official 2024 final EIA-861 ZIP from the [EIA electricity data page](https://www.eia.gov/electricity/data/eia861/), extract `Service_Territory_2024.xlsx`, then run:

```bash
python scripts/build_statewide_data.py \
  --eia-service-territory /path/to/Service_Territory_2024.xlsx
```

The EIA file is not committed. Its SHA-256 is recorded in `data/processed/source_metadata.csv` for the build used in this release.

## Repository layout

- `app.py` — Streamlit entry point.
- `src/` — data loading, selection logic, charts, maps, and validation helpers.
- `clean_data.py` — private-archive Santee ingestion tooling; the public app does not run it.
- `scripts/build_statewide_data.py` — statewide normalization from EIA-861 plus the supplied report.
- `data/raw/mentor/` — retained only on the private `main` branch; omitted here.
- `data/processed/` — normalized provider and Santee datasets, including separate 2026 refresh files so earlier forecast vintages remain reproducible.
- `data/reference/` — county/provider relationships and contextual large-load projects.
- `outputs/` — compatibility outputs and the static HTML review artifact.
- `docs/` — methodology, architecture, dictionary, source manifest, and workbook audit.
- `tests/` — data-integrity, provenance, selection, and Streamlit smoke tests.

## Non-negotiable interpretation rules

- Provider/system totals are never county demand.
- Duke current totals remain Carolinas-wide.
- Dominion bridge values are changes from a prior forecast, not absolute class demand.
- Central class counts are customer accounts, not MW or energy.
- Santee direct residential and commercial are combined.
- Wholesale, retail, municipal, and cooperative totals may overlap and must not be summed.
- Missing categories display as **Not publicly disclosed**; they are not filled with zero.
- Public project announcements are not utility forecasts, and MW is never inferred from dollars or square footage.

See [Methodology](docs/methodology.md), [Data Dictionary](docs/data_dictionary.md), [Architecture](docs/architecture.md), and [Workbook Audit](docs/workbook_audit.md).
