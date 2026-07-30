"""Build the deterministic, ignored Python bundle consumed by Pyodide."""

from __future__ import annotations

import base64
import hashlib
import importlib.metadata
import importlib.util
import json
import re
import shutil
import subprocess
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
MANIFEST_FILENAME = "manifest.json"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
IGNORED_DIRECTORY_NAMES = {"__pycache__"}
IGNORED_DIRECTORY_SUFFIXES = (".dist-info", ".egg-info")
IGNORED_FILE_SUFFIXES = {".pyc", ".pyo"}


class StagingError(RuntimeError):
    """The locked browser package bundle could not be built safely."""


@dataclass(frozen=True)
class PackageSpec:
    role: str
    distribution: str
    import_name: str
    version: str
    source: str
    artifact_url: str | None = None
    artifact_sha256: str | None = None


@dataclass(frozen=True)
class StageConfig:
    pyodide_version: str
    pyodide_packages: tuple[str, ...]
    packages: tuple[PackageSpec, ...]


def _normalized_distribution_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def load_stage_config(config_path: Path) -> StageConfig:
    """Load and strictly validate the browser-stage configuration."""

    try:
        raw = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise StagingError(f"Could not read stage config {config_path}.") from exc

    if set(raw) != {
        "packages",
        "pyodide_packages",
        "pyodide_version",
        "schema_version",
    }:
        raise StagingError(
            "Stage config must contain schema_version, pyodide_version, pyodide_packages, packages."
        )
    if raw["schema_version"] != SCHEMA_VERSION:
        raise StagingError(f"Stage config schema_version must be {SCHEMA_VERSION}.")
    pyodide_version = raw["pyodide_version"]
    if not isinstance(pyodide_version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", pyodide_version):
        raise StagingError("Stage config pyodide_version must be an exact semantic version.")
    pyodide_packages = raw["pyodide_packages"]
    if (
        not isinstance(pyodide_packages, list)
        or not all(
            isinstance(package, str) and re.fullmatch(r"[A-Za-z0-9_.-]+", package)
            for package in pyodide_packages
        )
        or len(set(pyodide_packages)) != len(pyodide_packages)
    ):
        raise StagingError("Stage config pyodide_packages must be a unique string list.")

    package_rows = raw["packages"]
    if not isinstance(package_rows, list) or not package_rows:
        raise StagingError("Stage config must contain one app package.")

    packages: list[PackageSpec] = []
    seen_roles: set[str] = set()
    seen_imports: set[str] = set()
    allowed_keys = {
        "artifact_sha256",
        "artifact_url",
        "distribution",
        "import_name",
        "role",
        "source",
        "version",
    }
    for index, row in enumerate(package_rows):
        if not isinstance(row, dict) or not set(row).issubset(allowed_keys):
            raise StagingError(f"Package {index} has unknown or invalid keys.")
        required = {"distribution", "import_name", "role", "source", "version"}
        if not required.issubset(row):
            raise StagingError(f"Package {index} is missing required configuration.")
        values = {key: row[key] for key in required}
        if not all(isinstance(value, str) and value for value in values.values()):
            raise StagingError(f"Package {index} fields must be non-empty strings.")
        if NAME_PATTERN.fullmatch(row["import_name"]) is None:
            raise StagingError(f"Package {index} import_name must be one Python identifier.")
        if row["source"] not in {"project", "external"}:
            raise StagingError(f"Package {index} source must be project or external.")
        if row["role"] in seen_roles:
            raise StagingError(f"Duplicate package role: {row['role']}.")
        if row["import_name"] in seen_imports:
            raise StagingError(f"Duplicate package import_name: {row['import_name']}.")
        seen_roles.add(row["role"])
        seen_imports.add(row["import_name"])

        artifact_url = row.get("artifact_url")
        artifact_sha256 = row.get("artifact_sha256")
        if (artifact_url is None) != (artifact_sha256 is None):
            raise StagingError(
                f"Package {index} must configure artifact_url and artifact_sha256 together."
            )
        if artifact_url is not None:
            if not isinstance(artifact_url, str) or not artifact_url.startswith("https://"):
                raise StagingError(f"Package {index} artifact_url must use HTTPS.")
            if (
                not isinstance(artifact_sha256, str)
                or SHA256_PATTERN.fullmatch(artifact_sha256) is None
            ):
                raise StagingError(
                    f"Package {index} artifact_sha256 must be 64 lowercase hex characters."
                )

        packages.append(
            PackageSpec(
                role=row["role"],
                distribution=row["distribution"],
                import_name=row["import_name"],
                version=row["version"],
                source=row["source"],
                artifact_url=artifact_url,
                artifact_sha256=artifact_sha256,
            )
        )

    app_packages = [package for package in packages if package.role == "app"]
    if len(app_packages) != 1 or app_packages[0].source != "project":
        raise StagingError("Stage config must contain exactly one project package with role app.")
    if any(package.source == "project" and package.role != "app" for package in packages):
        raise StagingError("Only the app package may use source = project.")
    return StageConfig(
        pyodide_version=pyodide_version,
        pyodide_packages=tuple(pyodide_packages),
        packages=tuple(packages),
    )


def _source_commit(project_root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise StagingError("Browser staging requires a Git commit.") from exc
    commit = completed.stdout.strip()
    if COMMIT_PATTERN.fullmatch(commit) is None:
        raise StagingError("Browser staging requires a lowercase 40-hex Git commit.")
    return commit


def _distribution(spec: PackageSpec) -> importlib.metadata.Distribution:
    try:
        distribution = importlib.metadata.distribution(spec.distribution)
    except importlib.metadata.PackageNotFoundError as exc:
        raise StagingError(f"Distribution {spec.distribution!r} is not installed.") from exc
    if distribution.version != spec.version:
        raise StagingError(
            f"Installed {spec.distribution!r} version is {distribution.version!r}; "
            f"expected {spec.version!r}."
        )
    return distribution


def _package_root(spec: PackageSpec) -> Path:
    module_spec = importlib.util.find_spec(spec.import_name)
    locations = None if module_spec is None else module_spec.submodule_search_locations
    if locations is None:
        raise StagingError(f"Package {spec.import_name!r} is not importable as a directory.")
    roots = [Path(location) for location in locations]
    if len(roots) != 1 or roots[0].is_symlink():
        raise StagingError(f"Package {spec.import_name!r} must resolve to one non-symlink root.")
    root = roots[0].resolve()
    if not root.is_dir() or not (root / "__init__.py").is_file():
        raise StagingError(f"Package {spec.import_name!r} must be a regular Python package.")
    return root


def _is_ignored(relative_path: Path) -> bool:
    directory_parts = relative_path.parts[:-1]
    if any(part in IGNORED_DIRECTORY_NAMES for part in directory_parts):
        return True
    if any(part.endswith(IGNORED_DIRECTORY_SUFFIXES) for part in directory_parts):
        return True
    return relative_path.suffix in IGNORED_FILE_SUFFIXES


def _source_files(package_root: Path) -> list[Path]:
    files = []
    for path in package_root.rglob("*"):
        if not path.is_file() or _is_ignored(path.relative_to(package_root)):
            continue
        if path.is_symlink():
            raise StagingError(f"Staged package file must not be a symlink: {path}.")
        files.append(path)
    files.sort(key=lambda path: path.relative_to(package_root).as_posix())
    if not files:
        raise StagingError(f"No package files found under {package_root}.")
    return files


def _lock_package(project_root: Path, spec: PackageSpec) -> dict[str, Any]:
    try:
        lock = tomllib.loads((project_root / "uv.lock").read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise StagingError("Could not read uv.lock.") from exc
    expected_name = _normalized_distribution_name(spec.distribution)
    matches = [
        package
        for package in lock.get("package", [])
        if _normalized_distribution_name(str(package.get("name", ""))) == expected_name
    ]
    if len(matches) != 1:
        raise StagingError(f"uv.lock must contain exactly one {spec.distribution!r} entry.")
    [package] = matches
    if package.get("version") != spec.version:
        raise StagingError(f"uv.lock does not pin {spec.distribution!r} {spec.version!r}.")
    return package


def _verify_artifact_provenance(
    project_root: Path,
    distribution: importlib.metadata.Distribution,
    spec: PackageSpec,
) -> None:
    if spec.artifact_url is None:
        return
    package = _lock_package(project_root, spec)
    if package.get("source") != {"url": spec.artifact_url}:
        raise StagingError(f"uv.lock does not use the configured URL for {spec.distribution!r}.")
    expected_wheel = {
        "url": spec.artifact_url,
        "hash": f"sha256:{spec.artifact_sha256}",
    }
    if package.get("wheels") != [expected_wheel]:
        raise StagingError(
            f"uv.lock does not bind {spec.distribution!r} to the configured checksum."
        )

    direct_url_text = distribution.read_text("direct_url.json")
    if direct_url_text is None:
        raise StagingError(f"Installed {spec.distribution!r} lacks direct_url.json.")
    try:
        direct_url = json.loads(direct_url_text)
    except json.JSONDecodeError as exc:
        raise StagingError(f"Installed {spec.distribution!r} has invalid direct_url.json.") from exc
    if not isinstance(direct_url, dict) or direct_url.get("url") != spec.artifact_url:
        raise StagingError(f"Installed {spec.distribution!r} came from an unexpected URL.")
    archive_info = direct_url.get("archive_info")
    recorded_hash = archive_info.get("hash") if isinstance(archive_info, dict) else None
    if recorded_hash not in {None, f"sha256={spec.artifact_sha256}"}:
        raise StagingError(f"Installed {spec.distribution!r} reports an unexpected artifact hash.")


def _record_digest(contents: bytes) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(contents).digest()).rstrip(b"=").decode()


def _verify_external_record(
    distribution: importlib.metadata.Distribution,
    spec: PackageSpec,
    package_root: Path,
    files: list[Path],
) -> None:
    if spec.source != "external":
        return
    distribution_files = distribution.files
    if distribution_files is None:
        raise StagingError(f"Installed {spec.distribution!r} has no RECORD file list.")
    records = {Path(str(record)): record for record in distribution_files}
    for source_path in files:
        relative = source_path.relative_to(package_root)
        record_path = Path(spec.import_name) / relative
        record = records.get(record_path)
        if record is None or record.hash is None or record.hash.mode != "sha256":
            raise StagingError(
                f"Installed {spec.distribution!r} has no SHA-256 RECORD for "
                f"{record_path.as_posix()}."
            )
        contents = source_path.read_bytes()
        if record.size != len(contents) or record.hash.value != _record_digest(contents):
            raise StagingError(f"Installed file differs from RECORD: {record_path.as_posix()}.")


def _package_record(
    project_root: Path,
    destination_root: Path,
    spec: PackageSpec,
) -> dict[str, Any]:
    distribution = _distribution(spec)
    package_root = _package_root(spec)
    if spec.source == "project":
        expected_root = (project_root / "src" / spec.import_name).resolve()
        if package_root != expected_root:
            raise StagingError(
                f"Project package {spec.import_name!r} did not resolve to {expected_root}."
            )
        _lock_package(project_root, spec)
    else:
        _lock_package(project_root, spec)
        _verify_artifact_provenance(project_root, distribution, spec)

    files = _source_files(package_root)
    _verify_external_record(distribution, spec, package_root, files)
    file_records: list[dict[str, Any]] = []
    for source_path in files:
        relative = source_path.relative_to(package_root)
        staged_path = Path(spec.import_name) / relative
        contents = source_path.read_bytes()
        destination = destination_root / staged_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(contents)
        file_records.append(
            {
                "bytes": len(contents),
                "path": staged_path.as_posix(),
                "sha256": hashlib.sha256(contents).hexdigest(),
            }
        )
    package_descriptor = _bundle_descriptor(file_records)
    return {
        "artifact_sha256": spec.artifact_sha256,
        "artifact_url": spec.artifact_url,
        "distribution": spec.distribution,
        "files": file_records,
        "import_name": spec.import_name,
        "package_sha256": hashlib.sha256(package_descriptor.encode()).hexdigest(),
        "role": spec.role,
        "version": spec.version,
    }


def _bundle_descriptor(file_records: list[dict[str, Any]]) -> str:
    return "".join(
        f"{record['path']}\0{record['sha256']}\0{record['bytes']}\n"
        for record in sorted(file_records, key=lambda item: item["path"])
    )


def stage_browser_packages(
    target_root: Path,
    *,
    project_root: Path,
    config_path: Path | None = None,
) -> dict[str, Any]:
    """Atomically replace the generated stage and return its manifest."""

    project_root = project_root.resolve()
    target_root = target_root.resolve()
    config_path = (
        (project_root / "browser-stage.toml") if config_path is None else config_path.resolve()
    )
    config = load_stage_config(config_path)
    target_parent = target_root.parent
    target_parent.mkdir(parents=True, exist_ok=True)
    temporary_root = Path(tempfile.mkdtemp(prefix=".py-stage-", dir=target_parent))
    try:
        packages = [
            _package_record(project_root, temporary_root, package) for package in config.packages
        ]
        all_files = [file for package in packages for file in package["files"]]
        manifest = {
            "bundle_sha256": hashlib.sha256(_bundle_descriptor(all_files).encode()).hexdigest(),
            "packages": packages,
            "pyodide_packages": list(config.pyodide_packages),
            "pyodide_version": config.pyodide_version,
            "schema_version": SCHEMA_VERSION,
            "source_commit": _source_commit(project_root),
        }
        manifest_text = json.dumps(
            manifest,
            allow_nan=False,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        (temporary_root / MANIFEST_FILENAME).write_text(
            f"{manifest_text}\n",
            encoding="utf-8",
        )
        if target_root.exists():
            shutil.rmtree(target_root)
        temporary_root.replace(target_root)
    except Exception:
        if temporary_root.exists():
            shutil.rmtree(temporary_root)
        raise
    return manifest


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    target_root = project_root / "web" / "assets" / "py"
    manifest = stage_browser_packages(target_root, project_root=project_root)
    summary = {
        "bundle_sha256": manifest["bundle_sha256"],
        "manifest": str(target_root / MANIFEST_FILENAME),
        "packages": [
            {
                "distribution": package["distribution"],
                "files": len(package["files"]),
                "package_sha256": package["package_sha256"],
                "version": package["version"],
            }
            for package in manifest["packages"]
        ],
        "source_commit": manifest["source_commit"],
    }
    print(json.dumps(summary, allow_nan=False, sort_keys=True))


if __name__ == "__main__":
    main()
