# Maintenance

## Status

Template status: active engineering scaffold, version 0.1.0.

AUTHOR ACTION REQUIRED after initialization: choose and state one maintenance status such as
experimental, active, maintenance-only, archived, or superseded.

## Ownership

Maintainer: Brian Locke (`@reblocke`). Use repository issues and pull requests for public project
coordination.

AUTHOR ACTION REQUIRED: confirm downstream ownership, review responsibilities, and a contact path.

## Dependency updates

Review Pyodide, Plotly, Python, uv, Ruff, pytest, Hypothesis, Playwright, and GitHub Actions
updates deliberately. For any external scientific core:

1. review its release notes and scientific changes;
2. update the exact package version and artifact checksum;
3. regenerate and review `uv.lock`;
4. run strict JSON, frozen scientific fixtures, staging, Chromium, and WebKit validation;
5. record the adopted core version in docs, UI, and release notes.

## Release

Use a reviewed pull request. After the exact merge commit is verified, create an annotated
semantic-version tag. The release workflow reruns the full suite and publishes a prerelease with
a deterministic source archive, browser-stage manifest, and SHA-256 checksums. Promote a release
only after hosted Pages and portfolio-level validation are complete.

## Deprecation

AUTHOR ACTION REQUIRED: define how users will be warned, how long the hosted app will remain
available, and where a successor is documented. Do not silently redirect or delete an old URL.
