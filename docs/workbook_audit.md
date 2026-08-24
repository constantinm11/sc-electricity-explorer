# Workbook Audit

Audit date: 2026-07-22

Release disposition: independently verified and implemented in local release pipeline.

## Scope and preservation

The four mentor workbooks under `data/raw/mentor/` and the statewide source DOCX are immutable inputs. Their SHA-256 hashes are recorded in `docs/sources/source_manifest.csv`. Corrections and exclusions described below apply only to processed data and ingestion logic.

## Historical Santee workbook

Source: `Historical data provided by santee cooper.xlsx`, sheet `Historical Load`.

The workbook contains monthly data for 2016-2025. Energy categories reconcile to Total Territorial Load, and coincident-peak components reconcile to total coincident peak.

For every month in 2018, 2019, and 2022:

- Central Energy is anomalously small while Transformer Losses/Other Energy is anomalously large.
- Central coincident peak is anomalously small while Transformer Losses/Other coincident peak is anomalously large.
- Central non-coincident peak remains in its normal range and has no Transformer Losses/Other counterpart.

Annual raw energy shares provide a clear diagnostic:

| Year | Raw Central share | Raw losses/other share | Provisional corrected Central share | Provisional corrected losses/other share |
|---:|---:|---:|---:|---:|
| 2018 | 2.84% | 57.09% | 57.09% | 2.84% |
| 2019 | 1.20% | 58.49% | 58.49% | 1.20% |
| 2022 | 1.22% | 59.67% | 59.67% | 1.22% |

Release rule `SANTEE_HIST_001` therefore swaps the two energy fields and the two coincident-peak fields for those years in processed data only. It does not modify Central non-coincident peak. The correction is provisional pending confirmation from the source owner.

## Historical utilization workbook

Source: `historical utilization metrics.xlsx`.

The `Utilization Metrics` formulas directly reference the anomalous historical categories. The cached `Annual Summary` consequently reports implausible Central average loads and load factors in 2018, 2019, and 2022. This workbook is not an authoritative release input. Utilization metrics should be regenerated later from corrected processed historical data.

## Primary Santee forecast workbook

Source: `Load Forecast Details - no link.xlsx`, sheet `Energy and Demand`.

This is the primary Santee forecast source. It provides complete 2025-2044 winter-peak and annual-energy tables with these published categories:

- Direct-Served Residential and Commercial, combined
- Direct-Served Industrial
- Municipal & Off-System
- Central
- Potential Large Load
- Total, High Case, and Low Case

Formula totals reconcile to the component categories. The release preserves residential and commercial as one combined category.

## Quarantined derivative forecast workbook

Source: `forecasts in peak load with_without PPL.xlsx`.

The exact alleged value `22` or display `2200%` is not present in the supplied bytes and no correction is manufactured. The workbook contains only rounded 2025, 2030, and 2040 inputs, generic source notes, and derived share calculations. It is excluded from authoritative ingestion because the complete primary forecast workbook is available.

## Statewide synthesis

The 16-page statewide DOCX contains provider forecasts, source vintages, source page/table references, availability gaps, supplier relationships, and public large-load announcements. Values are normalized only at their reported geography and vintage. The report does not provide measured county demand or an exhaustive county service-territory allocation.

## Release disposition summary

| Input | Disposition | Release use |
|---|---|---|
| `Historical data provided by santee cooper.xlsx` | Primary with provisional processed correction | Historical Santee totals and categories; raw bytes unchanged |
| `Load Forecast Details - no link.xlsx` | Primary | Complete Santee category and scenario forecast |
| `forecasts in peak load with_without PPL.xlsx` | Quarantined | No authoritative ingestion and no manufactured 22/2200% correction |
| `historical utilization metrics.xlsx` | Quarantined | Regeneration deferred until source confirmation |
| Statewide provider DOCX | Curated reference | Provider facts retain cited source page/table and geography |

The exact immutable input hashes and byte sizes are generated in `docs/sources/source_manifest.csv` by `scripts/generate_source_manifest.py`.
