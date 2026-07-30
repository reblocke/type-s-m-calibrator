from __future__ import annotations

from playwright.sync_api import Page, expect

FAKE_WORKER = """
globalThis.__mockCalculateDelayMs = 0;

function responseForRequest() {
  return {
    meta: {
      app_version: "0.1.2",
      axis_spacing: "linear",
      caption:
        "All values are assumed true effects. Values above 10x are clipped in the plot only.",
      conditioning_statement:
        "All curves condition on each x-axis value as the assumed true effect.",
      core_version: "0.4.1",
      effect_family: "additive",
      effect_label: "Mean difference",
      effect_type: "mean_difference",
      grid_points: 2,
      nonposterior_disclaimer: "Not posterior probabilities.",
      plot_exaggeration_cap: 10,
      plot_exaggeration_cap_applied: true,
      scenario_dedup_tolerance: {
        working_scale_absolute: 1e-12,
        working_scale_relative: 1e-12,
      },
      schema_version: 1,
      working_scale: "identity",
    },
    precision: {
      ci_implied_midpoint_display: null,
      ci_lower_display: null,
      ci_reconstruction_method: null,
      ci_upper_display: null,
      current_se_working: 0.2,
      information_multiplier: 1,
      information_note: "Scenario precision is hypothetical.",
      mode: "direct_se",
      scenario_se_working: 0.2,
      source_note: "The entered standard error supplies current precision.",
      working_scale_note: "Additive working scale.",
    },
    selection_rule: {
      active_controls: ["alpha"],
      alpha: 0.05,
      claim_direction: null,
      claim_threshold_display: null,
      claim_threshold_working: null,
      explanation: "Selects either tail.",
      key: "two_sided_p_lt_alpha",
      label: "Two-sided p < alpha",
      requires_direction: false,
      requires_threshold: false,
    },
    grid: {
      expected_selected_abs_z: [2.3, 2.5],
      observed_exaggeration_optional: [null, 12],
      selected_claim_probability: [0.05, 0.25],
      standardized_true_effect: [0, 1],
      true_effect_display: [0, 0.2],
      true_effect_working: [0, 0.2],
      type_m: [null, 12],
      type_s: [null, 0.1],
    },
    scenarios: [
      {
        current_se_working: 0.2,
        expected_selected_abs_z: 2.3,
        id: "scenario-null",
        information_multiplier: 1,
        label: "Null",
        merged_sources: ["null"],
        note: "Undefined at the null.",
        observed_exaggeration: null,
        reviewer_text: "Null scenario; not posterior probabilities.",
        scenario_se_working: 0.2,
        selected_claim_probability: 0.05,
        source: "null",
        standardized_true_effect: 0,
        true_effect_display: 0,
        true_effect_working: 0,
        type_m: null,
        type_s: null,
      },
      {
        current_se_working: 0.2,
        expected_selected_abs_z: 2.5,
        id: "scenario-reference",
        information_multiplier: 1,
        label: "Reference threshold as truth: 0.2",
        merged_sources: ["reference_threshold"],
        note: "Reference threshold treated as truth.",
        observed_exaggeration: 2.1,
        reviewer_text: "Reference scenario; not posterior probabilities.",
        scenario_se_working: 0.2,
        selected_claim_probability: 0.25,
        source: "reference_threshold",
        standardized_true_effect: 1,
        true_effect_display: 0.2,
        true_effect_working: 0.2,
        type_m: 1.5,
        type_s: 0.1,
      },
      {
        current_se_working: 0.2,
        expected_selected_abs_z: 2.8,
        id: "scenario-observed",
        information_multiplier: 1,
        label: "Observed estimate as truth: 0.4",
        merged_sources: ["observed_estimate_as_truth"],
        note: "Optimistic/circular scenario.",
        observed_exaggeration: 1,
        reviewer_text: "Optimistic/circular scenario; not posterior probabilities.",
        scenario_se_working: 0.2,
        selected_claim_probability: 0.6,
        source: "observed_estimate_as_truth",
        standardized_true_effect: 2,
        true_effect_display: 0.4,
        true_effect_working: 0.4,
        type_m: 1.2,
        type_s: 0.01,
      },
    ],
    warnings: ["Plot traces are capped at 10x; numeric values remain uncapped."],
  };
}

class FakeWorker {
  constructor() {
    this.listeners = { error: [], message: [] };
    this.terminated = false;
  }

  addEventListener(type, listener) {
    this.listeners[type].push(listener);
  }

  postMessage(message) {
    const delay = message.type === "calculate" ? globalThis.__mockCalculateDelayMs : 0;
    setTimeout(() => {
      if (this.terminated) {
        return;
      }
      const payload =
        message.type === "initialize"
          ? {
              packages: [
                { distribution: "type-s-m-calibrator", version: "0.1.2" },
                { distribution: "wald-inference", version: "0.4.1" },
              ],
            }
          : responseForRequest();
      for (const listener of this.listeners.message) {
        listener({ data: { id: message.id, payload, type: "result" } });
      }
    }, delay);
  }

  terminate() {
    this.terminated = true;
  }
}

globalThis.Worker = FakeWorker;
"""

PLOTLY_STUB = """
globalThis.Plotly = {
  Plots: {
    resize: async () => {},
  },
  react: async (element, _traces, layout) => {
    const container = document.createElement("div");
    container.className = "plot-container";
    container.textContent = [
      layout.title.text,
      ...layout.annotations.map((annotation) => annotation.text),
    ].join(" ");
    element.replaceChildren(container);
    element.dataset.plotTitle = layout.title.text;
  },
  toImage: async () => "data:image/png;base64,iVBORw0KGgo=",
};
"""


def _ready_with_mock_runtime(page: Page, app_url: str) -> None:
    page.add_init_script(script=FAKE_WORKER)
    page.route(
        "https://cdn.plot.ly/**",
        lambda route: route.fulfill(
            body=PLOTLY_STUB,
            content_type="application/javascript",
        ),
    )
    page.goto(app_url)
    expect(page.locator("#runtime-status")).to_have_attribute("data-state", "ready")


def _calculate(page: Page) -> None:
    page.locator("#calculate").click()
    expect(page.locator("#runtime-status")).to_have_text("Calculation complete.")


def test_client_error_clears_prior_result_and_exports(page: Page, app_url: str) -> None:
    _ready_with_mock_runtime(page, app_url)
    _calculate(page)
    expect(page.locator("#result")).to_be_visible()
    expect(page.locator("#export-csv")).to_be_enabled()

    page.locator("#null-value").fill("")
    page.locator("#calculate").click()

    expect(page.locator("#error-summary")).to_be_visible()
    expect(page.locator("#result")).to_be_hidden()
    expect(page.locator(".empty-state")).to_be_visible()
    expect(page.locator("#export-csv")).to_be_disabled()
    expect(page.locator("#runtime-status")).to_have_text("Check the highlighted inputs.")


def test_reset_discards_delayed_response_without_repopulating_result(
    page: Page,
    app_url: str,
) -> None:
    _ready_with_mock_runtime(page, app_url)
    page.evaluate("globalThis.__mockCalculateDelayMs = 250")
    page.locator("#calculate").click()
    expect(page.locator("#runtime-status")).to_have_text("Calculating…")

    page.locator('button[type="reset"]').click()
    expect(page.locator("#result")).to_be_hidden()
    page.wait_for_timeout(400)

    expect(page.locator("#result")).to_be_hidden()
    expect(page.locator(".empty-state")).to_be_visible()
    expect(page.locator("#export-csv")).to_be_disabled()
    expect(page.locator("#runtime-status")).to_have_text(
        "Ready. Calculations stay in this browser."
    )


def test_reviewer_table_and_plot_disclosure_follow_browser_contract(
    page: Page,
    app_url: str,
) -> None:
    _ready_with_mock_runtime(page, app_url)
    _calculate(page)

    expect(page.locator("#reviewer-scenario")).to_have_value("scenario-reference")
    reference_cells = page.locator("#scenario-table tbody tr").nth(1).locator("td")
    expect(reference_cells).to_have_count(7)
    assert [reference_cells.nth(index).text_content() for index in range(7)] == [
        "0.2",
        "1",
        "25%",
        "10%",
        "1.5x",
        "2.1x",
        "2.5",
    ]
    expect(page.locator("#plot")).to_have_attribute(
        "data-plot-title",
        "Forward calibration across assumed true effects"
        "<br><sup>Values above 10x are clipped in this plot only; "
        "numeric values remain uncapped.</sup>",
    )
