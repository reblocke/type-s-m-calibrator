# Decisions

## 2026-07-29 — Functional Python core and browser worker

Python is the calculation source of truth. The static UI sends strict JSON to a restartable
Web Worker running exact-version Pyodide. This prevents Python initialization and calculation
from blocking the main UI thread.

## 2026-07-29 — Generated, verified browser stage

The installed locked app and optional external packages are staged from a TOML manifest.
Generated files are ignored. File, package, and aggregate hashes are verified before Python is
loaded, avoiding a manually synchronized JavaScript file list.

## 2026-07-29 — No live shared UI dependency

The repository is a creation-time template, not a runtime framework. Initialized apps may evolve
independently without a shared component release becoming an application availability risk.

## 2026-07-29 — Strict client-side privacy boundary

There is no backend, telemetry, persistence, cookie, or input-bearing URL. Static CDN requests do
not include user input.

## New decision record

AUTHOR ACTION REQUIRED: append dated decisions that change scientific meaning, runtime,
dependencies, validation, privacy, exports, accessibility, or maintenance. Do not silently
rewrite historical decisions.
