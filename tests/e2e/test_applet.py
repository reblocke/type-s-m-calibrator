from __future__ import annotations

import csv
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect


def _ready(page: Page, app_url: str) -> None:
    page.goto(app_url)
    expect(page.locator("#runtime-status")).to_have_attribute(
        "data-state",
        "ready",
        timeout=120_000,
    )


def _calculate(page: Page) -> None:
    page.locator("#calculate").click()
    expect(page.locator("#runtime-status")).to_have_text(
        "Calculation complete.",
        timeout=30_000,
    )


def _rendered_rectangles(page: Page, selector: str) -> list[dict[str, float | str]]:
    return page.locator(selector).evaluate_all(
        """(elements) => elements
          .filter((element) => {
            const rect = element.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0;
          })
          .map((element) => {
            const rect = element.getBoundingClientRect();
            return {
              bottom: rect.bottom,
              left: rect.left,
              right: rect.right,
              text: element.textContent.trim(),
              top: rect.top,
            };
          })"""
    )


def _assert_nonoverlapping(rectangles: list[dict[str, float | str]]) -> None:
    for index, first in enumerate(rectangles):
        for second in rectangles[index + 1 :]:
            horizontal_overlap = min(float(first["right"]), float(second["right"])) - max(
                float(first["left"]), float(second["left"])
            )
            vertical_overlap = min(float(first["bottom"]), float(second["bottom"])) - max(
                float(first["top"]), float(second["top"])
            )
            assert horizontal_overlap <= 0 or vertical_overlap <= 0, (
                f"{first['text']!r} overlaps {second['text']!r}: "
                f"{horizontal_overlap=}, {vertical_overlap=}"
            )


def test_worker_loads_and_calculates(page: Page, app_url: str) -> None:
    _ready(page, app_url)
    _calculate(page)

    expect(page.locator("#result-summary")).to_contain_text("3 assumed-true-effect scenarios")
    expect(page.locator("#scenario-table tbody tr")).to_have_count(3)
    expect(page.locator("#plot .plot-container")).to_be_visible()
    expect(page.locator("#plot")).to_contain_text("A. Selected-claim probability")
    expect(page.locator("#plot")).to_contain_text("B. Type S")
    expect(page.locator("#plot")).to_contain_text("C. Type M")
    expect(page.locator("#observed-panel-note")).to_be_visible()
    expect(page.locator("#runtime-versions")).to_contain_text("type-s-m-calibrator 0.1.5")
    expect(page.locator("#runtime-versions")).to_contain_text("wald-inference 0.4.2")


def test_rule_controls_are_exactly_activated(page: Page, app_url: str) -> None:
    _ready(page, app_url)
    expect(page.locator("#claim-direction-field")).to_be_hidden()
    expect(page.locator("#claim-threshold-field")).to_be_hidden()

    page.locator("#selection-rule").select_option("ci_excludes_mcid")
    expect(page.locator("#claim-direction-field")).to_be_visible()
    expect(page.locator("#claim-threshold-field")).to_be_visible()
    expect(page.locator("#active-rule-controls")).to_contain_text(
        "Alpha, claim direction, claim threshold"
    )

    page.locator("#selection-rule").select_option("one_sided_negative_p_lt_alpha")
    expect(page.locator("#claim-direction-field")).to_be_hidden()
    expect(page.locator("#claim-threshold-field")).to_be_hidden()
    expect(page.locator("#active-rule-controls")).to_have_text("Active rule controls: Alpha.")


@pytest.mark.parametrize(
    "rule",
    [
        "two_sided_p_lt_alpha",
        "one_sided_positive_p_lt_alpha",
        "one_sided_negative_p_lt_alpha",
        "ci_excludes_null_in_beneficial_direction",
        "estimate_exceeds_mcid_and_p_lt_alpha",
        "ci_excludes_mcid",
    ],
)
def test_all_six_rules_calculate_in_browser(
    page: Page,
    app_url: str,
    rule: str,
) -> None:
    _ready(page, app_url)
    page.locator("#selection-rule").select_option(rule)
    if rule in {
        "estimate_exceeds_mcid_and_p_lt_alpha",
        "ci_excludes_mcid",
    }:
        page.locator("#claim-threshold").fill("0.2")
    _calculate(page)

    expect(page.locator("#rule-summary")).to_contain_text("alpha")
    expect(page.locator("#scenario-table tbody tr")).not_to_have_count(0)


def test_ci_mode_and_ratio_mode_are_explicit(page: Page, app_url: str) -> None:
    _ready(page, app_url)
    page.locator("#precision-mode").select_option("ci_95")
    expect(page.locator("#direct-se-fields")).to_be_hidden()
    expect(page.locator("#ci-fields")).to_be_visible()
    _calculate(page)
    expect(page.locator("#precision-summary")).to_contain_text("reported 95% CI")

    page.locator("#effect-type").select_option("odds_ratio")
    expect(page.locator("#null-value")).to_have_value("1")
    expect(page.locator("#ci-lower")).to_have_value("1.2")
    expect(page.locator("#ci-upper")).to_have_value("2.7")
    expect(page.locator("#axis-spacing-note")).to_contain_text("logarithmic")
    _calculate(page)
    expect(page.locator("#precision-summary")).to_contain_text("reported 95% CI")


def test_validation_error_and_worker_recovery(page: Page, app_url: str) -> None:
    _ready(page, app_url)
    page.locator("#standard-error").fill("0")
    page.locator("#calculate").click()

    expect(page.locator("#error-summary")).to_contain_text("must be positive")
    expect(page.locator("#runtime-status")).to_have_attribute("data-state", "error")

    page.locator("#standard-error").fill("0.2")
    _calculate(page)

    expect(page.locator("#runtime-status")).to_have_text("Calculation complete.")
    expect(page.locator("#result-summary")).to_contain_text("assumed-true-effect scenarios")


def test_input_errors_link_to_controls(page: Page, app_url: str) -> None:
    _ready(page, app_url)
    page.locator("#null-value").fill("")
    page.locator("#calculate").click()

    expect(page.locator("#error-summary")).to_be_visible()
    expect(page.locator("#error-summary a")).to_have_attribute("href", "#null-value")
    expect(page.locator("#null-value")).to_have_attribute("aria-invalid", "true")


def test_optional_observed_estimate_adds_panel_d_and_reviewer_text(
    page: Page,
    app_url: str,
) -> None:
    page.context.grant_permissions(
        ["clipboard-read", "clipboard-write"],
        origin=app_url.rstrip("/"),
    )
    _ready(page, app_url)
    page.locator("#observed-estimate").fill("0.42")
    _calculate(page)

    expect(page.locator("#scenario-table tbody tr")).to_have_count(4)
    expect(page.locator("#plot")).to_contain_text("D. Observed exaggeration")
    expect(page.locator("#observed-panel-note")).to_be_hidden()
    expect(page.locator("#warnings-list")).to_contain_text("not Type M")
    page.locator("#copy-reviewer").click()
    expect(page.locator("#runtime-status")).to_have_text("Reviewer text copied.")
    clipboard = page.evaluate("navigator.clipboard.readText()")
    assert "not posterior probabilities" in clipboard


def test_csv_png_and_caption_exports(page: Page, app_url: str, tmp_path: Path) -> None:
    page.context.grant_permissions(
        ["clipboard-read", "clipboard-write"],
        origin=app_url.rstrip("/"),
    )
    _ready(page, app_url)
    _calculate(page)

    with page.expect_download() as csv_info:
        page.locator("#export-csv").click()
    csv_download = csv_info.value
    csv_path = tmp_path / csv_download.suggested_filename
    csv_download.save_as(csv_path)
    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert rows[0] == [
        "true_effect_display",
        "true_effect_working",
        "standardized_true_effect",
        "selected_claim_probability",
        "type_s",
        "type_m",
        "expected_selected_abs_z",
        "observed_exaggeration",
    ]
    assert len(rows) == 402
    assert all(row[-1] == "" for row in rows[1:])

    for selector, suffix in [
        ("#export-figure", "-figure.png"),
        ("#export-dashboard", "-dashboard.png"),
    ]:
        with page.expect_download(timeout=30_000) as png_info:
            page.locator(selector).click()
        download = png_info.value
        png_path = tmp_path / download.suggested_filename
        download.save_as(png_path)
        assert download.suggested_filename.endswith(suffix)
        assert png_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")

    page.locator("#copy-caption").click()
    expect(page.locator("#runtime-status")).to_have_text("Caption copied.")
    clipboard = page.evaluate("navigator.clipboard.readText()")
    assert "assumed true effect" in clipboard
    assert "not posterior probabilities" in clipboard


def test_plot_cap_is_disclosed_but_csv_values_are_uncapped(
    page: Page,
    app_url: str,
    tmp_path: Path,
) -> None:
    _ready(page, app_url)
    page.locator("#standard-error").fill("1")
    page.locator("#true-effect-scenarios").fill("0.000001")
    page.locator("summary").click()
    page.locator("#plausible-min").fill("-0.01")
    page.locator("#plausible-max").fill("0.01")
    _calculate(page)

    expect(page.locator("#warnings-list")).to_contain_text("Plot traces are capped at 10x")
    with page.expect_download() as csv_info:
        page.locator("#export-csv").click()
    csv_path = tmp_path / csv_info.value.suggested_filename
    csv_info.value.save_as(csv_path)
    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    type_m_values = [float(row["type_m"]) for row in rows if row["type_m"]]
    assert max(type_m_values) > 10


def test_mobile_keyboard_and_privacy_smoke(page: Page, app_url: str) -> None:
    requests: list[tuple[str, str | None]] = []
    page.context.on("request", lambda request: requests.append((request.url, request.post_data)))
    page.set_viewport_size({"width": 390, "height": 844})
    _ready(page, app_url)
    initial_url = page.url
    page.locator("#observed-estimate").fill("12345.67891")
    page.locator("#effect-type").focus()
    page.keyboard.press("Tab")
    expect(page.locator("#precision-mode")).to_be_focused()
    _calculate(page)

    assert page.url == initial_url
    assert page.evaluate("localStorage.length") == 0
    assert page.evaluate("sessionStorage.length") == 0
    assert page.evaluate("document.cookie") == ""
    serialized_requests = "\n".join(f"{url}\n{body or ''}" for url, body in requests)
    assert "12345.67891" not in serialized_requests
    expect(page.locator(".controls")).to_be_visible()
    expect(page.locator(".results")).to_be_visible()
    assert page.evaluate(
        "document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )


def test_mobile_plot_labels_are_contained_and_nonoverlapping(
    page: Page,
    app_url: str,
) -> None:
    page.set_viewport_size({"width": 390, "height": 844})
    _ready(page, app_url)
    page.locator("#observed-estimate").fill("0.42")
    _calculate(page)

    title_and_panels = _rendered_rectangles(
        page,
        "#plot .gtitle, #plot .annotation-text, #plot .legendtext",
    )
    x_axis_titles = _rendered_rectangles(
        page,
        "#plot .xtitle, #plot .x2title, #plot .x3title, #plot .x4title",
    )
    y_axis_titles = _rendered_rectangles(
        page,
        "#plot .ytitle, #plot .y2title, #plot .y3title, #plot .y4title",
    )
    assert len(title_and_panels) == 6
    assert len(x_axis_titles) == 4
    assert len(y_axis_titles) == 4

    for rectangle in title_and_panels + x_axis_titles + y_axis_titles:
        assert float(rectangle["left"]) >= 0, rectangle
        assert float(rectangle["right"]) <= 390, rectangle
    _assert_nonoverlapping(title_and_panels)
    _assert_nonoverlapping(x_axis_titles)
    _assert_nonoverlapping(y_axis_titles)


def test_compact_plot_follows_container_width_and_category_crossing(
    page: Page,
    app_url: str,
) -> None:
    page.set_viewport_size({"width": 850, "height": 900})
    _ready(page, app_url)
    page.locator("#observed-estimate").fill("0.42")
    _calculate(page)

    plot = page.locator("#plot")
    assert page.viewport_size["width"] > 480
    assert float(plot.evaluate("(element) => element.getBoundingClientRect().width")) <= 480
    expect(plot).to_have_attribute("data-plot-layout", "compact")
    assert page.evaluate("() => document.querySelector('#plot').layout.title.text").startswith(
        "Forward calibration across<br>assumed true effects"
    )

    page.evaluate(
        """() => {
          const originalReact = globalThis.Plotly.react.bind(globalThis.Plotly);
          globalThis.__responsiveReactCalls = [];
          globalThis.Plotly.react = async (...args) => {
            globalThis.__responsiveReactCalls.push(args[0].dataset.plotLayout);
            return originalReact(...args);
          };
        }"""
    )

    page.set_viewport_size({"width": 870, "height": 900})
    page.wait_for_timeout(250)
    assert float(plot.evaluate("(element) => element.getBoundingClientRect().width")) <= 480
    assert page.evaluate("globalThis.__responsiveReactCalls.length") == 0

    page.set_viewport_size({"width": 1200, "height": 900})
    page.wait_for_function(
        "() => document.querySelector('#plot').getBoundingClientRect().width > 480"
    )
    expect(plot).to_have_attribute("data-plot-layout", "noncompact")
    assert page.evaluate("globalThis.__responsiveReactCalls") == ["noncompact"]

    page.set_viewport_size({"width": 1250, "height": 900})
    page.wait_for_timeout(250)
    assert page.evaluate("globalThis.__responsiveReactCalls") == ["noncompact"]

    page.set_viewport_size({"width": 850, "height": 900})
    page.wait_for_function(
        "() => document.querySelector('#plot').getBoundingClientRect().width <= 480"
    )
    expect(plot).to_have_attribute("data-plot-layout", "compact")
    assert page.evaluate("globalThis.__responsiveReactCalls") == [
        "noncompact",
        "compact",
    ]


def test_mobile_png_exports_use_temporary_noncompact_plot(
    page: Page,
    app_url: str,
    tmp_path: Path,
) -> None:
    page.set_viewport_size({"width": 390, "height": 844})
    _ready(page, app_url)
    page.locator("#observed-estimate").fill("0.42")
    _calculate(page)

    plot = page.locator("#plot")
    expect(plot).to_have_attribute("data-plot-layout", "compact")
    live_state_before = page.evaluate(
        """() => {
          const livePlot = document.querySelector("#plot");
          return {
            data: JSON.stringify(livePlot.data),
            title: livePlot.layout.title.text,
          };
        }"""
    )
    page.evaluate(
        """() => {
          const originalToImage = globalThis.Plotly.toImage.bind(globalThis.Plotly);
          globalThis.__plotExportChecks = [];
          globalThis.Plotly.toImage = async (target, options) => {
            const livePlot = document.querySelector("#plot");
            globalThis.__plotExportChecks.push({
              dataMatchesLive: JSON.stringify(target.data) === JSON.stringify(livePlot.data),
              height: target.layout.height,
              liveLayout: livePlot.dataset.plotLayout,
              panelTitles: target.layout.annotations.map((annotation) => annotation.text),
              purpose: target.dataset.plotPurpose,
              targetIsLive: target === livePlot,
              targetLayout: target.dataset.plotLayout,
              title: target.layout.title.text,
              width: target.layout.width,
              xTitle: target.layout.xaxis.title.text,
            });
            return originalToImage(target, options);
          };
        }"""
    )

    for selector in ("#export-figure", "#export-dashboard"):
        with page.expect_download(timeout=30_000) as download_info:
            page.locator(selector).click()
        download = download_info.value
        download.save_as(tmp_path / download.suggested_filename)
        expect(page.locator('[data-plot-purpose="export"]')).to_have_count(0)

    export_checks = page.evaluate("globalThis.__plotExportChecks")
    assert [(check["width"], check["height"]) for check in export_checks] == [
        (1600, 1200),
        (1200, 900),
    ]
    for check in export_checks:
        assert check["purpose"] == "export"
        assert check["targetLayout"] == "noncompact"
        assert check["liveLayout"] == "compact"
        assert check["targetIsLive"] is False
        assert check["dataMatchesLive"] is True
        assert check["title"].startswith("Forward calibration across assumed true effects")
        assert "numeric values remain uncapped" in check["title"]
        assert "<br>" not in check["panelTitles"][0]
        assert "<br>" not in check["xTitle"]

    expect(plot).to_have_attribute("data-plot-layout", "compact")
    assert (
        page.evaluate(
            """() => {
          const livePlot = document.querySelector("#plot");
          return {
            data: JSON.stringify(livePlot.data),
            title: livePlot.layout.title.text,
          };
        }"""
        )
        == live_state_before
    )
