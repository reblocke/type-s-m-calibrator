from __future__ import annotations

import json
import math

import pytest
from scipy.stats import norm

import type_sm_calibrator.contract as contract_module
from type_sm_calibrator import (
    ALL_SELECTION_RULES,
    CalibrationRequest,
    ValidationError,
    calculate,
    calculate_json,
)


def request_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "alpha": 0.05,
        "ci_lower": None,
        "ci_upper": None,
        "claim_direction": "positive",
        "claim_threshold": None,
        "effect_type": "mean_difference",
        "grid_points": 101,
        "information_multiplier": 1.0,
        "null_value": 0.0,
        "observed_estimate": None,
        "plausible_true_effect_max": None,
        "plausible_true_effect_min": None,
        "precision_mode": "direct_se",
        "reference_thresholds": [],
        "selection_rule": "two_sided_p_lt_alpha",
        "standard_error": 0.2,
        "true_effect_scenarios": [-0.4, 0.4],
    }
    payload.update(overrides)
    return payload


def response(**overrides: object):
    return calculate(CalibrationRequest.from_mapping(request_payload(**overrides)))


def scenario_by_display(result, value: float):
    return next(
        row for row in result.scenarios if row["true_effect_display"] == pytest.approx(value)
    )


def test_focused_contract_has_exact_top_level_and_grid_keys() -> None:
    payload = response().to_payload()

    assert set(payload) == {
        "meta",
        "precision",
        "selection_rule",
        "grid",
        "scenarios",
        "warnings",
    }
    assert set(payload["grid"]) == {
        "true_effect_display",
        "true_effect_working",
        "standardized_true_effect",
        "selected_claim_probability",
        "type_s",
        "type_m",
        "expected_selected_abs_z",
        "observed_exaggeration_optional",
    }
    assert all(len(values) == 101 for values in payload["grid"].values() if values is not None)


@pytest.mark.parametrize(
    ("rule", "direction", "threshold", "expected"),
    [
        ("two_sided_p_lt_alpha", "positive", None, 0.05),
        ("one_sided_positive_p_lt_alpha", "positive", None, 0.05),
        ("one_sided_negative_p_lt_alpha", "negative", None, 0.05),
        ("ci_excludes_null_in_beneficial_direction", "positive", None, 0.025),
        (
            "estimate_exceeds_mcid_and_p_lt_alpha",
            "positive",
            0.6,
            norm.sf(3.0),
        ),
        ("ci_excludes_mcid", "positive", 0.2, norm.sf(1.0 + norm.isf(0.025))),
    ],
)
def test_null_selected_claim_probability_by_rule(
    rule: str,
    direction: str,
    threshold: float | None,
    expected: float,
) -> None:
    result = response(
        selection_rule=rule,
        claim_direction=direction,
        claim_threshold=threshold,
        true_effect_scenarios=[],
    )

    null = scenario_by_display(result, 0.0)
    if rule in {
        "two_sided_p_lt_alpha",
        "one_sided_positive_p_lt_alpha",
        "one_sided_negative_p_lt_alpha",
    }:
        assert null["selected_claim_probability"] == expected
    else:
        assert null["selected_claim_probability"] == pytest.approx(expected, rel=2e-14)
    assert null["type_s"] is None
    assert null["type_m"] is None


def test_two_sided_metrics_are_symmetric() -> None:
    result = response(true_effect_scenarios=[-0.6, 0.6])
    negative = scenario_by_display(result, -0.6)
    positive = scenario_by_display(result, 0.6)

    for key in (
        "selected_claim_probability",
        "type_s",
        "type_m",
        "expected_selected_abs_z",
    ):
        assert negative[key] == pytest.approx(positive[key], rel=1e-13, abs=1e-15)


def test_wrong_sign_tail_and_one_sided_direction_are_preserved() -> None:
    positive_rule = response(
        selection_rule="one_sided_positive_p_lt_alpha",
        true_effect_scenarios=[-0.8, 0.8],
    )
    negative_truth = scenario_by_display(positive_rule, -0.8)
    positive_truth = scenario_by_display(positive_rule, 0.8)

    assert negative_truth["type_s"] == 1.0
    assert positive_truth["type_s"] == 0.0
    assert (
        negative_truth["selected_claim_probability"] < positive_truth["selected_claim_probability"]
    )


@pytest.mark.parametrize("rule", ALL_SELECTION_RULES)
def test_all_six_rules_have_exact_requirement_metadata(rule: str) -> None:
    threshold = (
        0.3
        if rule
        in {
            "estimate_exceeds_mcid_and_p_lt_alpha",
            "ci_excludes_mcid",
        }
        else None
    )
    result = response(
        selection_rule=rule,
        claim_threshold=threshold,
        true_effect_scenarios=[0.4],
    )
    summary = result.selection_rule

    assert summary["key"] == rule
    assert "alpha" in summary["active_controls"]
    assert ("claim_direction" in summary["active_controls"]) == (
        rule
        in {
            "ci_excludes_null_in_beneficial_direction",
            "estimate_exceeds_mcid_and_p_lt_alpha",
            "ci_excludes_mcid",
        }
    )
    assert ("claim_threshold" in summary["active_controls"]) == (threshold is not None)
    assert "0.05" not in summary["label"]
    if rule == "one_sided_positive_p_lt_alpha":
        assert summary["claim_direction"] == "positive"
    elif rule == "one_sided_negative_p_lt_alpha":
        assert summary["claim_direction"] == "negative"
    if threshold is not None:
        assert summary["claim_threshold_display"] == threshold
        assert not any(row["source"] == "claim_threshold" for row in result.scenarios)


def test_directional_ci_and_threshold_rules_reverse_cleanly() -> None:
    positive = response(
        selection_rule="ci_excludes_null_in_beneficial_direction",
        claim_direction="positive",
        true_effect_scenarios=[0.5],
    )
    negative = response(
        selection_rule="ci_excludes_null_in_beneficial_direction",
        claim_direction="negative",
        true_effect_scenarios=[-0.5],
    )
    assert scenario_by_display(positive, 0.5)["selected_claim_probability"] == pytest.approx(
        scenario_by_display(negative, -0.5)["selected_claim_probability"]
    )

    threshold = response(
        selection_rule="ci_excludes_mcid",
        claim_direction="positive",
        claim_threshold=0.4,
        true_effect_scenarios=[0.4],
    )
    boundary = scenario_by_display(threshold, 0.4)
    assert boundary["selected_claim_probability"] == pytest.approx(0.025)

    negative_threshold = response(
        selection_rule="ci_excludes_mcid",
        claim_direction="negative",
        claim_threshold=-0.4,
        true_effect_scenarios=[-0.4],
    )
    negative_boundary = scenario_by_display(negative_threshold, -0.4)
    assert negative_boundary["selected_claim_probability"] == pytest.approx(0.025)


def test_alpha_label_is_neutral_and_tiny_alpha_fails_safely() -> None:
    first = response(alpha=0.05)
    second = response(alpha=0.01)
    assert first.selection_rule["label"] == second.selection_rule["label"]
    assert "0.05" not in first.selection_rule["label"]

    with pytest.raises(ValidationError, match="too small"):
        response(alpha=5e-324)


def test_released_core_probability_and_metrics_remain_coherent_at_tiny_alpha() -> None:
    result = response(
        alpha=1e-6,
        standard_error=1.0,
        true_effect_scenarios=[-3.36, 3.36],
    )

    assert scenario_by_display(result, 0.0)["selected_claim_probability"] == 1e-6
    assert scenario_by_display(result, -3.36)["selected_claim_probability"] == pytest.approx(
        0.06280583619349671,
        rel=0,
        abs=1e-16,
    )


def test_probability_coherence_guard_still_rejects_material_core_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = contract_module.selected_claim_probability

    def drifted_probability(*args, **kwargs):
        values = original(*args, **kwargs)
        return [float(value) + 1e-8 for value in values]

    monkeypatch.setattr(contract_module, "selected_claim_probability", drifted_probability)

    with pytest.raises(RuntimeError, match="Core selected-claim APIs disagree"):
        response()


def test_large_delta_has_low_type_s_and_type_m_near_one() -> None:
    row = scenario_by_display(
        response(standard_error=0.1, true_effect_scenarios=[1.0]),
        1.0,
    )

    assert row["selected_claim_probability"] > 0.999
    assert row["type_s"] < 1e-20
    assert row["type_m"] == pytest.approx(1.0, rel=0.01)


def test_near_null_is_undefined_but_expected_selected_abs_z_is_retained() -> None:
    row = scenario_by_display(
        response(
            standard_error=1.0,
            true_effect_scenarios=[1e-13],
        ),
        1e-13,
    )

    assert row["type_s"] is None
    assert row["type_m"] is None
    assert row["observed_exaggeration"] is None
    assert row["expected_selected_abs_z"] == pytest.approx(2.3378027922014146)
    assert "undefined at the null" in row["note"]
    assert "undefined at or near the null" in row["reviewer_text"]
    assert "numerically zero" not in row["reviewer_text"]


def test_zero_probability_conditioning_is_not_mislabeled_as_near_null() -> None:
    result = response(
        selection_rule="one_sided_positive_p_lt_alpha",
        standard_error=1.0,
        true_effect_scenarios=[-50.0],
    )
    row = scenario_by_display(result, -50.0)

    assert row["selected_claim_probability"] == 0.0
    assert row["type_s"] is None
    assert row["type_m"] is None
    assert row["expected_selected_abs_z"] is None
    assert "probability is numerically zero" in row["note"]
    assert (
        "unavailable because selected-claim probability is numerically zero" in row["reviewer_text"]
    )
    assert any("conditioning event cannot be evaluated" in warning for warning in result.warnings)


def test_information_multiplier_changes_scenario_se_only() -> None:
    result = response(information_multiplier=4.0)

    assert result.precision["current_se_working"] == 0.2
    assert result.precision["scenario_se_working"] == 0.1
    assert result.precision["information_multiplier"] == 4.0
    assert any("scenario SE only" in warning for warning in result.warnings)


def test_ci_mode_reconstructs_precision_without_using_observed_estimate() -> None:
    result = response(
        precision_mode="ci_95",
        standard_error=None,
        ci_lower=0.11,
        ci_upper=0.73,
        observed_estimate=0.3,
    )

    assert result.precision["current_se_working"] == pytest.approx(0.15816617164664273)
    assert result.precision["ci_implied_midpoint_display"] == pytest.approx(0.42)
    observed = next(
        row for row in result.scenarios if row["source"] == "observed_estimate_as_truth"
    )
    assert observed["true_effect_display"] == 0.3
    assert observed["observed_exaggeration"] == 1.0


def test_ci_midpoint_is_not_silently_promoted_to_an_assumed_truth() -> None:
    result = response(
        precision_mode="ci_95",
        standard_error=None,
        ci_lower=0.11,
        ci_upper=0.73,
        true_effect_scenarios=[],
    )

    assert result.precision["ci_implied_midpoint_display"] == pytest.approx(0.42)
    assert all(
        "observed_estimate_as_truth" not in row["merged_sources"] for row in result.scenarios
    )
    assert result.grid["observed_exaggeration_optional"] is None


def test_ratio_uses_log_working_scale_and_separate_observed_exaggeration() -> None:
    result = response(
        effect_type="odds_ratio",
        null_value=1.0,
        standard_error=0.2,
        true_effect_scenarios=[2.0],
        observed_estimate=1.5,
    )
    row = scenario_by_display(result, 2.0)

    assert row["true_effect_working"] == pytest.approx(math.log(2.0))
    assert row["standardized_true_effect"] == pytest.approx(math.log(2.0) / 0.2)
    assert row["observed_exaggeration"] == pytest.approx(abs(math.log(1.5) / math.log(2.0)))
    assert result.meta["axis_spacing"] == "log"
    assert "log scale" in result.precision["working_scale_note"]
    assert any("not Type M" in warning for warning in result.warnings)


def test_scenario_deduplication_uses_documented_working_scale_tolerance() -> None:
    result = response(
        true_effect_scenarios=[0.0, 5e-13, 2e-12, 0.2, 0.2],
        reference_thresholds=[0.2, 0.4],
        observed_estimate=0.4,
    )

    assert [row["true_effect_display"] for row in result.scenarios] == [
        0.0,
        2e-12,
        0.2,
        0.4,
    ]
    assert result.meta["scenario_dedup_tolerance"] == {
        "working_scale_relative": 1e-12,
        "working_scale_absolute": 1e-12,
    }
    merged_observed = scenario_by_display(result, 0.4)
    assert "observed_estimate_as_truth" in merged_observed["merged_sources"]
    assert "Optimistic/circular" in merged_observed["note"]
    assert "optimistic/circular scenario" in merged_observed["reviewer_text"]


def test_display_cap_never_changes_contract_scenario_or_grid_values() -> None:
    result = response(
        standard_error=1.0,
        true_effect_scenarios=[1e-6],
        plausible_true_effect_min=-0.01,
        plausible_true_effect_max=0.01,
    )
    row = scenario_by_display(result, 1e-6)

    assert row["type_m"] > result.meta["plot_exaggeration_cap"]
    assert max(value for value in result.grid["type_m"] if value is not None) > 10
    assert result.meta["plot_exaggeration_cap_applied"] is True
    assert any("CSV retain uncapped" in warning for warning in result.warnings)
    assert "clipped in the plot only" in result.meta["caption"]


def test_scenario_only_clipping_is_disclosed_when_grid_values_are_below_cap() -> None:
    result = response(
        standard_error=1.0,
        true_effect_scenarios=[1e-6],
        plausible_true_effect_min=1.0,
        plausible_true_effect_max=2.0,
    )

    assert scenario_by_display(result, 1e-6)["type_m"] > 10
    assert max(value for value in result.grid["type_m"] if value is not None) < 10
    assert result.meta["plot_exaggeration_cap_applied"] is True
    assert any("Standalone plot PNGs include" in warning for warning in result.warnings)


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_contract_rejects_nonstandard_json_numbers(constant: str) -> None:
    payload = json.dumps(request_payload())
    payload = payload.replace('"alpha": 0.05', f'"alpha": {constant}')
    with pytest.raises(ValidationError, match="Non-finite JSON constant"):
        calculate_json(payload)


def test_contract_returns_strict_json_and_null_optional_observed_grid() -> None:
    result_json = calculate_json(json.dumps(request_payload()))

    assert "NaN" not in result_json
    assert "Infinity" not in result_json
    parsed = json.loads(result_json)
    assert parsed["grid"]["observed_exaggeration_optional"] is None
    assert all(row["observed_exaggeration"] is None for row in parsed["scenarios"])


def test_observed_estimate_enables_uncapped_optional_grid() -> None:
    result = response(observed_estimate=0.5)

    assert result.grid["observed_exaggeration_optional"] is not None
    assert len(result.grid["observed_exaggeration_optional"]) == 101
    assert any(value is None for value in result.grid["observed_exaggeration_optional"])


def test_reviewer_text_is_conditioned_nonposterior_and_scale_aware() -> None:
    result = response(true_effect_scenarios=[0.4])
    text = scenario_by_display(result, 0.4)["reviewer_text"]

    assert "assuming the true mean difference is 0.4" in text
    assert "information" in text
    assert "alpha 0.05" in text
    assert "selected-claim probability" in text
    assert "conditional Type S" in text
    assert "conditional Type M" in text
    assert "not posterior probabilities" in text


def test_contract_contains_no_out_of_scope_output_keys() -> None:
    serialized = json.dumps(response().to_payload(), sort_keys=True).lower()

    for forbidden in (
        '"compatibility"',
        '"relative_likelihood"',
        '"s_minus_2"',
        '"precision_targets"',
        '"required_information"',
        '"required_se"',
    ):
        assert forbidden not in serialized


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"standard_error": 0}, "must be positive"),
        ({"information_multiplier": 0}, "greater than 0"),
        ({"alpha": 1}, "between 0 and 1"),
        (
            {
                "selection_rule": "ci_excludes_mcid",
                "claim_threshold": None,
            },
            "threshold is required",
        ),
        ({"claim_threshold": 0.2}, "threshold must be blank"),
        (
            {
                "precision_mode": "ci_95",
                "standard_error": None,
                "ci_lower": 0.2,
                "ci_upper": None,
            },
            "Both 95% confidence limits",
        ),
        (
            {
                "plausible_true_effect_min": -1,
                "plausible_true_effect_max": None,
            },
            "must be supplied together",
        ),
    ],
)
def test_semantic_validation_is_explicit(
    overrides: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        response(**overrides)


def test_request_rejects_unknown_fields_and_non_numeric_lists() -> None:
    with pytest.raises(ValidationError, match="Unexpected field"):
        CalibrationRequest.from_mapping(request_payload(extra=True))
    with pytest.raises(ValidationError, match="JSON array"):
        CalibrationRequest.from_mapping(request_payload(true_effect_scenarios="0.1, 0.2"))
