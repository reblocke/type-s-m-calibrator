# Decisions

## 2026-07-29 — Functional Python contract and browser worker

Python owns request validation and response assembly. The static UI sends
strict JSON to a restartable Web Worker running exact-version Pyodide. This
keeps calculation and initialization off the main thread while retaining a
safe, finite JSON boundary.

## 2026-07-29 — Generated, verified browser stage

Installed locked packages are staged from a TOML manifest. Generated files are
ignored. File, package, and aggregate hashes are verified before Python is
loaded. The initialized app has no live template dependency.

## 2026-07-29 — Strict client-side privacy boundary

There is no backend, telemetry, persistence, cookie, input-bearing URL, upload,
or input logging. Static CDN requests do not contain user values.

## 2026-07-30 — Core is the only formula authority and is artifact-pinned

`wald-inference` owns transformations, CI reconstruction, information scaling,
selection rules, canonical selected-claim probabilities, Type S/M metrics, and
the near-null tolerance. The app may validate and assemble inputs but must not
implement or copy a Wald probability or Type S/M formula.

Release and browser execution use the official `wald-inference` 0.3.0 wheel:

```text
https://github.com/reblocke/wald-inference-core/releases/download/v0.3.0/wald_inference-0.3.0-py3-none-any.whl
SHA-256 630fdece13c2940f751d1f5d3a4d6477182dbb099131a9907ceef7067348f939
```

The annotated upstream tag peels to
`9618abf3a632838794e9e40752af7823e77115cb`. The same URL, version, and
checksum are bound in package metadata, `uv.lock`, and `browser-stage.toml`.

The app uses canonical `selected_claim_probability` for its probability
output. It uses `DesignMetric` only for Type S, Type M, expected selected
absolute Z, and observed exaggeration. A tight comparison detects unexpected
drift without requiring byte equality from the frozen legacy probability
field.

The released v0.3 canonical probability kernel and the retained Type S/M
metric probability can differ by directed-rounding noise. An official-wheel
25,000-case sweep across all six rules found no difference outside relative
tolerance `3e-14` with absolute tolerance `3e-16`; the prior `2e-14` bound
rejected valid tiny-alpha cases. The app keeps the canonical probability as
output and still fails closed on material cross-API drift.

## 2026-07-30 — Direct SE is default; CI mode supplies precision only

Direct working-scale SE is the clearest design input and is the default. CI
mode reconstructs current precision from two reported 95% limits and reuses it
hypothetically. A separate optional observed estimate never alters SE or truth;
it enables observed exaggeration and an explicitly optimistic/circular
scenario.

This focused app intentionally does not promote the CI-implied midpoint to an
assumed-truth scenario without an explicit observed-estimate input. That is a
narrow divergence from the integrated Ticket 05 scenario list: it keeps CI
mode precision-only, works consistently with direct-SE mode, and avoids silently
turning reconstructed observed-data metadata into an assumed truth. Users may
enter the midpoint explicitly when that optimistic sensitivity scenario is
desired.

## 2026-07-30 — Focused forward-only response

The response contains only `meta`, `precision`, `selection_rule`, `grid`,
`scenarios`, and `warnings`. It excludes observed-data inference panels and
inverse precision results. Undefined numerical values are `null`.

Null, user, reference-threshold, and optional observed scenarios are
deduplicated on the working scale using relative and absolute tolerance
`1e-12`, retaining the first occurrence while merging later source notes. The
active claim threshold stays a rule input and plot marker and is not
automatically assumed true.

Reviewer text defaults to the first user scenario, then the first non-null
reference threshold, then the observed-estimate-as-truth scenario, then the
first retained row. A merged observed-estimate source always preserves the
optimistic/circular qualification.

## 2026-07-30 — Fixed panels and plot-only 10× treatment

Selected-claim probability, Type S, and Type M remain simultaneously visible
in panels A–C. Panel D appears only with an observed estimate. Ratio-valued
traces use 1× and 2× guides and are capped at 10× only in plotted y-values.
Hover source data, response, table, reviewer text, and CSV remain uncapped.
The plot title carries a dynamic clipping disclosure so standalone plot PNGs
cannot lose it.

Ratio-measure x axes are logarithmic, while the grid is equally spaced on the
core working scale. Null, reference thresholds, active claim thresholds, and
scenario markers use distinct line/point encodings.

## 2026-07-30 — Stable numeric CSV requires companion context

The curve CSV remains an exact eight-column numeric grid contract. Adding
preamble rows or repeated metadata columns would break that stable shape.
Because the file does not repeat rule, alpha, precision, or conditioning
metadata, it must be reused with the copied caption or focused JSON response.
Probability fields remain proportions even though the HTML table displays
percentages. Public documentation must not call the CSV self-contained.

## 2026-07-30 — Release records are bound to the release commit

Version `0.1.0` is recorded in package metadata, `CITATION.cff`, and the
changelog. Publication still requires a reviewed merge, annotated tag, green
tag workflow, verified assets, Pages deployment, and hosted smoke; a version
string alone is not release evidence.

## 2026-07-30 — Public interpretation boundary

Every public surface states that x values are assumed true effects and metrics
are forward repeated-study operating characteristics. Type S/M are conditional
on selection and are not posterior probabilities. Thresholds are not claimed
to be clinically validated, and the app is not clinical guidance or a
validated device.
