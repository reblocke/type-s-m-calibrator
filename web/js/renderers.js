function formatNumber(value, options = {}) {
  if (value === null || value === undefined) {
    return "—";
  }
  return Number(value).toLocaleString("en-US", {
    maximumSignificantDigits: options.maximumSignificantDigits || 6,
  });
}

function formatProbability(value) {
  if (value === null || value === undefined) {
    return "—";
  }
  return `${formatNumber(value * 100, { maximumSignificantDigits: 4 })}%`;
}

function scenarioSymbols(scenarios) {
  const symbols = {
    null: "x",
    observed_estimate_as_truth: "square-open",
    reference_threshold: "triangle-up-open",
    user_assumed_true_effect: "circle-open",
  };
  return scenarios.map((scenario) => symbols[scenario.source] || "circle-open");
}

function capped(values, cap) {
  return values.map((value) => (value === null ? null : Math.min(value, cap)));
}

function scenarioValues(scenarios, key, cap = null) {
  return scenarios.map((scenario) => {
    const value = scenario[key];
    if (value === null || cap === null) {
      return value;
    }
    return Math.min(value, cap);
  });
}

function panelTrace(response, key, name, axes, color, cap = null) {
  const values = response.grid[key];
  const y = cap === null ? values : capped(values, cap);
  return {
    connectgaps: false,
    customdata: values,
    hovertemplate: `%{x:.6g}<br>${name}: %{customdata:.6g}<extra></extra>`,
    line: { color, width: 3 },
    mode: "lines",
    name,
    showlegend: false,
    type: "scatter",
    x: response.grid.true_effect_display,
    xaxis: axes.x,
    y,
    yaxis: axes.y,
  };
}

function scenarioTrace(response, key, name, axes, cap = null, showlegend = false) {
  const customdata = response.scenarios.map((scenario) => [
    scenario.label,
    scenario[key],
  ]);
  return {
    customdata,
    hovertemplate: "%{customdata[0]}<br>%{customdata[1]:.6g}<extra></extra>",
    marker: {
      color: "#17202a",
      line: { color: "#17202a", width: 1.5 },
      size: 9,
      symbol: scenarioSymbols(response.scenarios),
    },
    mode: "markers",
    name: "Scenario values",
    showlegend,
    type: "scatter",
    x: response.scenarios.map((scenario) => scenario.true_effect_display),
    xaxis: axes.x,
    y: scenarioValues(response.scenarios, key, cap),
    yaxis: axes.y,
  };
}

function xAxis(response, title, compact = false) {
  return {
    gridcolor: "#dce3e5",
    title: {
      font: { size: compact ? 11 : 14 },
      standoff: compact ? 8 : 15,
      text: title,
    },
    type: response.meta.axis_spacing,
    zeroline: false,
  };
}

function addVerticalShapes(response, axes, shapes) {
  const nullScenario = response.scenarios.find((scenario) => scenario.source === "null");
  for (const axis of axes) {
    shapes.push({
      line: { color: "#17202a", dash: "dot", width: 1.5 },
      type: "line",
      x0: nullScenario.true_effect_display,
      x1: nullScenario.true_effect_display,
      xref: axis.x,
      y0: 0,
      y1: 1,
      yref: `${axis.y} domain`,
    });
  }
  if (response.selection_rule.claim_threshold_display !== null) {
    for (const axis of axes) {
      shapes.push({
        line: { color: "#b05a00", dash: "dash", width: 2 },
        type: "line",
        x0: response.selection_rule.claim_threshold_display,
        x1: response.selection_rule.claim_threshold_display,
        xref: axis.x,
        y0: 0,
        y1: 1,
        yref: `${axis.y} domain`,
      });
    }
  }
  for (const scenario of response.scenarios.filter(
    (candidate) => candidate.merged_sources.includes("reference_threshold"),
  )) {
    for (const axis of axes) {
      shapes.push({
        line: { color: "#4f6470", dash: "dashdot", width: 1.5 },
        type: "line",
        x0: scenario.true_effect_display,
        x1: scenario.true_effect_display,
        xref: axis.x,
        y0: 0,
        y1: 1,
        yref: `${axis.y} domain`,
      });
    }
  }
}

function renderScenarioTable(response, table) {
  table.querySelector("caption").textContent =
    "Scenario values condition on the listed value being true. Probabilities are percentages; " +
    "Type M and observed exaggeration are x-fold ratios; an em dash is explained by the row " +
    "or interpretation notes." +
    (response.meta.effect_family === "ratio"
      ? " Type M is computed on the log scale."
      : "");
  const body = table.querySelector("tbody");
  body.replaceChildren();
  for (const scenario of response.scenarios) {
    const row = document.createElement("tr");
    const label = document.createElement("th");
    label.scope = "row";
    label.textContent = scenario.label;
    if (scenario.note) {
      const note = document.createElement("span");
      note.className = "scenario-note";
      note.textContent = scenario.note;
      label.append(note);
    }
    row.append(label);
    const cells = [
      formatNumber(scenario.true_effect_display),
      formatNumber(scenario.standardized_true_effect),
      formatProbability(scenario.selected_claim_probability),
      formatProbability(scenario.type_s),
      scenario.type_m === null ? "—" : `${formatNumber(scenario.type_m)}x`,
      scenario.observed_exaggeration === null
        ? "—"
        : `${formatNumber(scenario.observed_exaggeration)}x`,
      formatNumber(scenario.expected_selected_abs_z),
    ];
    for (const value of cells) {
      const cell = document.createElement("td");
      cell.textContent = value;
      row.append(cell);
    }
    body.append(row);
  }
}

function renderReviewerChoices(response, select, text) {
  select.replaceChildren();
  const hasSource = (scenario, source) =>
    scenario.source === source || scenario.merged_sources.includes(source);
  const preferred =
    response.scenarios.find((scenario) => hasSource(scenario, "user_assumed_true_effect")) ||
    response.scenarios.find(
      (scenario) =>
        hasSource(scenario, "reference_threshold") &&
        scenario.standardized_true_effect !== 0,
    ) ||
    response.scenarios.find((scenario) => hasSource(scenario, "observed_estimate_as_truth")) ||
    response.scenarios[0];
  for (const scenario of response.scenarios) {
    const option = document.createElement("option");
    option.value = scenario.id;
    option.textContent = scenario.label;
    option.selected = scenario.id === preferred.id;
    select.append(option);
  }
  text.value = preferred.reviewer_text;
}

function renderWarnings(response, list) {
  list.replaceChildren();
  for (const warning of response.warnings) {
    const item = document.createElement("li");
    item.textContent = warning;
    list.append(item);
  }
}

export async function renderResult(response, elements) {
  const observed = response.grid.observed_exaggeration_optional !== null;
  const cap = response.meta.plot_exaggeration_cap;
  const capApplied = response.meta.plot_exaggeration_cap_applied;
  const compact = globalThis.innerWidth <= 480;
  elements.summary.textContent =
    `${response.scenarios.length} assumed-true-effect scenarios at ` +
    `${formatNumber(response.precision.information_multiplier)}x information; ` +
    `${response.selection_rule.label}.`;
  elements.precision.textContent =
    `Current SE ${formatNumber(response.precision.current_se_working)}; ` +
    `hypothetical scenario SE ${formatNumber(response.precision.scenario_se_working)}. ` +
    `${response.precision.source_note} ${response.precision.working_scale_note} ` +
    response.precision.information_note;
  const ruleDetails = [
    response.selection_rule.label,
    `alpha ${formatNumber(response.selection_rule.alpha)}`,
  ];
  if (response.selection_rule.claim_direction !== null) {
    ruleDetails.push(`${response.selection_rule.claim_direction} direction`);
  }
  if (response.selection_rule.claim_threshold_display !== null) {
    ruleDetails.push(
      `claim threshold ${formatNumber(
        response.selection_rule.claim_threshold_display,
      )}`,
    );
  }
  elements.rule.textContent =
    `${ruleDetails.join("; ")}. Active controls: ` +
    `${response.selection_rule.active_controls.join(", ")}. ` +
    response.selection_rule.explanation;
  elements.conditioning.textContent = response.meta.conditioning_statement;
  elements.caption.textContent = response.meta.caption;
  elements.observedNote.hidden = observed;
  renderScenarioTable(response, elements.table);
  renderReviewerChoices(response, elements.reviewerSelect, elements.reviewerText);
  renderWarnings(response, elements.warnings);

  if (!globalThis.Plotly) {
    throw new Error("The plotting library did not load.");
  }
  const axes = [
    { x: "x", y: "y" },
    { x: "x2", y: "y2" },
    { x: "x3", y: "y3" },
  ];
  if (observed) {
    axes.push({ x: "x4", y: "y4" });
  }
  const traces = [
    panelTrace(
      response,
      "selected_claim_probability",
      "Selected-claim probability",
      axes[0],
      "#176b78",
    ),
    scenarioTrace(response, "selected_claim_probability", "Scenario values", axes[0], null, true),
    panelTrace(response, "type_s", "Type S", axes[1], "#a84c00"),
    scenarioTrace(response, "type_s", "Scenario values", axes[1]),
    panelTrace(response, "type_m", "Type M", axes[2], "#513a83", cap),
    scenarioTrace(response, "type_m", "Scenario values", axes[2], cap),
  ];
  if (observed) {
    traces.push(
      panelTrace(
        response,
        "observed_exaggeration_optional",
        "Observed exaggeration",
        axes[3],
        "#087f5b",
        cap,
      ),
      scenarioTrace(response, "observed_exaggeration", "Scenario values", axes[3], cap),
    );
  }
  const effectLabel = response.meta.effect_label.toLowerCase();
  const xTitle = compact
    ? `Assumed true<br>${effectLabel}`
    : `Assumed true ${effectLabel}`;
  const shapes = [];
  addVerticalShapes(response, axes, shapes);
  shapes.push(
    {
      line: { color: "#17202a", dash: "dash", width: 1.3 },
      type: "line",
      x0: 0,
      x1: 1,
      xref: "x3 domain",
      y0: 1,
      y1: 1,
      yref: "y3",
    },
    {
      line: { color: "#68777d", dash: "dot", width: 1.3 },
      type: "line",
      x0: 0,
      x1: 1,
      xref: "x3 domain",
      y0: 2,
      y1: 2,
      yref: "y3",
    },
  );
  if (observed) {
    shapes.push(
      {
        line: { color: "#17202a", dash: "dash", width: 1.3 },
        type: "line",
        x0: 0,
        x1: 1,
        xref: "x4 domain",
        y0: 1,
        y1: 1,
        yref: "y4",
      },
      {
        line: { color: "#68777d", dash: "dot", width: 1.3 },
        type: "line",
        x0: 0,
        x1: 1,
        xref: "x4 domain",
        y0: 2,
        y1: 2,
        yref: "y4",
      },
    );
  }
  const panelTitles = observed
    ? [
        {
          text: compact
            ? "A. Selected-claim<br>probability"
            : "A. Selected-claim probability",
          x: 0.22,
          y: 1,
        },
        { text: "B. Type S", x: 0.78, y: 1 },
        { text: "C. Type M", x: 0.22, y: 0.45 },
        {
          text: compact
            ? "D. Observed<br>exaggeration"
            : "D. Observed exaggeration",
          x: 0.78,
          y: 0.45,
        },
      ]
    : [
        {
          text: compact
            ? "A. Selected-claim<br>probability"
            : "A. Selected-claim probability",
          x: 0.5,
          y: 0.98,
        },
        { text: "B. Type S", x: 0.5, y: 0.62 },
        { text: "C. Type M", x: 0.5, y: 0.25 },
      ];
  const layout = {
    annotations: panelTitles.map((title) => ({
      ...title,
      showarrow: false,
      xref: "paper",
      xanchor: "center",
      yref: "paper",
      font: { size: compact ? 12 : 14 },
    })),
    autosize: true,
    grid: observed
      ? { columns: 2, pattern: "independent", rows: 2 }
      : { columns: 1, pattern: "independent", rows: 3 },
    height: observed ? (compact ? 900 : 820) : 1100,
    legend: {
      font: { size: compact ? 11 : 12 },
      orientation: "h",
      x: compact ? 0.03 : 0,
      y: compact ? 1.07 : 1.08,
    },
    margin: compact
      ? { b: 80, l: 66, r: 16, t: 176 }
      : { b: 72, l: 72, r: 32, t: capApplied ? 112 : 84 },
    paper_bgcolor: "#ffffff",
    plot_bgcolor: "#ffffff",
    shapes,
    title: {
      text:
        (compact
          ? "Forward calibration across<br>assumed true effects"
          : "Forward calibration across assumed true effects") +
        (capApplied
          ? compact
            ? `<br><sup>Plot capped above ${cap}x; numeric values remain uncapped.</sup>`
            : `<br><sup>Values above ${cap}x are clipped in this plot only; ` +
              "numeric values remain uncapped.</sup>"
          : ""),
      font: { size: compact ? 16 : 17 },
      x: 0.5,
      y: compact ? 0.98 : undefined,
      yanchor: compact ? "top" : undefined,
      yref: compact ? "container" : undefined,
    },
    xaxis: xAxis(response, xTitle, compact),
    xaxis2: xAxis(response, xTitle, compact),
    xaxis3: xAxis(response, xTitle, compact),
    yaxis: {
      gridcolor: "#dce3e5",
      range: [0, 1],
      tickformat: ".0%",
      title: { font: { size: compact ? 11 : 14 }, text: "Probability" },
    },
    yaxis2: {
      gridcolor: "#dce3e5",
      range: [0, 1],
      tickformat: ".0%",
      title: {
        font: { size: compact ? 11 : 14 },
        text: "Conditional probability",
      },
    },
    yaxis3: {
      gridcolor: "#dce3e5",
      range: [0, cap],
      ticksuffix: "x",
      title: { font: { size: compact ? 11 : 14 }, text: "Type M (x-fold)" },
    },
  };
  if (observed) {
    layout.xaxis4 = xAxis(response, xTitle, compact);
    layout.yaxis4 = {
      gridcolor: "#dce3e5",
      range: [0, cap],
      ticksuffix: "x",
      title: {
        font: { size: compact ? 11 : 14 },
        text: compact
          ? "Observed exaggeration<br>(x-fold)"
          : "Observed exaggeration (x-fold)",
      },
    };
  }
  await globalThis.Plotly.react(
    elements.plot,
    traces,
    layout,
    {
      displayModeBar: compact ? false : "hover",
      displaylogo: false,
      responsive: true,
      scrollZoom: false,
    },
  );
}
