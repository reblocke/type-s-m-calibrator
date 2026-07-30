from __future__ import annotations

import math

import pytest
from scipy.stats import norm

from type_sm_calibrator import CalibrationRequest, calculate


def result_for(
    true_effect: float,
    *,
    alpha: float = 0.05,
    standard_error: float = 0.4,
):
    return calculate(
        CalibrationRequest.from_mapping(
            {
                "alpha": alpha,
                "ci_lower": None,
                "ci_upper": None,
                "claim_direction": "positive",
                "claim_threshold": None,
                "effect_type": "mean_difference",
                "grid_points": 51,
                "information_multiplier": 1.0,
                "null_value": 0.0,
                "observed_estimate": None,
                "plausible_true_effect_max": None,
                "plausible_true_effect_min": None,
                "precision_mode": "direct_se",
                "reference_thresholds": [],
                "selection_rule": "two_sided_p_lt_alpha",
                "standard_error": standard_error,
                "true_effect_scenarios": [true_effect],
            }
        )
    )


def test_two_sided_probability_and_type_s_match_normal_tail_identity() -> None:
    true_effect = 0.6
    standard_error = 0.4
    alpha = 0.05
    delta = true_effect / standard_error
    critical = norm.isf(alpha / 2)
    upper = norm.sf(critical - delta)
    lower = norm.cdf(-critical - delta)
    selected = upper + lower

    result = result_for(
        true_effect,
        alpha=alpha,
        standard_error=standard_error,
    )
    scenario = result.scenarios[1]

    assert scenario["standardized_true_effect"] == pytest.approx(delta)
    assert scenario["selected_claim_probability"] == pytest.approx(selected, rel=2e-14)
    assert scenario["type_s"] == pytest.approx(lower / selected, rel=2e-14)


def test_type_m_and_expected_selected_abs_z_match_truncated_normal_moment() -> None:
    true_effect = 0.6
    standard_error = 0.4
    alpha = 0.05
    delta = true_effect / standard_error
    critical = norm.isf(alpha / 2)
    upper_probability = norm.sf(critical - delta)
    lower_probability = norm.cdf(-critical - delta)
    selected_probability = upper_probability + lower_probability
    upper_moment = delta * upper_probability + norm.pdf(critical - delta)
    lower_absolute_moment = -delta * lower_probability + norm.pdf(-critical - delta)
    expected_selected_abs_z = (upper_moment + lower_absolute_moment) / selected_probability

    scenario = result_for(
        true_effect,
        alpha=alpha,
        standard_error=standard_error,
    ).scenarios[1]

    assert scenario["expected_selected_abs_z"] == pytest.approx(
        expected_selected_abs_z,
        rel=2e-14,
    )
    assert scenario["type_m"] == pytest.approx(
        expected_selected_abs_z / abs(delta),
        rel=2e-14,
    )


def test_information_multiplier_has_inverse_square_root_se_identity() -> None:
    result = calculate(
        CalibrationRequest.from_mapping(
            {
                "alpha": 0.05,
                "ci_lower": None,
                "ci_upper": None,
                "claim_direction": "positive",
                "claim_threshold": None,
                "effect_type": "mean_difference",
                "grid_points": 51,
                "information_multiplier": 9.0,
                "null_value": 0.0,
                "observed_estimate": None,
                "plausible_true_effect_max": None,
                "plausible_true_effect_min": None,
                "precision_mode": "direct_se",
                "reference_thresholds": [],
                "selection_rule": "two_sided_p_lt_alpha",
                "standard_error": 0.6,
                "true_effect_scenarios": [0.4],
            }
        )
    )

    assert result.precision["scenario_se_working"] == pytest.approx(0.6 / math.sqrt(9.0))
