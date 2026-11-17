"""Streamlit entry point for the South Carolina electricity decision-support dashboard."""

from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from src.chart_builder import historical_category_chart, provider_forecast_chart, santee_series_chart
from src.config import GARNET, MISSING_LABEL, SECTIONS
from src.data_loaders import DashboardData, load_dashboard_data
from src.display import format_value, humanize, humanize_table, option_map
from src.map_builder import build_santee_presence_map, build_statewide_relationship_map
from src.selection import forecasts_for_provider, relationships_for_county


st.set_page_config(
    page_title="SC Electricity Provider Explorer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _style() -> None:
    """Small component styles layered on top of the deterministic light theme."""
    st.markdown(
        f"""
        <style>
        :root {{
            --garnet: {GARNET}; --ink: #1F2933; --muted: #52606D;
            --canvas: #F7F5F2; --paper: #FFFFFF; --border: #DDD7D0;
        }}
        [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
            background-color: var(--canvas); color: var(--ink);
        }}
        [data-testid="stHeader"] {{ background-color: rgba(247,245,242,.96); }}
        [data-testid="stSidebar"] {{
            background-color: #EFEAE4; color: var(--ink); border-right: 1px solid var(--border);
        }}
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span, [data-testid="stSidebar"] h2 {{ color: var(--ink); }}
        .block-container {{ max-width: 1480px; padding-top: 4.25rem; padding-bottom: 2rem; }}
        h1, h2, h3 {{ color: var(--ink); letter-spacing: -.02em; }}
        h1 {{ color: var(--garnet); margin-bottom: .35rem; }}
        p, label, [data-testid="stCaptionContainer"], .stCaption {{ color: var(--ink); }}
        [data-testid="stCaptionContainer"] p, .stCaption p {{ color: var(--muted) !important; }}
        [data-testid="stAlert"] {{ color: var(--ink); border: 1px solid var(--border); }}
        [data-testid="stAlert"] * {{ color: var(--ink) !important; }}
        [data-testid="stExpander"] {{
            background: var(--paper); color: var(--ink); border: 1px solid var(--border); border-radius: 8px;
        }}
        [data-testid="stExpander"] * {{ color: var(--ink); }}
        div[data-baseweb="select"] > div {{
            background-color: var(--paper) !important; color: var(--ink) !important;
            border-color: #AFA7A0 !important;
        }}
        div[data-baseweb="select"] * {{ color: var(--ink) !important; }}
        div[data-baseweb="popover"] ul, div[data-baseweb="menu"] {{
            background-color: var(--paper) !important; color: var(--ink) !important;
        }}
        div[role="radiogroup"] label, div[role="radiogroup"] p {{ color: var(--ink) !important; }}
        [data-testid="stDataFrame"] {{ background: var(--paper); border-radius: 8px; }}
        .eyebrow {{ color: var(--garnet); font-weight: 800; font-size: .76rem;
            letter-spacing: .1em; text-transform: uppercase; margin-bottom: .2rem; }}
        .intro {{ color: var(--ink); font-size: 1.08rem; line-height: 1.55; max-width: 960px;
            margin: 0 0 1rem; }}
        .section-kicker {{ color: var(--garnet); font-weight: 750; font-size: .82rem;
            letter-spacing: .06em; text-transform: uppercase; margin: .2rem 0 .1rem; }}
        .guide-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: .65rem; margin: .7rem 0 1.25rem; }}
        .guide-step {{ background: var(--paper); color: var(--ink); border: 1px solid var(--border);
            border-radius: 9px; padding: .75rem .85rem; line-height: 1.35; }}
        .step-number {{ display: inline-flex; align-items: center; justify-content: center; width: 1.55rem;
            height: 1.55rem; border-radius: 50%; background: var(--garnet); color: white;
            font-weight: 800; margin-right: .45rem; }}
        .summary-card {{ background: var(--paper); color: var(--ink); border: 1px solid var(--border);
            border-top: 4px solid var(--garnet); border-radius: 9px; padding: .78rem .9rem; min-height: 108px; }}
        .summary-label {{ color: var(--muted); font-weight: 750; font-size: .73rem;
            letter-spacing: .055em; text-transform: uppercase; margin-bottom: .35rem; }}
        .summary-value {{ color: var(--ink); font-weight: 720; font-size: .98rem; line-height: 1.3; }}
        .summary-note {{ color: var(--muted); font-size: .8rem; line-height: 1.3; margin-top: .3rem; }}
        .availability-badge {{ display: inline-block; background: #EEE9E3; color: #4A5562;
            border: 1px solid #D8D0C8; border-radius: 999px; padding: .18rem .5rem;
            font-size: .78rem; font-weight: 700; }}
        .scope-card {{ border-left: 5px solid var(--garnet); background: #F1ECE6; color: var(--ink);
            padding: .72rem .9rem; border-radius: 5px; margin: .5rem 0 .8rem; line-height: 1.45; }}
        .scope-card *, .plain-note *, .correction-note *, .interpretation * {{ color: var(--ink); }}
        .plain-note {{ background: #EDF5F6; color: var(--ink); border: 1px solid #C9DEE1;
            border-radius: 8px; padding: .7rem .85rem; margin: .55rem 0 .8rem; }}
        .correction-note {{ background: #FFF7E6; color: var(--ink); border: 1px solid #E7CF99;
            border-left: 4px solid #B7791F; border-radius: 6px; padding: .65rem .8rem; margin: .55rem 0 .9rem;
            font-size: .9rem; line-height: 1.4; }}
        .interpretation {{ background: var(--paper); color: var(--ink); border: 1px solid var(--border);
            border-left: 4px solid var(--garnet); border-radius: 6px; padding: .72rem .85rem; margin: -.1rem 0 .9rem; }}
        .can-card, .cannot-card {{ background: var(--paper); color: var(--ink); border: 1px solid var(--border);
            border-radius: 10px; padding: .9rem 1rem; min-height: 168px; }}
        .can-card {{ border-top: 5px solid #167D8D; }} .cannot-card {{ border-top: 5px solid var(--garnet); }}
        .can-card h3, .cannot-card h3 {{ margin-top: 0; font-size: 1.05rem; }}
        .can-card li, .cannot-card li {{ color: var(--ink); margin-bottom: .35rem; }}
        @media (max-width: 900px) {{ .guide-grid {{ grid-template-columns: 1fr; }} .summary-card {{ min-height: auto; }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def _load() -> DashboardData:
    return load_dashboard_data()


def _card(label: str, value: object, note: str = "", unavailable: bool = False) -> None:
    shown_value = escape(str(value))
    value_html = (
        f'<span class="availability-badge">{shown_value}</span>' if unavailable else shown_value
    )
    note_html = f'<div class="summary-note">{escape(note)}</div>' if note else ""
    st.markdown(
        f'<div class="summary-card"><div class="summary-label">{escape(label)}</div>'
        f'<div class="summary-value">{value_html}</div>{note_html}</div>',
        unsafe_allow_html=True,
    )


def _source_caption(row: pd.Series) -> None:
    source_document = row.get("source_document", row.get("source_file", MISSING_LABEL))
    st.caption(
        f"Source: {source_document} · {row.get('source_page', MISSING_LABEL)} · "
        f"{row.get('source_table', MISSING_LABEL)} · "
        f"Status: {humanize(row.get('reported_or_modeled', MISSING_LABEL))}"
    )


def _planning_system_name(data: DashboardData, provider_id: str) -> str:
    match = data.providers.loc[data.providers["provider_id"].eq(provider_id), "provider_name"]
    return str(match.iloc[0]) if not match.empty else humanize(provider_id)


def statewide_explorer(data: DashboardData) -> None:
    st.markdown('<div class="eyebrow">Statewide decision support</div>', unsafe_allow_html=True)
    st.title("Statewide Provider Explorer")
    st.markdown(
        '<div class="intro">This dashboard helps users identify electricity providers associated with a '
        'South Carolina county and review the published planning forecasts relevant to those providers. '
        '<strong>County records show provider presence—not measured county electricity demand.</strong></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="guide-grid">
          <div class="guide-step"><span class="step-number">1</span><strong>Select a county.</strong></div>
          <div class="guide-step"><span class="step-number">2</span><strong>Review its documented provider relationships.</strong></div>
          <div class="guide-step"><span class="step-number">3</span><strong>Select a provider to explore its published planning forecast.</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-kicker">County context</div>', unsafe_allow_html=True)
    st.subheader("Find providers associated with a county")
    county_names = sorted(data.counties["county_name"].tolist())
    selected_county = st.selectbox(
        "South Carolina county", county_names, index=county_names.index("Richland")
    )
    relationships = relationships_for_county(data.county_lookup, selected_county)

    map_col, rel_col = st.columns([1.38, 1], gap="large")
    with map_col:
        st.plotly_chart(
            build_statewide_relationship_map(
                data.counties, data.county_lookup, selected_county, data.geojson
            ),
            width="stretch",
            key="statewide_relationship_map",
        )
        st.caption(
            "Color represents the number of sourced provider relationships—not electricity demand, "
            "market share, percent coverage, or an exact service boundary. The dark outline marks the selected county."
        )
    with rel_col:
        st.subheader(f"{selected_county} County relationships")
        st.markdown(
            f'<div class="scope-card"><strong>{len(relationships)} documented relationships</strong><br>'
            "This lookup is non-exhaustive. A provider may serve only part of a county, and multiple providers may be present.</div>",
            unsafe_allow_html=True,
        )
        rel_display = relationships[
            ["provider_name", "provider_type", "relationship_type", "coverage_type"]
        ].copy()
        rel_display["relationship_type"] = rel_display["relationship_type"].map(humanize)
        rel_display["coverage_type"] = rel_display["coverage_type"].map(humanize)
        rel_display = rel_display.rename(
            columns={
                "provider_name": "Provider",
                "provider_type": "Provider type",
                "relationship_type": "Relationship",
                "coverage_type": "Coverage",
            }
        )
        st.dataframe(rel_display, width="stretch", hide_index=True, height=315)
        with st.expander("Relationship provenance and detailed caveats"):
            details = relationships[
                ["provider_name", "relationship_type", "coverage_type", "confidence", "source_year", "source_url", "notes"]
            ]
            st.dataframe(
                humanize_table(details, ["relationship_type", "coverage_type", "confidence"]),
                width="stretch",
                hide_index=True,
            )

    st.divider()
    st.markdown('<div class="section-kicker">Provider planning forecast</div>', unsafe_allow_html=True)
    st.subheader("Explore the planning forecast relevant to a provider")
    st.markdown(
        f'<div class="scope-card"><strong>Important:</strong> The forecast below keeps its published '
        f'utility or planning-system geography. It is relevant to the selected provider, but it is '
        f'<strong>not a {escape(selected_county)} County total</strong>.</div>',
        unsafe_allow_html=True,
    )
    provider_options = dict(zip(relationships["provider_name"], relationships["provider_id"]))
    selected_name = st.selectbox(
        "Provider relationship", list(provider_options), key="statewide_provider"
    )
    selected_provider = provider_options[selected_name]
    forecast_provider_id, forecasts = forecasts_for_provider(
        data.forecasts, data.providers, selected_provider
    )
    profile_rows = data.profiles.loc[data.profiles["provider_id"].eq(selected_provider)]
    profile = profile_rows.iloc[0] if not profile_rows.empty else None

    vintage = MISSING_LABEL
    metric = None
    scenario = None
    selected_rows = pd.DataFrame()
    if not forecasts.empty:
        control_cols = st.columns(3)
        with control_cols[0]:
            vintage = st.selectbox(
                "Forecast vintage", sorted(forecasts["forecast_vintage"].unique()), key="provider_vintage"
            )
        vintage_rows = forecasts.loc[forecasts["forecast_vintage"].eq(vintage)]
        metric_options = option_map(sorted(vintage_rows["metric"].unique()))
        with control_cols[1]:
            metric_label = st.selectbox("Forecast measure", list(metric_options), key="provider_metric")
        metric = metric_options[metric_label]
        metric_rows = vintage_rows.loc[vintage_rows["metric"].eq(metric)]
        scenario_options = option_map(sorted(metric_rows["scenario"].unique()))
        with control_cols[2]:
            scenario_label = st.selectbox("Forecast scenario", list(scenario_options), key="provider_scenario")
        scenario = scenario_options[scenario_label]
        selected_rows = metric_rows.loc[metric_rows["scenario"].eq(scenario)].copy()

    provider_type = str(profile["provider_type"]) if profile is not None else MISSING_LABEL
    planning_system = _planning_system_name(data, forecast_provider_id)
    geography = (
        str(selected_rows["geography_scope"].iloc[0])
        if not selected_rows.empty
        else (str(profile["geography_scope"]) if profile is not None else MISSING_LABEL)
    )
    card_cols = st.columns(4)
    with card_cols[0]:
        _card("Provider type", provider_type)
    with card_cols[1]:
        _card("Relevant planning system", planning_system)
    with card_cols[2]:
        _card("Forecast vintage", vintage, unavailable=vintage == MISSING_LABEL)
    with card_cols[3]:
        _card("Geography covered", geography)

    if forecasts.empty:
        st.info(
            "A detailed numeric planning forecast is not publicly disclosed for this provider in the release sources. "
            "Its documented county or supplier relationship remains available above."
        )
    else:
        chart = provider_forecast_chart(forecasts, str(metric), str(vintage), str(scenario))
        if chart is not None:
            st.plotly_chart(chart, width="stretch", key="provider_forecast_chart")
            st.markdown(
                f'<div class="interpretation"><strong>How to read this chart:</strong> It shows '
                f'{escape(humanize(metric).lower())} for <strong>{escape(geography)}</strong> from the '
                f'{escape(str(vintage))} source. It should not be interpreted as demand for '
                f'{escape(selected_county)} County.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.info("This source record has no multi-year numeric series suitable for a chart.")
        with st.expander("Forecast values, provenance, and source notes"):
            detail = selected_rows.copy()
            detail["value"] = detail.apply(
                lambda row: format_value(row["value"], row["unit"], row["metric"]), axis=1
            )
            if "year" in detail:
                detail["year"] = detail["year"].map(
                    lambda value: int(value) if pd.notna(value) else MISSING_LABEL
                )
            detail = detail[
                ["year", "metric", "category", "scenario", "value", "geography_scope", "forecast_vintage", "reported_or_modeled", "source_document", "source_page", "source_table", "notes"]
            ]
            st.dataframe(
                humanize_table(
                    detail, ["metric", "category", "scenario", "reported_or_modeled"]
                ),
                width="stretch",
                hide_index=True,
            )
            _source_caption(selected_rows.iloc[0])

    county_projects = data.large_loads.loc[data.large_loads["county_name"].eq(selected_county)]
    with st.expander("Public large-load project context for this county"):
        if county_projects.empty:
            st.write(f"Public project records for this county: **{MISSING_LABEL}**.")
        else:
            project_display = county_projects[
                ["company", "project_name", "mw_display", "grid_or_onsite", "utility_forecast_link_status", "notes", "source_url"]
            ]
            st.dataframe(
                humanize_table(project_display, ["grid_or_onsite", "utility_forecast_link_status"]),
                width="stretch",
                hide_index=True,
            )
        st.caption(
            "Project announcements are contextual records and are not added to utility forecasts. "
            "No MW is inferred from investment dollars or square footage."
        )


def santee_deep_dive(data: DashboardData) -> None:
    st.markdown('<div class="eyebrow">Utility-system analysis</div>', unsafe_allow_html=True)
    st.title("Santee Cooper Deep Dive")
    st.markdown(
        '<div class="intro">Review reported historical demand and published Santee Cooper planning '
        'forecasts. Residential and commercial remain combined exactly as reported by the source.</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="plain-note"><strong>What is potential large load?</strong> Potential Large Load (PLL) '
        'represents prospective very large electricity users included in Santee Cooper planning scenarios. '
        'The with-PLL and without-PLL views show how those prospective loads change the system forecast.</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="correction-note"><strong>Provisional data-quality correction:</strong> In processed '
        'historical data, Central and Transformer Losses/Other energy and coincident-peak labels are swapped '
        'for 2018, 2019, and 2022. Central non-coincident peak is unchanged; source confirmation remains pending.</div>',
        unsafe_allow_html=True,
    )

    view = st.radio("Data period", ["Forecast", "Historical"], horizontal=True)
    dataset = view.lower()
    available = data.santee_demand.loc[data.santee_demand["dataset"].eq(dataset)].copy()
    selected_vintage = None
    if dataset == "forecast":
        vintages = sorted(available["forecast_vintage"].dropna().unique())
        selected_vintage = st.selectbox(
            "Forecast vintage",
            vintages,
            index=len(vintages) - 1,
            key="santee_vintage",
        )
        available = available.loc[available["forecast_vintage"].eq(selected_vintage)].copy()
    metric_values = available["metric_key"].drop_duplicates().tolist()
    metric_options = option_map(metric_values)
    control_cols = st.columns([1, 1, 1.2])
    with control_cols[0]:
        selected_metric_label = st.selectbox("Measure", list(metric_options), key="santee_metric")
    metric_key = metric_options[selected_metric_label]
    metric_rows = available.loc[available["metric_key"].eq(metric_key)]
    scenario_order = ["including_pll", "excluding_pll", "pll_only", "high_case", "low_case", "actual"]
    available_scenarios = set(metric_rows["scenario_key"])
    scenario_values = [value for value in scenario_order if value in available_scenarios]
    scenario_options = option_map(scenario_values)
    with control_cols[1]:
        selected_scenario_label = st.selectbox("Scenario", list(scenario_options), key="santee_scenario")
    scenario_key = scenario_options[selected_scenario_label]
    scenario_rows = metric_rows.loc[metric_rows["scenario_key"].eq(scenario_key)]
    years = sorted(scenario_rows["year"].dropna().astype(int).unique())
    with control_cols[2]:
        selected_year = st.select_slider(
            "Year", options=years, value=(2040 if 2040 in years else max(years)), key="santee_year"
        )
    selected = scenario_rows.loc[scenario_rows["year"].eq(selected_year)].iloc[0]

    st.markdown(
        f'<div class="scope-card"><strong>Planning geography:</strong> {escape(str(selected["geography_scope"]))} · '
        f'<strong>Forecast vintage:</strong> {escape(str(selected["forecast_vintage"]))}<br>'
        'These values describe the Santee Cooper utility system, not any individual county.</div>',
        unsafe_allow_html=True,
    )

    if dataset == "forecast":
        by_scenario = metric_rows.loc[metric_rows["year"].eq(selected_year)].set_index("scenario_key")
        compare_cols = st.columns(3)
        for column, key, label, note in (
            (compare_cols[0], "including_pll", "Including potential large load", "Full published forecast"),
            (compare_cols[1], "excluding_pll", "Excluding potential large load", "System forecast without PLL"),
            (compare_cols[2], "pll_only", "Potential large load only", "Incremental PLL component"),
        ):
            with column:
                if key in by_scenario.index:
                    row = by_scenario.loc[key]
                    _card(label, format_value(row["value"], row["unit"], metric_key), note)
                else:
                    _card(label, MISSING_LABEL, unavailable=True)
    else:
        historical_cols = st.columns(3)
        with historical_cols[0]:
            _card("Selected year", selected_year)
        with historical_cols[1]:
            _card("Reported value", format_value(selected["value"], selected["unit"], metric_key))
        with historical_cols[2]:
            _card("Data status", humanize(selected["reported_or_modeled"]))

    chart = santee_series_chart(available, str(metric_key), dataset, int(selected_year))
    if chart is not None:
        st.plotly_chart(chart, width="stretch", key="santee_series_chart")

    if dataset == "forecast":
        with_row = by_scenario.loc["including_pll"]
        without_row = by_scenario.loc["excluding_pll"]
        pll_row = by_scenario.loc["pll_only"]
        st.markdown(
            f'<div class="interpretation"><strong>{selected_year} interpretation:</strong> The published '
            f'forecast is <strong>{escape(format_value(with_row["value"], with_row["unit"], metric_key))}</strong> '
            f'with potential large load and <strong>{escape(format_value(without_row["value"], without_row["unit"], metric_key))}</strong> '
            f'without it. The PLL-only component is {escape(format_value(pll_row["value"], pll_row["unit"], metric_key))}. '
            'These are Santee Cooper system forecasts, not county totals.</div>',
            unsafe_allow_html=True,
        )
        with st.expander("Scenario values for the selected year"):
            comparison = metric_rows.loc[
                metric_rows["year"].eq(selected_year), ["scenario_key", "value", "unit"]
            ].copy()
            comparison["value"] = comparison.apply(
                lambda row: format_value(row["value"], row["unit"], metric_key), axis=1
            )
            comparison["scenario_key"] = comparison["scenario_key"].map(humanize)
            st.dataframe(
                comparison[["scenario_key", "value"]].rename(
                    columns={"scenario_key": "Scenario", "value": "Value"}
                ),
                width="stretch",
                hide_index=True,
            )
            st.caption(
                "Including PLL equals excluding PLL plus PLL-only, subject to source precision. "
                "High and low are separate modeled cases."
            )
    else:
        category_chart = historical_category_chart(data.santee_historical, "annual_energy")
        if category_chart is not None:
            st.plotly_chart(category_chart, width="stretch", key="santee_category_chart")
        st.markdown(
            '<div class="interpretation"><strong>How to read the historical view:</strong> The main series '
            'shows reported Santee Cooper system demand by year. The category chart uses the provisional '
            'processed correction for 2018, 2019, and 2022; it does not change the reported system total.</div>',
            unsafe_allow_html=True,
        )

    with st.expander("Santee Cooper service-presence map"):
        st.plotly_chart(
            build_santee_presence_map(data.counties, data.county_lookup, data.geojson),
            width="stretch",
            key="santee_presence_map",
        )
        st.caption("Service-presence context only; system totals are not repeated or allocated by county.")
    with st.expander("Source detail and processed-data events"):
        _source_caption(selected)
        events = data.quality_events.loc[data.quality_events["provider_id"].eq("santee_cooper")]
        st.dataframe(
            humanize_table(
                events,
                ["event_id", "provider_id", "event_type", "correction_rule_id", "affected_fields", "untouched_fields", "status", "confirmation_status"],
            ),
            width="stretch",
            hide_index=True,
        )


def methodology(data: DashboardData) -> None:
    st.markdown('<div class="eyebrow">Interpretation guardrails</div>', unsafe_allow_html=True)
    st.title("Methodology and Data Quality")
    st.markdown(
        '<div class="intro">Use this page to understand what the county relationships and planning '
        'forecasts support—and where the public evidence stops.</div>',
        unsafe_allow_html=True,
    )
    can_col, cannot_col = st.columns(2, gap="large")
    with can_col:
        st.markdown(
            """
            <div class="can-card"><h3>What this dashboard can tell you</h3><ul>
            <li>Which sourced provider relationships are associated with a county.</li>
            <li>Which published planning forecast is relevant to a selected provider.</li>
            <li>The geography, vintage, units, scenario, and source status of a forecast.</li>
            <li>Where information is not publicly disclosed or has a documented quality event.</li>
            </ul></div>
            """,
            unsafe_allow_html=True,
        )
    with cannot_col:
        st.markdown(
            """
            <div class="cannot-card"><h3>What this dashboard cannot tell you</h3><ul>
            <li>Measured electricity demand for an individual county.</li>
            <li>Exact subcounty service boundaries, exclusivity, or percent coverage.</li>
            <li>A de-duplicated statewide total from overlapping retail and wholesale forecasts.</li>
            <li>Unpublished project MW, customer-class demand, or utility commitments.</li>
            </ul></div>
            """,
            unsafe_allow_html=True,
        )

    st.subheader("Geography and reported status")
    st.markdown(
        """
        County records are a **many-to-many provider-presence and service-relationship layer**. They do not
        establish exclusive territories, exact subcounty boundaries, coverage percentages, or county demand.
        Provider forecasts remain at their reported utility, planning-area, or Carolinas-wide geography. This
        project contains **no modeled county-demand allocation**.

        “Reported” values reproduce figures from a source table or workbook. “Modeled” values are source-authored
        scenarios or projections, not measurements. Public data-center announcements are a separate contextual
        layer unless a credible source both supplies MW and connects the project to a utility forecast.
        """
    )

    st.subheader("Forecast vintage and double-counting risk")
    st.markdown(
        """
        Forecast vintages are not silently combined. Duke 2023 class forecasts, Duke 2025 and 2026 Carolinas-wide
        forecasts, Santee Cooper 2025 and 2026 forecasts, and Spring 2026 large-load records remain distinct.
        Dominion bridge figures are **changes from a prior
        forecast**, not absolute category demand. Central class values are customer-account counts unless explicit
        energy or capacity units are supplied. Santee, Central, member cooperative, municipal, and supplier totals
        can overlap and must not be summed as independent demand.
        """
    )

    st.subheader("Santee Cooper correction and quarantined sources")
    st.markdown(
        """
        The 2018, 2019, and 2022 Central and Transformer Losses/Other energy and coincident-peak fields are
        provisionally swapped only in processed data; Central non-coincident peak is untouched. The raw workbook
        remains unchanged. The derived `forecasts in peak load with_without PPL.xlsx` workbook is quarantined from
        authoritative ingestion because its provenance and derivation are insufficient for source-of-truth use;
        no unsupported 22/2200% correction was manufactured. The derived historical utilization workbook is also
        quarantined pending regeneration from corrected processed data.
        """
    )

    with st.expander("Data availability by provider and category"):
        availability = data.availability.copy()
        availability["display_status"] = availability["display_status"].replace("", MISSING_LABEL)
        st.dataframe(
            humanize_table(
                availability, ["provider_id", "category", "metric", "display_status"]
            ),
            width="stretch",
            hide_index=True,
        )
    with st.expander("Data-quality event registry"):
        st.dataframe(
            humanize_table(
                data.quality_events,
                ["event_id", "provider_id", "event_type", "correction_rule_id", "affected_fields", "untouched_fields", "status", "confirmation_status"],
            ),
            width="stretch",
            hide_index=True,
        )
    with st.expander("Full source registry"):
        st.dataframe(
            humanize_table(
                data.sources,
                ["source_id", "source_type", "authoritative_status"],
            ),
            width="stretch",
            hide_index=True,
        )


def main() -> None:
    _style()
    data = _load()
    with st.sidebar:
        st.markdown("## SC Electricity")
        st.caption("Provider and planning-system decision support")
        section = st.radio("Navigate", SECTIONS)
        st.divider()
        st.info(
            "County maps show sourced provider relationships only. Provider totals are never presented as measured county demand."
        )
    if section == SECTIONS[0]:
        statewide_explorer(data)
    elif section == SECTIONS[1]:
        santee_deep_dive(data)
    else:
        methodology(data)


if __name__ == "__main__":
    main()
