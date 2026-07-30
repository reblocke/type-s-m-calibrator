export async function renderResult(response, elements) {
  elements.summary.textContent = response.summary;
  const body = elements.table.querySelector("tbody");
  body.replaceChildren();
  for (const row of response.rows) {
    const tableRow = document.createElement("tr");
    const label = document.createElement("th");
    label.scope = "row";
    label.textContent = row.label;
    const value = document.createElement("td");
    value.textContent = Number(row.value).toLocaleString("en-US", {
      maximumSignificantDigits: 12,
    });
    tableRow.append(label, value);
    body.append(tableRow);
  }
  if (!globalThis.Plotly) {
    throw new Error("The plotting library did not load.");
  }
  await globalThis.Plotly.react(
    elements.plot,
    response.figure.data,
    {
      ...response.figure.layout,
      autosize: true,
      margin: { b: 64, l: 64, r: 24, t: 56 },
    },
    {
      displaylogo: false,
      responsive: true,
      scrollZoom: false,
    },
  );
  elements.result.hidden = false;
}
