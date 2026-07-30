# Scientific Applet Template

[![CI](https://github.com/reblocke/scientific-applet-template/actions/workflows/ci.yml/badge.svg)](https://github.com/reblocke/scientific-applet-template/actions/workflows/ci.yml)

Reusable client-side Python scaffold for a focused scientific applet

This is an engineering template, not a statistical package or validated scientific tool. Its
two-number arithmetic demonstration exists only to prove the complete Python-to-worker-to-browser
path. Replace that demonstration and complete the author-action prompts before making a scientific
claim.

## Create an app

Use GitHub’s “Use this template” control, clone the new repository, then run the guarded
initializer once:

```bash
uv sync --locked
uv run python scripts/initialize_template.py \
  --repository-name compatibility-curve \
  --distribution-name compatibility-curve \
  --import-name compatibility_curve \
  --app-title "Wald Compatibility Curve" \
  --description "A focused client-side scientific applet"
```

The command validates names, updates package paths and repository metadata, removes
template-maintainer-only checks, writes an ignored replacement report, and fails if any required
template identity remains. It never enters or edits `.git`. A second run is refused unless
`--force` is explicit.

Review the diff, complete every `AUTHOR ACTION REQUIRED` prompt, then verify:

```bash
uv sync --locked
uv run playwright install chromium webkit
make verify
```

The initializer updates the existing lockfile identity, so `uv sync --locked` works immediately.
If dependencies are added or changed later, intentionally run `uv lock`, review `uv.lock`, and
rerun the full verification suite.

Detailed initialization and replacement guidance is in
[docs/TEMPLATE_USAGE.md](docs/TEMPLATE_USAGE.md).

## Architecture

```text
browser form
  -> dedicated Web Worker
  -> verified generated Python bundle
  -> template_applet.contract.calculate_json
  -> strict JSON response
  -> textual summary + Plotly hook + explicit exports
```

- `src/template_applet/` is the only source-of-truth Python package.
- `browser-stage.toml` lists the app and zero or more optional, exact-version external packages.
- `scripts/stage_browser_packages.py` discovers installed packages from the locked environment,
  removes stale stage output, and emits file, package, and bundle SHA-256 hashes.
- `web/pyodide_worker.js` verifies the manifest and every staged byte before loading Python. The
  main thread can terminate and restart the worker after a failure.
- `web/js/` separates inputs, runtime lifecycle, result rendering, exports, and accessibility.
- `web/assets/py/` is generated, ignored, and never hand-edited.

The template is copied at project creation time; it is not a shared runtime UI dependency.

## Optional external scientific core

The default stage has no external core. Add an installed, locked, pure-Python package to
`browser-stage.toml`:

```toml
pyodide_packages = ["numpy", "scipy"]

[[packages]]
role = "core"
distribution = "example-scientific-core"
import_name = "example_scientific_core"
version = "1.2.3"
source = "external"
artifact_url = "https://github.com/OWNER/REPO/releases/download/v1.2.3/example.whl"
artifact_sha256 = "REPLACE_WITH_THE_64_CHARACTER_SHA256"
```

Pin the same artifact in `pyproject.toml` and `uv.lock`. Staging fails on a version mismatch,
lock mismatch, artifact provenance mismatch, modified installed file, symlink, or unsafe package
shape. External packages must be pure Python, use one regular top-level package, and expose
`__version__`. List any Pyodide-provided dependencies in `pyodide_packages`.

## Browser and exports

The minimal responsive shell includes labels, linked error summaries, visible focus, an
`aria-live` status, a keyboard-operable advanced-controls pattern, a textual result, a table, and
a plot hook. Export helpers provide:

- CSV from an explicit column list;
- dashboard PNG;
- figure-only/manuscript PNG;
- copyable caption;
- deterministic filename slugs.

The example exports only the three displayed demonstration rows. Downstream apps must explicitly
define their own columns, figure dimensions, caption, and scope.

## Privacy

The application is static and client-side. It has no backend, database, telemetry, cookies,
browser storage, or input-bearing URL state. Inputs exist only in page and worker memory.
Static CDN requests load pinned runtime libraries and do not contain user values. See
[docs/PRIVACY.md](docs/PRIVACY.md).

## Commands

```bash
uv sync --locked
make stage-web
make fmt
make fmt-check
make lint
make test
make e2e
make e2e-webkit-smoke
make verify
make serve
make clean
```

`make verify` expects Chromium and WebKit to have been installed. CI runs the same targets. Pages
deploys the staged `web/` directory, and tagged releases rerun all checks before publishing a
deterministic source archive, browser-stage manifest, and checksums.

## Author checklist

Before calling an initialized app complete:

1. Define the scientific question, assumptions, input/output units, formula authorities,
   validation targets, limitations, and non-goals.
2. Replace the demo request, response, computation, chart, table, caption, and fixtures.
3. Decide whether an external released scientific core is required and pin it exactly.
4. Replace generic browser copy without overstating validation or clinical readiness.
5. Verify privacy, accessibility, strict JSON, Chromium, WebKit, cold initialization, and Pages.
6. Update citation, license applicability, hosted URL, maintenance status, decision records, and
   release notes.

## License and citation

Code is MIT licensed. Copyright (c) 2026 Brian Locke. `CITATION.cff` is valid template metadata,
but its author-action message must be resolved for the initialized scientific app.
