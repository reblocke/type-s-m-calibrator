# Validation

## Template evidence

The template verifies only its engineering contract:

- typed request/response and strict JSON;
- a deterministic replace-me arithmetic calculation;
- exact-version, hash-manifested browser staging;
- worker load, validation error, recovery, and rendering;
- CSV, dashboard PNG, figure PNG, and caption hooks;
- accessibility and privacy smoke tests;
- initializer identity exhaustion and disposable-app cold start;
- Chromium full E2E and WebKit initial smoke.

This evidence does not validate a downstream scientific method.

## Scientific validation targets

AUTHOR ACTION REQUIRED: identify an independent oracle or primary reference for each calculation.
Define fixture provenance, edge cases, acceptable tolerances, and why each tolerance is
scientifically appropriate.

## Browser parity

AUTHOR ACTION REQUIRED: compare local Python results with Pyodide results using frozen,
source-controlled fixtures. Record Python, package, Pyodide, and browser versions.

## Interpretation and display

AUTHOR ACTION REQUIRED: verify that labels, units, defaults, warnings, plots, table columns,
captions, and exports communicate the same validated result.

## Release evidence

For each release, record:

- exact commit and tag;
- locked dependency and core versions;
- stage manifest and checksums;
- unit/property/contract results;
- Chromium and WebKit results;
- hosted Pages smoke;
- known limitations and skipped checks.
