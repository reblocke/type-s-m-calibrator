from __future__ import annotations

import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_makefile_exposes_required_commands() -> None:
    makefile = (PROJECT_ROOT / "Makefile").read_text(encoding="utf-8")

    for target in [
        "stage-web:",
        "fmt:",
        "fmt-check:",
        "lint:",
        "test:",
        "scientific-test:",
        "e2e:",
        "verify:",
        "serve:",
        "clean:",
    ]:
        assert target in makefile


def test_ci_and_pages_use_repository_targets() -> None:
    ci = (PROJECT_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    pages = (PROJECT_ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")

    assert "make fmt-check" in ci
    assert "make lint" in ci
    assert "make test" in ci
    assert "make e2e" in ci
    assert "make e2e-webkit-smoke" in ci
    assert "make stage-web" in pages
    assert "web" in pages


def test_generated_stage_is_ignored_and_not_tracked() -> None:
    gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "web/assets/py/" in gitignore
    assert (
        subprocess.run(
            ["git", "check-ignore", "web/assets/py/manifest.json"],
            cwd=PROJECT_ROOT,
            check=False,
        ).returncode
        == 0
    )
    assert (
        subprocess.run(
            ["git", "ls-files", "web/assets/py"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        == ""
    )


def test_public_documents_have_no_unresolved_template_prompts() -> None:
    public_files = [
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / "CHANGELOG.md",
        PROJECT_ROOT / "CITATION.cff",
        PROJECT_ROOT / "llms.txt",
        *sorted((PROJECT_ROOT / "docs").glob("*.md")),
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in public_files)

    assert "AUTHOR ACTION REQUIRED" not in combined
    assert "replace-me" not in combined.lower()
    assert "arithmetic demonstration" not in combined.lower()
    assert "engineering scaffold only" not in combined.lower()


def test_related_wald_tools_are_exact_in_readme_and_footer() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    html = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")
    footer = html.split("<footer>", maxsplit=1)[1].split("</footer>", maxsplit=1)[0]
    links = [
        "https://reblocke.github.io/wald-inference-tools/",
        "https://reblocke.github.io/precision-guardrail-planner/",
        "https://reblocke.github.io/conf_curve_likelihood/",
        "https://github.com/reblocke/type-s-m-calibrator",
        "https://github.com/reblocke/wald-inference-core/releases/tag/v0.3.0",
    ]

    assert "## Related Wald tools" in readme
    assert "<h2>Related Wald tools</h2>" in footer
    for link in links:
        assert link in readme
        assert f'href="{link}"' in footer
    assert "wald-inference Core v0.3.0" in readme
    assert "wald-inference Core v0.3.0" in footer
    assert "[Privacy](docs/PRIVACY.md)" in readme
    assert (
        'href="https://github.com/reblocke/type-s-m-calibrator/blob/main/docs/PRIVACY.md"' in footer
    )
