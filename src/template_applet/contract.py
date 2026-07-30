"""Strict JSON boundary for the replace-me demonstration."""

from __future__ import annotations

import json
import math

from .models import DemoRequest, DemoResponse, ValidationError


def _reject_nonstandard_constant(value: str) -> None:
    raise ValidationError(f"Non-finite JSON constant is not allowed: {value}.")


def calculate(request: DemoRequest) -> DemoResponse:
    """Add two values as a deterministic, non-scientific demonstration.

    Replace this function and its models before making scientific claims.
    """

    total = request.first_value + request.second_value
    if not math.isfinite(total):
        raise ValidationError("The demonstration total must be finite.")
    return DemoResponse(
        first_value=request.first_value,
        second_value=request.second_value,
        total=total,
    )


def calculate_json(request_json: str) -> str:
    """Validate a strict JSON request and return strict JSON."""

    try:
        payload = json.loads(request_json, parse_constant=_reject_nonstandard_constant)
    except json.JSONDecodeError as exc:
        raise ValidationError("Request must be valid JSON.") from exc
    response = calculate(DemoRequest.from_mapping(payload))
    return json.dumps(
        response.to_payload(),
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
