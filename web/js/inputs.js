const DIRECTION_RULES = new Set([
  "ci_excludes_null_in_beneficial_direction",
  "estimate_exceeds_mcid_and_p_lt_alpha",
  "ci_excludes_mcid",
]);
const THRESHOLD_RULES = new Set([
  "estimate_exceeds_mcid_and_p_lt_alpha",
  "ci_excludes_mcid",
]);
const RATIO_EFFECTS = new Set([
  "odds_ratio",
  "risk_ratio",
  "hazard_ratio",
  "incidence_rate_ratio",
  "ratio_of_means",
]);

function parseFiniteNumber(form, name, label, { optional = false } = {}) {
  const control = form.elements.namedItem(name);
  const value = control.value.trim();
  if (value === "" && optional) {
    return { value: null };
  }
  if (value === "") {
    control.setAttribute("aria-invalid", "true");
    return { error: { controlId: control.id, message: `${label} is required.` } };
  }
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    control.setAttribute("aria-invalid", "true");
    return {
      error: { controlId: control.id, message: `${label} must be a finite number.` },
    };
  }
  return { value: parsed };
}

function parseInteger(form, name, label) {
  const parsed = parseFiniteNumber(form, name, label);
  if (parsed.error) {
    return parsed;
  }
  if (!Number.isInteger(parsed.value)) {
    const control = form.elements.namedItem(name);
    control.setAttribute("aria-invalid", "true");
    return { error: { controlId: control.id, message: `${label} must be an integer.` } };
  }
  return parsed;
}

function parseNumberList(form, name, label) {
  const control = form.elements.namedItem(name);
  const text = control.value.trim();
  if (text === "") {
    return { value: [] };
  }
  const values = text.split(",").map((item) => item.trim());
  const invalid = values.find((item) => item === "" || !Number.isFinite(Number(item)));
  if (invalid !== undefined) {
    control.setAttribute("aria-invalid", "true");
    return {
      error: {
        controlId: control.id,
        message: `${label} must be comma-separated finite numbers.`,
      },
    };
  }
  return { value: values.map(Number) };
}

function directionForRule(form, rule) {
  if (rule === "one_sided_negative_p_lt_alpha") {
    return "negative";
  }
  if (rule === "one_sided_positive_p_lt_alpha" || rule === "two_sided_p_lt_alpha") {
    return "positive";
  }
  return form.elements.namedItem("claim_direction").value;
}

export function updateControlState(form) {
  const precisionMode = form.elements.namedItem("precision_mode").value;
  const direct = precisionMode === "direct_se";
  const directGroup = document.querySelector("#direct-se-fields");
  const ciGroup = document.querySelector("#ci-fields");
  directGroup.hidden = !direct;
  ciGroup.hidden = direct;
  form.elements.namedItem("standard_error").disabled = !direct;
  form.elements.namedItem("ci_lower").disabled = direct;
  form.elements.namedItem("ci_upper").disabled = direct;

  const rule = form.elements.namedItem("selection_rule").value;
  const directionActive = DIRECTION_RULES.has(rule);
  const thresholdActive = THRESHOLD_RULES.has(rule);
  const directionGroup = document.querySelector("#claim-direction-field");
  const thresholdGroup = document.querySelector("#claim-threshold-field");
  directionGroup.hidden = !directionActive;
  thresholdGroup.hidden = !thresholdActive;
  form.elements.namedItem("claim_direction").disabled = !directionActive;
  form.elements.namedItem("claim_threshold").disabled = !thresholdActive;

  const active = ["Alpha"];
  if (directionActive) {
    active.push("claim direction");
  }
  if (thresholdActive) {
    active.push("claim threshold");
  }
  document.querySelector("#active-rule-controls").textContent =
    `Active rule controls: ${active.join(", ")}.`;

  const effectType = form.elements.namedItem("effect_type").value;
  const workingScale = RATIO_EFFECTS.has(effectType) ? "log" : "additive";
  document.querySelector("#se-scale-note").textContent =
    `Enter standard error on the ${workingScale} working scale.`;
  document.querySelector("#axis-spacing-note").textContent = RATIO_EFFECTS.has(effectType)
    ? "The assumed-true-effect axis is logarithmic for this ratio measure."
    : "The assumed-true-effect axis is linear for this additive measure.";
}

export function applyEffectDefaults(form) {
  const ratio = RATIO_EFFECTS.has(form.elements.namedItem("effect_type").value);
  form.elements.namedItem("null_value").value = ratio ? "1" : "0";
  form.elements.namedItem("claim_threshold").value = ratio ? "1.25" : "0.2";
  form.elements.namedItem("true_effect_scenarios").value = ratio
    ? "1.1, 1.5, 2"
    : "0.1, 0.3";
  form.elements.namedItem("ci_lower").value = ratio ? "1.2" : "0.11";
  form.elements.namedItem("ci_upper").value = ratio ? "2.7" : "0.73";
}

export function readRequest(form) {
  const precisionMode = form.elements.namedItem("precision_mode").value;
  const selectionRule = form.elements.namedItem("selection_rule").value;
  const direct = precisionMode === "direct_se";
  const thresholdActive = THRESHOLD_RULES.has(selectionRule);

  const parsed = {
    alpha: parseFiniteNumber(form, "alpha", "Alpha"),
    ciLower: direct
      ? { value: null }
      : parseFiniteNumber(form, "ci_lower", "Lower 95% confidence limit"),
    ciUpper: direct
      ? { value: null }
      : parseFiniteNumber(form, "ci_upper", "Upper 95% confidence limit"),
    claimThreshold: thresholdActive
      ? parseFiniteNumber(form, "claim_threshold", "Claim threshold")
      : { value: null },
    gridPoints: parseInteger(form, "grid_points", "Grid points"),
    informationMultiplier: parseFiniteNumber(
      form,
      "information_multiplier",
      "Information multiplier",
    ),
    nullValue: parseFiniteNumber(form, "null_value", "Null value"),
    observedEstimate: parseFiniteNumber(form, "observed_estimate", "Observed estimate", {
      optional: true,
    }),
    plausibleMax: parseFiniteNumber(
      form,
      "plausible_true_effect_max",
      "Plausible true-effect maximum",
      { optional: true },
    ),
    plausibleMin: parseFiniteNumber(
      form,
      "plausible_true_effect_min",
      "Plausible true-effect minimum",
      { optional: true },
    ),
    standardError: direct
      ? parseFiniteNumber(form, "standard_error", "Working-scale standard error")
      : { value: null },
    trueEffects: parseNumberList(
      form,
      "true_effect_scenarios",
      "Assumed true-effect scenarios",
    ),
    referenceThresholds: parseNumberList(
      form,
      "reference_thresholds",
      "Reference thresholds",
    ),
  };
  const errors = Object.values(parsed)
    .map((result) => result.error)
    .filter(Boolean);
  if ((parsed.plausibleMin.value === null) !== (parsed.plausibleMax.value === null)) {
    const control =
      parsed.plausibleMin.value === null
        ? form.elements.namedItem("plausible_true_effect_min")
        : form.elements.namedItem("plausible_true_effect_max");
    control.setAttribute("aria-invalid", "true");
    errors.push({
      controlId: control.id,
      message: "Supply both plausible-range endpoints or leave both blank.",
    });
  }
  if (errors.length > 0) {
    return { errors, request: null };
  }
  return {
    errors: [],
    request: {
      alpha: parsed.alpha.value,
      ci_lower: parsed.ciLower.value,
      ci_upper: parsed.ciUpper.value,
      claim_direction: directionForRule(form, selectionRule),
      claim_threshold: parsed.claimThreshold.value,
      effect_type: form.elements.namedItem("effect_type").value,
      grid_points: parsed.gridPoints.value,
      information_multiplier: parsed.informationMultiplier.value,
      null_value: parsed.nullValue.value,
      observed_estimate: parsed.observedEstimate.value,
      plausible_true_effect_max: parsed.plausibleMax.value,
      plausible_true_effect_min: parsed.plausibleMin.value,
      precision_mode: precisionMode,
      reference_thresholds: parsed.referenceThresholds.value,
      selection_rule: selectionRule,
      standard_error: parsed.standardError.value,
      true_effect_scenarios: parsed.trueEffects.value,
    },
  };
}
