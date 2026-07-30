"""Typed demonstration models.

Replace this entire demonstration contract when defining an app's scientific
question. It intentionally performs no scientific inference.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


class ValidationError(ValueError):
    """A user-correctable request error safe to show in the browser."""


def _finite_number(value: object, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValidationError(f"{field} must be a number.")
    number = float(value)
    if not math.isfinite(number):
        raise ValidationError(f"{field} must be finite.")
    return number


@dataclass(frozen=True)
class DemoRequest:
    """Two values for the conspicuously non-scientific demonstration."""

    first_value: float
    second_value: float

    @classmethod
    def from_mapping(cls, payload: object) -> DemoRequest:
        if not isinstance(payload, dict):
            raise ValidationError("Request must be a JSON object.")
        expected = {"first_value", "second_value"}
        unexpected = sorted(set(payload) - expected)
        missing = sorted(expected - set(payload))
        if missing:
            raise ValidationError(f"Missing required field: {missing[0]}.")
        if unexpected:
            raise ValidationError(f"Unexpected field: {unexpected[0]}.")
        return cls(
            first_value=_finite_number(payload["first_value"], field="First value"),
            second_value=_finite_number(payload["second_value"], field="Second value"),
        )


@dataclass(frozen=True)
class DemoResponse:
    """Serializable output for the replace-me demonstration."""

    first_value: float
    second_value: float
    total: float

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "summary": (
                "Demonstration only: "
                f"{self.first_value:g} + {self.second_value:g} = {self.total:g}."
            ),
            "rows": [
                {"label": "First value", "value": self.first_value},
                {"label": "Second value", "value": self.second_value},
                {"label": "Demonstration total", "value": self.total},
            ],
            "figure": {
                "data": [
                    {
                        "type": "bar",
                        "x": ["First", "Second", "Total"],
                        "y": [self.first_value, self.second_value, self.total],
                        "marker": {"color": ["#276b78", "#8b5f36", "#363b74"]},
                    }
                ],
                "layout": {
                    "title": {"text": "Replace-me demonstration values"},
                    "xaxis": {"title": {"text": "Demonstration field"}},
                    "yaxis": {"title": {"text": "Value"}},
                    "showlegend": False,
                },
            },
            "caption": (
                "Replace-me demonstration: two supplied values and their arithmetic sum. "
                "This scaffold does not implement a scientific method."
            ),
        }
