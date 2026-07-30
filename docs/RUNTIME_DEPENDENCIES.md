# Runtime Dependencies and Provenance

## Browser runtime

- Pyodide 0.29.3 is loaded from its versioned jsDelivr path.
- Plotly.js 3.1.0 is loaded from Plotly’s versioned CDN path.
- Generated local Python files are listed and hashed by `web/assets/py/manifest.json`.

These CDN requests are static and do not include user values. Availability still depends on the
user reaching the CDNs unless downstream apps vendor reviewed assets.

## Python packages

`uv.lock` controls local and CI resolution. `browser-stage.toml` independently states which
installed package directories are copied into the browser and the exact expected versions.
Released URL artifacts may additionally be bound by URL and SHA-256.

AUTHOR ACTION REQUIRED: document every downstream runtime/scientific dependency, why it is
needed, its license, version, source URL, checksum where practical, and scientific authority
where applicable.

## Licenses

Template repository code is MIT licensed. Pyodide, Plotly, Python packages, papers, data, figures,
and publisher assets retain their own licenses. Do not copy an external artifact without
confirming compatible rights and attribution.
