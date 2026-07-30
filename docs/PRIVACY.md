# Privacy

## Data flow

User input is read by the page, sent with `postMessage` to a same-origin Web
Worker, processed by Python in Pyodide, and returned to the page for local
display/export. Inputs exist only in page and worker memory during the open
session.

Effect estimates, confidence limits, thresholds, and scenarios can be
sensitive even without direct identifiers. The app is not a storage or
sharing system and users should avoid entering protected health information.

## Guardrails

The app has:

- no backend, database, or upload path;
- no telemetry or analytics;
- no local or session storage;
- no input values in URL query strings or fragments;
- no cookies;
- no application logging of input or protected health information;
- no hidden persistence;
- no sharing endpoint.

Static requests fetch HTML, CSS, JavaScript, Plotly, Pyodide, and generated
Python files. User values are not included in request URLs, headers, or
bodies. CDN operators can observe ordinary network metadata such as IP address
and requested static asset, but not values entered into the app.

## Exports

CSV and PNG files are created locally only after an explicit button press.
Caption and reviewer text are copied only after an explicit button press. The
browser and operating system control the download directory and clipboard.
The app does not upload or retain exports.

## Fixtures and screenshots

Committed tests use synthetic/frozen numerical examples without patient
identifiers. Browser privacy tests use conspicuous synthetic sentinel values
and assert they do not enter network requests. Release evidence must not
include user-entered or patient-derived values in screenshots or logs.

Any future storage, telemetry, server, analytics, sharing, or upload proposal
requires a separate data-flow, retention, access, and compliance review before
implementation.
