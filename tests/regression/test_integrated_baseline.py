from __future__ import annotations

import json
from pathlib import Path

import pytest

from type_sm_calibrator import CalibrationRequest, calculate

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "integrated_baseline"
    / "type_sm_scenarios.json"
)
EXPECTED_FOCUSED_SCENARIO_ORDER = {
    "B04": [
        (0.0, "null"),
        (0.1, "user_assumed_true_effect"),
        (0.3, "user_assumed_true_effect"),
        (0.2, "reference_threshold"),
        (0.42, "observed_estimate_as_truth"),
    ],
    "B05": [
        (1.0, "null"),
        (1.1, "user_assumed_true_effect"),
        (1.5, "user_assumed_true_effect"),
        (2.0, "user_assumed_true_effect"),
        (1.8, "observed_estimate_as_truth"),
    ],
    "B07a-null": [
        (0.0, "null"),
        (0.42, "observed_estimate_as_truth"),
    ],
    "B07b-near-null": [
        (0.0, "null"),
        (1.2e-12, "user_assumed_true_effect"),
        (0.42, "observed_estimate_as_truth"),
    ],
}


@pytest.mark.parametrize(
    "case",
    json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"],
    ids=lambda case: case["id"],
)
def test_focused_scenarios_match_frozen_integrated_baseline(
    case: dict[str, object],
) -> None:
    result = calculate(CalibrationRequest.from_mapping(case["request"]))

    assert result.precision["current_se_working"] == pytest.approx(
        case["expected_current_se"],
        rel=1e-14,
        abs=1e-15,
    )
    assert [
        (row["true_effect_display"], row["source"]) for row in result.scenarios
    ] == EXPECTED_FOCUSED_SCENARIO_ORDER[case["id"]]
    assert all(row["source"] != "claim_threshold" for row in result.scenarios)
    for display, expected in case["expected_scenarios"].items():
        numeric_display = float(display)
        row = next(
            candidate
            for candidate in result.scenarios
            if candidate["true_effect_display"]
            == pytest.approx(
                numeric_display,
                rel=0,
                abs=1e-15,
            )
        )
        actual = [
            row["selected_claim_probability"],
            row["type_s"],
            row["type_m"],
            row["observed_exaggeration"],
        ]
        for observed, target in zip(actual, expected, strict=True):
            if target is None:
                assert observed is None
            else:
                assert observed == pytest.approx(target, rel=2e-13, abs=2e-15)


def test_fixture_records_exact_frozen_git_provenance() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    assert fixture["behavior_source_commit"] == ("830756ecb11b4e8161f8dfe1fc75afc346ef4467")
    assert fixture["baseline_fixture_commit"] == ("5fd501dd947d9b951d736014cfc2b310efa5e7b0")
    assert fixture["baseline_tag"] == "pre-split-baseline-2026-07-29"
