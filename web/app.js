import { clearFieldErrors, setStatus, showErrors } from "./js/accessibility.js";
import { APP_TITLE } from "./js/config.js";
import {
  copyCaption,
  exportCsv,
  exportDashboardPng,
  exportFigurePng,
} from "./js/exports.js";
import { readRequest } from "./js/inputs.js";
import { renderResult } from "./js/renderers.js";
import { WorkerRuntime } from "./js/runtime.js";

const form = document.querySelector("#applet-form");
const errorSummary = document.querySelector("#error-summary");
const status = document.querySelector("#runtime-status");
const retryButton = document.querySelector("#retry-worker");
const calculateButton = document.querySelector("#calculate");
const result = document.querySelector("#result");
const summary = document.querySelector("#result-summary");
const table = document.querySelector("#result-table");
const plot = document.querySelector("#plot");
const exportButtons = [...document.querySelectorAll("[data-export]")];
const copyButton = document.querySelector("#copy-caption");
const emptyState = document.querySelector(".empty-state");
const runtime = new WorkerRuntime();
let currentResponse = null;

function setExportAvailability(enabled) {
  for (const button of [...exportButtons, copyButton]) {
    button.disabled = !enabled;
  }
}

async function startRuntime() {
  calculateButton.disabled = true;
  retryButton.hidden = true;
  setStatus(status, "Loading the local Python runtime…", "loading");
  try {
    const ready = await runtime.restart();
    document.querySelector("#runtime-versions").textContent = ready.packages
      .map((entry) => `${entry.distribution} ${entry.version}`)
      .join(" · ");
    const externalPackages = ready.packages.slice(1);
    document.querySelector("#core-version").textContent =
      externalPackages.length === 0
        ? "Core: none configured"
        : `Core: ${externalPackages
            .map((entry) => `${entry.distribution} ${entry.version}`)
            .join(" · ")}`;
    calculateButton.disabled = false;
    setStatus(status, "Ready. Calculations stay in this browser.", "ready");
  } catch {
    retryButton.hidden = false;
    setStatus(status, "The calculation worker could not start.", "error");
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearFieldErrors(form);
  const { errors, request } = readRequest(form);
  showErrors(errorSummary, errors);
  if (errors.length > 0) {
    return;
  }

  calculateButton.disabled = true;
  setExportAvailability(false);
  setStatus(status, "Calculating…", "loading");
  try {
    const response = await runtime.calculate(request);
    await renderResult(response, { plot, result, summary, table });
    emptyState.hidden = true;
    currentResponse = response;
    setExportAvailability(true);
    setStatus(status, "Calculation complete.", "ready");
  } catch (error) {
    currentResponse = null;
    result.hidden = true;
    emptyState.hidden = false;
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
    calculateButton.disabled = false;
  }
});

form.addEventListener("reset", () => {
  requestAnimationFrame(() => {
    clearFieldErrors(form);
    showErrors(errorSummary, []);
    result.hidden = true;
    emptyState.hidden = false;
    currentResponse = null;
    setExportAvailability(false);
    setStatus(status, "Ready. Calculations stay in this browser.", "ready");
  });
});

retryButton.addEventListener("click", startRuntime);

document.querySelector("#export-csv").addEventListener("click", () => {
  exportCsv(currentResponse.rows, APP_TITLE);
});
document.querySelector("#export-figure").addEventListener("click", async () => {
  await exportFigurePng(plot, APP_TITLE);
});
document.querySelector("#export-dashboard").addEventListener("click", async () => {
  await exportDashboardPng(plot, currentResponse.summary, APP_TITLE);
});
copyButton.addEventListener("click", async () => {
  await copyCaption(currentResponse.caption);
  setStatus(status, "Caption copied.", "ready");
});

setExportAvailability(false);
startRuntime();
