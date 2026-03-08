# ============================================================
# Makefile — Notebook Market Analysis ETL Pipeline
# ============================================================
# Usage examples:
#   make extract           - Run the Scrapy spider
#   make transform         - Run the ETL pipeline
#   make dashboard         - Launch the Streamlit dashboard
#   make test              - Run unit tests
#   make lint              - Run ruff linter
#   make all               - Full pipeline (extract + transform)
# ============================================================

.PHONY: extract transform dashboard test lint all help

# ── Extract ──────────────────────────────────────────────────
extract:
	@echo ">>> Running Scrapy spider..."
	cd src/extraction/data_gathering && scrapy crawl notebook

# ── Transform & Load ─────────────────────────────────────────
transform:
	@echo ">>> Running ETL pipeline..."
	python -m src.transform.main

# ── Dashboard ─────────────────────────────────────────────────
dashboard:
	@echo ">>> Launching Streamlit dashboard..."
	streamlit run src/dashboard/app.py

# ── Full pipeline ─────────────────────────────────────────────
all: extract transform
	@echo ">>> Full pipeline complete."

# ── Tests ─────────────────────────────────────────────────────
test:
	@echo ">>> Running tests..."
	python -m pytest tests/ -v

# ── Lint ──────────────────────────────────────────────────────
lint:
	@echo ">>> Running ruff linter..."
	ruff check src/ tests/

# ── Help ──────────────────────────────────────────────────────
help:
	@echo ""
	@echo "Available targets:"
	@echo "  extract    - Run Scrapy spider (writes to data/raw/)"
	@echo "  transform  - Run ETL pipeline (reads raw/, writes to analytics/ and processed/)"
	@echo "  dashboard  - Launch Streamlit dashboard"
	@echo "  all        - Run extract + transform"
	@echo "  test       - Run unit tests with pytest"
	@echo "  lint       - Run ruff linter on src/ and tests/"
	@echo ""
