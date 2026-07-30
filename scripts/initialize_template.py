"""One-time, guarded identity initializer for this repository template."""

from __future__ import annotations

import argparse
import json
import keyword
import re
import shutil
from pathlib import Path
from typing import Any

IDENTITY_FILENAME = ".template-identity.json"
REPORT_FILENAME = ".applet-template-initialized.json"
TEXT_SUFFIXES = {
    ".cff",
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
TEXT_FILENAMES = {"Makefile", "uv.lock"}
SKIPPED_PARTS = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "playwright-report",
    "test-results",
}
TEMPLATE_ONLY_PATHS = (
    Path(".github/workflows/template-self-test.yml"),
    Path("docs/TEMPLATE_PROVENANCE.md"),
    Path("scripts/self_test_template.py"),
    Path("tests/template"),
)
REPOSITORY_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DISTRIBUTION_PATTERN = re.compile(r"^[a-z0-9]+(?:[-_.][a-z0-9]+)*$")
IMPORT_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


class InitializationError(RuntimeError):
    """The requested template identity is unsafe or incomplete."""


def _nonempty_text(value: str, *, label: str, maximum: int) -> str:
    normalized = " ".join(value.split())
    if not normalized or len(normalized) > maximum:
        raise InitializationError(f"{label} must contain 1-{maximum} characters.")
    if any(character in normalized for character in "\r\n<>"):
        raise InitializationError(f"{label} contains unsupported characters.")
    return normalized


def validate_identity(
    *,
    repository_name: str,
    distribution_name: str,
    import_name: str,
    app_title: str,
    description: str,
) -> dict[str, str]:
    """Validate and normalize all user-controlled identity values."""

    if REPOSITORY_PATTERN.fullmatch(repository_name) is None:
        raise InitializationError(
            "repository-name must be lowercase kebab-case (letters, numbers, hyphens)."
        )
    if DISTRIBUTION_PATTERN.fullmatch(distribution_name) is None:
        raise InitializationError("distribution-name must be a normalized Python project name.")
    if IMPORT_PATTERN.fullmatch(import_name) is None or keyword.iskeyword(import_name):
        raise InitializationError("import-name must be a lowercase, non-keyword Python identifier.")
    return {
        "app_title": _nonempty_text(app_title, label="app-title", maximum=100),
        "description": _nonempty_text(description, label="description", maximum=240),
        "distribution_name": distribution_name,
        "import_name": import_name,
        "repository_name": repository_name,
    }


def _load_identity(project_root: Path) -> dict[str, Any]:
    path = project_root / IDENTITY_FILENAME
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InitializationError(f"Could not read {IDENTITY_FILENAME}.") from exc
    if (
        not isinstance(raw, dict)
        or set(raw) != {"initialized", "schema_version", "values"}
        or raw["schema_version"] != 1
        or not isinstance(raw["initialized"], bool)
        or not isinstance(raw["values"], dict)
        or set(raw["values"])
        != {
            "app_title",
            "description",
            "distribution_name",
            "import_name",
            "repository_name",
        }
        or not all(isinstance(value, str) and value for value in raw["values"].values())
    ):
        raise InitializationError(f"{IDENTITY_FILENAME} has an invalid schema.")
    return raw


def _text_paths(project_root: Path) -> list[Path]:
    paths: list[Path] = []
    for path in project_root.rglob("*"):
        if not path.is_file() or any(part in SKIPPED_PARTS for part in path.parts):
            continue
        if any(part.endswith(".egg-info") for part in path.parts):
            continue
        if path.name == REPORT_FILENAME:
            continue
        if "web/assets/py" in path.relative_to(project_root).as_posix():
            continue
        if path.suffix in TEXT_SUFFIXES or path.name in TEXT_FILENAMES:
            paths.append(path)
    return sorted(paths)


def _replace_text(
    project_root: Path,
    old_values: dict[str, str],
    new_values: dict[str, str],
) -> list[dict[str, Any]]:
    replacements = [
        (old_values[key], new_values[key])
        for key in old_values
        if old_values[key] != new_values[key]
    ]
    replacements.sort(key=lambda pair: len(pair[0]), reverse=True)
    changed: list[dict[str, Any]] = []
    for path in _text_paths(project_root):
        original = path.read_text(encoding="utf-8")
        revised = original
        count = 0
        for old, new in replacements:
            occurrences = revised.count(old)
            revised = revised.replace(old, new)
            count += occurrences
        if revised != original:
            path.write_text(revised, encoding="utf-8")
            changed.append(
                {
                    "path": path.relative_to(project_root).as_posix(),
                    "replacements": count,
                }
            )
    return changed


def _rename_import_package(
    project_root: Path,
    *,
    old_import_name: str,
    new_import_name: str,
) -> list[dict[str, str]]:
    if old_import_name == new_import_name:
        return []
    source = project_root / "src" / old_import_name
    destination = project_root / "src" / new_import_name
    if not source.is_dir():
        raise InitializationError(f"Expected package directory is missing: {source}.")
    if destination.exists():
        raise InitializationError(f"Requested package directory already exists: {destination}.")
    source.rename(destination)
    return [
        {
            "from": source.relative_to(project_root).as_posix(),
            "to": destination.relative_to(project_root).as_posix(),
        }
    ]


def _remove_template_only_paths(project_root: Path) -> list[str]:
    removed: list[str] = []
    for relative in TEMPLATE_ONLY_PATHS:
        path = project_root / relative
        if not path.exists():
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        removed.append(relative.as_posix())
    return removed


def _find_unresolved_values(
    project_root: Path,
    old_values: dict[str, str],
    new_values: dict[str, str],
) -> list[str]:
    unresolved: list[str] = []
    for path in _text_paths(project_root):
        contents = path.read_text(encoding="utf-8")
        for label, value in old_values.items():
            if value == new_values[label]:
                continue
            if value in contents:
                unresolved.append(f"{path.relative_to(project_root).as_posix()}:{label}")
    return unresolved


def initialize(project_root: Path, new_values: dict[str, str], *, force: bool) -> dict[str, Any]:
    """Initialize a repository in place without entering or modifying `.git`."""

    project_root = project_root.resolve()
    identity = _load_identity(project_root)
    old_values: dict[str, str] = identity["values"]
    if identity["initialized"] and not force:
        raise InitializationError(
            "This repository was already initialized; pass --force to rerun explicitly."
        )

    changed_files = _replace_text(project_root, old_values, new_values)
    renames = _rename_import_package(
        project_root,
        old_import_name=old_values["import_name"],
        new_import_name=new_values["import_name"],
    )
    removed = _remove_template_only_paths(project_root)
    identity_path = project_root / IDENTITY_FILENAME
    identity_path.write_text(
        json.dumps(
            {
                "initialized": True,
                "schema_version": 1,
                "values": new_values,
            },
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    unresolved = _find_unresolved_values(project_root, old_values, new_values)
    if unresolved:
        raise InitializationError(
            "Required template identity values remain unresolved: " + ", ".join(unresolved)
        )
    report = {
        "changed_files": changed_files,
        "identity": new_values,
        "removed_template_only_paths": removed,
        "renamed_paths": renames,
        "unresolved_required_values": [],
    }
    (project_root / REPORT_FILENAME).write_text(
        json.dumps(report, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Apply a one-time identity to a repository created from this template."
    )
    parser.add_argument("--repository-name", required=True)
    parser.add_argument("--distribution-name", required=True)
    parser.add_argument("--import-name", required=True)
    parser.add_argument("--app-title", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Explicitly permit rerunning an already initialized repository.",
    )
    return parser


def main() -> None:
    arguments = _parser().parse_args()
    try:
        identity = validate_identity(
            repository_name=arguments.repository_name,
            distribution_name=arguments.distribution_name,
            import_name=arguments.import_name,
            app_title=arguments.app_title,
            description=arguments.description,
        )
        report = initialize(
            Path(__file__).resolve().parents[1],
            identity,
            force=arguments.force,
        )
    except InitializationError as exc:
        raise SystemExit(f"Initialization failed: {exc}") from exc
    print(json.dumps(report, allow_nan=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
