from __future__ import annotations

import json
import math

from hypothesis import given, settings
from hypothesis import strategies as st

from type_sm_calibrator import CalibrationRequest, calculate, calculate_json


def payload(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "alpha": 0.05,
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
        "standard_error": 1.0,
        "true_effect_scenarios": [],
    }
    request.update(overrides)
    return request


@given(
    true_effect=st.floats(
        min_value=-50,
        max_value=50,
        allow_nan=False,
        allow_infinity=False,
    ),
    standard_error=st.floats(
        min_value=1e-3,
        max_value=10,
        allow_nan=False,
        allow_infinity=False,
    ),
    alpha=st.floats(
        min_value=1e-6,
        max_value=0.25,
        allow_nan=False,
        allow_infinity=False,
    ),
)
@settings(max_examples=35, deadline=None)
def test_finite_additive_requests_produce_bounded_strict_outputs(
    true_effect: float,
    standard_error: float,
    alpha: float,
) -> None:
    request = payload(
        alpha=alpha,
        standard_error=standard_error,
        true_effect_scenarios=[true_effect],
    )
    serialized = calculate_json(json.dumps(request))
    result = json.loads(serialized)

    assert "NaN" not in serialized
    assert "Infinity" not in serialized
    for probability in result["grid"]["selected_claim_probability"]:
        assert 0 <= probability <= 1
    for type_s in result["grid"]["type_s"]:
        assert type_s is None or 0 <= type_s <= 1
    for type_m in result["grid"]["type_m"]:
        assert type_m is None or (math.isfinite(type_m) and type_m >= 0)


@given(
    magnitude=st.floats(
        min_value=1e-6,
        max_value=20,
        allow_nan=False,
        allow_infinity=False,
    ),
    standard_error=st.floats(
        min_value=0.05,
        max_value=5,
        allow_nan=False,
        allow_infinity=False,
    ),
)
@settings(max_examples=30, deadline=None)
def test_two_sided_positive_negative_scenarios_are_symmetric(
    magnitude: float,
    standard_error: float,
) -> None:
    result = calculate(
        CalibrationRequest.from_mapping(
            payload(
                standard_error=standard_error,
                true_effect_scenarios=[-magnitude, magnitude],
            )
        )
    )
    negative, positive = result.scenarios[1:3]

    for key in (
        "selected_claim_probability",
        "type_s",
        "type_m",
        "expected_selected_abs_z",
    ):
        left = negative[key]
        right = positive[key]
        if left is None or right is None:
            assert left is right is None
        else:
            assert math.isclose(left, right, rel_tol=2e-13, abs_tol=2e-15)
