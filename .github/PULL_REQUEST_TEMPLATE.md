## Scope

Describe the engineering, scientific-orchestration, documentation, governance, or maintenance
problem addressed. Name `wald-inference` when its released numerical behavior owns the issue.

## Risk and release impact

Describe silent-failure risks, Type S/M interpretation, privacy/accessibility implications,
generated-stage effects, and whether the change requires a new release.

## Verification

List the exact commands run and their outcomes. Include skipped checks and warnings.

## Checklist

- [ ] No Wald, selection-tail, Type S, Type M, or observed-exaggeration formula was added or copied
      into this repository.
- [ ] The six-part response and forward-only assumed-truth, selection-conditioned, log-ratio,
      near-null, plot-only-cap, and nonposterior meanings remain intact.
- [ ] Public copy stays within validated functionality and does not imply clinical or regulatory
      readiness.
- [ ] Examples and fixtures are synthetic and contain no credentials, sensitive data, or protected
      health information.
- [ ] No backend, telemetry, persistence, cookies, hidden state, upload, or input-bearing URL was
      added.
- [ ] Generated Python under `web/assets/py/` was produced by `make stage-web`, not edited by hand.
- [ ] Every third-party GitHub Action remains pinned to a full commit SHA with a version comment.
- [ ] The official Core version, URL, and checksum remain synchronized across package metadata,
      lockfile, browser-stage configuration, docs, and tests.
- [ ] `uv sync --locked`, `make scientific-test`, and `make verify` pass.
- [ ] README, scientific scope, validation, privacy, decisions, maintenance, runtime provenance,
      citation, and changelog were reviewed for synchronization.
