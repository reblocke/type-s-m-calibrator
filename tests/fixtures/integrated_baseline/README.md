# Integrated baseline fixture provenance

These compact scenario targets are derived from the frozen integrated
`reblocke/conf_curve_likelihood` baseline:

- behavior source commit: `830756ecb11b4e8161f8dfe1fc75afc346ef4467`;
- fixture-bearing freeze merge: `5fd501dd947d9b951d736014cfc2b310efa5e7b0`;
- annotated tag: `pre-split-baseline-2026-07-29`;
- original files: `tests/golden/requests/*.json` and
  `tests/golden/responses/*.json`;
- extracted cases: B04, B05, B07a, and B07b.

The JSON keeps only inputs and forward-design values relevant to this focused
app. It intentionally excludes observed-data curves and inverse-precision
outputs. Values were copied without recalculation. Tests compare floating
results with a tight tolerance because the canonical Core v0.3 selected-claim
API makes null alpha exact while the frozen legacy Type S/M probability field
can differ by a few floating-point ULPs.

The focused regression also asserts exact retained scenario order and source:
null, user entries in input order, reference entries in input order, then the
optional observed-estimate-as-truth row. An active claim threshold remains rule
metadata and is not automatically added as an assumed-truth row. Those
adapter-level assertions are local ticket decisions, not copied numerical
fixture values.
