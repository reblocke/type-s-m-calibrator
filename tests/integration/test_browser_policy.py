from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = PROJECT_ROOT / "web"


def _relative_luminance(hex_color: str) -> float:
    channels = [int(hex_color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(first: str, second: str) -> float:
    light, dark = sorted(
        (_relative_luminance(first), _relative_luminance(second)),
        reverse=True,
    )
    return (light + 0.05) / (dark + 0.05)


def test_worker_is_manifest_driven_and_verifies_before_import() -> None:
    worker = (WEB_ROOT / "pyodide_worker.js").read_text(encoding="utf-8")

    assert "manifest.packages" in worker
    assert "fileRecord.path" in worker
    assert "PACKAGE_FILES" not in worker
    assert "fetchVerifiedBundle()" in worker
    assert worker.index("await fetchVerifiedBundle()") < worker.index("importScripts(")
    assert worker.index("failed integrity verification") < worker.index("loadPyodide(")
    assert "if (bundle.manifest.pyodide_packages.length > 0)" in worker


def test_production_web_code_has_no_persistence_telemetry_or_input_urls() -> None:
    production = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(WEB_ROOT.rglob("*"))
        if path.is_file() and "assets/py" not in path.as_posix()
    )

    forbidden_fragments = [
        "localStorage",
        "sessionStorage",
        "document.cookie",
        "location.search",
        "location.hash",
        "sendBeacon",
        "gtag(",
        "analytics",
        "console.log",
    ]
    assert not [fragment for fragment in forbidden_fragments if fragment in production]
    assert "new URL(path" not in production
    for argument in re.findall(r"fetch\(([^,)]+)", production):
        assert "input" not in argument.lower()


def test_ui_contains_accessibility_conditioning_and_scope_landmarks() -> None:
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    css = (WEB_ROOT / "styles.css").read_text(encoding="utf-8")

    assert 'aria-live="polite"' in html
    assert 'role="alert"' in html
    for control in (
        "effect-type",
        "precision-mode",
        "standard-error",
        "null-value",
        "selection-rule",
        "alpha",
        "information-multiplier",
        "true-effect-scenarios",
        "observed-estimate",
        "grid-points",
    ):
        assert re.search(rf'<label for="{control}">', html)
    assert "<details>" in html and "<summary>" in html
    assert 'class="skip-link"' in html
    assert ":focus-visible" in css
    assert "Every x-axis value is an assumed true effect" in html
    assert "not posterior probabilities" in html
    assert "does not estimate truth" in html


def test_focus_indicator_has_non_text_contrast_against_page_surfaces() -> None:
    css = (WEB_ROOT / "styles.css").read_text(encoding="utf-8")
    focus = re.search(r"--focus:\s*(#[0-9a-fA-F]{6})", css)

    assert focus is not None
    assert _contrast(focus.group(1), "#ffffff") >= 3
    assert _contrast(focus.group(1), "#f4f6f7") >= 3
    assert "outline: 3px solid var(--focus)" in css


def test_all_six_exact_rule_keys_and_alpha_neutral_labels_are_visible() -> None:
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")

    for rule in (
        "two_sided_p_lt_alpha",
        "one_sided_positive_p_lt_alpha",
        "one_sided_negative_p_lt_alpha",
        "ci_excludes_null_in_beneficial_direction",
        "estimate_exceeds_mcid_and_p_lt_alpha",
        "ci_excludes_mcid",
    ):
        assert f'value="{rule}"' in html
    assert "p &lt; alpha" in html
    assert "selected alpha" in html


def test_exports_use_exact_columns_and_uncapped_contract_rows() -> None:
    exports = (WEB_ROOT / "js" / "exports.js").read_text(encoding="utf-8")
    renderers = (WEB_ROOT / "js" / "renderers.js").read_text(encoding="utf-8")

    assert "csvFromRows(columns, rows)" in exports
    for column in (
        "true_effect_display",
        "true_effect_working",
        "standardized_true_effect",
        "selected_claim_probability",
        "type_s",
        "type_m",
        "expected_selected_abs_z",
        "observed_exaggeration",
    ):
        assert f'key: "{column}"' in exports
    assert "gridRows(response)" in exports
    assert "Math.min(value, cap)" not in exports
    assert "Math.min(value, cap)" in renderers
    assert "plot_exaggeration_cap_applied" in renderers
    assert "clipped in this plot only" in renderers
    assert "exportDashboardPng" in exports
    assert "exportFigurePng" in exports
    assert "globalThis.Plotly.toImage(plotElement" in exports
    assert "copyText" in exports
    assert "filenameSlug" in exports


def test_fixed_panels_and_conditional_observed_panel_are_rendered_textually() -> None:
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    renderers = (WEB_ROOT / "js" / "renderers.js").read_text(encoding="utf-8")

    for label in (
        "A. Selected-claim probability",
        "B. Type S",
        "C. Type M",
        "D. Observed exaggeration",
    ):
        assert label in renderers
    assert "observed_exaggeration_optional !== null" in renderers
    assert 'id="scenario-table"' in html
    assert "Current SE" in renderers
    assert "hypothetical scenario SE" in renderers
    assert "Copyable reviewer/scenario text" in html
    for heading in (
        "Scenario / source note",
        "Delta vs null (SE)",
        "Selected-claim probability (%)",
        "Type S among selected (%)",
        "Type M (x-fold)",
        "Observed exaggeration (x-fold)",
        "Expected selected |Z|",
    ):
        assert heading in html
    assert "formatProbability(scenario.selected_claim_probability)" in renderers
    assert "formatProbability(scenario.type_s)" in renderers
    assert "Type M is computed on the log scale." in renderers
    assert "an em dash is explained by the row" in renderers


def test_app_invalidates_stale_calculations_before_accepting_new_state() -> None:
    app = (WEB_ROOT / "app.js").read_text(encoding="utf-8")
    renderers = (WEB_ROOT / "js" / "renderers.js").read_text(encoding="utf-8")
    submit = app.split('form.addEventListener("submit"', maxsplit=1)[1].split(
        'form.addEventListener("reset"',
        maxsplit=1,
    )[0]

    assert "let calculationGeneration = 0" in app
    assert submit.index("const generation = ++calculationGeneration") < submit.index(
        "const { errors, request } = readRequest(form)"
    )
    assert submit.index("clearResultState();") < submit.index(
        "const { errors, request } = readRequest(form)"
    )
    assert app.count("generation !== calculationGeneration") >= 3
    assert "calculationGeneration += 1" in app
    assert "elements.result.hidden = false" not in renderers


def test_reviewer_default_uses_ticket_priority_and_merged_sources() -> None:
    renderers = (WEB_ROOT / "js" / "renderers.js").read_text(encoding="utf-8")

    custom = 'hasSource(scenario, "user_assumed_true_effect")'
    reference = 'hasSource(scenario, "reference_threshold")'
    observed = 'hasSource(scenario, "observed_estimate_as_truth")'
    assert renderers.index(custom) < renderers.index(reference) < renderers.index(observed)
    assert "scenario.merged_sources.includes(source)" in renderers
    assert 'candidate.merged_sources.includes("reference_threshold")' in renderers


def test_public_web_surface_has_no_out_of_scope_controls() -> None:
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8").lower()

    for forbidden_name in (
        'name="target_power"',
        'name="max_type_s"',
        'name="max_type_m"',
        'name="required_information"',
        'name="compatibility"',
        'name="relative_likelihood"',
    ):
        assert forbidden_name not in html
