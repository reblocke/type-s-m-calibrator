function requestError(payload) {
  const error = new Error(payload?.message || "The calculation worker failed.");
  error.code = payload?.code || "runtime_error";
  return error;
}

export class WorkerRuntime {
  constructor(workerUrl = new URL("../pyodide_worker.js", import.meta.url)) {
    this.workerUrl = workerUrl;
    this.worker = null;
    this.pending = new Map();
    this.sequence = 0;
  }

  async start() {
    this.stop();
    this.worker = new Worker(this.workerUrl);
    this.worker.addEventListener("message", (event) => {
      const message = event.data;
      const pending = this.pending.get(message?.id);
      if (!pending) {
        return;
      }
      this.pending.delete(message.id);
      if (message.type === "error") {
        pending.reject(requestError(message.error));
      } else {
        pending.resolve(message.payload);
      }
    });
    this.worker.addEventListener("error", () => {
      this._rejectAll(requestError({ message: "The calculation worker stopped unexpectedly." }));
    });
    return this._request("initialize", null);
  }

  calculate(input) {
    return this._request("calculate", input);
  }

  restart() {
    return this.start();
  }

  stop() {
    if (this.worker) {
      this.worker.terminate();
      this.worker = null;
    }
    this._rejectAll(requestError({ message: "The calculation worker was restarted." }));
  }

  _request(type, input) {
    if (!this.worker) {
      return Promise.reject(requestError({ message: "The calculation worker is not running." }));
    }
    const id = `request-${++this.sequence}`;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.worker.postMessage({ id, input, type });
    });
  }

  _rejectAll(error) {
    for (const pending of this.pending.values()) {
      pending.reject(error);
    }
    this.pending.clear();
  }
}
