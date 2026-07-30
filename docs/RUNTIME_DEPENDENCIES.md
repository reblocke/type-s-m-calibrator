# Runtime Dependencies and Provenance

## Scientific core

`wald-inference` is the sole runtime numerical/formula authority. Release
0.4.1 supplies effect transformations, 95% CI reconstruction, information
scaling, all six selection rules, canonical selected-claim probability, and
Type S/M design metrics.

The adopted official artifact is:

```text
Release: https://github.com/reblocke/wald-inference-core/releases/tag/v0.4.1
Wheel:   https://github.com/reblocke/wald-inference-core/releases/download/v0.4.1/wald_inference-0.4.1-py3-none-any.whl
SHA-256: d7272023f65088729d3ff997cab7cac57b84f22ac6108244ec2170434557d99b
Tag commit: f4613177b6dc81d194aa70762152de2bfa86663b
Retrieved: 2026-07-30
License: MIT
```

The URL, version, and SHA-256 are recorded identically in:

- `pyproject.toml`;
- `uv.lock`;
- `browser-stage.toml`;
- the generated browser-stage manifest.

No local path, sibling checkout, or mutable branch is an acceptable release
dependency.

The upstream v0.4.1 changelog and release metadata were reviewed before
adoption. The release repairs active-threshold inverse-precision bracketing,
extreme pairwise support comparison, and strict ratio back-transform
underflow while retaining the selected-claim and Type S/M interfaces used
here.

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
