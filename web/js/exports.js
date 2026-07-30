import { renderPlot } from "./renderers.js";

export function filenameSlug(value) {
  const slug = value
    .normalize("NFKD")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
  return slug || "scientific-applet";
}

function csvCell(value) {
  const text = String(value ?? "");
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

export function csvFromRows(columns, rows) {
  const header = columns.map((column) => csvCell(column.label)).join(",");
  const records = rows.map((row) => {
    return columns.map((column) => csvCell(row[column.key])).join(",");
  });
  return [header, ...records].join("\r\n") + "\r\n";
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

function dataUrlToBlob(dataUrl) {
  const [metadata, encoded] = dataUrl.split(",", 2);
  const mime = metadata.match(/^data:([^;]+);base64$/)?.[1] || "application/octet-stream";
  const bytes = Uint8Array.from(atob(encoded), (character) => character.charCodeAt(0));
  return new Blob([bytes], { type: mime });
}

function canvasBlob(canvas) {
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (blob) {
        resolve(blob);
      } else {
        reject(new Error("The browser could not create a PNG."));
      }
    }, "image/png");
  });
}

function loadImage(dataUrl) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.addEventListener("load", () => resolve(image), { once: true });
    image.addEventListener("error", () => reject(new Error("Could not render the plot image.")), {
      once: true,
    });
    image.src = dataUrl;
  });
}

function drawWrappedText(context, text, x, y, maxWidth, lineHeight, maxLines) {
  const words = text.split(/\s+/);
  let line = "";
  let lineIndex = 0;
  for (const word of words) {
    const candidate = line ? `${line} ${word}` : word;
    if (context.measureText(candidate).width <= maxWidth) {
      line = candidate;
      continue;
    }
    context.fillText(line, x, y + lineIndex * lineHeight);
    lineIndex += 1;
    if (lineIndex >= maxLines) {
      return;
    }
    line = word;
  }
  if (line && lineIndex < maxLines) {
    context.fillText(line, x, y + lineIndex * lineHeight);
  }
}

export function gridRows(response) {
  const observed = response.grid.observed_exaggeration_optional;
  return response.grid.true_effect_display.map((value, index) => ({
    true_effect_display: value,
    true_effect_working: response.grid.true_effect_working[index],
    standardized_true_effect: response.grid.standardized_true_effect[index],
    selected_claim_probability: response.grid.selected_claim_probability[index],
    type_s: response.grid.type_s[index],
    type_m: response.grid.type_m[index],
    expected_selected_abs_z: response.grid.expected_selected_abs_z[index],
    observed_exaggeration: observed === null ? null : observed[index],
  }));
}

export function exportCsv(response, appTitle) {
  const columns = [
    { key: "true_effect_display", label: "true_effect_display" },
    { key: "true_effect_working", label: "true_effect_working" },
    { key: "standardized_true_effect", label: "standardized_true_effect" },
    { key: "selected_claim_probability", label: "selected_claim_probability" },
    { key: "type_s", label: "type_s" },
    { key: "type_m", label: "type_m" },
    { key: "expected_selected_abs_z", label: "expected_selected_abs_z" },
    { key: "observed_exaggeration", label: "observed_exaggeration" },
  ];
  const csv = csvFromRows(columns, gridRows(response));
  downloadBlob(
    new Blob([csv], { type: "text/csv;charset=utf-8" }),
    `${filenameSlug(appTitle)}-curves.csv`,
  );
}

async function exportPlotDataUrl(response, width, height) {
  const exportPlot = document.createElement("div");
  exportPlot.setAttribute("aria-hidden", "true");
  Object.assign(exportPlot.style, {
    height: `${height}px`,
    left: "0",
    opacity: "0",
    pointerEvents: "none",
    position: "fixed",
    top: "0",
    width: `${width}px`,
    zIndex: "-1",
  });
  document.body.append(exportPlot);
  try {
    await renderPlot(response, exportPlot, {
      compact: false,
      height,
      purpose: "export",
      width,
    });
    return await globalThis.Plotly.toImage(exportPlot, {
      format: "png",
      height,
      scale: 1,
      width,
    });
  } finally {
    globalThis.Plotly.purge(exportPlot);
    exportPlot.remove();
  }
}

export async function exportFigurePng(response, appTitle) {
  const dataUrl = await exportPlotDataUrl(response, 1600, 1200);
  downloadBlob(dataUrlToBlob(dataUrl), `${filenameSlug(appTitle)}-figure.png`);
}

export async function exportDashboardPng(response, summary, appTitle) {
  const plotDataUrl = await exportPlotDataUrl(response, 1200, 900);
  const plotImage = await loadImage(plotDataUrl);
  const canvas = document.createElement("canvas");
  canvas.width = 1400;
  canvas.height = 1280;
  const context = canvas.getContext("2d");
  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, canvas.width, canvas.height);
  context.fillStyle = "#17202a";
  context.font = "700 42px system-ui";
  context.fillText(appTitle, 80, 80, 1240);
  context.font = "24px system-ui";
  drawWrappedText(context, summary, 80, 135, 1240, 34, 3);
  context.drawImage(plotImage, 100, 270, 1200, 900);
  const blob = await canvasBlob(canvas);
  downloadBlob(blob, `${filenameSlug(appTitle)}-dashboard.png`);
}

export async function copyText(text) {
  await navigator.clipboard.writeText(text);
}
