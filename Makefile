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
	@if [ -f .venv/bin/python ]; then \
		.venv/bin/python build.py; \
	else \
		python3 build.py; \
	fi

# Build and serve locally
serve: build
	@echo ""
	@echo "Starting local server at http://localhost:8787"
	@echo "Press Ctrl+C to stop"
	@echo ""
	cd dist && python3 -m http.server 8787

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf dist/
	rm -rf *.pyc __pycache__
	rm -rf .venv/
	@echo "Done!"

