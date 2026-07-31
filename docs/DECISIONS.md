# Decisions

## 2026-07-31 — Release automation uses only the job-scoped GitHub token

This decision supersedes only the 2026-07-30 requirements for a GitHub-verified tag signature and
a repository-scoped Administration-read `RELEASE_SETTINGS_READ_TOKEN`. The earlier decision is
preserved below as the historical policy record.

Future releases still require an annotated semantic-version tag. Before repository code executes,
the workflow confirms the local annotated tag, remote tag-object type and SHA, tag name, peeled
event commit, protected-`main` containment, and exact project-version match. Deterministic assets,
checksums, bundle transfer, draft-first creation, release-body and asset byte comparison, and
stable one-time publication are unchanged.

The publishing job no longer queries repository immutable-release settings before creating the
draft. Every credentialed GitHub command uses the exact checksummed GitHub CLI with the job-scoped
`github.token`; no separately managed release credential is required. Immutable releases must
still be enabled before creating the tag. Immediately after publication, the workflow requires
the release to report immutable and independently verifies the release and every asset.
Because the settings query is intentionally removed, maintainers must confirm immutable releases
are enabled before tagging; the workflow detects a disabled setting only after publication.

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

Release and browser execution use the official `wald-inference` 0.4.1 wheel:

```text
https://github.com/reblocke/wald-inference-core/releases/download/v0.4.1/wald_inference-0.4.1-py3-none-any.whl
SHA-256 d7272023f65088729d3ff997cab7cac57b84f22ac6108244ec2170434557d99b
```

The annotated upstream tag peels to
`f4613177b6dc81d194aa70762152de2bfa86663b`. The same URL, version, and
checksum are bound in package metadata, `uv.lock`, and `browser-stage.toml`.

The initial v0.1.0 app used Core v0.3.0. Patch release v0.1.1 adopts v0.4.1 because it repairs an
active-threshold inverse-precision bracket, extreme finite pairwise support comparison, and strict
ratio back-transform underflow while retaining forward selection and Type S/M definitions. The
repairs remain in Core; no corresponding formula is copied into this app.

The app uses canonical `selected_claim_probability` for its probability
output. It uses `DesignMetric` only for Type S, Type M, expected selected
absolute Z, and observed exaggeration. A tight comparison detects unexpected
drift without requiring byte equality from the frozen legacy probability
field.

The canonical probability kernel introduced in v0.3 and retained in v0.4.1, and the Type S/M
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

## 2026-07-30 — Compact plot labels follow the plot container

Plotly uses its compact layout when the rendered plot container is no wider than 480 px, regardless
of the overall viewport width. The compact layout wraps the figure, panel, and axis titles,
reserves additional margins and height, and hides the mode bar so controls cannot cover the title.
A `ResizeObserver` tracks the plot content box and rerenders only when its width crosses the compact
boundary; ordinary size changes within one category do not rebuild the plot.

Figure and dashboard PNGs use the same trace and layout builder but render into a temporary,
fixed-size, noncompact plot before image encoding. The temporary plot is purged and removed after
each export, and the live plot retains its compact state. This keeps high-resolution typography
independent of the initiating viewport while preserving plotted values and the clipping
disclosure.

Chromium regressions cover 390 px rendered-label containment and peer-label non-overlap, an
approximately 850 px two-column viewport whose plot container is still compact, post-render
boundary crossings, and mobile-origin exports. These presentation decisions do not change Core
v0.4.1, the six-part response, plotted data, numerical tables, or client-only privacy.

## 2026-07-30 — Fail-closed repository and release governance

Third-party GitHub Actions are content-addressed by reviewed full commit SHAs and receive grouped,
review-only Dependabot proposals. CI has explicit read-only contents permission. Pages separates
the read-only build from the narrowly write-enabled deploy. Checkout credentials are never
persisted, and the release-artifact build disables shared dependency caching.

A future release requires a GitHub-verified signed annotated tag whose remote tag object resolves
to the event commit. The verified target must be contained in protected `main` history before
isolated project-version parsing or any repository dependency installation, test, or build. The
tag must equal `v` plus the authoritative project version.

Release assets are built and checksummed before release creation, then transferred to a separate
publishing job. Credentialed release commands use an exact checksummed GitHub CLI. A
repository-scoped Administration-read `RELEASE_SETTINGS_READ_TOKEN` fails closed unless immutable
releases are enabled; it is not used to publish. The job-scoped token creates a draft stable
release containing every asset and only the current version's changelog section. The workflow
downloads and compares the release body and every asset before publishing once, then verifies the
immutable release and each asset.

Private vulnerability reporting is the disclosure path. Public issue forms exclude credentials,
restricted data, sensitive values, and protected health information. These governance changes do
not alter Core v0.4.1, Type S/M calculations or interpretation, the six-part response, browser
behavior, exports, version metadata, or scientific scope.
