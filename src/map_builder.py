"""Maps intentionally encode geography relationships, never county demand."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.config import GARNET, INK, TEAL, WHITE


def build_statewide_relationship_map(
    counties: pd.DataFrame, lookup: pd.DataFrame, selected_county: str, geojson: dict
):
    summary = (
        lookup.groupby(["county_fips", "county_name"], as_index=False)
        .agg(
            sourced_relationships=("provider_id", "size"),
        )
        .rename(columns={"county_fips": "fips"})
    )
    map_df = counties.merge(summary, on=["fips", "county_name"], how="left")
    map_df["sourced_relationships"] = map_df["sourced_relationships"].fillna(0).astype(int)
    selected_fips = str(map_df.loc[map_df["county_name"].eq(selected_county), "fips"].iloc[0])

    fig = px.choropleth(
        map_df,
        geojson=geojson,
        locations="fips",
        featureidkey="properties.FIPS",
        color="sourced_relationships",
        color_continuous_scale=["#F5EAEB", "#DDB9BC", "#A54A52", GARNET],
        hover_name="county_name",
        hover_data={
            "fips": False,
            "sourced_relationships": True,
        },
        labels={"sourced_relationships": "Sourced relationships"},
    )
    fig.update_traces(
        marker_line_color=WHITE,
        marker_line_width=0.9,
        hovertemplate="<b>%{hovertext} County</b><br>Sourced provider relationships: %{z}<extra></extra>",
    )
    fig.add_trace(
        go.Choropleth(
            geojson=geojson,
            locations=[selected_fips],
            featureidkey="properties.FIPS",
            z=[1],
            colorscale=[[0, "rgba(255,255,255,0)"], [1, "rgba(255,255,255,0)"]],
            showscale=False,
            marker={"line": {"color": INK, "width": 3.2}},
            hoverinfo="skip",
            name=f"Selected: {selected_county} County",
        )
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor=WHITE,
        font={"color": INK},
        hoverlabel={"bgcolor": WHITE, "bordercolor": GARNET, "font": {"color": INK}},
        height=520,
        margin={"r": 0, "t": 8, "l": 0, "b": 0},
        coloraxis_colorbar={"title": "Sourced<br>relationships", "thickness": 13, "tickfont": {"color": INK}},
        showlegend=False,
    )
    return fig


def build_santee_presence_map(
    counties: pd.DataFrame, lookup: pd.DataFrame, geojson: dict
):
    direct = set(
        lookup.loc[
            lookup["provider_id"].eq("santee_cooper")
            & lookup["relationship_type"].eq("distribution_equipment_presence"),
            "county_fips",
        ]
    )
    map_df = counties.copy()
    map_df["presence"] = map_df["fips"].isin(direct).map(
        {True: "Sourced Santee presence", False: "Other SC county"}
    )
    fig = px.choropleth(
        map_df,
        geojson=geojson,
        locations="fips",
        featureidkey="properties.FIPS",
        color="presence",
        hover_name="county_name",
        hover_data={"fips": False, "presence": True},
        color_discrete_map={
            "Sourced Santee presence": TEAL,
            "Other SC county": "#E9ECEF",
        },
        category_orders={"presence": ["Sourced Santee presence", "Other SC county"]},
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_traces(marker_line_color="white", marker_line_width=0.7)
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor=WHITE,
        font={"color": INK},
        hoverlabel={"bgcolor": WHITE, "bordercolor": GARNET, "font": {"color": INK}},
        height=430,
        margin={"r": 0, "t": 12, "l": 0, "b": 0},
        legend={"orientation": "h", "y": -0.06, "title": None},
    )
    return fig
