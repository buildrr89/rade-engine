SHELL := /bin/sh

UV ?= uv
PYTHON ?= python3
OUTPUT_DIR ?= output
WEB_DIR ?= web
export UV_CACHE_DIR ?= .uv-cache
export UV_OFFLINE ?= 0
PY_SOURCES ?= src tests agent

.PHONY: bootstrap test lint format analyze api worker agent-scan web-install web-dev web-test clean

bootstrap:
	$(UV) sync --dev
	pnpm --dir $(WEB_DIR) install

test:
	./rade-proof

lint:
	$(UV) run ruff check $(PY_SOURCES)
	$(UV) run black --check $(PY_SOURCES)

format:
	$(UV) run ruff check --fix $(PY_SOURCES)
	$(UV) run black $(PY_SOURCES)

analyze:
	$(PYTHON) -m src.core.cli analyze \
		--input examples/sample_ios_output.json \
		--app-id com.example.legacyapp \
		--json-output $(OUTPUT_DIR)/modernization_report.json \
		--md-output $(OUTPUT_DIR)/modernization_report.md

api:
	./rade-devserver src.api.wsgi:application --host 127.0.0.1 --port 8000

worker:
	$(PYTHON) -m src.worker.main

agent-scan:
	$(PYTHON) -m agent.cli scan

web-install:
	pnpm --dir $(WEB_DIR) install

web-dev:
	node $(WEB_DIR)/scripts/dev.mjs

web-test:
	pnpm --dir $(WEB_DIR) test

clean:
	rm -rf $(OUTPUT_DIR)/*.json $(OUTPUT_DIR)/*.md .uv-cache .ruff_cache
