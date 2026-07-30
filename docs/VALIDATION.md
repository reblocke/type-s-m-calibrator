# Validation

## Validation boundary

The app validates orchestration and presentation around `wald-inference`; it
does not duplicate core formulas. The exact official 0.4.1 artifact and its
numerical release tests are authoritative for normal tails, selection
intervals, truncated normal moments, transforms, and CI reconstruction.

Core v0.4.1 repairs active-threshold inverse-precision bracketing, extreme pairwise support
comparison, and strict ratio back-transform underflow while retaining the forward selection and
Type S/M definitions used here. This app adds no local formula.

Engineering and numerical parity do not establish clinical validity or the
scientific appropriateness of a user threshold.

## Scientific and contract targets

The local suite covers:

- exact response and eight-field grid shape;
- all six selection rules and rule-specific controls;
- exact canonical alpha at the null for two- and one-sided p rules;
- rule-dependent null probabilities for directional/threshold rules;
- positive/negative two-sided symmetry;
- wrong-sign tails and one-sided direction;
- directional CI and threshold boundaries;
- alpha-neutral labels and tiny-alpha rejection;
- released-Core cross-API coherence at tiny alpha, with material-drift
  rejection;
- large-delta Type S/Type M behavior;
- near-null undefined values and expected selected absolute Z;
- direct-SE and 95% CI precision modes;
- information scaling;
- ratio log conversion;
- scenario deduplication while retaining threshold rule metadata;
- separate near-null and zero-selection explanations;
- optimistic/circular reviewer qualification after scenario deduplication;
- plot-only cap detected from curves or scenarios, with uncapped
  contract/table/hover/reviewer/CSV sources;
- strict JSON and absent/present observed estimate behavior;
- conditioned, nonposterior reviewer text;
- absence of inverse-planning and observed-data outputs.

Property tests generate finite additive inputs, check probability bounds and
strict serialization, and verify two-sided sign symmetry.

## Frozen integrated parity

Compact B04, B05, B07a, and B07b scenario targets were extracted without
recalculation from:

- behavior source `830756ecb11b4e8161f8dfe1fc75afc346ef4467`;
- fixture-bearing freeze merge
  `5fd501dd947d9b951d736014cfc2b310efa5e7b0`;
- annotated tag `pre-split-baseline-2026-07-29`.

The fixture and provenance note live under
`tests/fixtures/integrated_baseline/`. Float comparisons use relative
tolerance `2e-13` and absolute tolerance `2e-15`, tight enough to detect
semantic drift while permitting the intended few-ULP difference between the
canonical Core v0.3 null probability and the frozen legacy Type S/M
probability field.

## Browser and display targets

Static policy and Playwright tests verify:

- manifest-driven, hash-verified Pyodide staging;
- exact app and core versions at runtime;
- direct-SE and CI workflows;
- all six rules;
- active/disabled direction and threshold controls;
- visible assumed-truth and nonposterior wording;
- fixed panels A–C and conditional panel D;
- textual scenario rows independent of the plot;
- standardized delta, percentage probabilities, x-fold ratios, and undefined
  notes in the scenario table;
- exact eight-column numeric CSV and blank undefined cells;
- uncapped CSV despite the 10× plot treatment;
- clipping disclosure preserved in standalone plot/dashboard PNGs;
- PNG, caption, and reviewer-text exports;
- safe validation errors and worker recovery;
- prior-result clearing on client errors and stale-response rejection after
  Reset;
- ticket-priority reviewer fallback;
- keyboard, mobile, focus-contrast, and linked-error behavior;
- 390 px rendered bounding-box containment and peer-label non-overlap for the calculated
  four-panel figure title, panel labels, legend text, and axis titles;
- no input in URLs or network requests;
- no backend, cookies, browser storage, telemetry, or logging.

Chromium runs the full browser suite. WebKit reruns the worker/calculation
smoke.

## Dependency and clean-checkout gate

Before release:

1. pin the official `wald-inference` 0.4.1 wheel URL and SHA-256 in
   `pyproject.toml`, `uv.lock`, and `browser-stage.toml`;
2. verify the upstream changelog and public API;
3. stage from a clean checkout with no sibling core repository;
4. verify manifest schema, package versions, artifact provenance, file hashes,
   package hashes, bundle hash, and source commit;
5. run all commands below;
6. verify CI, release assets/checksums, Pages, and hosted browser behavior.

## Commands

```bash
uv sync --locked
uv run playwright install chromium webkit
make verify
uv run pytest -q tests/scientific_reference tests/regression
uv run python scripts/stage_browser_packages.py
git diff --check
git status --short
```

## Release evidence

Release evidence records the exact commit/tag, Core artifact/checksum,
browser-stage manifest/checksums, test counts, Chromium/WebKit results, Pages
run, hosted smoke, and remaining limitations. Local results are recorded in
the pull request and release handoff; GitHub Actions reruns the complete gates
from the reviewed commit.

The 2026-07-30 local release-candidate run used the official Core 0.4.1 wheel
and passed:

- 73 non-E2E tests through `make verify`;
- 18 real Chromium E2E tests covering the six-rule matrix and exports;
- one real WebKit worker/calculation smoke;
- eight focused scientific-reference and frozen-regression tests;
- a source distribution and wheel build plus cold-wheel calculation smoke;
- exact CFF identity/date/license checks; and
- a 25,000-case, all-six-rule cross-API probability-coherence sweep.

The generated browser stage contained five app files and 14 Core files, with
Core package SHA-256
`44c52ba0189155e0d976e283d383f17f3db0679563ec6dc6d45b9829c4a43b4d`.
Because generated output records the current Git commit, final source-commit
and bundle hashes are regenerated and recorded by the tag workflow.
