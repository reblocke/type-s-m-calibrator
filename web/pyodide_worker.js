const PYODIDE_VERSION = "0.29.3";
const PYODIDE_INDEX_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
const PYTHON_ROOT = "/home/pyodide";
const SHA256_PATTERN = /^[0-9a-f]{64}$/;
const COMMIT_PATTERN = /^[0-9a-f]{40}$/;
const SAFE_SEGMENT_PATTERN = /^[A-Za-z0-9._-]+$/;
let runtimePromise = null;

function exactKeys(value, expected, label) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(`${label} must be an object.`);
  }
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  if (
    actual.length !== wanted.length ||
    actual.some((key, index) => key !== wanted[index])
  ) {
    throw new Error(`${label} has an unexpected schema.`);
  }
}

function validatePath(path, importName) {
  const segments = typeof path === "string" ? path.split("/") : [];
  if (
    segments.length < 2 ||
    segments[0] !== importName ||
    path.startsWith("/") ||
    path.includes("\\") ||
    path.includes("?") ||
    path.includes("#") ||
    segments.some(
      (segment) =>
        segment === "" ||
        segment === "." ||
        segment === ".." ||
        !SAFE_SEGMENT_PATTERN.test(segment),
    )
  ) {
    throw new Error("The Python manifest contains an unsafe file path.");
  }
}

function bundleDescriptor(records) {
  return [...records]
    .sort((left, right) => left.path.localeCompare(right.path))
    .map((record) => `${record.path}\0${record.sha256}\0${record.bytes}\n`)
    .join("");
}

async function sha256Hex(bytes) {
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest), (value) => {
    return value.toString(16).padStart(2, "0");
  }).join("");
}

function validateManifest(manifest) {
  exactKeys(
    manifest,
    [
      "bundle_sha256",
      "packages",
      "pyodide_packages",
      "pyodide_version",
      "schema_version",
      "source_commit",
    ],
    "Manifest",
  );
  if (
    manifest.schema_version !== 1 ||
    manifest.pyodide_version !== PYODIDE_VERSION ||
    !COMMIT_PATTERN.test(manifest.source_commit) ||
    !SHA256_PATTERN.test(manifest.bundle_sha256)
  ) {
    throw new Error("The Python manifest identity is invalid.");
  }
  if (
    !Array.isArray(manifest.pyodide_packages) ||
    manifest.pyodide_packages.some(
      (entry) => typeof entry !== "string" || !/^[A-Za-z0-9_.-]+$/.test(entry),
    ) ||
    new Set(manifest.pyodide_packages).size !== manifest.pyodide_packages.length
  ) {
    throw new Error("The Pyodide package list is invalid.");
  }
  if (!Array.isArray(manifest.packages) || manifest.packages.length < 1) {
    throw new Error("The Python manifest has no packages.");
  }
  const roles = new Set();
  const paths = new Set();
  for (const packageRecord of manifest.packages) {
    exactKeys(
      packageRecord,
      [
        "artifact_sha256",
        "artifact_url",
        "distribution",
        "files",
        "import_name",
        "package_sha256",
        "role",
        "version",
      ],
      "Package",
    );
    if (
      typeof packageRecord.role !== "string" ||
      roles.has(packageRecord.role) ||
      typeof packageRecord.distribution !== "string" ||
      typeof packageRecord.import_name !== "string" ||
      !/^[A-Za-z_][A-Za-z0-9_]*$/.test(packageRecord.import_name) ||
      typeof packageRecord.version !== "string" ||
      !SHA256_PATTERN.test(packageRecord.package_sha256) ||
      !Array.isArray(packageRecord.files) ||
      packageRecord.files.length === 0
    ) {
      throw new Error("A Python package manifest record is invalid.");
    }
    if (
      (packageRecord.artifact_url === null) !==
        (packageRecord.artifact_sha256 === null) ||
      (packageRecord.artifact_url !== null &&
        (typeof packageRecord.artifact_url !== "string" ||
          !packageRecord.artifact_url.startsWith("https://") ||
          !SHA256_PATTERN.test(packageRecord.artifact_sha256)))
    ) {
      throw new Error("A Python package artifact record is invalid.");
    }
    roles.add(packageRecord.role);
    for (const fileRecord of packageRecord.files) {
      exactKeys(fileRecord, ["bytes", "path", "sha256"], "Package file");
      validatePath(fileRecord.path, packageRecord.import_name);
      if (
        paths.has(fileRecord.path) ||
        !Number.isSafeInteger(fileRecord.bytes) ||
        fileRecord.bytes < 0 ||
        !SHA256_PATTERN.test(fileRecord.sha256)
      ) {
        throw new Error("A Python package file record is invalid.");
      }
      paths.add(fileRecord.path);
    }
  }
  if (!roles.has("app") || [...roles].filter((role) => role === "app").length !== 1) {
    throw new Error("The Python manifest must contain one app package.");
  }
  return manifest;
}

async function fetchVerifiedBundle() {
  const manifestUrl = new URL("./assets/py/manifest.json", self.location.href);
  const manifestResponse = await fetch(manifestUrl, { cache: "no-store" });
  if (!manifestResponse.ok) {
    throw new Error("The Python manifest could not be loaded.");
  }
  const manifest = validateManifest(await manifestResponse.json());
  const verifiedFiles = [];
  for (const packageRecord of manifest.packages) {
    const packageFiles = [];
    for (const fileRecord of packageRecord.files) {
      const fileUrl = new URL(fileRecord.path, manifestUrl);
      fileUrl.searchParams.set("sha256", fileRecord.sha256);
      const response = await fetch(fileUrl, { cache: "no-store" });
      if (!response.ok) {
        throw new Error("A staged Python file could not be loaded.");
      }
      const contents = new Uint8Array(await response.arrayBuffer());
      if (
        contents.byteLength !== fileRecord.bytes ||
        (await sha256Hex(contents)) !== fileRecord.sha256
      ) {
        throw new Error("A staged Python file failed integrity verification.");
      }
      const verified = { ...fileRecord, contents };
      packageFiles.push(verified);
      verifiedFiles.push(verified);
    }
    const packageHash = await sha256Hex(
      new TextEncoder().encode(bundleDescriptor(packageFiles)),
    );
    if (packageHash !== packageRecord.package_sha256) {
      throw new Error("A staged Python package failed integrity verification.");
    }
  }
  const bundleHash = await sha256Hex(
    new TextEncoder().encode(bundleDescriptor(verifiedFiles)),
  );
  if (bundleHash !== manifest.bundle_sha256) {
    throw new Error("The staged Python bundle failed integrity verification.");
  }
  return { files: verifiedFiles, manifest };
}

function strictJson(value) {
  const visit = (current) => {
    if (current === null || typeof current === "string" || typeof current === "boolean") {
      return;
    }
    if (typeof current === "number") {
      if (!Number.isFinite(current)) {
        throw new Error("Request contains a non-finite number.");
      }
      return;
    }
    if (Array.isArray(current)) {
      current.forEach(visit);
      return;
    }
    if (
      typeof current === "object" &&
      (Object.getPrototypeOf(current) === Object.prototype ||
        Object.getPrototypeOf(current) === null)
    ) {
      Object.values(current).forEach(visit);
      return;
    }
    throw new Error("Request contains a value that cannot be represented in JSON.");
  };
  visit(value);
  return JSON.stringify(value);
}

async function initializeRuntime() {
  const bundle = await fetchVerifiedBundle();
  importScripts(`${PYODIDE_INDEX_URL}pyodide.js`);
  const pyodide = await loadPyodide({ indexURL: PYODIDE_INDEX_URL });
  if (bundle.manifest.pyodide_packages.length > 0) {
    await pyodide.loadPackage(bundle.manifest.pyodide_packages);
  }
  for (const fileRecord of bundle.files) {
    const destination = `${PYTHON_ROOT}/${fileRecord.path}`;
    pyodide.FS.mkdirTree(destination.slice(0, destination.lastIndexOf("/")));
    pyodide.FS.writeFile(destination, fileRecord.contents);
  }
  await pyodide.runPythonAsync(`
import sys
if "${PYTHON_ROOT}" not in sys.path:
    sys.path.insert(0, "${PYTHON_ROOT}")
`);
  pyodide.globals.set(
    "package_expectations_json",
    JSON.stringify(
      bundle.manifest.packages.map((entry) => ({
        distribution: entry.distribution,
        import_name: entry.import_name,
        version: entry.version,
      })),
    ),
  );
  const versionsJson = await pyodide.runPythonAsync(`
import importlib
import json

expectations = json.loads(package_expectations_json)
versions = []
for expectation in expectations:
    module = importlib.import_module(expectation["import_name"])
    observed = getattr(module, "__version__", None)
    if observed != expectation["version"]:
        raise RuntimeError(
            f'Imported {expectation["import_name"]} version {observed!r}; '
            f'expected {expectation["version"]!r}.'
        )
    versions.append({
        "distribution": expectation["distribution"],
        "version": observed,
    })
json.dumps(versions, allow_nan=False)
`);
  pyodide.globals.delete("package_expectations_json");
  const appPackage = bundle.manifest.packages.find((entry) => entry.role === "app");
  return {
    appImportName: appPackage.import_name,
    packages: JSON.parse(versionsJson),
    pyodide,
  };
}

function getRuntime() {
  runtimePromise ||= initializeRuntime().catch((error) => {
    runtimePromise = null;
    throw error;
  });
  return runtimePromise;
}

function safeError(error) {
  const message = error instanceof Error ? error.message : String(error);
  const validationLine = message
    .split("\n")
    .map((line) => line.trim())
    .findLast((line) => line.includes("ValidationError:"));
  if (validationLine) {
    return {
      code: "validation_error",
      message: validationLine
        .replace(/^.*ValidationError:\s*/, "")
        .replace(/[\u0000-\u001f\u007f]/g, " ")
        .slice(0, 240),
    };
  }
  return {
    code: "runtime_error",
    message: "The local calculation runtime failed.",
  };
}

async function calculate(input) {
  const runtime = await getRuntime();
  const inputJson = strictJson(input);
  runtime.pyodide.globals.set("input_json", inputJson);
  runtime.pyodide.globals.set("app_import_name", runtime.appImportName);
  try {
    const responseJson = await runtime.pyodide.runPythonAsync(`
import importlib

contract = importlib.import_module(f"{app_import_name}.contract")
contract.calculate_json(input_json)
`);
    const response = JSON.parse(responseJson);
    strictJson(response);
    return response;
  } finally {
    runtime.pyodide.globals.delete("input_json");
    runtime.pyodide.globals.delete("app_import_name");
  }
}

self.addEventListener("message", async (event) => {
  const { id, input, type } = event.data || {};
  if (typeof id !== "string") {
    return;
  }
  try {
    if (type === "initialize") {
      const runtime = await getRuntime();
      self.postMessage({
        id,
        payload: { packages: runtime.packages },
        type: "ready",
      });
      return;
    }
    if (type === "calculate") {
      self.postMessage({
        id,
        payload: await calculate(input),
        type: "calculation",
      });
      return;
    }
    self.postMessage({
      error: { code: "request_error", message: "Unknown worker request." },
      id,
      type: "error",
    });
  } catch (error) {
    self.postMessage({ error: safeError(error), id, type: "error" });
  }
});
