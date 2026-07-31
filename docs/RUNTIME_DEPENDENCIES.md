# Runtime Dependencies and Provenance

## Scientific core

`wald-inference` is the sole runtime numerical/formula authority. Release
0.4.2 supplies effect transformations, 95% CI reconstruction, information
scaling, all six selection rules, canonical selected-claim probability, and
Type S/M design metrics.

The adopted official artifact is:

```text
Release: https://github.com/reblocke/wald-inference-core/releases/tag/v0.4.2
Wheel:   https://github.com/reblocke/wald-inference-core/releases/download/v0.4.2/wald_inference-0.4.2-py3-none-any.whl
SHA-256: 225331d7b9d7b70e2508eecb92851a92a8c4e245baf412a1eb0f464d85da1349
Tag commit: 8afd0a463cc1d2586b8ce5cf92f40900647c3190
Retrieved: 2026-07-31
License: MIT
```

The URL, version, and SHA-256 are recorded identically in:

- `pyproject.toml`;
- `uv.lock`;
- `browser-stage.toml`;
- the generated browser-stage manifest.

No local path, sibling checkout, or mutable branch is an acceptable release
dependency.

The upstream v0.4.2 changelog, immutable release metadata, and artifact checksum were reviewed
before adoption. This patch changes Core governance and release controls only and explicitly
preserves every numerical formula, public API, tolerance, dependency resolution, and frozen
baseline value. The v0.4.1 active-threshold, extreme-support, and ratio-underflow repairs and the
selected-claim and Type S/M interfaces used here remain unchanged.

## Browser runtime

- Pyodide 0.29.3 is loaded from its versioned jsDelivr path and is licensed
  under MPL-2.0.
- Plotly.js 3.1.0 is loaded from Plotly’s versioned CDN path and is MIT
  licensed.
- NumPy and SciPy are provided by the pinned Pyodide distribution for the
  staged pure-Python core; their licenses are BSD-3-Clause.
- Generated local Python files are listed and hashed by
  `web/assets/py/manifest.json`.

These static CDN requests do not include user values. Availability depends on
reaching the CDNs; no offline guarantee is made.

## Build and test dependencies

`uv.lock` controls Python, CI, and development resolution. The repository uses
uv, setuptools, wheel, Ruff, pytest, Hypothesis, Playwright, and GitHub
Actions. These tools are not separate scientific authorities.

`browser-stage.toml` independently identifies which exact installed
distributions are copied to the browser. Staging verifies distribution
version, direct artifact URL/checksum, installed `direct_url.json`, wheel
`RECORD`, safe package shape, and deterministic file/package/bundle hashes.

## Repository automation

Every third-party GitHub Action is pinned to a reviewed full commit SHA with a
human-readable version comment. Dependabot proposes grouped weekly updates
after a seven-day cooldown for both `uv` dependencies and Action pins. An
update remains a reviewed source and supply-chain change: inspect upstream
release notes, confirm the referenced commit belongs to the stated release,
and rerun scientific, contract, staging, Chromium, and WebKit checks before
merging. Dependency automation does not authorize a Core upgrade or automatic
merging.

The release workflow downloads GitHub CLI 2.93.0 from its versioned official
archive and verifies SHA-256
`02d1290eba130e0b896f3709ffff22e1c75a51475ddb70476a85abc6b5807af0`
before any credentialed `gh` command. This build-time tool is not a scientific
or browser runtime dependency.

## Creation-time provenance

The repository was initialized from
`reblocke/scientific-applet-template` v0.1.0, exact source commit
`a360bde95c192d8de4f9a3b531e73600ebf3d8b8`. The template is a creation-time
MIT-licensed source, not a live runtime dependency.

Frozen integrated scenario provenance is recorded under
`tests/fixtures/integrated_baseline/`. No external figure, table, publisher
asset, or dataset is committed.

## Method reference

Gelman A, Carlin J. Beyond Power Calculations: Assessing Type S (Sign) and Type
M (Magnitude) Errors. *Perspectives on Psychological Science*. 2014;9(6):
641–651. <https://doi.org/10.1177/1745691614551642>. Retrieved 2026-06-14.

The citation motivates terminology and interpretation. Core APIs and tests
control behavior; the exact official pinned artifact controls runtime
execution.
