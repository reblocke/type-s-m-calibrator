# Maintenance

## Status and ownership

Status: experimental, actively maintained research/education software.

Maintainer: Brian Locke (`@reblocke`). Use repository issues and pull requests
for public coordination. Scientific changes require focused numerical review;
browser, privacy, accessibility, provenance, and public-copy changes require
their corresponding review gates.

## Dependency updates

Review Pyodide, Plotly, Python, uv, Ruff, pytest, Hypothesis, Playwright, GitHub
Actions, and especially `wald-inference` deliberately. Dependabot groups
weekly `uv` and GitHub Actions updates after a seven-day cooldown for review;
it does not authorize automatic merging. Keep each third-party Action pinned
to a reviewed full commit SHA with its version in a comment. For a core
update:

1. review the upstream changelog, public API, scientific changes, license, and
   official release assets;
2. update the exact wheel URL, version, and SHA-256 together in
   `pyproject.toml`, `uv.lock`, and `browser-stage.toml`;
3. regenerate and inspect the lock and browser-stage manifest;
4. run strict JSON, B04/B05/B07 parity, contract, property, staging, Chromium,
   and WebKit validation;
5. verify a clean checkout without sibling repositories;
6. record the adopted core version and evidence in docs and release notes.

Do not replace the core with a local formula, copied module, path dependency,
floating version, or mutable branch artifact.

## Release

Use a reviewed pull request. After the exact merge commit is verified, create
a signed, annotated semantic-version tag. The release workflow verifies the
remote tag object and signature, binds the tag target to the event commit, and
requires that commit to be contained in protected `main` history before
isolated project-version parsing or repository execution. It reruns the full
suite under read-only contents permission, disables the shared dependency
cache, and builds the deterministic source archive, browser-stage manifest,
and SHA-256 checksums before a release exists.

A separate job with narrowly scoped contents-write permission uses an exact
checksummed GitHub CLI, requires repository release immutability through the
`RELEASE_SETTINGS_READ_TOKEN` Actions secret, and creates a draft stable
release containing every asset and only the tagged version's nonempty
changelog section. It re-downloads and compares the exact draft assets and
release body, then publishes the verified draft once as stable.

If the workflow fails after draft creation, retain the draft for inspection.
Repair the workflow and create a new tag only after the failure is understood;
never move a published tag or replace a published asset. Complete CI, GitHub
Pages, hosted runtime/version display, all-six-rule smoke, strict error
presentation, exports, privacy, and portfolio-level validation before creating
the tag.

Repository settings must retain read-only default workflow permissions,
protect `main` and `v*` tags, enable private vulnerability reporting and
Dependabot security updates, and enable immutable releases before the next tag
is created. Store a repository-scoped Administration-read token as the
`RELEASE_SETTINGS_READ_TOKEN` Actions secret so the workflow can fail closed
before publication. The job-scoped GitHub token, not that settings-read
secret, creates the release.

## Deprecation

Breaking scientific or contract changes require a new major version, a
changelog entry, migration notes, and a visible hosted warning before removal.
The Pages URL should remain available for at least one documented release
cycle or link clearly to a successor. Do not silently redirect, delete, or
repurpose the app.
