"""Initialize and verify a disposable downstream app."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def _run(command: list[str], *, cwd: Path, environment: dict[str, str]) -> None:
    subprocess.run(command, cwd=cwd, env=environment, check=True)


def _copy_template(source: Path, destination: Path) -> None:
    excluded = {
        ".git",
        ".hypothesis",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "playwright-report",
        "py",
        "test-results",
    }
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns(*excluded, "*.egg-info"),
    )


def _forbidden_source_terms() -> tuple[str, ...]:
    return (
        "conf" + "curve",
        "Stew" + "art Light",
        "sod" + "ium",
        "Type" + " S/M",
    )


def _assert_no_source_app_terms(project_root: Path) -> None:
    violations: list[str] = []
    ignored = {".git", ".venv", "__pycache__"}
    for path in project_root.rglob("*"):
        if not path.is_file() or any(part in ignored for part in path.parts):
            continue
        try:
            contents = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        lowered = contents.lower()
        for term in _forbidden_source_terms():
            if term.lower() in lowered:
                violations.append(f"{path.relative_to(project_root)}:{term}")
    if violations:
        raise RuntimeError("Source-app terms remain: " + ", ".join(violations))


def run_self_test(*, browser: str | None) -> dict[str, object]:
    source_root = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment.pop("VIRTUAL_ENV", None)
    with tempfile.TemporaryDirectory(prefix="scientific-applet-template-self-test-") as temporary:
        target = Path(temporary) / "example-applet"
        _copy_template(source_root, target)
        _run(
            [
                "uv",
                "run",
                "python",
                "scripts/initialize_template.py",
                "--repository-name",
                "example-applet",
                "--distribution-name",
                "example-applet",
                "--import-name",
                "example_applet",
                "--app-title",
                "Example Applet",
                "--description",
                "Disposable generic app used to verify template initialization",
            ],
            cwd=target,
            environment=environment,
        )
        _run(["git", "init", "-b", "main"], cwd=target, environment=environment)
        _run(
            ["git", "config", "user.name", "Template Self Test"],
            cwd=target,
            environment=environment,
        )
        _run(
            ["git", "config", "user.email", "template-self-test@example.invalid"],
            cwd=target,
            environment=environment,
        )
        _run(["git", "add", "."], cwd=target, environment=environment)
        _run(
            ["git", "commit", "-m", "Initialize disposable app"],
            cwd=target,
            environment=environment,
        )
        _run(["uv", "sync", "--locked"], cwd=target, environment=environment)
        _run(["make", "stage-web"], cwd=target, environment=environment)
        _run(
            ["uv", "run", "pytest", "-q", "-m", "not e2e"],
            cwd=target,
            environment=environment,
        )
        if browser is not None:
            _run(
                [
                    "uv",
                    "run",
                    "pytest",
                    "-q",
                    "tests/e2e/test_applet.py::test_worker_loads_and_calculates",
                    "--browser",
                    browser,
                ],
                cwd=target,
                environment=environment,
            )
        _assert_no_source_app_terms(target)
        manifest = target / "web/assets/py/manifest.json"
        if not manifest.is_file() or not (target / "web/.nojekyll").is_file():
            raise RuntimeError("Disposable Pages artifact is incomplete.")
        parsed_manifest = json.loads(manifest.read_text(encoding="utf-8"))
        return {
            "browser": browser,
            "bundle_sha256": parsed_manifest["bundle_sha256"],
            "initialized_repository": "example-applet",
            "packages": len(parsed_manifest["packages"]),
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--browser", choices=["chromium", "webkit"])
    arguments = parser.parse_args()
    report = run_self_test(browser=arguments.browser)
    print(json.dumps(report, allow_nan=False, sort_keys=True))


if __name__ == "__main__":
    main()
