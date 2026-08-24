# Data Dictionary

Blank numeric cells mean no numeric value was disclosed. Display layers convert unavailable categories to **Not publicly disclosed** rather than zero.

## Core statewide outputs

### `data/processed/providers.csv`

Provider registry. `provider_id` is the stable key; `forecast_provider_id` links a retail entity to its documented planning entity. `overlap_group` identifies records that must not be added as independent demand. `eia_utility_number` retains the EIA identifier where applicable.

### `data/processed/provider_forecasts.csv`

Normalized provider forecast facts. Required provenance fields include `forecast_vintage`, `source_id`, `source_document`, `source_page`, `source_table`, and `geography_scope`. Fact fields are `year`, `time_horizon`, `metric`, `category`, `scenario`, `value`, and `unit`. `reported_or_modeled` distinguishes source-reported facts, source-authored projections, and reported changes. `do_not_sum_group` identifies overlaps.

### `data/processed/provider_profiles.csv`

Display and interpretation metadata by provider: type, linked forecast entity, geography, latest known vintage, summary, availability, overlap warning, and notes.

### `data/processed/data_availability.csv`

Explicit provider/category/metric availability. `available` is Boolean; unavailable rows use `display_status=Not publicly disclosed`. Vintage, geography, and notes explain why a category is or is not available.

### `data/processed/source_metadata.csv`

Source registry keyed by `source_id`, with publisher, source type, vintage, URL, local path status, SHA-256 when locally archived, page/table, geography, authority status, and notes.

### `data/processed/data_quality_events.csv`

Correction, quarantine, and scope events. It records event/provider/year, affected and untouched fields, rule ID, status, confirmation status, reason, source document/sheet, and notes.

## Reference layers

### `data/reference/county_provider_lookup.csv`

Many-to-many county/provider relationships. `county_fips` is a five-character South Carolina FIPS code. Each row includes provider identity/type, `relationship_type`, `coverage_type`, confidence, source/year/URL, `non_exhaustive`, and notes. There are no demand, exclusivity, percent-coverage, or boundary-allocation fields.

### `data/reference/large_load_projects.csv`

Contextual public project announcements. `announced_mw` is populated only when a source explicitly reports MW; `mw_display` carries the public wording. `mw_source_type`, `grid_or_onsite`, `utility_forecast_link_status`, and `context_only` prevent announcements from being interpreted as accepted utility forecasts.

## Santee processed outputs

### `data/processed/santee_historical_monthly.csv`

Monthly 2016–2025 historical fields. For affected Central and Transformer Losses/Other energy and coincident-peak columns, both `_raw` and corrected fields are retained. `ncp_central_mw` is untouched. Correction and source-row fields preserve the audit trail.

### `data/processed/santee_historical_categories.csv`

Annual historical category facts with metric/category/scenario/value/unit plus geography, vintage, reported status, correction status, and source location.

### `data/processed/santee_forecast_wide.csv`

Source-shaped 2025–2044 forecast table for peak and annual energy by published category and scenario.

### `data/processed/santee_forecast_scenarios.csv`

Long-form total/scenario series used by the deep dive: including PLL, excluding PLL, PLL-only, high, and low.

### `data/processed/santee_forecast_categories.csv`

Long-form Santee category forecast facts. Direct residential and commercial use the single category `direct_residential_commercial_combined`.

### `data/processed/santee_correction_events.csv`

The three year-specific `SANTEE_HIST_001` audit events.

## Compatibility and presentation files

`outputs/` retains the original prototype filenames used by the dashboard/export workflow. `outputs/sc_energy_map_demo.html` is a static review artifact, not a substitute for the interactive Streamlit app.
