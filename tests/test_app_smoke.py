"""Noninteractive Streamlit smoke coverage for every primary section."""

from streamlit.testing.v1 import AppTest


def _run_section(section: str) -> AppTest:
    app = AppTest.from_file("app.py", default_timeout=30).run()
    if section != "Statewide Provider Explorer":
        app.radio[0].set_value(section).run()
    return app


def test_statewide_page_smoke() -> None:
    app = _run_section("Statewide Provider Explorer")
    assert not app.exception
    assert app.title[0].value == "Statewide Provider Explorer"
    assert any(
        "This dashboard helps users identify electricity providers" in block.value
        for block in app.markdown
    )


def test_santee_page_smoke() -> None:
    app = _run_section("Santee Cooper Deep Dive")
    assert not app.exception
    assert app.title[0].value == "Santee Cooper Deep Dive"
    assert any("What is potential large load?" in block.value for block in app.markdown)
    vintage = next(box for box in app.selectbox if box.label == "Forecast vintage")
    assert vintage.value == "Santee Cooper 2026 Triennial IRP"


def test_santee_historical_state_smoke() -> None:
    app = _run_section("Santee Cooper Deep Dive")
    app.radio[0].set_value("Historical").run()
    assert not app.exception
    assert app.radio[0].value == "Historical"


def test_methodology_page_smoke() -> None:
    app = _run_section("Methodology and Data Quality")
    assert not app.exception
    assert app.title[0].value == "Methodology and Data Quality"
    assert any("What this dashboard can tell you" in block.value for block in app.markdown)
    assert any("What this dashboard cannot tell you" in block.value for block in app.markdown)
