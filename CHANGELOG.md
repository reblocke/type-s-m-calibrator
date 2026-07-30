# Changelog

All notable changes use a release-oriented record here. This repository follows
[Semantic Versioning](https://semver.org/).

## [Unreleased]

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

[Unreleased]: https://github.com/reblocke/type-s-m-calibrator/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/reblocke/type-s-m-calibrator/releases/tag/v0.1.0
