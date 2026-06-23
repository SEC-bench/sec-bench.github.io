# SEC-bench Website

This repository builds the static GitHub Pages website for SEC-bench Pro and the legacy SEC-bench leaderboard.

SEC-bench Pro is the default view. The Pro leaderboards and run-detail pages are rendered from the checked-in static snapshot at `data/results.json`, so GitHub Pages does not need access to the sibling `trajectories` repository.

## Quick Start

```bash
# Optional: create and use a virtual environment
make venv
source .venv/bin/activate

# Install Python build dependencies
make install

# Build the static site into dist/
make build

# Build and serve locally.
# The server starts at 8888, or the next available port if 8888 is busy.
make serve
```

`make build` reads `data/leaderboards.yaml` and `data/citations.yaml` through PyYAML, so install the Python dependencies before local builds. GitHub Actions installs `requirements.txt` before building.

## Data Model

### Pro Results

`data/results.json` is the canonical checked-in snapshot for SEC-bench Pro. It contains:

- Overall, V8, Firefox, and Linux leaderboard rows
- Per-run detail data for all generated run pages
- Token, runtime, timeout, result, and project contribution summaries

`make build` always runs `make_results.py` before `build.py`.

If `data/results.json` exists, `make_results.py` exits immediately and does not read trajectories:

```text
✓ Using existing data/results.json
```

If `data/results.json` is missing, regeneration is explicit and requires:

```bash
SEC_BENCH_TRAJECTORIES_DIR=/path/to/trajectories make build
```

After regenerating, review and commit the new `data/results.json`. Do not rely on GitHub Pages CI to access `trajectories`; it will only have files committed to this repository.

### Site Metadata And Legacy Results

`data/leaderboards.yaml` is still used for site metadata, shared descriptions, Pro footnotes, navigation resource links, legacy SEC-bench leaderboard content, and non-Pro navigation behavior.

`data/citations.yaml` stores citation text for both SEC-bench Pro and legacy SEC-bench.

## Project Structure

```text
sec-bench.github.io/
├── build.py                 # Static site renderer
├── make_results.py          # Optional results snapshot generator
├── Makefile                 # Build, serve, and cleanup commands
├── requirements.txt         # Python build dependencies
├── templates/               # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── run_detail.html
│   └── pages/
├── content/                 # Markdown fallback/page content
├── data/
│   ├── results.json         # Checked-in SEC-bench Pro results snapshot
│   ├── leaderboards.yaml    # Site metadata and legacy leaderboard data
│   └── citations.yaml       # Citation formats
├── css/                     # Stylesheets
├── js/                      # Client-side filters, tabs, theme switching
├── img/                     # Logos and static images
└── dist/                    # Generated site output
```

## Updating Pro Results

For a new benchmark snapshot:

```bash
rm data/results.json
SEC_BENCH_TRAJECTORIES_DIR=/absolute/path/to/trajectories make build
git diff -- data/results.json
```

Then commit the regenerated `data/results.json` together with any related source changes.

For small corrections to the published static snapshot, update `data/results.json` directly and avoid adding one-off patch scripts or build-time special cases.

## Local Development

- Edit templates under `templates/`.
- Edit styles under `css/`.
- Edit client behavior under `js/`.
- Run `make build` after changes.
- Run `make serve` to preview the generated `dist/` site locally.

`make serve` binds to `127.0.0.1` and automatically chooses the next available port starting from `8888`.

## GitHub Pages Deployment

The GitHub Actions workflows build the site with:

```bash
make build
```

The generated `dist/` directory is uploaded as the Pages artifact. `dist/` itself is build output and does not need to be committed.

Before pushing, make sure these files are committed when relevant:

- `data/results.json`
- `make_results.py`
- Any new assets under `img/`
- Template, CSS, JavaScript, and workflow changes

If `data/results.json` is not committed, GitHub Pages will not have the Pro snapshot and should not be expected to rebuild it from trajectories.

## Theme

The site supports dark and light themes. Dark mode is the default. Inter is the default font for page text, headers, tabs, and controls.
