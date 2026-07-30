from __future__ import annotations

import hashlib
import importlib.metadata
import json
import subprocess
from pathlib import Path

import pytest
from scripts.stage_browser_packages import StagingError, stage_browser_packages

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _descriptor(files: list[dict[str, object]]) -> str:
    return "".join(
        f"{record['path']}\0{record['sha256']}\0{record['bytes']}\n"
        for record in sorted(files, key=lambda item: str(item["path"]))
    )


def test_stage_manifest_records_versions_files_and_hashes(tmp_path: Path) -> None:
    target = tmp_path / "py"
    manifest = stage_browser_packages(target, project_root=PROJECT_ROOT)

    assert json.loads((target / "manifest.json").read_text(encoding="utf-8")) == manifest
    assert manifest["schema_version"] == 1
    assert manifest["pyodide_version"] == "0.29.3"
    assert manifest["pyodide_packages"] == []
    assert (
        manifest["source_commit"]
        == subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )
    [package] = manifest["packages"]
    assert package["role"] == "app"
    assert package["distribution"] == "scientific-applet-template-package"
    assert package["import_name"] == "template_applet"
    assert package["version"] == "0.1.0"
    assert package["artifact_url"] is None
    assert package["artifact_sha256"] is None
    assert package["files"]

    all_files = package["files"]
    for record in all_files:
        contents = (target / record["path"]).read_bytes()
        assert len(contents) == record["bytes"]
        assert hashlib.sha256(contents).hexdigest() == record["sha256"]
    descriptor = _descriptor(all_files)
    assert hashlib.sha256(descriptor.encode()).hexdigest() == package["package_sha256"]
    assert hashlib.sha256(descriptor.encode()).hexdigest() == manifest["bundle_sha256"]


def test_stage_is_deterministic_and_removes_stale_files(tmp_path: Path) -> None:
    target = tmp_path / "py"
    target.mkdir()
    (target / "stale.py").write_text("stale = True\n", encoding="utf-8")

    first = stage_browser_packages(target, project_root=PROJECT_ROOT)
    first_bytes = (target / "manifest.json").read_bytes()
    second = stage_browser_packages(target, project_root=PROJECT_ROOT)

    assert not (target / "stale.py").exists()
    assert second == first
    assert (target / "manifest.json").read_bytes() == first_bytes


def test_stage_fails_on_configured_version_mismatch(tmp_path: Path) -> None:
    config = tmp_path / "browser-stage.toml"
    source = (PROJECT_ROOT / "browser-stage.toml").read_text(encoding="utf-8")
    config.write_text(source.replace('version = "0.1.0"', 'version = "9.9.9"'), encoding="utf-8")

    with pytest.raises(StagingError, match="expected '9.9.9'"):
        stage_browser_packages(
            tmp_path / "py",
            project_root=PROJECT_ROOT,
            config_path=config,
        )


def test_stage_supports_an_external_locked_pure_python_package(tmp_path: Path) -> None:
    version = importlib.metadata.version("hypothesis")
    config = tmp_path / "browser-stage.toml"
    config.write_text(
        (PROJECT_ROOT / "browser-stage.toml").read_text(encoding="utf-8")
        + "\n[[packages]]\n"
        + 'role = "test-core"\n'
        + 'distribution = "hypothesis"\n'
        + 'import_name = "hypothesis"\n'
        + f'version = "{version}"\n'
        + 'source = "external"\n',
        encoding="utf-8",
    )

    manifest = stage_browser_packages(
        tmp_path / "py",
        project_root=PROJECT_ROOT,
        config_path=config,
    )

    assert [package["role"] for package in manifest["packages"]] == ["app", "test-core"]
    assert manifest["packages"][1]["version"] == version
    assert manifest["packages"][1]["files"]
