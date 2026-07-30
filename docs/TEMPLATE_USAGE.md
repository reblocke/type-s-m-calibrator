# Template Usage

## 1. Create and initialize

Create a repository with GitHub’s template control, clone it, restore the locked environment, and
run:

```bash
uv run python scripts/initialize_template.py \
  --repository-name compatibility-curve \
  --distribution-name compatibility-curve \
  --import-name compatibility_curve \
  --app-title "Wald Compatibility Curve" \
  --description "A focused client-side scientific applet"
```

Accepted naming rules:

- repository: lowercase kebab-case;
- distribution: normalized lowercase Python project name;
- import: lowercase Python identifier;
- title and description: single-line non-empty text.

The initializer changes only working-tree files. It renames `src/template_applet/`, updates the
identity in code, metadata, docs, workflows, HTML, tests, and lockfile, removes template-only
provenance/self-test files, and writes `.applet-template-initialized.json`. It does not modify
`.git`. Without `--force`, an initialized repository is rejected.

## 2. Establish scientific authority

Complete `SCIENTIFIC_SCOPE.md` and `VALIDATION.md` before replacing the demonstration. Identify
the controlling source for each formula. If a released core owns the method, consume it rather
than copying formulas into the app.

## 3. Replace the demonstration

Replace:

- request/response dataclasses in `src/<import_name>/models.py`;
- the calculation and strict contract in `contract.py`;
- form inputs and parsing;
- textual result, table, plot, caption, and explicit export columns;
- unit, contract, property, and browser fixtures.

Keep `allow_nan=False` and the worker’s finite-number checks. User-correctable validation errors
may be displayed; unexpected Python details, paths, and tracebacks must not be exposed.

## 4. Configure browser packages

Keep the project app entry in `browser-stage.toml`. Add zero or more exact-version external
packages. For release URLs, configure both artifact URL and SHA-256, and use the same direct URL
pin in `pyproject.toml` and `uv.lock`. Add Pyodide-provided dependencies to
`pyodide_packages`.

Run `make stage-web`; never edit `web/assets/py/`.

## 5. Complete public metadata

Resolve every `AUTHOR ACTION REQUIRED` prompt. Verify README, scientific scope, validation,
privacy, decisions, maintenance, changelog, citation, license applicability, UI footer, hosted
URL, core version, repository description, and related-tool links.

## 6. Verify and publish

```bash
uv sync --locked
uv run playwright install chromium webkit
make verify
git diff --check
git status --short
```

Open a reviewed pull request. Confirm CI, template self-test (template repository only), Pages,
and the deployed app. Tag only the exact reviewed merge commit.
