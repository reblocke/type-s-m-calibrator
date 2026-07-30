# Codex AGENTS

## Purpose

- This repository is a focused static app for forward Type S/M calibration
  under one-parameter Wald models.
- Released `wald-inference` is the sole numerical/formula authority.
- Python under `src/type_sm_calibrator/` owns validation, orchestration, strict
  JSON, warnings, and reviewer text.
- Generated browser Python is ignored.

## Commands

- Setup: `uv sync --locked`
- Stage: `make stage-web`
- Format: `make fmt`
- Verify formatting: `make fmt-check`
- Lint: `make lint`
- Python/integration/property tests: `make test`
- Scientific/regression tests: `make scientific-test`
- Chromium: `make e2e`
- WebKit smoke: `make e2e-webkit-smoke`
- Full verification: `make verify`

## Working rules

- Before non-trivial changes, state assumptions, ambiguities, tradeoffs,
  success criteria, risks, expected files, and verification commands.
- Never implement or copy a Wald, selection-tail, Type S, Type M, or
  observed-exaggeration formula in application source. Documentation may
  explain the released core semantics; add/release a missing executable
  primitive in the core first.
- Pin core upgrades to one official release artifact URL and SHA-256 in
  package metadata, `uv.lock`, and `browser-stage.toml`.
- Run staging; never hand-edit `web/assets/py/`.
- Preserve the focused six-part response and forward-only scope.
- Keep the assumed-true-effect, selection-conditioning, log-ratio, near-null,
  plot-only-cap, and nonposterior meanings visible.
- Preserve client-side privacy: no backend, telemetry, persistence, cookies,
  uploads, PHI logging, or input-bearing URLs.
- Keep accessible textual outputs; plots are never the sole result carrier.

## Done criteria

- Unit, property, contract, frozen B04/B05/B07 regression, staging, privacy,
  Chromium, and WebKit checks pass.
- All six rules and both precision modes pass in the browser.
- Stage output is reproducible from a clean checkout without a sibling core
  repository.
- Scope, validation, privacy, citation, maintenance, provenance, and public
  copy remain truthful.
