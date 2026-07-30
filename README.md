# Type S/M Calibrator

[![CI](https://github.com/reblocke/type-s-m-calibrator/actions/workflows/ci.yml/badge.svg)](https://github.com/reblocke/type-s-m-calibrator/actions/workflows/ci.yml)

A focused, static app for forward Type S and Type M calibration under a
one-parameter Wald model.

The app answers:

> If a candidate value were the true effect, how often would the selected-claim
> rule be satisfied, how often would a selected claim have the wrong sign, and
> how much would selected estimates exaggerate magnitude?

Every curve conditions on its x-axis value being the true effect. These are
repeated-study operating characteristics, not posterior probabilities and not
evidence conditional on an observed dataset.

Hosted app: <https://reblocke.github.io/type-s-m-calibrator/>.

## What it provides

- direct working-scale SE or reported 95% CI precision input;
- all six supported Wald selected-claim rules;
- current and information-scaled hypothetical SE;
- fixed panels for selected-claim probability, Type S, and Type M;
- a fourth observed-exaggeration panel only when an observed estimate is
  supplied;
- null, user, reference-threshold, and explicitly optimistic/circular
  observed-estimate scenarios with working-scale deduplication;
- an uncapped full scenario table and stable eight-column numeric curve CSV;
- figure and dashboard PNGs, a caption, and scenario-specific reviewer text;
- strict JSON, client-only computation, and no input-bearing URL state.

The visible 10× ceiling is a plot-only readability treatment. Contract, table,
hover, reviewer-text, and CSV values remain uncapped, and standalone plot PNGs
carry the clipping disclosure. Ratio measures use log-scale distance from the
null for Type M; natural odds/risk/hazard-ratio inflation is not Type M.

The curve CSV intentionally contains only the eight documented grid columns.
It does not repeat the selected rule, alpha, precision assumptions, or
conditioning statement; keep the copied caption or focused JSON response with
the CSV when reusing it.

## Not included

The app does not provide inverse precision or exact sample-size planning,
posterior probabilities, observed-data confidence/support panels, clinical
validation of thresholds, simulation, or multi-parameter models.

## Architecture

```text
browser form
  -> dedicated Web Worker
  -> verified generated Python bundle
  -> type_sm_calibrator.contract.calculate_json
  -> wald_inference numerical APIs
  -> strict focused JSON
  -> textual results + fixed Plotly panels + explicit exports
```

- `wald-inference` is the sole numerical/formula authority.
- `src/type_sm_calibrator/` owns validation, orchestration, response assembly,
  warnings, reviewer text, and strict JSON.
- `web/` owns the client-only UI and display-only plot cap.
- `scripts/stage_browser_packages.py` stages exact installed packages and
  records file/package/bundle SHA-256 hashes.
- `web/assets/py/` is generated, ignored, and never hand-edited.

The app pins the official `wald-inference` 0.3.0 release wheel by URL and
SHA-256
`630fdece13c2940f751d1f5d3a4d6477182dbb099131a9907ceef7067348f939`.
No sibling checkout or mutable branch is a runtime dependency.

## Inputs and interpretation

Direct SE is entered on the effect measure’s working scale. For ratio measures,
that means the log scale. CI mode reconstructs current working-scale precision
from the reported 95% limits, then reuses that precision as a hypothetical
future-study SE. The observed CI does not determine the true effect.

An information multiplier changes only the hypothetical design SE:
4× information halves the SE. It is not an exact sample-size conversion.

The optional observed estimate is used only for a separate realized
observed-exaggeration calculation and an explicitly optimistic/circular
scenario. It does not set precision or truth. CI mode does not silently promote
its reconstructed midpoint to a truth scenario; enter that midpoint explicitly
if the optimistic sensitivity analysis is intended.

See [Scientific Scope](docs/SCIENTIFIC_SCOPE.md) for the model, six rule
definitions, Type S/M formulas, working scales, undefined values, and
limitations.

## Development

The canonical verification is:

```bash
uv sync --locked
uv run playwright install chromium webkit
make verify
make scientific-test
```

Other useful commands:

```bash
make stage-web
make fmt
make fmt-check
make lint
make test
make e2e
make e2e-webkit-smoke
make serve
make clean
```

Generated browser Python must remain ignored. Before release, a clean checkout
must stage from the locked official artifact without a sibling repository.

## Validation and provenance

Scientific orchestration tests cover all six rules, direct-SE and CI modes,
null and near-null behavior, sign symmetry, directional tails, threshold
boundaries, tiny alpha, information scaling, ratio conversion, scenario
deduplication, display-only capping, strict JSON, and absent/present observed
estimates.

Compact B04, B05, and B07 scenario fixtures come from the frozen integrated
baseline. Their behavior-source commit, fixture-bearing freeze commit, and tag
are recorded in
[tests/fixtures/integrated_baseline/README.md](tests/fixtures/integrated_baseline/README.md).
Engineering tests validate implementation and parity; they do not establish
clinical validity.

See [Validation](docs/VALIDATION.md),
[Runtime Dependencies](docs/RUNTIME_DEPENDENCIES.md), and
[Privacy](docs/PRIVACY.md).

## Related Wald tools

[Wald inference tools catalog](https://reblocke.github.io/wald-inference-tools/) ·
[Precision guardrail planner](https://reblocke.github.io/precision-guardrail-planner/) ·
[Integrated workbench](https://reblocke.github.io/conf_curve_likelihood/) ·
[Repository](https://github.com/reblocke/type-s-m-calibrator)

Numerical authority:
[wald-inference Core v0.3.0](https://github.com/reblocke/wald-inference-core/releases/tag/v0.3.0).
[Privacy](docs/PRIVACY.md) documents the client-side, no-storage boundary.

## Method reference

Gelman A, Carlin J. Beyond Power Calculations: Assessing Type S (Sign) and Type
M (Magnitude) Errors. *Perspectives on Psychological Science*. 2014;9(6):
641–651. <https://doi.org/10.1177/1745691614551642>.

The paper motivates the Type S/M framework. Core APIs and their tests are the
implementation authority; the exact pinned 0.3.0 release artifact is the
runtime authority. No external figure, table, or substantial text is copied
here.

## License and maintenance

Code is MIT licensed: Copyright (c) 2026 Brian Locke.

The app is experimental research/education software maintained by Brian Locke
(`@reblocke`). Use GitHub issues for public coordination. See
[Maintenance](docs/MAINTENANCE.md).
