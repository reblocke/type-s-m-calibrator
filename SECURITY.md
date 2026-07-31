# Security Policy

## Supported versions

Security fixes are applied to the latest release and the current `main` branch. Older tags remain
reproducibility records and are not silently rewritten.

## Report a vulnerability privately

Use GitHub's **Report a vulnerability** control in this repository's Security tab:

<https://github.com/reblocke/type-s-m-calibrator/security/advisories/new>

Do not disclose vulnerability details in a public issue, pull request, discussion, commit, or
workflow log. If the private-reporting control is unavailable, use the repository's **Private
security coordination request** issue form. That public form records only that the control is
unavailable; do not identify the vulnerability class, affected component, reproduction, or impact
in that issue.

Include privately:

- the exact tag or full commit SHA;
- the affected Type S/M orchestration, strict response contract, browser stage, static interface,
  export, workflow, or release path;
- a minimal reproduction using synthetic values;
- expected and observed behavior;
- environment and browser versions when relevant; and
- any suspected exposure of credentials, user input, or release integrity.

Never send protected health information, patient-level data, credentials, unpublished restricted
data, or other sensitive material. Redact local paths and logs. A reproducer should use synthetic
values and the smallest safe artifact needed to demonstrate the issue.

## Scope distinctions

- A vulnerability or privacy defect belongs in private vulnerability reporting.
- A suspected discrepancy in Type S/M orchestration or presentation belongs in this repository's
  correction process.
- A suspected discrepancy in a Wald, selection-tail, Type S, Type M, or observed-exaggeration
  formula belongs to the authoritative
  [`wald-inference`](https://github.com/reblocke/wald-inference-core) repository; identify that
  upstream owner rather than copying a formula into this app.
- A routine, nonsensitive repository bug may use the public engineering issue form.
- Requests for clinical interpretation are out of scope. Publication in this repository does not
  establish clinical decision support or regulatory readiness.

Publishing a fixed release does not authorize moving an old tag or replacing an old release asset.
Preserve the affected record, publish a new version, and describe the affected range.
