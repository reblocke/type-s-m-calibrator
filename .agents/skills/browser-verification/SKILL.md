---
name: browser-verification
description: Verify Pyodide worker, staging, static UI, exports, or Pages changes.
---

# Browser Verification

- Keep `src/` as source of truth and regenerate the ignored browser stage.
- Verify manifest schema, versions, paths, file/package/bundle hashes, and stale-file removal.
- Run Python/contract tests, Chromium E2E, and WebKit smoke.
- Confirm relative Pages paths, `.nojekyll`, worker restart, strict JSON, textual results, exports,
  keyboard use, and visible focus.
- Do not add persistence, telemetry, external APIs, or input-bearing URLs.
