.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Targets:"
	@echo "  uv-sync          Restore the locked environment"
	@echo "  stage-web        Generate the ignored browser package bundle"
	@echo "  fmt              Format Python with Ruff"
	@echo "  fmt-check        Check Python formatting"
	@echo "  lint             Run Ruff lint"
	@echo "  test             Run non-browser tests"
	@echo "  e2e              Run the full Chromium browser suite"
	@echo "  e2e-webkit-smoke Run the initial WebKit worker smoke test"
	@echo "  verify           Run formatting, lint, tests, Chromium, and WebKit"
	@echo "  template-self-test Initialize and verify a disposable app"
	@echo "  serve            Stage and serve web/ on http://127.0.0.1:8000"
	@echo "  clean            Remove generated and local test artifacts"

.PHONY: uv-sync
uv-sync:
	uv sync --locked

.PHONY: stage-web
stage-web:
	uv run python scripts/stage_browser_packages.py

.PHONY: fmt
fmt:
	uv run ruff format .

.PHONY: fmt-check
fmt-check:
	uv run ruff format --check .

.PHONY: lint
lint:
	uv run ruff check .

.PHONY: test
test: stage-web
	uv run pytest -q -m "not e2e"

.PHONY: e2e
e2e: stage-web
	uv run pytest -q -m e2e \
		--browser chromium \
		--tracing retain-on-failure \
		--video retain-on-failure \
		--screenshot only-on-failure \
		--output test-results

.PHONY: e2e-webkit-smoke
e2e-webkit-smoke: stage-web
	uv run pytest -q \
		tests/e2e/test_applet.py::test_worker_loads_and_calculates \
		--browser webkit \
		--tracing retain-on-failure \
		--video retain-on-failure \
		--screenshot only-on-failure \
		--output test-results-webkit

.PHONY: verify
verify: fmt-check lint test e2e e2e-webkit-smoke

.PHONY: template-self-test
template-self-test:
	uv run python scripts/self_test_template.py --browser chromium

.PHONY: serve
serve: stage-web
	uv run python -m http.server --bind 127.0.0.1 --directory web 8000

.PHONY: clean
clean:
	@rm -rf .pytest_cache .ruff_cache build dist playwright-report
	@rm -rf test-results test-results-webkit web/assets/py
	@find src -maxdepth 1 -type d -name '*.egg-info' -prune -exec rm -rf {} +
	@find src scripts tests -type d -name __pycache__ -prune -exec rm -rf {} +
