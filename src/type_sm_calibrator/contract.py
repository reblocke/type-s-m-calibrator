"""Strict JSON boundary for forward Type S/M design calibration."""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from typing import Any

import wald_inference
from wald_inference import (
    design_metrics_for_true_effects,
    from_working_scale,
    get_effect_spec,
    information_scaled_standard_error,
    reconstruct_wald_from_95_ci,
    selected_claim_probability,
    selection_rule_spec,
    to_working_scale,
)

from .models import CalibrationRequest, CalibrationResponse, ValidationError
from .version import __version__

RULES_REQUIRING_DIRECTION = {
    "ci_excludes_null_in_beneficial_direction",
    "estimate_exceeds_mcid_and_p_lt_alpha",
    "ci_excludes_mcid",
}
RULES_REQUIRING_THRESHOLD = {
    "estimate_exceeds_mcid_and_p_lt_alpha",
    "ci_excludes_mcid",
}
ALL_SELECTION_RULES = (
    "two_sided_p_lt_alpha",
    "one_sided_positive_p_lt_alpha",
    "one_sided_negative_p_lt_alpha",
    "ci_excludes_null_in_beneficial_direction",
    "estimate_exceeds_mcid_and_p_lt_alpha",
    "ci_excludes_mcid",
)
SCENARIO_DEDUP_REL_TOLERANCE = 1e-12
SCENARIO_DEDUP_ABS_TOLERANCE = 1e-12
PLOT_EXAGGERATION_CAP = 10.0
DEFAULT_GRID_HALF_WIDTH_STANDARD_ERRORS = 4.0
CORE_PROBABILITY_REL_TOLERANCE = 3e-14
CORE_PROBABILITY_ABS_TOLERANCE = 3e-16


def _reject_nonstandard_constant(value: str) -> None:
    raise ValidationError(f"Non-finite JSON constant is not allowed: {value}.")


def _call_core(function, /, *args, **kwargs):
    """Translate the released core's user-facing errors to this app boundary."""

    try:
        return function(*args, **kwargs)
    except wald_inference.ValidationError as exc:
        raise ValidationError(str(exc)) from exc


def _working_value(effect_type: str, value: float) -> float:
    return float(_call_core(to_working_scale, effect_type, value))


def _display_value(effect_type: str, value: float) -> float:
    return float(_call_core(from_working_scale, effect_type, value))


def _validate_request_semantics(request: CalibrationRequest) -> None:
    if request.selection_rule not in ALL_SELECTION_RULES:
        valid = ", ".join(ALL_SELECTION_RULES)
        raise ValidationError(f"Unsupported selected-claim rule. Expected one of: {valid}.")
    if request.claim_direction not in {"positive", "negative"}:
        raise ValidationError("Claim direction must be 'positive' or 'negative'.")
    if not 0 < request.alpha < 1:
        raise ValidationError("Alpha must be between 0 and 1.")
    if request.information_multiplier <= 0:
        raise ValidationError("Information multiplier must be greater than 0.")

    needs_threshold = request.selection_rule in RULES_REQUIRING_THRESHOLD
    if needs_threshold and request.claim_threshold is None:
        raise ValidationError("Claim threshold is required for the selected rule.")
    if not needs_threshold and request.claim_threshold is not None:
        raise ValidationError("Claim threshold must be blank for the selected rule.")

    plausible_pair = (
        request.plausible_true_effect_min,
        request.plausible_true_effect_max,
    )
    if (plausible_pair[0] is None) != (plausible_pair[1] is None):
        raise ValidationError(
            "Plausible true-effect minimum and maximum must be supplied together."
        )
    if (
        plausible_pair[0] is not None
        and plausible_pair[1] is not None
        and plausible_pair[0] >= plausible_pair[1]
    ):
        raise ValidationError("Plausible true-effect minimum must be less than the maximum.")

    if request.precision_mode == "direct_se":
        if request.standard_error is None:
            raise ValidationError("Working-scale standard error is required in direct-SE mode.")
        if request.standard_error <= 0:
            raise ValidationError("Working-scale standard error must be positive.")
        if request.ci_lower is not None or request.ci_upper is not None:
            raise ValidationError("Confidence limits must be blank in direct-SE mode.")
    else:
        if request.standard_error is not None:
            raise ValidationError("Working-scale standard error must be blank in CI mode.")
        if request.ci_lower is None or request.ci_upper is None:
            raise ValidationError("Both 95% confidence limits are required in CI mode.")


def _precision(
    request: CalibrationRequest,
    *,
    effect_spec,
) -> tuple[dict[str, Any], float, float, list[str]]:
    warnings: list[str] = []
    if request.precision_mode == "direct_se":
        assert request.standard_error is not None
        current_se = request.standard_error
        ci_details: dict[str, Any] = {
            "ci_lower_display": None,
            "ci_upper_display": None,
            "ci_implied_midpoint_display": None,
            "ci_reconstruction_method": None,
        }
        source_note = (
            "The entered standard error is interpreted on the log working scale."
            if effect_spec.family == "ratio"
            else "The entered standard error is interpreted on the additive working scale."
        )
    else:
        assert request.ci_lower is not None and request.ci_upper is not None
        reconstruction = _call_core(
            reconstruct_wald_from_95_ci,
            effect_type=request.effect_type,
            lower=request.ci_lower,
            upper=request.ci_upper,
            null_value=request.null_value,
        )
        current_se = float(reconstruction.standard_error)
        ci_details = {
            "ci_lower_display": reconstruction.lower_display,
            "ci_upper_display": reconstruction.upper_display,
            "ci_implied_midpoint_display": reconstruction.estimate_display,
            "ci_reconstruction_method": reconstruction.se_method,
        }
        warnings.extend(reconstruction.warnings)
        source_note = (
            "The reported 95% CI reconstructs current working-scale precision. "
            "That precision is reused for a hypothetical future study; the observed CI does "
            "not determine the true effect."
        )

    scenario_se = float(
        _call_core(
            information_scaled_standard_error,
            current_se,
            request.information_multiplier,
        )
    )
    working_scale_note = (
        "Ratio measures are analyzed on the log scale. Type M and observed exaggeration use "
        "distance from the log null, not a natural-scale ratio."
        if effect_spec.family == "ratio"
        else "Additive measures are analyzed on their identity working scale."
    )
    precision = {
        "mode": request.precision_mode,
        "current_se_working": current_se,
        "scenario_se_working": scenario_se,
        "information_multiplier": request.information_multiplier,
        **ci_details,
        "source_note": source_note,
        "working_scale_note": working_scale_note,
        "information_note": (
            "The multiplier changes only hypothetical design precision: "
            "scenario SE = current SE / sqrt(information multiplier)."
        ),
    }
    return precision, current_se, scenario_se, warnings


def _grid_range_working(
    request: CalibrationRequest,
    *,
    null_working: float,
    scenario_se: float,
    scenario_working_values: Sequence[float],
    threshold_working: float | None,
    observed_working: float | None,
) -> tuple[float, float]:
    if request.plausible_true_effect_min is not None:
        assert request.plausible_true_effect_max is not None
        lower = _working_value(request.effect_type, request.plausible_true_effect_min)
        upper = _working_value(request.effect_type, request.plausible_true_effect_max)
        if lower >= upper:
            raise ValidationError(
                "Plausible true-effect minimum must be less than the maximum on the working scale."
            )
        return lower, upper

    anchors = [
        null_working - DEFAULT_GRID_HALF_WIDTH_STANDARD_ERRORS * scenario_se,
        null_working + DEFAULT_GRID_HALF_WIDTH_STANDARD_ERRORS * scenario_se,
        null_working,
        *scenario_working_values,
    ]
    if threshold_working is not None:
        anchors.append(threshold_working)
    if observed_working is not None:
        anchors.append(observed_working)
    lower = min(anchors)
    upper = max(anchors)
    if not math.isfinite(lower) or not math.isfinite(upper) or lower >= upper:
        raise ValidationError("Could not construct a finite assumed-true-effect plot range.")
    return lower, upper


def _linear_grid(lower: float, upper: float, count: int) -> list[float]:
    span = upper - lower
    if not math.isfinite(span) or span <= 0:
        raise ValidationError("Assumed-true-effect plot range must be finite and positive.")
    values = [lower + span * index / (count - 1) for index in range(count)]
    values[0] = lower
    values[-1] = upper
    if not all(math.isfinite(value) for value in values):
        raise ValidationError("Assumed-true-effect grid exceeds the finite numeric range.")
    return values


def _is_duplicate(value: float, existing: Sequence[float]) -> bool:
    return any(
        math.isclose(
            value,
            prior,
            rel_tol=SCENARIO_DEDUP_REL_TOLERANCE,
            abs_tol=SCENARIO_DEDUP_ABS_TOLERANCE,
        )
        for prior in existing
    )


def _scenario_candidates(
    request: CalibrationRequest,
    *,
    null_working: float,
    observed_working: float | None,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = [
        {
            "source": "null",
            "label": "Null",
            "display": request.null_value,
            "working": null_working,
            "note": "Type S and Type M are undefined at the null.",
        }
    ]
    candidates.extend(
        {
            "source": "user_assumed_true_effect",
            "label": f"Assumed true effect: {value:g}",
            "display": value,
            "working": _working_value(request.effect_type, value),
            "note": None,
        }
        for value in request.true_effect_scenarios
    )
    candidates.extend(
        {
            "source": "reference_threshold",
            "label": f"Reference threshold as truth: {value:g}",
            "display": value,
            "working": _working_value(request.effect_type, value),
            "note": (
                "This display/reference threshold is treated as an assumed true effect in "
                "this row; it is not the active claim threshold."
            ),
        }
        for value in request.reference_thresholds
    )
    if observed_working is not None:
        assert request.observed_estimate is not None
        candidates.append(
            {
                "source": "observed_estimate_as_truth",
                "label": f"Observed estimate as truth: {request.observed_estimate:g}",
                "display": request.observed_estimate,
                "working": observed_working,
                "note": (
                    "Optimistic/circular scenario: the observed estimate is being assumed true. "
                    "It is not an estimate of the true-effect distribution."
                ),
            }
        )

    retained: list[dict[str, Any]] = []
    retained_working: list[float] = []
    for candidate in candidates:
        working = float(candidate["working"])
        if _is_duplicate(working, retained_working):
            duplicate_index = next(
                index
                for index, prior in enumerate(retained_working)
                if math.isclose(
                    working,
                    prior,
                    rel_tol=SCENARIO_DEDUP_REL_TOLERANCE,
                    abs_tol=SCENARIO_DEDUP_ABS_TOLERANCE,
                )
            )
            retained_candidate = retained[duplicate_index]
            retained_candidate["merged_sources"].append(candidate["source"])
            if candidate["note"]:
                existing_note = retained_candidate["note"]
                retained_candidate["note"] = (
                    candidate["note"]
                    if existing_note is None
                    else f"{existing_note} {candidate['note']}"
                )
            if candidate["source"] == "observed_estimate_as_truth":
                retained_candidate["label"] += " (also the observed estimate)"
            continue
        candidate["merged_sources"] = [candidate["source"]]
        retained.append(candidate)
        retained_working.append(working)
    return retained


def _reviewer_text(
    scenario: dict[str, Any],
    *,
    request: CalibrationRequest,
    effect_spec,
    rule_label: str,
) -> str:
    probability = scenario["selected_claim_probability"]
    type_s = scenario["type_s"]
    type_m = scenario["type_m"]
    zero_selection = probability == 0.0 or scenario["expected_selected_abs_z"] is None
    undefined_reason = (
        "unavailable because selected-claim probability is numerically zero"
        if zero_selection
        else "undefined at or near the null"
    )
    metric_parts = [f"selected-claim probability {probability:.4g}"]
    if type_s is None:
        metric_parts.append(f"Type S {undefined_reason}")
    else:
        metric_parts.append(f"conditional Type S probability {type_s:.4g}")
    if type_m is None:
        metric_parts.append(f"Type M {undefined_reason}")
    else:
        metric_parts.append(f"conditional Type M {type_m:.4g}x")
    scale_note = (
        "Type M uses log-scale distance from the null for this ratio measure."
        if effect_spec.family == "ratio"
        else "Type M uses additive working-scale distance from the null."
    )
    optimistic_note = (
        " This is an optimistic/circular scenario because the observed estimate is being "
        "treated as truth."
        if "observed_estimate_as_truth" in scenario["merged_sources"]
        else ""
    )
    return (
        f"Under {request.information_multiplier:g}x the current information "
        f"(hypothetical SE {scenario['scenario_se_working']:.4g}), and assuming the true "
        f"{effect_spec.label.lower()} is {scenario['true_effect_display']:.6g}, the rule "
        f"“{rule_label}” at alpha {request.alpha:g} gives "
        f"{', '.join(metric_parts)}. {scale_note} These are repeated-study operating "
        "characteristics conditional on the assumed true effect, not posterior probabilities "
        f"about an observed dataset.{optimistic_note}"
    )


def _metric_payload(
    true_effects_working: Sequence[float],
    *,
    request: CalibrationRequest,
    null_working: float,
    scenario_se: float,
    observed_working: float | None,
    threshold_working: float | None,
) -> tuple[list[float], list[Any]]:
    canonical_probabilities = _call_core(
        selected_claim_probability,
        list(true_effects_working),
        null_working=null_working,
        standard_error=scenario_se,
        alpha=request.alpha,
        selection_rule=request.selection_rule,
        claim_direction=request.claim_direction,
        threshold_working=threshold_working,
    )
    metrics = _call_core(
        design_metrics_for_true_effects,
        list(true_effects_working),
        null_working=null_working,
        se=scenario_se,
        estimate_working=observed_working,
        alpha=request.alpha,
        selection_rule=request.selection_rule,
        claim_direction=request.claim_direction,
        threshold_working=threshold_working,
    )
    probabilities = [float(value) for value in canonical_probabilities]
    if len(probabilities) != len(metrics):
        raise RuntimeError("Core selected-claim and Type S/M results have different lengths.")
    for probability, metric in zip(probabilities, metrics, strict=True):
        if not math.isclose(
            probability,
            metric.selected_claim_probability,
            rel_tol=CORE_PROBABILITY_REL_TOLERANCE,
            abs_tol=CORE_PROBABILITY_ABS_TOLERANCE,
        ):
            raise RuntimeError("Core selected-claim APIs disagree beyond the frozen tolerance.")
    return probabilities, metrics


def _selection_summary(
    request: CalibrationRequest,
    *,
    null_working: float,
    scenario_se: float,
    threshold_working: float | None,
) -> tuple[dict[str, Any], str]:
    spec = _call_core(
        selection_rule_spec,
        selection_rule=request.selection_rule,
        alpha=request.alpha,
        null_working=null_working,
        se=scenario_se,
        claim_direction=request.claim_direction,
        threshold_working=threshold_working,
    )
    requires_direction = request.selection_rule in RULES_REQUIRING_DIRECTION
    requires_threshold = request.selection_rule in RULES_REQUIRING_THRESHOLD
    if request.selection_rule == "one_sided_positive_p_lt_alpha":
        explanation = "Selects only sufficiently positive future Wald estimates."
    elif request.selection_rule == "one_sided_negative_p_lt_alpha":
        explanation = "Selects only sufficiently negative future Wald estimates."
    elif request.selection_rule == "two_sided_p_lt_alpha":
        explanation = "Selects either sufficiently positive or sufficiently negative estimates."
    elif request.selection_rule == "ci_excludes_null_in_beneficial_direction":
        explanation = "Selects only when the interval excludes the null in the chosen direction."
    elif request.selection_rule == "estimate_exceeds_mcid_and_p_lt_alpha":
        explanation = (
            "Selects only when the estimate crosses the claim threshold and the two-sided "
            "null test is below alpha."
        )
    else:
        explanation = (
            "Selects only when the interval excludes the claim threshold in the chosen direction."
        )
    active_controls = ["alpha"]
    if requires_direction:
        active_controls.append("claim_direction")
    if requires_threshold:
        active_controls.append("claim_threshold")
    return (
        {
            "key": spec.key,
            "label": spec.label,
            "alpha": spec.alpha,
            "claim_direction": (
                "positive"
                if request.selection_rule == "one_sided_positive_p_lt_alpha"
                else (
                    "negative"
                    if request.selection_rule == "one_sided_negative_p_lt_alpha"
                    else (spec.claim_direction if requires_direction else None)
                )
            ),
            "claim_threshold_display": (request.claim_threshold if requires_threshold else None),
            "claim_threshold_working": (threshold_working if requires_threshold else None),
            "requires_direction": requires_direction,
            "requires_threshold": requires_threshold,
            "active_controls": active_controls,
            "explanation": explanation,
        },
        spec.label,
    )


def _ensure_finite_payload(value: object, *, path: str = "response") -> None:
    if value is None or isinstance(value, str | bool):
        return
    if isinstance(value, int | float):
        if not math.isfinite(float(value)):
            raise RuntimeError(f"{path} contains a non-finite number.")
        return
    if isinstance(value, list | tuple):
        for index, item in enumerate(value):
            _ensure_finite_payload(item, path=f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _ensure_finite_payload(item, path=f"{path}.{key}")
        return
    raise RuntimeError(f"{path} contains a non-JSON value.")


def calculate(request: CalibrationRequest) -> CalibrationResponse:
    """Compute focused forward calibration through released core APIs."""

    _validate_request_semantics(request)
    effect_spec = _call_core(get_effect_spec, request.effect_type)
    null_working = _working_value(request.effect_type, request.null_value)
    threshold_working = (
        None
        if request.claim_threshold is None
        else _working_value(request.effect_type, request.claim_threshold)
    )
    observed_working = (
        None
        if request.observed_estimate is None
        else _working_value(request.effect_type, request.observed_estimate)
    )
    precision, current_se, scenario_se, warnings = _precision(
        request,
        effect_spec=effect_spec,
    )
    selection_summary, rule_label = _selection_summary(
        request,
        null_working=null_working,
        scenario_se=scenario_se,
        threshold_working=threshold_working,
    )

    candidates = _scenario_candidates(
        request,
        null_working=null_working,
        observed_working=observed_working,
    )
    scenario_working = [float(candidate["working"]) for candidate in candidates]
    grid_lower, grid_upper = _grid_range_working(
        request,
        null_working=null_working,
        scenario_se=scenario_se,
        scenario_working_values=scenario_working,
        threshold_working=threshold_working,
        observed_working=observed_working,
    )
    grid_working = _linear_grid(grid_lower, grid_upper, request.grid_points)
    grid_probability, grid_metrics = _metric_payload(
        grid_working,
        request=request,
        null_working=null_working,
        scenario_se=scenario_se,
        observed_working=observed_working,
        threshold_working=threshold_working,
    )
    scenario_probability, scenario_metrics = _metric_payload(
        scenario_working,
        request=request,
        null_working=null_working,
        scenario_se=scenario_se,
        observed_working=observed_working,
        threshold_working=threshold_working,
    )

    scenarios: list[dict[str, Any]] = []
    for index, (candidate, probability, metric) in enumerate(
        zip(candidates, scenario_probability, scenario_metrics, strict=True),
        start=1,
    ):
        note = candidate["note"]
        if (metric.type_s is None or metric.type_m is None) and candidate["source"] != "null":
            undefined_note = (
                "Selection-conditioned metrics are unavailable because selected-claim "
                "probability is numerically zero."
                if probability == 0.0 or metric.expected_selected_abs_z is None
                else "Type S and Type M are undefined at or near the null."
            )
            note = undefined_note if note is None else f"{note} {undefined_note}"
        row = {
            "id": f"scenario-{index}",
            "source": candidate["source"],
            "merged_sources": candidate["merged_sources"],
            "label": candidate["label"],
            "true_effect_display": float(candidate["display"]),
            "true_effect_working": float(candidate["working"]),
            "standardized_true_effect": float(metric.delta),
            "selected_claim_probability": probability,
            "type_s": metric.type_s,
            "type_m": metric.type_m,
            "expected_selected_abs_z": metric.expected_selected_abs_z,
            "observed_exaggeration": metric.observed_exaggeration,
            "current_se_working": current_se,
            "scenario_se_working": scenario_se,
            "information_multiplier": request.information_multiplier,
            "note": note,
        }
        row["reviewer_text"] = _reviewer_text(
            row,
            request=request,
            effect_spec=effect_spec,
            rule_label=rule_label,
        )
        scenarios.append(row)

    grid_display = [_display_value(request.effect_type, working) for working in grid_working]
    grid = {
        "true_effect_display": grid_display,
        "true_effect_working": grid_working,
        "standardized_true_effect": [float(metric.delta) for metric in grid_metrics],
        "selected_claim_probability": grid_probability,
        "type_s": [metric.type_s for metric in grid_metrics],
        "type_m": [metric.type_m for metric in grid_metrics],
        "expected_selected_abs_z": [metric.expected_selected_abs_z for metric in grid_metrics],
        "observed_exaggeration_optional": (
            None
            if observed_working is None
            else [metric.observed_exaggeration for metric in grid_metrics]
        ),
    }
    all_metrics = [*grid_metrics, *scenario_metrics]
    plot_cap_applied = any(
        value is not None and value > PLOT_EXAGGERATION_CAP
        for metric in all_metrics
        for value in (metric.type_m, metric.observed_exaggeration)
    )
    zero_selection_metrics_unavailable = any(
        probability == 0.0 and (metric.type_s is None or metric.type_m is None)
        for probability, metric in [
            *zip(grid_probability, grid_metrics, strict=True),
            *zip(scenario_probability, scenario_metrics, strict=True),
        ]
    )

    warnings.insert(
        0,
        "Every x-axis value is an assumed true effect in a repeated-study Wald model.",
    )
    warnings.append(
        "Selected-claim probability is a forward operating characteristic, not evidence "
        "conditional on an observed dataset and not a posterior probability."
    )
    warnings.append(
        "Type S is conditional on selection and true-effect direction; Type M is conditional "
        "expected selected magnitude divided by true magnitude."
    )
    warnings.append("Type S and Type M are undefined at or near the null under the core tolerance.")
    if zero_selection_metrics_unavailable:
        warnings.append(
            "Selection-conditioned metrics can also be unavailable when the selected-claim "
            "probability is numerically zero, because that conditioning event cannot be evaluated."
        )
    if request.information_multiplier != 1:
        warnings.append("The information multiplier changes hypothetical scenario SE only.")
    if observed_working is not None:
        warnings.append("Observed exaggeration is a separate realized ratio and is not Type M.")
    if plot_cap_applied:
        warnings.append(
            f"Plot traces are capped at {PLOT_EXAGGERATION_CAP:g}x for readability; "
            "the contract, scenario table, hover and reviewer text, and CSV retain uncapped "
            "values. Standalone plot PNGs include this clipping disclosure."
        )

    conditioning_statement = (
        "All curves condition on each x-axis value as the assumed true effect and on the "
        "selected future-study rule."
    )
    caption = (
        f"Forward repeated-study calibration for {effect_spec.label.lower()}. "
        f"{conditioning_statement} Selected rule: {rule_label} at alpha {request.alpha:g}; "
        f"information multiplier {request.information_multiplier:g}. Type S and Type M are "
        "conditional on selection and are undefined at or near the null; they may also be "
        "unavailable when the selected-claim probability is numerically zero. These curves are "
        "not posterior probabilities."
    )
    if plot_cap_applied:
        caption += (
            f" Values above {PLOT_EXAGGERATION_CAP:g}x are clipped in the plot only; "
            "reported numeric values remain uncapped."
        )
    meta = {
        "schema_version": 1,
        "app_version": __version__,
        "core_version": wald_inference.__version__,
        "effect_type": effect_spec.key,
        "effect_label": effect_spec.label,
        "effect_family": effect_spec.family,
        "working_scale": effect_spec.working_scale,
        "grid_points": request.grid_points,
        "axis_spacing": "log" if effect_spec.family == "ratio" else "linear",
        "plot_exaggeration_cap": PLOT_EXAGGERATION_CAP,
        "plot_exaggeration_cap_applied": plot_cap_applied,
        "conditioning_statement": conditioning_statement,
        "nonposterior_disclaimer": (
            "Outputs are forward operating characteristics, not posterior probabilities "
            "or evidence conditional on the observed dataset."
        ),
        "caption": caption,
        "scenario_dedup_tolerance": {
            "working_scale_relative": SCENARIO_DEDUP_REL_TOLERANCE,
            "working_scale_absolute": SCENARIO_DEDUP_ABS_TOLERANCE,
        },
    }
    response = CalibrationResponse(
        meta=meta,
        precision=precision,
        selection_rule=selection_summary,
        grid=grid,
        scenarios=scenarios,
        warnings=warnings,
    )
    _ensure_finite_payload(response.to_payload())
    return response


def calculate_json(request_json: str) -> str:
    """Validate a strict JSON request and return strict focused JSON."""

    try:
        payload = json.loads(request_json, parse_constant=_reject_nonstandard_constant)
    except json.JSONDecodeError as exc:
        raise ValidationError("Request must be valid JSON.") from exc
    response = calculate(CalibrationRequest.from_mapping(payload))
    return json.dumps(
        response.to_payload(),
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
