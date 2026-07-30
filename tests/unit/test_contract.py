from __future__ import annotations

import json
import math

import pytest
from hypothesis import given
from hypothesis import strategies as st

from template_applet import DemoRequest, ValidationError, calculate, calculate_json


def test_demonstration_contract_is_typed_and_deterministic() -> None:
    response = calculate(DemoRequest(first_value=2.0, second_value=3.0))

    assert response.total == 5.0
    assert response.to_payload()["summary"] == "Demonstration only: 2 + 3 = 5."
    assert response.to_payload()["rows"][-1] == {
        "label": "Demonstration total",
        "value": 5.0,
    }


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_contract_rejects_nonstandard_json_numbers(constant: str) -> None:
    with pytest.raises(ValidationError, match="Non-finite JSON constant"):
        calculate_json(f'{{"first_value": {constant}, "second_value": 1}}')


def test_contract_returns_strict_json() -> None:
    response_json = calculate_json('{"first_value": 1.25, "second_value": 2.75}')

    assert "NaN" not in response_json
    assert "Infinity" not in response_json
    assert json.loads(response_json)["rows"][-1]["value"] == 4.0


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({}, "Missing required field"),
        ({"first_value": 1, "second_value": 2, "extra": 3}, "Unexpected field"),
        ({"first_value": True, "second_value": 2}, "First value must be a number"),
        ({"first_value": 1, "second_value": "2"}, "Second value must be a number"),
    ],
)
def test_request_validation_is_explicit(payload: object, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        DemoRequest.from_mapping(payload)


@given(
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e100, max_value=1e100),
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e100, max_value=1e100),
)
def test_demonstration_total_matches_python_addition(first: float, second: float) -> None:
    response = calculate(DemoRequest(first_value=first, second_value=second))

    assert math.isfinite(response.total)
    assert response.total == first + second


def test_overflow_is_a_validation_error() -> None:
    with pytest.raises(ValidationError, match="total must be finite"):
        calculate(DemoRequest(first_value=1e308, second_value=1e308))
