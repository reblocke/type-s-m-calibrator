# Changelog

All notable changes use a release-oriented record here. This repository follows
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.5] - 2026-07-31

- Update the locked test/build toolchain to pytest 9.1.1 and setuptools 83.0.0.
- Update the reviewed, full-SHA GitHub Actions pins used by CI, Pages, and release workflows, and
  keep the exact reviewed pin set enforced by repository-policy tests.
- Publish the maintenance-only app state as an immutable patch release so the hosted Pages commit,
  package metadata, citation, and release artifacts identify the same source commit.
- Preserve the exact Core v0.4.2 pin, all six Type S/M selection rules and calculations, focused
  response/export contracts, browser behavior, interpretation boundaries, and client-side privacy.

## [0.1.4] - 2026-07-31

- Harden CI, Pages, and future releases with full-SHA Action pins, explicit least-privilege
  permissions, nonpersisted checkout credentials, and a disabled dependency cache in the
  release-artifact job.
- Require an annotated tag whose exact remote tag object is bound to the event commit, protected
  `main` history, and declared app version before repository code is executed, without making
  GitHub signature verification a release gate.
- Use only the job-scoped GitHub token for remote tag and release operations; remove the external
  settings credential and prepublication immutable-settings query while retaining exact draft
  body/asset comparison and post-publication immutable-release and asset verification.
- Add grouped weekly Dependabot proposals with a seven-day cooldown for `uv` and GitHub Actions,
  private vulnerability reporting guidance, contribution policy, scoped issue and pull-request
  templates, and repository-policy regressions. Dependency proposals remain review-only.
- Adopt the exact immutable `wald-inference` v0.4.2 wheel and checksum in package metadata, the
  lockfile, browser staging, runtime copy, and validation contracts. Core v0.4.2 changes governance
  and release controls only; all scientific calculations, the six-part response, browser behavior,
  exports, and forward-only Type S/M scope remain unchanged.

## [0.1.3] - 2026-07-30

- State the declared app version, canonical release record, experimental release maturity,
  versioned publication-state source, and exact tagged-release or commit citation guidance in the
  README, guarded by a repository policy regression.
- Synchronize package, lock, browser staging, runtime displays and tests, and machine-readable
  citation metadata at 0.1.3. Scientific calculations, the focused contract, UI behavior, and the
  checksum-bound `wald-inference` v0.4.1 authority are unchanged.

## [0.1.2] - 2026-07-30

- Make calculated plots readable whenever their actual container is no wider than 480 px,
  including a narrow results column in a wider two-column viewport. A `ResizeObserver` rerenders
  Plotly only when the container crosses that compact-layout boundary.
- Build standalone figure and dashboard PNGs from disposable fixed-size noncompact plots, so
  high-resolution exports retain desktop typography without changing the live compact plot. The
  shared builder preserves the same traces and clipping disclosure.
- Add Chromium regressions for rendered-label containment and overlap, container-width selection,
  post-render threshold crossings, and isolated noncompact export targets. This remains a
  presentation-only patch; Core stays at v0.4.1 and numerical responses and tables are unchanged.

## [0.1.1] - 2026-07-30

- Publish the related-tool-navigation Pages source as a checksum-addressed patch release so the
  deployed app, annotated tag, and release artifacts resolve to the same commit.
- Constrain the two-column layout and resize Plotly after the results panel is visible so the
  calculated app remains contained at a 390 px viewport; cover this with a browser regression.
- Adopt the checksum-bound `wald-inference` v0.4.1 wheel with its precision-bracketing,
  extreme-support, and strict ratio-underflow repairs. The six-rule focused contract and exports
  remain unchanged; no formula is implemented locally.

## [0.1.0] - 2026-07-30

- Builds the initial focused forward Type S/M calibrator.
- Supports direct-SE and reported-95%-CI precision, relative information
  scaling, and all six canonical selected-claim rules.
- Provides fixed selected-claim, Type S, and Type M panels plus conditional
  observed exaggeration, scenario tables, reviewer text, CSV/PNG exports, and
  strict finite JSON.
- Exercises B04/B05/B07 integrated baseline parity and client-only
  privacy/accessibility guardrails.
- Keeps `wald-inference` as the sole numerical authority and pins the official
  0.3.0 wheel by URL and SHA-256 for local and browser execution.
- Verifies deterministic clean staging, Chromium and WebKit behavior, strict
  error handling, exports, accessibility, and client-only privacy.

[Unreleased]: https://github.com/reblocke/type-s-m-calibrator/compare/v0.1.5...HEAD
[0.1.5]: https://github.com/reblocke/type-s-m-calibrator/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/reblocke/type-s-m-calibrator/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/reblocke/type-s-m-calibrator/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/reblocke/type-s-m-calibrator/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/reblocke/type-s-m-calibrator/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/reblocke/type-s-m-calibrator/releases/tag/v0.1.0
