import { clearFieldErrors, setStatus, showErrors } from "./js/accessibility.js";
import { APP_TITLE } from "./js/config.js";
import {
  copyText,
  exportCsv,
  exportDashboardPng,
  exportFigurePng,
} from "./js/exports.js";
import {
  applyEffectDefaults,
  readRequest,
  updateControlState,
} from "./js/inputs.js";
import {
  plotUsesCompactLayout,
  renderPlot,
  renderResult,
} from "./js/renderers.js";
import { WorkerRuntime } from "./js/runtime.js";

const form = document.querySelector("#applet-form");
const errorSummary = document.querySelector("#error-summary");
const status = document.querySelector("#runtime-status");
const retryButton = document.querySelector("#retry-worker");
const calculateButton = document.querySelector("#calculate");
const result = document.querySelector("#result");
const summary = document.querySelector("#result-summary");
const table = document.querySelector("#scenario-table");
const plot = document.querySelector("#plot");
const exportButtons = [...document.querySelectorAll("[data-export]")];
const copyButtons = [...document.querySelectorAll("[data-copy]")];
const emptyState = document.querySelector(".empty-state");
const reviewerSelect = document.querySelector("#reviewer-scenario");
const reviewerText = document.querySelector("#reviewer-text");
const runtime = new WorkerRuntime();
let currentResponse = null;
let calculationGeneration = 0;
let calculationInFlight = false;
let runtimeGeneration = 0;
let runtimeReady = false;
let observedPlotCompact = null;
let resizeRenderGeneration = 0;
let resizeRenderQueue = Promise.resolve();

function resultElements() {
  return {
    caption: document.querySelector("#figure-caption"),
    conditioning: document.querySelector("#conditioning-result"),
    observedNote: document.querySelector("#observed-panel-note"),
    plot,
    precision: document.querySelector("#precision-summary"),
    result,
    reviewerSelect,
    reviewerText,
    rule: document.querySelector("#rule-summary"),
    summary,
    table,
    warnings: document.querySelector("#warnings-list"),
  };
}

function setExportAvailability(enabled) {
  for (const button of [...exportButtons, ...copyButtons]) {
    button.disabled = !enabled;
  }
}

function clearResultState() {
  currentResponse = null;
  observedPlotCompact = null;
  resizeRenderGeneration += 1;
  result.hidden = true;
  emptyState.hidden = false;
  setExportAvailability(false);
}

function queueResponsivePlotRender(compact) {
  const response = currentResponse;
  const calculation = calculationGeneration;
  const resizeGeneration = ++resizeRenderGeneration;
  resizeRenderQueue = resizeRenderQueue
    .catch(() => {})
    .then(async () => {
      if (
        resizeGeneration !== resizeRenderGeneration ||
        calculation !== calculationGeneration ||
        response !== currentResponse ||
        result.hidden
      ) {
        return;
      }
      await renderPlot(response, plot, { compact });
    })
    .catch(() => {
      if (
        resizeGeneration === resizeRenderGeneration &&
        calculation === calculationGeneration &&
        response === currentResponse
      ) {
        setStatus(status, "The plot could not adapt to its available width.", "error");
      }
    });
}

const plotResizeObserver = new ResizeObserver((entries) => {
  const plotEntry = entries.find((entry) => entry.target === plot);
  const width = plotEntry?.contentRect.width || 0;
  if (width <= 0) {
    return;
  }
  const compact = plotUsesCompactLayout(plot, width);
  const crossedCategory =
    observedPlotCompact !== null && compact !== observedPlotCompact;
  observedPlotCompact = compact;
  if (crossedCategory && currentResponse !== null) {
    queueResponsivePlotRender(compact);
  }
});
plotResizeObserver.observe(plot);

async function startRuntime() {
  const generation = ++runtimeGeneration;
  calculationGeneration += 1;
  calculationInFlight = false;
  runtimeReady = false;
  clearResultState();
  calculateButton.disabled = true;
  retryButton.hidden = true;
  setStatus(status, "Loading the local Python runtime…", "loading");
  try {
    const ready = await runtime.restart();
    if (generation !== runtimeGeneration) {
      return;
    }
    document.querySelector("#runtime-versions").textContent = ready.packages
      .map((entry) => `${entry.distribution} ${entry.version}`)
      .join(" · ");
    const externalPackages = ready.packages.slice(1);
    document.querySelector("#core-version").textContent =
      `Core: ${externalPackages
        .map((entry) => `${entry.distribution} ${entry.version}`)
        .join(" · ")}`;
    runtimeReady = true;
    calculateButton.disabled = false;
    setStatus(status, "Ready. Calculations stay in this browser.", "ready");
  } catch {
    if (generation !== runtimeGeneration) {
      return;
    }
    retryButton.hidden = false;
    setStatus(status, "The calculation worker could not start.", "error");
  }
}

form.addEventListener("change", (event) => {
  if (["effect_type", "precision_mode", "selection_rule"].includes(event.target.name)) {
    if (event.target.name === "effect_type") {
      applyEffectDefaults(form);
    }
    updateControlState(form);
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const generation = ++calculationGeneration;
  clearResultState();
  clearFieldErrors(form);
  const { errors, request } = readRequest(form);
  showErrors(errorSummary, errors);
  if (errors.length > 0) {
    setStatus(status, "Check the highlighted inputs.", "error");
    return;
  }

  calculationInFlight = true;
  calculateButton.disabled = true;
  setStatus(status, "Calculating…", "loading");
  try {
    const response = await runtime.calculate(request);
    if (generation !== calculationGeneration) {
      return;
    }
    await renderResult(response, resultElements());
    if (generation !== calculationGeneration) {
      return;
    }
    emptyState.hidden = true;
    result.hidden = false;
    await new Promise((resolve) =>
      globalThis.requestAnimationFrame(resolve),
    );
    await globalThis.Plotly.Plots.resize(plot);
    currentResponse = response;
    observedPlotCompact = plotUsesCompactLayout(plot);
    setExportAvailability(true);
    setStatus(status, "Calculation complete.", "ready");
  } catch (error) {
    if (generation !== calculationGeneration) {
      return;
    }
    clearResultState();
    showErrors(errorSummary, [
      {
        controlId: null,
        message:
          error.code === "validation_error"
            ? error.message
            : "Calculation failed safely. Restart the worker and try again.",
      },
    ]);
    retryButton.hidden = false;
    setStatus(status, "Calculation failed.", "error");
  } finally {
    calculationInFlight = false;
    calculateButton.disabled = !runtimeReady;
    if (generation !== calculationGeneration && runtimeReady) {
      setStatus(status, "Ready. Calculations stay in this browser.", "ready");
    }
  }
});

form.addEventListener("reset", () => {
  calculationGeneration += 1;
  clearResultState();
  clearFieldErrors(form);
  showErrors(errorSummary, []);
  requestAnimationFrame(() => {
    updateControlState(form);
    calculateButton.disabled = calculationInFlight || !runtimeReady;
    setStatus(
      status,
      calculationInFlight
        ? "Reset complete. Discarding the in-flight result…"
        : "Ready. Calculations stay in this browser.",
      calculationInFlight ? "loading" : "ready",
    );
  });
});

reviewerSelect.addEventListener("change", () => {
  const scenario = currentResponse?.scenarios.find(
    (candidate) => candidate.id === reviewerSelect.value,
  );
  reviewerText.value = scenario?.reviewer_text || "";
});

retryButton.addEventListener("click", startRuntime);

document.querySelector("#export-csv").addEventListener("click", () => {
  exportCsv(currentResponse, APP_TITLE);
});
document.querySelector("#export-figure").addEventListener("click", async () => {
  await exportFigurePng(currentResponse, APP_TITLE);
});
document.querySelector("#export-dashboard").addEventListener("click", async () => {
  const dashboardSummary =
    `${currentResponse.meta.conditioning_statement} ` +
    `Rule: ${currentResponse.selection_rule.label}; ` +
    `alpha ${currentResponse.selection_rule.alpha}; ` +
    `${currentResponse.precision.information_multiplier}x information. ` +
    (currentResponse.meta.plot_exaggeration_cap_applied
      ? `Plot values above ${currentResponse.meta.plot_exaggeration_cap}x are clipped; ` +
        "numeric values remain uncapped. "
      : "") +
    "Not a posterior probability.";
  await exportDashboardPng(currentResponse, dashboardSummary, APP_TITLE);
});
document.querySelector("#copy-caption").addEventListener("click", async () => {
  await copyText(currentResponse.meta.caption);
  setStatus(status, "Caption copied.", "ready");
});
document.querySelector("#copy-reviewer").addEventListener("click", async () => {
  await copyText(reviewerText.value);
  setStatus(status, "Reviewer text copied.", "ready");
});

updateControlState(form);
setExportAvailability(false);
startRuntime();
