# Codex AGENTS

## Purpose

- This repository is a reusable engineering scaffold for a static, client-side, Python-first
  scientific applet.
- It contains no scientific formula. The arithmetic demonstration is conspicuously replaceable.
- Python under `src/template_applet/` is source of truth; generated browser Python is ignored.

## Commands

- Setup: `uv sync --locked`
- Stage: `make stage-web`
- Format: `make fmt`
- Verify formatting: `make fmt-check`
- Lint: `make lint`
- Python/integration/template tests: `make test`
- Chromium: `make e2e`
- WebKit smoke: `make e2e-webkit-smoke`
- Full verification: `make verify`

## Working rules

- Before non-trivial changes, state assumptions, ambiguities, tradeoffs, success criteria, risks,
  expected files, and verification commands.
- Keep scientific methods out of the template demonstration. An initialized app must document and
  validate its own formula authority.
- Run staging; never hand-edit `web/assets/py/`.
- Keep external scientific dependencies exact-version locked and, for URL artifacts, checksum
  bound in package metadata, `uv.lock`, and `browser-stage.toml`.
- Preserve client-side privacy: no backend, telemetry, persistence, cookies, PHI logging, or
  input-bearing URLs.
- Keep accessible textual output; a plot must never be the sole carrier of a result.
- Use `uv`, Ruff, pytest, Hypothesis, and Playwright; do not add parallel toolchains casually.

## Skills

- Plan non-trivial work with `.agents/skills/implementation-strategy/SKILL.md`.
- Verify browser/staging work with `.agents/skills/browser-verification/SKILL.md`.
- Review input or deployment changes with `.agents/skills/privacy-review/SKILL.md`.
- Synchronize behavior and public docs with `.agents/skills/docs-sync/SKILL.md`.

## Done criteria

- Relevant unit, contract, property, initializer, staging, privacy, Chromium, and WebKit checks
  pass.
- Stage output is reproducible from a clean checkout without a sibling repository.
- Scientific scope, validation, privacy, citation, maintenance, and decisions are truthful.
- The final report names commands, results, generated files, limitations, and residual risks.
