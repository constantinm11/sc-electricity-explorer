"""Plotly chart builders with a deterministic light presentation layer."""

from __future__ import annotations

import pandas as pd
import plotly.express as px

from src.config import GARNET, GOLD, GRID, INK, MUTED_INK, TEAL, WHITE
from src.display import axis_label, display_value, humanize

SERIES_COLORS = [GARNET, TEAL, GOLD, "#536878", "#8C5A74", "#A66A00"]


def _light_layout(fig, *, height: int) -> None:
    fig.update_layout(
        template="plotly_white",
        height=height,
        paper_bgcolor=WHITE,
        plot_bgcolor=WHITE,
        font={"color": INK, "size": 13},
        title={"font": {"color": INK, "size": 18}},
        margin={"r": 18, "t": 70, "l": 18, "b": 24},
        legend={
            "orientation": "h",
            "y": -0.22,
            "title": None,
            "font": {"color": INK},
            "bgcolor": "rgba(255,255,255,0.9)",
        },
        hoverlabel={"bgcolor": WHITE, "bordercolor": GARNET, "font": {"color": INK}},
    )
    fig.update_xaxes(
        gridcolor=GRID,
        linecolor=GRID,
        tickfont={"color": INK},
        title_font={"color": INK},
        showline=True,
    )
    fig.update_yaxes(
        gridcolor=GRID,
        linecolor=GRID,
        tickfont={"color": INK},
        title_font={"color": INK},
        tickformat=",.0f",
        exponentformat="none",
        showexponent="none",
        separatethousands=True,
        showline=True,
    )


def _display_chart_values(chart: pd.DataFrame, metric: str) -> tuple[pd.DataFrame, str, str]:
    shown = chart.copy()
    source_unit = str(shown["unit"].iloc[0])
    shown["display_value"] = shown["value"].map(
        lambda value: display_value(value, source_unit, metric)[0]
    )
    shown_unit = display_value(0, source_unit, metric)[1]
    return shown, shown_unit, axis_label(metric, source_unit)


def provider_forecast_chart(rows: pd.DataFrame, metric: str, vintage: str, scenario: str):
    chart = rows.loc[
        rows["metric"].eq(metric)
        & rows["forecast_vintage"].eq(vintage)
        & rows["scenario"].eq(scenario)
        & rows["year"].notna()
        & rows["value"].notna()
    ].copy()
    if chart.empty:
        return None
    chart, shown_unit, y_label = _display_chart_values(chart, metric)
    chart["Category"] = chart["category"].map(humanize)
    geography = str(chart["geography_scope"].iloc[0])
    hover = {"display_value": ":,.1f", "Category": True, "year": True}
    if chart["year"].nunique() == 1:
        fig = px.bar(
            chart.sort_values("Category"),
            x="Category",
            y="display_value",
            color="Category",
            labels={"Category": "Category", "display_value": y_label},
            color_discrete_sequence=SERIES_COLORS,
            hover_data=hover,
        )
    else:
        fig = px.line(
            chart.sort_values(["Category", "year"]),
            x="year",
            y="display_value",
            color="Category",
            markers=True,
            labels={"year": "Year", "display_value": y_label, "Category": "Category"},
            color_discrete_sequence=SERIES_COLORS,
            hover_data=hover,
        )
    fig.update_layout(
        title={"text": f"{humanize(metric)}<br><sup>{geography} · {vintage}</sup>"}
    )
    _light_layout(fig, height=430)
    fig.update_traces(hovertemplate="<b>%{fullData.name}</b><br>Year: %{x}<br>Value: %{y:,.1f} " + shown_unit + "<extra></extra>")
    return fig


def santee_series_chart(rows: pd.DataFrame, metric_key: str, dataset: str, selected_year: int):
    chart = rows.loc[rows["metric_key"].eq(metric_key) & rows["dataset"].eq(dataset)].copy()
    if dataset == "historical":
        chart = chart.loc[chart["scenario_key"].eq("actual")]
    else:
        scenarios = ["including_pll", "excluding_pll", "pll_only", "high_case", "low_case"]
        chart = chart.loc[chart["scenario_key"].isin(scenarios)]
    if chart.empty:
        return None
    chart, shown_unit, y_label = _display_chart_values(chart, metric_key)
    chart["Scenario"] = chart["scenario_key"].map(humanize)
    geography = str(chart["geography_scope"].iloc[0])
    vintage = str(chart["forecast_vintage"].iloc[0])
    fig = px.line(
        chart.sort_values(["Scenario", "year"]),
        x="year",
        y="display_value",
        color="Scenario",
        markers=True,
        labels={"year": "Year", "display_value": y_label, "Scenario": "Scenario"},
        color_discrete_sequence=SERIES_COLORS,
    )
    fig.add_vline(x=selected_year, line_dash="dot", opacity=0.55, line_color=MUTED_INK)
    fig.update_layout(
        title={"text": f"{humanize(metric_key)}<br><sup>{geography} · {vintage}</sup>"}
    )
    _light_layout(fig, height=455)
    fig.update_traces(hovertemplate="<b>%{fullData.name}</b><br>Year: %{x}<br>Value: %{y:,.1f} " + shown_unit + "<extra></extra>")
    return fig


def historical_category_chart(rows: pd.DataFrame, metric: str):
    chart = rows.loc[rows["metric"].eq(metric)].copy()
    if chart.empty:
        return None
    chart, shown_unit, y_label = _display_chart_values(chart, metric)
    chart["Category"] = chart["category"].map(humanize)
    fig = px.line(
        chart.sort_values(["Category", "year"]),
        x="year",
        y="display_value",
        color="Category",
        markers=True,
        labels={"year": "Year", "display_value": y_label, "Category": "Category"},
        color_discrete_sequence=SERIES_COLORS,
    )
    fig.update_layout(
        title={
            "text": "Historical category series<br><sup>Santee Cooper utility system · Historical 2016–2025</sup>"
        }
    )
    _light_layout(fig, height=440)
    fig.update_traces(hovertemplate="<b>%{fullData.name}</b><br>Year: %{x}<br>Value: %{y:,.1f} " + shown_unit + "<extra></extra>")
    return fig
