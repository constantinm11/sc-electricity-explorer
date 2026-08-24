# Methodology and Data Quality

## Geographic interpretation

`county_provider_lookup.csv` is a many-to-many relationship layer. Its primary statewide input is the official 2024 final EIA-861 Service Territory workbook, where a utility/county row indicates distribution equipment presence. This supports county presence, not exclusivity, percent coverage, an exact service-territory polygon, or measured county demand. Every lookup row therefore carries a source, year, relationship type, coverage type, confidence, notes, and `non_exhaustive=true`.

All 46 South Carolina counties render. The application uses a county selectbox for reliable selection and a choropleth of sourced relationship counts for context. The map never encodes MW, MWh, GWh, customer load, or a share of a utility total.

## Provider forecasts

Forecast records retain provider, source document, page/table, vintage, geography, metric, category, scenario, units, reported-versus-modeled status, and an overlap group. A retail provider can link to a planning-system forecast, but the planning geography remains visible beside the chart.

- Santee direct residential and commercial remain combined.
- Duke 2025 totals remain Carolinas-wide. Duke 2023 class forecasts and Spring 2026 large-load records are distinct vintages and record types.
- Dominion bridge records are changes versus the prior forecast, not absolute class demand.
- Central class records are customer accounts unless a source explicitly supplies MW or MWh.
- Lockhart and municipal records retain supplier relationships and explicit unavailable forecast categories.
- Santee, Central, member cooperative, municipal, retail, and wholesale totals can overlap. `do_not_sum_group` and UI warnings prevent interpretation as additive statewide demand.

Missing information is represented as **Not publicly disclosed**, not as zero and not by an estimate.

## Historical Santee correction

Rule `SANTEE_HIST_001` applies only to processed data for 2018, 2019, and 2022:

- swap Central Energy with Transformer Losses/Other Energy;
- swap Central coincident peak with Transformer Losses/Other coincident peak;
- leave Central non-coincident peak unchanged.

Raw and corrected fields coexist in the processed monthly dataset. The event registry records the rule, affected years and fields, untouched fields, reason, provisional status, and pending source confirmation. Raw workbooks are byte-preserved.

The derived `historical utilization metrics.xlsx` workbook inherits the anomaly and is quarantined pending regeneration. The exact alleged 22/2200% value is not present in the supplied `forecasts in peak load with_without PPL.xlsx` bytes; no correction was invented. That derivative is excluded because the complete primary workbook, `Load Forecast Details - no link.xlsx`, has stronger provenance.

## Large-load context

Google, Meta, QTS, Cielo, and NorthMark announcements are separate contextual records. No MW is inferred from cost or floor area. Cielo’s up-to-300-MW figure is labeled public-report context rather than utility-accepted forecast capacity. NorthMark records reported on-site generation. These records are never summed with provider forecasts.

## Reported versus modeled

“Reported” means transcribed from a source table or workbook. “Modeled” identifies source-authored forecasts or scenarios and does not imply observed demand. Source vintage differences are maintained rather than blended. The release contains no modeled county-demand allocation.
