# Maintenance

## Status and ownership

Status: experimental, actively maintained research/education software.

Maintainer: Brian Locke (`@reblocke`). Use repository issues and pull requests
for public coordination. Scientific changes require focused numerical review;
browser, privacy, accessibility, provenance, and public-copy changes require
their corresponding review gates.

## Dependency updates

Review Pyodide, Plotly, Python, uv, Ruff, pytest, Hypothesis, Playwright, GitHub
Actions, and especially `wald-inference` deliberately. For a core update:

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
an annotated semantic-version tag. The release workflow reruns all checks and
publishes a prerelease with a deterministic source archive,
browser-stage manifest, and SHA-256 checksums.

Promote only after CI, release assets, GitHub Pages, hosted runtime/version
display, all-six-rule smoke, strict error presentation, exports, privacy, and
portfolio-level validation are complete.

## Deprecation

Breaking scientific or contract changes require a new major version, a
changelog entry, migration notes, and a visible hosted warning before removal.
The Pages URL should remain available for at least one documented release
cycle or link clearly to a successor. Do not silently redirect, delete, or
repurpose the app.
