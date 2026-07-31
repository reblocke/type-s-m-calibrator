from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = PROJECT_ROOT / ".github" / "workflows"
GH_CLI_VERSION = "2.93.0"
GH_CLI_LINUX_AMD64_SHA256 = "02d1290eba130e0b896f3709ffff22e1c75a51475ddb70476a85abc6b5807af0"
EXPECTED_ACTION_PINS = {
    "actions/checkout": ("d23441a48e516b6c34aea4fa41551a30e30af803", "6.1.0"),
    "actions/setup-python": ("ece7cb06caefa5fff74198d8649806c4678c61a1", "6.3.0"),
    "astral-sh/setup-uv": ("37802adc94f370d6bfd71619e3f0bf239e1f3b78", "7.6.0"),
    "actions/upload-artifact": ("043fb46d1a93c77aae656e7c1c64a875d1fc6a0a", "7.0.1"),
    "actions/download-artifact": ("3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c", "8.0.1"),
    "actions/configure-pages": ("983d7736d9b0ae728b81ab479565c72886d7745b", "5.0.0"),
    "actions/upload-pages-artifact": ("7b1f4a764d45c48632c6b24a0339c27f5614fb0b", "4.0.0"),
    "actions/deploy-pages": ("d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e", "4.0.5"),
}


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


def test_workflows_pin_reviewed_external_actions_to_full_shas() -> None:
    use_value_pattern = re.compile(r"^\s*(?:-\s+)?uses:\s+(?P<value>\S+)(?:\s+#.*)?$")
    external_use_pattern = re.compile(
        r"^\s*(?:-\s+)?uses:\s+"
        r"(?P<action>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_./-]+)?)"
        r"@(?P<sha>[0-9a-f]{40})"
        r"\s+#\s+v(?P<version>\d+\.\d+\.\d+)\s*$"
    )
    violations: list[str] = []
    seen_pins: dict[str, set[tuple[str, str]]] = {}
    workflows = sorted(
        {*WORKFLOW_ROOT.glob("*.yml"), *WORKFLOW_ROOT.glob("*.yaml")},
    )

    for workflow in workflows:
        for line_number, line in enumerate(
            workflow.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            if "uses:" not in line:
                continue
            parsed_use = use_value_pattern.fullmatch(line)
            if parsed_use is None:
                violations.append(f"{workflow.name}:{line_number}:{line.strip()}")
                continue
            if parsed_use.group("value").startswith("./"):
                continue
            parsed_external = external_use_pattern.fullmatch(line)
            if parsed_external is None:
                violations.append(f"{workflow.name}:{line_number}:{line.strip()}")
                continue
            action = parsed_external.group("action")
            pin = (parsed_external.group("sha"), parsed_external.group("version"))
            seen_pins.setdefault(action, set()).add(pin)

    assert violations == []
    assert seen_pins == {action: {pin} for action, pin in EXPECTED_ACTION_PINS.items()}


def test_workflow_permissions_credentials_and_release_cache_are_fail_closed() -> None:
    ci = (WORKFLOW_ROOT / "ci.yml").read_text(encoding="utf-8")
    pages = (WORKFLOW_ROOT / "pages.yml").read_text(encoding="utf-8")
    release = (WORKFLOW_ROOT / "release.yml").read_text(encoding="utf-8")

    assert "permissions:\n  contents: read" in ci
    assert "group: ci-${{ github.workflow }}-${{ github.ref }}" in ci
    assert "cancel-in-progress: true" in ci
    for job_name in ("test", "e2e-chromium", "e2e-webkit-smoke"):
        assert f"    name: {job_name}" in ci
    assert "permissions: {}" in pages
    assert "build:\n    name: build\n    permissions:\n      contents: read" in pages
    assert (
        "deploy:\n"
        "    name: deploy\n"
        "    needs: build\n"
        "    permissions:\n"
        "      pages: write # Required to publish the verified Pages artifact.\n"
        "      id-token: write # Required for the Pages deployment identity token." in pages
    )
    build_block, deploy_block = pages.split("\n  deploy:", maxsplit=1)
    assert "id-token: write" not in build_block
    assert "pages: write" not in build_block
    assert "actions/configure-pages@" not in build_block
    assert "contents: read" not in deploy_block
    assert "actions/configure-pages@" in deploy_block

    assert "permissions: {}" in release
    assert (
        "verify-and-build:\n    name: verify-and-build\n    permissions:\n      contents: read"
        in release
    )
    verify_build_block, publish_block = release.split("\n  publish:", maxsplit=1)
    assert "enable-cache: true" not in verify_build_block
    assert "enable-cache: false" in verify_build_block
    assert release.count("contents: write") == 1
    assert (
        "publish:\n"
        "    name: publish\n"
        "    needs: verify-and-build\n"
        "    permissions:\n"
        "      contents: write # Required only to create and publish the verified release."
        in release
    )
    assert "attestations: read # Required to verify the immutable release" in publish_block
    assert "attestations: read" not in verify_build_block
    assert "contents: read" not in publish_block

    workflow_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(
            {*WORKFLOW_ROOT.glob("*.yml"), *WORKFLOW_ROOT.glob("*.yaml")},
        )
    )
    checkout_count = workflow_text.count("uses: actions/checkout@")
    assert checkout_count > 0
    assert workflow_text.count("persist-credentials: false") == checkout_count


def test_release_note_guards_reject_whitespace_before_transfer_and_publish(
    tmp_path: Path,
) -> None:
    release = (WORKFLOW_ROOT / "release.yml").read_text(encoding="utf-8")
    verify_build, publish = release.split("\n  publish:", maxsplit=1)

    assert "grep -q '[^[:space:]]' \"$bundle/release-notes.md\"" in verify_build
    assert "grep -q '[^[:space:]]' dist/release-notes.md" in publish
    assert release.count("grep -q '[^[:space:]]'") == 2
    assert 'test -s "$bundle/release-notes.md"' not in release
    assert "test -s dist/release-notes.md" not in release

    notes = tmp_path / "release-notes.md"
    for whitespace_only in ("", "\n", " \t\r\n"):
        notes.write_text(whitespace_only, encoding="utf-8")
        result = subprocess.run(
            ["grep", "-q", "[^[:space:]]", str(notes)],
            check=False,
        )
        assert result.returncode == 1

    notes.write_text("\nRelease notes\n", encoding="utf-8")
    result = subprocess.run(
        ["grep", "-q", "[^[:space:]]", str(notes)],
        check=False,
    )
    assert result.returncode == 0


def test_release_verifies_annotated_main_contained_tag_before_repository_execution() -> None:
    release = (WORKFLOW_ROOT / "release.yml").read_text(encoding="utf-8")
    version_parse = (
        "python -I -c 'import tomllib; "
        'print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])\''
    )

    assert 'git cat-file -t "$GITHUB_REF_NAME"' in release
    assert 'git rev-parse "$GITHUB_REF_NAME^{commit}"' in release
    assert "/git/ref/tags/${GITHUB_REF_NAME}" in release
    assert 'git rev-parse "refs/tags/$GITHUB_REF_NAME"' in release
    assert "--jq '.tag'" in release
    assert ".verification.verified" not in release
    assert ".verification.reason" not in release
    assert "--jq '.object.sha'" in release
    assert "--jq '.object.type'" in release
    assert ')" = "commit"' in release
    assert '"https://github.com/${GITHUB_REPOSITORY}.git"' in release
    assert "+refs/heads/main:refs/remotes/origin/main" in release
    assert 'git merge-base --is-ancestor "$GITHUB_SHA" refs/remotes/origin/main' in release
    assert version_parse in release
    assert 'test "$GITHUB_REF_NAME" = "v${project_version}"' in release

    remote_tag = release.index("/git/ref/tags/${GITHUB_REF_NAME}")
    protected_main = release.index("git merge-base --is-ancestor")
    version = release.index(version_parse)
    install = release.index("uv sync --locked")
    execute = release.index("make verify")
    assert remote_tag < protected_main < version < install < execute


def test_release_is_exact_draft_first_stable_and_postpublish_immutable() -> None:
    release = (WORKFLOW_ROOT / "release.yml").read_text(encoding="utf-8")
    publish = release[release.index("\n  publish:") :]

    assert "/immutable-releases" not in release
    assert "RELEASE_SETTINGS_READ_TOKEN" not in release
    assert publish.count("GH_TOKEN: ${{ github.token }}") == 3
    assert 'git archive --format=tar --prefix="type-s-m-calibrator-${GITHUB_REF_NAME}/"' in release
    assert '"$assets/browser-stage-manifest-${GITHUB_REF_NAME}.json"' in release
    assert "sha256sum --check SHA256SUMS" in release
    assert "actions/upload-artifact@" in release
    assert "actions/download-artifact@" in release
    assert 'test "$(find dist/assets -maxdepth 1 -type f | wc -l)" -eq 3' in release
    assert "--draft" in release
    assert "--verify-tag" in release
    assert "--prerelease" not in release
    assert 'awk -v version="$version"' in release
    assert "--notes-file dist/release-notes.md" in release
    assert "--notes-file CHANGELOG.md" not in release
    assert "jq --exit-status --join-output '.body'" in release
    assert "cmp --silent dist/release-notes.md" in release
    assert "GH_REPO: ${{ github.repository }}" in release
    assert "gh release download" in release
    assert "diff --recursive --brief dist/assets remote-dist" in release
    assert "--draft=false" in release
    assert "--json isImmutable" in release
    assert "gh release verify" in release
    assert "gh release verify-asset" in release
    assert (
        publish.index("gh release create")
        < publish.index("gh release download")
        < publish.index("--draft=false")
        < publish.index("gh release verify")
    )


def test_release_installs_checksummed_github_cli_before_credentialed_commands() -> None:
    release = (WORKFLOW_ROOT / "release.yml").read_text(encoding="utf-8")

    assert f'GH_CLI_VERSION: "{GH_CLI_VERSION}"' in release
    assert f'GH_CLI_LINUX_AMD64_SHA256: "{GH_CLI_LINUX_AMD64_SHA256}"' in release
    assert release.count("Install checksummed GitHub CLI") == 2
    assert release.count("sha256sum --check --strict -") == 2
    assert release.count("Confirm the checksummed GitHub CLI is selected") == 2
    assert release.index("Install checksummed GitHub CLI") < release.index(
        "Verify the annotated remote tag and event commit"
    )
    publish = release[release.index("\n  publish:") :]
    assert publish.index("Confirm the checksummed GitHub CLI is selected") < publish.index(
        "gh release create"
    )


def test_dependabot_covers_locked_python_and_actions_without_auto_merge() -> None:
    dependabot = (PROJECT_ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")

    assert 'package-ecosystem: "uv"' in dependabot
    assert 'package-ecosystem: "github-actions"' in dependabot
    assert dependabot.count('interval: "weekly"') == 2
    assert dependabot.count("default-days: 7") == 2
    assert "python-dependencies:" in dependabot
    assert "github-actions:" in dependabot
    assert "automerge" not in dependabot.lower()


def test_public_coordination_files_preserve_scientific_scope_and_private_reporting() -> None:
    security = (PROJECT_ROOT / "SECURITY.md").read_text(encoding="utf-8")
    normalized_security = " ".join(security.lower().split())
    contributing = (PROJECT_ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    issue_config = (PROJECT_ROOT / ".github" / "ISSUE_TEMPLATE" / "config.yml").read_text(
        encoding="utf-8"
    )
    engineering_issue = (
        PROJECT_ROOT / ".github" / "ISSUE_TEMPLATE" / "engineering-bug.yml"
    ).read_text(encoding="utf-8")
    accessibility_issue = (
        PROJECT_ROOT / ".github" / "ISSUE_TEMPLATE" / "accessibility-report.yml"
    ).read_text(encoding="utf-8")
    security_contact = (
        PROJECT_ROOT / ".github" / "ISSUE_TEMPLATE" / "security-contact.yml"
    ).read_text(encoding="utf-8")
    pull_request = (PROJECT_ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md").read_text(
        encoding="utf-8"
    )

    assert "/security/advisories/new" in security
    assert "Do not disclose vulnerability details in a public issue" in security
    assert "protected health information" in security.lower()
    assert "synthetic" in security.lower()
    assert "does not establish clinical decision support" in normalized_security
    assert "sole numerical and formula authority" in contributing
    assert "six-part response" in contributing
    assert "private" in contributing.lower()
    assert "release_settings_read_token" not in contributing.lower()
    assert "blank_issues_enabled: false" in issue_config
    assert "/security/advisories/new" in issue_config
    assert "protected health information" in engineering_issue.lower()
    assert "behavior owned by this repository" in engineering_issue.lower()
    assert "authoritative upstream" in engineering_issue.lower()
    assert "assistive technology" in accessibility_issue.lower()
    assert "protected health information" in accessibility_issue.lower()
    assert "include no vulnerability details" in security_contact.lower()
    assert "protected health information" in security_contact.lower()
    assert "six-part response" in pull_request
    assert "make scientific-test" in pull_request
    assert "make verify" in pull_request


def test_current_release_docs_match_credential_free_annotated_tag_policy() -> None:
    current_docs = (
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / "CHANGELOG.md",
        PROJECT_ROOT / "CONTRIBUTING.md",
        PROJECT_ROOT / "docs" / "MAINTENANCE.md",
        PROJECT_ROOT / "docs" / "VALIDATION.md",
    )
    for path in current_docs:
        text = path.read_text(encoding="utf-8")
        assert "RELEASE_SETTINGS_READ_TOKEN" not in text
        assert re.search(r"\bsigned\b", text, flags=re.IGNORECASE) is None

    decisions = (PROJECT_ROOT / "docs" / "DECISIONS.md").read_text(encoding="utf-8")
    assert "2026-07-31 — Release automation uses only the job-scoped GitHub token" in decisions
    assert "supersedes only the 2026-07-30 requirements" in decisions
    assert "GitHub-verified signed annotated tag" in decisions


def test_governance_docs_preserve_version_core_and_type_sm_boundaries() -> None:
    project = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]
    stage = tomllib.loads((PROJECT_ROOT / "browser-stage.toml").read_text(encoding="utf-8"))
    scope = (PROJECT_ROOT / "docs" / "SCIENTIFIC_SCOPE.md").read_text(encoding="utf-8")
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert project["version"] == "0.1.3"
    assert project["dependencies"] == [
        "wald-inference @ "
        "https://github.com/reblocke/wald-inference-core/releases/download/v0.4.1/"
        "wald_inference-0.4.1-py3-none-any.whl"
        "#sha256=d7272023f65088729d3ff997cab7cac57b84f22ac6108244ec2170434557d99b"
    ]
    app, core = stage["packages"]
    assert (app["version"], core["version"]) == ("0.1.3", "0.4.1")
    assert core["artifact_sha256"] == (
        "d7272023f65088729d3ff997cab7cac57b84f22ac6108244ec2170434557d99b"
    )
    assert "The focused response contains exactly:" in scope
    for key in ("meta", "precision", "selection_rule", "grid", "scenarios", "warnings"):
        assert key in scope
    assert "posterior probability" in scope
    assert "No inverse precision solver is included." in scope
    assert "Current app version: **0.1.3**." in readme


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


def test_readme_records_current_version_release_status_and_citation() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    normalized_readme = " ".join(readme.split())
    project_version = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]["version"]

    assert f"Current app version: **{project_version}**." in normalized_readme
    assert (
        f"https://github.com/reblocke/type-s-m-calibrator/releases/tag/v{project_version}"
    ) in readme
    assert "Release maturity: experimental software." in normalized_readme
    assert (
        "GitHub publication state is recorded on the versioned release page." in normalized_readme
    )
    assert "[`CITATION.cff`](CITATION.cff)" in readme
    assert "cite the exact tagged release used" in normalized_readme
    assert "cite the exact repository commit instead" in normalized_readme


def test_related_wald_tools_are_exact_in_readme_and_footer() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    html = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")
    footer = html.split("<footer>", maxsplit=1)[1].split("</footer>", maxsplit=1)[0]
    links = [
        "https://reblocke.github.io/wald-inference-tools/",
        "https://reblocke.github.io/precision-guardrail-planner/",
        "https://reblocke.github.io/conf_curve_likelihood/",
        "https://github.com/reblocke/type-s-m-calibrator",
        "https://github.com/reblocke/wald-inference-core/releases/tag/v0.4.1",
    ]

    assert "## Related Wald tools" in readme
    assert "<h2>Related Wald tools</h2>" in footer
    for link in links:
        assert link in readme
        assert f'href="{link}"' in footer
    assert "wald-inference Core v0.4.1" in readme
    assert "wald-inference Core v0.4.1" in footer
    assert "[Privacy](docs/PRIVACY.md)" in readme
    assert (
        'href="https://github.com/reblocke/type-s-m-calibrator/blob/main/docs/PRIVACY.md"' in footer
    )
