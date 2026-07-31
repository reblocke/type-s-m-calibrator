# Contributing

## Repository scope

This repository owns the focused, client-side orchestration and presentation for forward Type S/M
calibration. Released `wald-inference` is the sole numerical and formula authority. Do not add or
copy a Wald, selection-tail, Type S, Type M, or observed-exaggeration formula here. Preserve the
six-part response, forward-only assumed-truth interpretation, selection conditioning, log-ratio
meaning, near-null behavior, plot-only cap, and nonposterior scope.

Use the public issue forms only for nonsensitive repository engineering and accessibility reports.
Report vulnerabilities through the private process in [SECURITY.md](SECURITY.md). Never place
credentials, protected health information, patient-level data, unpublished restricted data, or
other sensitive values in an issue, pull request, fixture, screenshot, URL, or workflow log.

## Change process

1. Start from the current `main` branch and make one reviewable change.
2. State assumptions, success criteria, silent-failure risks, and verification before editing.
3. Route a missing numerical primitive to a released `wald-inference` version before adopting it
   here.
4. Keep Python under `src/` as source of truth and regenerate browser Python with `make stage-web`.
5. Keep the official Core wheel exact-version, URL, and checksum bound.
6. Keep third-party GitHub Actions pinned to reviewed full commit SHAs with version comments.
7. Open a pull request and let all required checks complete before merging.

Do not add a backend, telemetry, persistence, cookies, hidden state, input-bearing URLs, uploads, or
new scientific scope as conveniences.

## Verification

Restore the locked environment and run the complete documented suite:

```bash
uv sync --locked
uv run playwright install chromium webkit
make scientific-test
make verify
git diff --check
git status --short
```

Document any skipped check or warning. A Core update additionally requires review of the upstream
release, exact artifact/checksum synchronization, clean staging without a sibling checkout, frozen
B04/B05/B07 parity, all-six-rule browser coverage, and scientific review.

## Release changes

A release change requires a reviewed pull request and a signed, annotated version tag pointing to
the exact reviewed merge commit. The tag must equal `v` plus the authoritative project version,
and that version needs a nonempty changelog section. The tag workflow:

1. cryptographically verifies the tag before executing repository code;
2. requires the verified tag target to be contained in protected `main` history and match the
   project version;
3. verifies the scientific, contract, privacy, staging, Chromium, and WebKit suite with read-only
   contents permission;
4. builds and checksums all assets before creating a release;
5. transfers the complete bundle to a narrowly write-enabled publishing job;
6. requires repository release immutability;
7. creates a draft stable release using only the current version's changelog section;
8. downloads and compares every draft asset and the release body; and
9. publishes only the verified draft once as stable.

Before creating the tag, enable immutable releases and configure a repository-scoped
Administration-read token as the `RELEASE_SETTINGS_READ_TOKEN` Actions secret. The publishing job
uses that secret only for the fail-closed settings query; release creation uses the job-scoped
GitHub token.

If a release job fails after draft creation, leave the release as a draft for inspection. Do not
replace assets or move a tag after publication.
