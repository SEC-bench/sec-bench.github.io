.PHONY: install build serve clean help venv

# Default target
help:
	@echo "SEC-bench Leaderboard - Build Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make venv       - Create virtual environment"
	@echo "  make install    - Install dependencies in venv"
	@echo "  make build      - Build static site"
	@echo "  make serve      - Build and serve site locally"
	@echo "  make clean      - Remove build artifacts"
	@echo ""
	@echo "If data/results.json is missing, set SEC_BENCH_TRAJECTORIES_DIR=/path/to/trajectories before make build."
	@echo ""

# Create virtual environment
venv:
	@echo "Creating virtual environment..."
	python3 -m venv .venv
	@echo "Virtual environment created. Run: source .venv/bin/activate"

# Install dependencies
install:
	@echo "Installing dependencies..."
	@if [ -f .venv/bin/pip ]; then \
		.venv/bin/pip install -r requirements.txt; \
	else \
		pip install -r requirements.txt; \
	fi

# Build static site
build:
	@echo "Building site..."
	@set -e; \
	if [ -f .venv/bin/python ]; then \
		PY=.venv/bin/python; \
	else \
		PY=python3; \
	fi; \
	$$PY make_results.py; \
	$$PY build.py

# Build and serve locally
serve: build
	@echo ""
	@PORT=8888; \
	while ! python3 -c "import socket, sys; s = socket.socket(); s.bind(('127.0.0.1', int(sys.argv[1]))); s.close()" $$PORT >/dev/null 2>&1; do \
		PORT=$$((PORT + 1)); \
	done; \
	echo "Starting local server at http://localhost:$$PORT"; \
	echo "Press Ctrl+C to stop"; \
	echo ""; \
	cd dist && python3 -m http.server $$PORT --bind 127.0.0.1

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf dist/
	rm -rf *.pyc __pycache__
	rm -rf .venv/
	@echo "Done!"
