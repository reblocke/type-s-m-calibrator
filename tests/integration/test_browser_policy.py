from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = PROJECT_ROOT / "web"


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


def test_ui_contains_accessibility_and_scope_landmarks() -> None:
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    css = (WEB_ROOT / "styles.css").read_text(encoding="utf-8")

    assert 'aria-live="polite"' in html
    assert 'role="alert"' in html
    assert re.search(r'<label for="first-value">', html)
    assert re.search(r'<label for="second-value">', html)
    assert "<details>" in html and "<summary>" in html
    assert 'class="skip-link"' in html
    assert ":focus-visible" in css
    assert "No scientific formula or inference claim is included." in html


def test_exports_use_explicit_columns_and_separate_png_hooks() -> None:
    exports = (WEB_ROOT / "js" / "exports.js").read_text(encoding="utf-8")

    assert "csvFromRows(columns, rows)" in exports
    assert 'key: "label"' in exports
    assert 'key: "value"' in exports
    assert "exportDashboardPng" in exports
    assert "exportFigurePng" in exports
    assert "copyCaption" in exports
    assert "filenameSlug" in exports
