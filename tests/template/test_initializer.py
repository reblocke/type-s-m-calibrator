from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from scripts.initialize_template import (
    InitializationError,
    initialize,
    validate_identity,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _copy_repository(tmp_path: Path) -> Path:
    target = tmp_path / "copy"
    shutil.copytree(
        PROJECT_ROOT,
        target,
        ignore=shutil.ignore_patterns(
            ".git",
            ".hypothesis",
            ".pytest_cache",
            ".ruff_cache",
            ".venv",
            "__pycache__",
            "*.egg-info",
            "py",
            "test-results",
        ),
    )
    (target / ".git").mkdir()
    (target / ".git" / "sentinel").write_text("unchanged\n", encoding="utf-8")
    return target


def _example_identity() -> dict[str, str]:
    return validate_identity(
        repository_name="compatibility-curve",
        distribution_name="compatibility-curve",
        import_name="compatibility_curve",
        app_title="Wald Compatibility Curve",
        description="A deliberately generic initialization test",
    )


def test_initializer_renames_exhausts_identity_and_preserves_git(tmp_path: Path) -> None:
    target = _copy_repository(tmp_path)
    old_identity = json.loads((target / ".template-identity.json").read_text(encoding="utf-8"))[
        "values"
    ]

    report = initialize(target, _example_identity(), force=False)

    assert (target / "src/compatibility_curve/__init__.py").is_file()
    assert not (target / "src/template_applet").exists()
    assert report["unresolved_required_values"] == []
    assert report["changed_files"]
    assert report["renamed_paths"]
    assert (target / ".git" / "sentinel").read_text(encoding="utf-8") == "unchanged\n"
    assert not (target / "tests/template").exists()
    assert not (target / "docs/TEMPLATE_PROVENANCE.md").exists()
    assert not (target / ".github/workflows/template-self-test.yml").exists()
    assert not (target / "scripts/self_test_template.py").exists()

    readable = "\n".join(
        path.read_text(encoding="utf-8")
        for path in target.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and path.name != ".applet-template-initialized.json"
        and path.suffix not in {".pyc"}
        and not any(part.endswith(".egg-info") for part in path.parts)
    )
    for value in old_identity.values():
        assert value not in readable


def test_initializer_refuses_twice_without_force(tmp_path: Path) -> None:
    target = _copy_repository(tmp_path)
    identity = _example_identity()
    initialize(target, identity, force=False)

    with pytest.raises(InitializationError, match="already initialized"):
        initialize(target, identity, force=False)

    report = initialize(target, identity, force=True)
    assert report["changed_files"] == []
    assert report["renamed_paths"] == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("repository_name", "Not Valid"),
        ("distribution_name", "not valid"),
        ("import_name", "not-valid"),
        ("import_name", "class"),
        ("app_title", ""),
        ("description", "<unsafe>"),
    ],
)
def test_initializer_validates_names(field: str, value: str) -> None:
    values = {
        "repository_name": "example-applet",
        "distribution_name": "example-applet",
        "import_name": "example_applet",
        "app_title": "Example Applet",
        "description": "Generic example",
    }
    values[field] = value

    with pytest.raises(InitializationError):
        validate_identity(**values)
