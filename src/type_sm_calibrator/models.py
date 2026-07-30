"""Typed request and response models for forward Type S/M calibration."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Literal

type PrecisionMode = Literal["direct_se", "ci_95"]


class ValidationError(ValueError):
    """A user-correctable request error safe to show in the browser."""


def _finite_number(value: object, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValidationError(f"{field} must be a number.")
    number = float(value)
    if not math.isfinite(number):
        raise ValidationError(f"{field} must be finite.")
    return number


def _optional_finite_number(value: object, *, field: str) -> float | None:
    if value is None:
        return None
    return _finite_number(value, field=field)


def _required_string(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{field} must be a non-empty string.")
    return value


def _numeric_list(value: object, *, field: str) -> tuple[float, ...]:
    if not isinstance(value, list):
        raise ValidationError(f"{field} must be a JSON array of numbers.")
    if len(value) > 50:
        raise ValidationError(f"{field} may contain at most 50 values.")
    return tuple(
        _finite_number(item, field=f"{field} item {index + 1}") for index, item in enumerate(value)
    )


@dataclass(frozen=True)
class CalibrationRequest:
    """Validated controls for a single forward repeated-study calibration."""

    precision_mode: PrecisionMode
    effect_type: str
    standard_error: float | None
    ci_lower: float | None
    ci_upper: float | None
    null_value: float
    alpha: float
    selection_rule: str
    claim_direction: str
    claim_threshold: float | None
    information_multiplier: float
    true_effect_scenarios: tuple[float, ...]
    reference_thresholds: tuple[float, ...]
    plausible_true_effect_min: float | None
    plausible_true_effect_max: float | None
    grid_points: int
    observed_estimate: float | None

    @classmethod
    def from_mapping(cls, payload: object) -> CalibrationRequest:
        """Build a request from a strict, flat JSON object."""

        if not isinstance(payload, dict):
            raise ValidationError("Request must be a JSON object.")
        allowed = {
            "alpha",
            "ci_lower",
            "ci_upper",
            "claim_direction",
            "claim_threshold",
            "effect_type",
            "grid_points",
            "information_multiplier",
            "null_value",
            "observed_estimate",
            "plausible_true_effect_max",
            "plausible_true_effect_min",
            "precision_mode",
            "reference_thresholds",
            "selection_rule",
            "standard_error",
            "true_effect_scenarios",
        }
        unexpected = sorted(set(payload) - allowed)
        if unexpected:
            raise ValidationError(f"Unexpected field: {unexpected[0]}.")
        required = {
            "alpha",
            "claim_direction",
            "effect_type",
            "grid_points",
            "information_multiplier",
            "null_value",
            "precision_mode",
            "selection_rule",
            "true_effect_scenarios",
        }
        missing = sorted(required - set(payload))
        if missing:
            raise ValidationError(f"Missing required field: {missing[0]}.")

        precision_mode = _required_string(
            payload["precision_mode"],
            field="Precision mode",
        )
        if precision_mode not in {"direct_se", "ci_95"}:
            raise ValidationError("Precision mode must be 'direct_se' or 'ci_95'.")

        grid_points = payload["grid_points"]
        if isinstance(grid_points, bool) or not isinstance(grid_points, int):
            raise ValidationError("Grid points must be an integer.")
        if not 51 <= grid_points <= 1601:
            raise ValidationError("Grid points must be between 51 and 1601.")

        return cls(
            precision_mode=precision_mode,
            effect_type=_required_string(payload["effect_type"], field="Effect measure"),
            standard_error=_optional_finite_number(
                payload.get("standard_error"),
                field="Working-scale standard error",
            ),
            ci_lower=_optional_finite_number(
                payload.get("ci_lower"),
                field="Lower 95% confidence limit",
            ),
            ci_upper=_optional_finite_number(
                payload.get("ci_upper"),
                field="Upper 95% confidence limit",
            ),
            null_value=_finite_number(payload["null_value"], field="Null value"),
            alpha=_finite_number(payload["alpha"], field="Alpha"),
            selection_rule=_required_string(
                payload["selection_rule"],
                field="Selected-claim rule",
            ),
            claim_direction=_required_string(
                payload["claim_direction"],
                field="Claim direction",
            ),
            claim_threshold=_optional_finite_number(
                payload.get("claim_threshold"),
                field="Claim threshold",
            ),
            information_multiplier=_finite_number(
                payload["information_multiplier"],
                field="Information multiplier",
            ),
            true_effect_scenarios=_numeric_list(
                payload["true_effect_scenarios"],
                field="Assumed true-effect scenarios",
            ),
            reference_thresholds=_numeric_list(
                payload.get("reference_thresholds", []),
                field="Reference thresholds",
            ),
            plausible_true_effect_min=_optional_finite_number(
                payload.get("plausible_true_effect_min"),
                field="Plausible true-effect minimum",
            ),
            plausible_true_effect_max=_optional_finite_number(
                payload.get("plausible_true_effect_max"),
                field="Plausible true-effect maximum",
            ),
            grid_points=grid_points,
            observed_estimate=_optional_finite_number(
                payload.get("observed_estimate"),
                field="Observed estimate",
            ),
        )


@dataclass(frozen=True)
class CalibrationResponse:
    """Focused response with no observed-data or inverse-planning outputs."""

    meta: dict[str, Any]
    precision: dict[str, Any]
    selection_rule: dict[str, Any]
    grid: dict[str, Any]
    scenarios: list[dict[str, Any]]
    warnings: list[str]

    def to_payload(self) -> dict[str, Any]:
        """Return the stable six-part browser payload."""

        return {
            "meta": self.meta,
            "precision": self.precision,
            "selection_rule": self.selection_rule,
            "grid": self.grid,
            "scenarios": self.scenarios,
            "warnings": self.warnings,
        }
