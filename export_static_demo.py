"""Export a standalone local HTML review artifact without county-demand allocation."""

from __future__ import annotations

from pathlib import Path

import plotly.io as pio

from src.chart_builder import santee_series_chart
from src.data_loaders import load_dashboard_data
from src.map_builder import build_statewide_relationship_map
from src.selection import relationships_for_county

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "outputs" / "sc_energy_map_demo.html"


def main() -> None:
    data = load_dashboard_data()
    county = "Richland"
    relationships = relationships_for_county(data.county_lookup, county)
    fig_map = build_statewide_relationship_map(
        data.counties, data.county_lookup, county, data.geojson
    )
    fig_map.update_layout(
        title={"text": "Statewide sourced provider relationships<br><sup>2024 EIA-861 county presence · relationship count, not demand</sup>"},
        margin={"r": 0, "t": 70, "l": 0, "b": 0},
    )
    fig_chart = santee_series_chart(
        data.santee_demand, "winter_peak_mw", "forecast", 2040
    )
    if fig_chart is None:
        raise RuntimeError("Expected Santee forecast series was not available")

    map_html = pio.to_html(
        fig_map, full_html=False, include_plotlyjs=True, div_id="statewide-relationship-map"
    )
    chart_html = pio.to_html(
        fig_chart, full_html=False, include_plotlyjs=False, div_id="santee-forecast-chart"
    )
    provider_list = "".join(
        f"<li><strong>{row.provider_name}</strong> — {row.provider_type}; "
        f"{row.relationship_type}; {row.coverage_type}</li>"
        for row in relationships.itertuples(index=False)
    )
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SC Electricity Provider Explorer — Static Review</title>
<style>
body {{ font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; color: #1f2933; background: #fbfaf8; }}
header {{ background: #73000a; color: white; padding: 32px max(24px, 5vw); }}
main {{ max-width: 1500px; margin: 0 auto; padding: 26px; }}
.grid {{ display: grid; grid-template-columns: 1.05fr 1fr; gap: 22px; }}
.card {{ background: white; border: 1px solid #e5e0db; border-radius: 12px; padding: 16px; box-shadow: 0 2px 9px rgba(0,0,0,.05); }}
.note {{ background: #f7f3ec; border-left: 5px solid #73000a; padding: 14px 18px; margin-bottom: 22px; }}
small {{ color: #5f6b76; }}
@media (max-width: 1000px) {{ .grid {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<header><h1>South Carolina Electricity Provider Explorer</h1><p>Static local review artifact</p></header>
<main>
<div class="note"><strong>Interpretation:</strong> County shading is sourced provider-relationship count only. The Santee chart is a utility-system forecast shown separately. No provider total is measured or allocated as county demand.</div>
<div class="grid"><section class="card">{map_html}</section><section class="card">{chart_html}</section></div>
<section class="card"><h2>{county} County sourced relationships</h2><ul>{provider_list}</ul><small>Non-exhaustive; relationships may cover only part of the county and are not exclusive.</small></section>
</main>
</body>
</html>"""
    OUTPUT.parent.mkdir(exist_ok=True)
    clean_html = "\n".join(line.rstrip() for line in html.splitlines()) + "\n"
    OUTPUT.write_text(clean_html, encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
