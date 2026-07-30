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

export function exportCsv(rows, appTitle) {
  const columns = [
    { key: "label", label: "Label" },
    { key: "value", label: "Value" },
  ];
  const csv = csvFromRows(columns, rows);
  downloadBlob(
    new Blob([csv], { type: "text/csv;charset=utf-8" }),
    `${filenameSlug(appTitle)}-results.csv`,
  );
}

export async function exportFigurePng(plotElement, appTitle) {
  const dataUrl = await globalThis.Plotly.toImage(plotElement, {
    format: "png",
    height: 1200,
    scale: 1,
    width: 1600,
  });
  downloadBlob(dataUrlToBlob(dataUrl), `${filenameSlug(appTitle)}-figure.png`);
}

export async function exportDashboardPng(plotElement, summary, appTitle) {
  const plotDataUrl = await globalThis.Plotly.toImage(plotElement, {
    format: "png",
    height: 800,
    scale: 1,
    width: 1200,
  });
  const plotImage = await loadImage(plotDataUrl);
  const canvas = document.createElement("canvas");
  canvas.width = 1400;
  canvas.height = 1100;
  const context = canvas.getContext("2d");
  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, canvas.width, canvas.height);
  context.fillStyle = "#17202a";
  context.font = "700 42px system-ui";
  context.fillText(appTitle, 80, 80, 1240);
  context.font = "26px system-ui";
  context.fillText(summary, 80, 140, 1240);
  context.drawImage(plotImage, 100, 210, 1200, 800);
  const blob = await canvasBlob(canvas);
  downloadBlob(blob, `${filenameSlug(appTitle)}-dashboard.png`);
}

export async function copyCaption(caption) {
  await navigator.clipboard.writeText(caption);
}
