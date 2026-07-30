# Scientific Scope

## Focused question

For each candidate value treated as the true effect, and for a specified
future-study Wald standard error and selected-claim rule, the app reports:

1. the probability that a future study satisfies the rule;
2. the probability that a selected claim has the wrong sign (Type S);
3. the expected selected magnitude divided by true magnitude (Type M); and
4. when an observed estimate is supplied, its realized magnitude relative to
   each assumed truth.

The conditioning statement is essential: x-axis values are assumed true
effects. None of these outputs is a posterior probability or evidence
conditional on an observed dataset.

## Intended use

The app is an experimental educational and research-facing aid for examining
one-parameter Wald operating characteristics. It can support statistical
teaching, design critique, and sensitivity discussion. It is not a validated
clinical device, does not recommend treatment, and does not validate whether a
user-supplied threshold is clinically meaningful.

## Generative repeated-study model

Let:

```text
eta_true = assumed true effect on the working scale
eta_null = null value on the working scale
se       = hypothetical future-study working-scale standard error
delta    = (eta_true - eta_null) / se
Z        = (future estimate - eta_null) / se
```

The model is:

```text
Z ~ Normal(delta, 1)
```

Additive measures use the identity working scale. Odds ratios, risk ratios,
hazard ratios, incidence-rate ratios, and ratios of means use the natural-log
working scale. The app calls the released `wald-inference` 0.4.1
transformations and normal-tail routines; it does not implement these formulas
locally.

## Precision inputs

### Direct SE

The user supplies a finite positive SE on the working scale. For a ratio
measure this is a log-scale SE.

### Reported 95% CI

The core transforms both limits to the working scale and reconstructs the Wald
midpoint and SE. For symmetric working-scale limits:

```text
eta_mid = (eta_lower + eta_upper) / 2
se      = (eta_upper - eta_lower) / (2 * z_0.975)
```

The resulting precision is reused as a hypothetical future-study SE. The
reported CI does not determine the true effect. A separately supplied observed
estimate does not alter the reconstructed SE.

### Information multiplier

For positive multiplier `m`:

```text
se_scenario = se_current / sqrt(m)
```

This is relative one-parameter Wald information scaling, not an exact
study-specific sample-size calculation.

## Six selected-claim rules

Let:

```text
c2  = z_(1 - alpha / 2)
c1  = z_(1 - alpha)
tau = (eta_threshold - eta_null) / se
```

Each rule defines a selected set `A` on the future `Z` scale:

1. `two_sided_p_lt_alpha`

   ```text
   A = (-infinity, -c2) union (c2, infinity)
   ```

2. `one_sided_positive_p_lt_alpha`

   ```text
   A = (c1, infinity)
   ```

3. `one_sided_negative_p_lt_alpha`

   ```text
   A = (-infinity, -c1)
   ```

4. `ci_excludes_null_in_beneficial_direction`

   ```text
   positive claim: A = (c2, infinity)
   negative claim: A = (-infinity, -c2)
   ```

5. `estimate_exceeds_mcid_and_p_lt_alpha`

   ```text
   positive claim: A = (max(c2, tau), infinity)
   negative claim: A = (-infinity, min(-c2, tau))
   ```

6. `ci_excludes_mcid`

   ```text
   positive claim: A = (tau + c2, infinity)
   negative claim: A = (-infinity, tau - c2)
   ```

Threshold rules require a threshold above the null for a positive claim and
below the null for a negative claim. Alpha, direction, and threshold controls
are activated only when the chosen rule uses them. Reference thresholds are
display/scenario values; an active claim threshold defines the rule. Neither
is automatically a plausible true effect.

## Metrics and selection conditioning

Selected-claim probability is:

```text
P(selected | eta_true) = P(Z in A | delta)
```

Type S is conditional on selection and on a nonzero true-effect direction:

```text
Type S =
  P(Z in A and sign(Z) differs from sign(delta) | delta)
  / P(Z in A | delta)
```

Type M is conditional expected selected magnitude divided by true
working-scale magnitude:

```text
Type M = E(abs(Z) | Z in A, delta) / abs(delta)
```

The core evaluates the exact normal tail probabilities and truncated normal
first moment. The app does not simulate when the analytic result is available.

Observed exaggeration is separate:

```text
observed exaggeration =
  abs(eta_observed - eta_null) / abs(eta_true - eta_null)
```

It is a realized comparison under an assumed truth, not Type M and not a
posterior quantity. Supplying an observed estimate also creates an explicitly
optimistic/circular scenario that assumes that estimate is true.

For ratio measures, Type M and observed exaggeration use log-scale distance
from the ratio null. They are not natural-scale inflation factors for an odds,
risk, hazard, incidence-rate, or means ratio.

## Scenarios and grid

The null is always included. User-entered true effects, optional reference
thresholds, and an optional observed estimate can add scenario rows. The active
claim threshold remains a rule parameter and plot marker; it is not
automatically promoted to an assumed-truth scenario. Values are deduplicated on
the working scale with relative and absolute tolerance `1e-12`; the first
occurrence is retained and later source qualifications are merged into its
note.

The reviewer-text default is the first user scenario, otherwise the first
non-null reference-threshold scenario, otherwise the observed-estimate-as-truth
scenario, and otherwise the first retained row. Any row whose merged sources
include the observed estimate keeps the optimistic/circular qualification.
The CI-implied midpoint remains precision metadata and is not silently promoted
to an assumed-truth scenario; entering it in the optional observed-estimate
field makes that optimistic sensitivity analysis explicit.

An optional plausible range sets the curve endpoints. Otherwise the display
range spans the null plus or minus four scenario SEs and expands to include
scenario and threshold values. This is a visualization convention, not a
probability statement. Grid points are equally spaced on the working scale;
ratio-measure display axes are logarithmic.

## Undefined and display-only values

The core defines Type S, Type M, and observed exaggeration as `null` when
`abs(delta) <= 1e-12`. At the null there is no true direction for Type S and
the magnitude denominator for Type M is zero. Type S and Type M can also be
unavailable when selection probability is numerically zero, because the
conditioning event cannot be evaluated numerically.

JSON and CSV never use `NaN` or `Infinity`. Undefined values are JSON `null`
and CSV blanks; the scenario table uses an em dash plus a row or interpretation
note.

Type M and observed exaggeration can diverge near the null. Plot traces are
capped at 10× with 1× and 2× guides. This treatment is disclosed and applies
only to plotted y-values; the response contract, scenario table, reviewer
text, hover source data, and CSV retain uncapped values. The disclosure is
embedded in the plot title so it remains visible in standalone plot PNGs.

## Outputs

The focused response contains exactly:

```text
meta
precision
selection_rule
grid
scenarios
warnings
```

The grid contains:

```text
true_effect_display
true_effect_working
standardized_true_effect
selected_claim_probability
type_s
type_m
expected_selected_abs_z
observed_exaggeration_optional
```

The UI presents fixed panels A–C for selected-claim probability, Type S, and
Type M. Panel D is omitted unless an observed estimate is supplied. The table,
caption, reviewer text, and focused JSON state assumed-truth conditioning and
the selected rule.

The curve CSV has exactly these eight numeric columns:

```text
true_effect_display
true_effect_working
standardized_true_effect
selected_claim_probability
type_s
type_m
expected_selected_abs_z
observed_exaggeration
```

The CSV deliberately does not repeat the rule, alpha, precision, or
conditioning metadata. Probability columns remain numeric proportions on
`[0, 1]`, whereas the scenario table formats them as percentages. The CSV is
not self-contained and must travel with the caption or focused JSON response
when reused.

## Limitations and non-goals

- The model is a one-parameter normal/Wald approximation.
- Inputs do not reconstruct an original fitted-model likelihood.
- User thresholds and assumed truths are not clinically validated.
- Relative information is not exact sample size.
- No inverse precision solver is included.
- No observed-data confidence/support display is included.
- No posterior probability, multiple-parameter model, multiplicity
  adjustment, or study-specific sampling design is included.
- The app does not diagnose, treat, or direct clinical care.

## Authorities

Numerical implementation and runtime authority is the exact official
`wald-inference` 0.4.1 artifact recorded in `uv.lock` and
`browser-stage.toml`.

Methodology reference:

Gelman A, Carlin J. Beyond Power Calculations: Assessing Type S (Sign) and Type
M (Magnitude) Errors. *Perspectives on Psychological Science*. 2014;9(6):
641–651. <https://doi.org/10.1177/1745691614551642>. Retrieved 2026-06-14.

No external figure, table, dataset, or substantial source text is copied into
this repository.
