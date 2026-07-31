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
an annotated semantic-version tag. The release workflow verifies the remote
tag object and binds the tag target to the event commit, then
requires that commit to be contained in protected `main` history before
isolated project-version parsing or repository execution. It reruns the full
suite under read-only contents permission, disables the shared dependency
cache, and builds the deterministic source archive, browser-stage manifest,
and SHA-256 checksums before a release exists.

A separate job with narrowly scoped contents-write permission uses an exact
checksummed GitHub CLI and the job-scoped GitHub token to create a draft stable
release containing every asset and only the tagged version's nonempty
changelog section. It re-downloads and compares the exact draft assets and
release body, publishes the verified draft once as stable, then requires the
published release to report immutable and independently verifies every asset.

If the workflow fails while the release remains a draft, retain the draft for
inspection. If a post-publication verification fails, preserve the published
artifacts and investigate the release state. Repair the workflow and create a
new tag only after the failure is understood; never move a published tag or
replace a published asset. Complete CI, GitHub
Pages, hosted runtime/version display, all-six-rule smoke, strict error
presentation, exports, privacy, and portfolio-level validation before creating
the tag.

Repository settings must retain read-only default workflow permissions,
protect `main` and `v*` tags, enable private vulnerability reporting and
Dependabot security updates, and enable immutable releases before the next tag
is created. Release automation requires no external release credential; all
credentialed GitHub commands use the job-scoped GitHub token. Because the
workflow verifies immutability after publication rather than querying the
setting beforehand, confirm this repository setting before creating the tag.

## Deprecation

Breaking scientific or contract changes require a new major version, a
changelog entry, migration notes, and a visible hosted warning before removal.
The Pages URL should remain available for at least one documented release
cycle or link clearly to a successor. Do not silently redirect, delete, or
repurpose the app.
