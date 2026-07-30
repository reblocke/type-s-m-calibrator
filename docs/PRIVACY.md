# Privacy

## Data flow

User input is read by the page, sent through `postMessage` to a same-origin Web Worker, processed
by Python in Pyodide, and returned to the page for display/export. Inputs exist only in page and
worker memory.

## Guardrails

The app has:

- no backend or database;
- no telemetry or analytics;
- no local storage or session storage;
- no input values in URL query strings or fragments;
- no cookies;
- no application logging of inputs or protected health information;
- no hidden persistence;
- no upload path.

Static requests fetch HTML, CSS, JavaScript, Plotly, Pyodide, and generated Python files. User
values are not included in request URLs, headers, or bodies. CDN operators can observe ordinary
network metadata such as IP address and requested static asset, but not values entered into this
app.

## Exports

CSV and PNG files are created locally after an explicit button press. The browser’s normal
download behavior determines where those files are saved. The app does not upload or retain
them.

## Author actions

AUTHOR ACTION REQUIRED: review every new input, example, fixture, URL, log, export, dependency,
and deployment change. Use synthetic fixtures. If any storage, server, analytics, sharing, or
upload feature is proposed, stop and document data path, retention, access, and compliance
assumptions before implementation.
