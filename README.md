# SEC-bench Leaderboard

This is the leaderboard website for SEC-bench: Automated Benchmarking of LLM Agents on Real-World Software Security Tasks.

## Quick Start

```bash
# Create virtual environment
make venv
source .venv/bin/activate

# Install dependencies
make install

# Build the static site
make build

# Serve locally at http://localhost:8000
make serve
```

## Project Structure

```
sec-bench.github.io/
├── build.py              # Static site generator
├── Makefile              # Build commands
├── requirements.txt      # Python dependencies
├── templates/            # Jinja2 HTML templates
│   ├── base.html         # Base layout (sidebar, footer)
│   └── index.html        # Main leaderboard page
├── content/
│   └── about.md          # About/Citation content
├── data/
│   └── leaderboards.yaml # Leaderboard configuration & data
├── css/                  # Stylesheets
├── js/                   # JavaScript files
├── img/                  # Images and logos
├── chromium/             # Password-protected Chromium section
└── dist/                 # Built site output (generated)
```

## How to Update Content

### 1. Adding/Modifying Leaderboard Results

Edit `data/leaderboards.yaml` to add or modify leaderboard entries:

```yaml
leaderboards:
  - display_name: PoC Generation    # Tab name displayed in UI
    info_sections:                   # Info boxes shown below table
      - title: 'Section Title'
        content: |
          Description text here. Supports HTML.
    
    results:                         # Model results
      - model: Model Name            # Model name (required)
        org: Organization            # Organization name (required)
        resolved: 25.5               # % Resolved score (required)
        date: "2024-06-20"           # Date in YYYY-MM-DD format (required)
        open_source: true            # true for OSS badge, false otherwise
        verified: true               # true for verified checkmark badge
        newest: false                # true for NEW badge
        logs_link: "https://..."     # Link to logs (optional)
        footnote: "Note text"        # Footnote text (optional)
```

### 2. Adding a New Leaderboard Tab

Add a new entry under `leaderboards:` in `data/leaderboards.yaml`:

```yaml
leaderboards:
  - display_name: PoC Generation
    # ... existing config ...
    
  - display_name: New Benchmark     # This creates a new tab
    info_sections:
      - title: 'About This Benchmark'
        content: Description here.
    results:
      - model: First Model
        org: Org Name
        resolved: 50.0
        date: "2024-01-01"
        open_source: false
        verified: true
```

### 3. Modifying Website Title and Description

In `data/leaderboards.yaml`, update the top-level fields:

```yaml
# Main title in the header
website_title: SEC-bench

# Subtitle shown below title
website_subtitle: Automated Benchmarking of LLM Agents on Real-World Software Security Tasks

# Section header above tabs
section_title: Leaderboard

# Description text (supports HTML)
section_description: 'Performance of LLM agents on security tasks...'

# Footer links
footer_links:
  - name: GitHub
    url: https://github.com/SEC-bench/SEC-bench
  - name: Data
    url: https://huggingface.co/datasets/SEC-bench/SEC-bench
  - name: Paper
    url: https://arxiv.org/abs/2506.11791
```

### 4. Updating Citation Information

Edit `content/about.md`:

```markdown
# About

<!-- Paper URL: https://arxiv.org/abs/2506.11791 -->
<!-- Code URL: https://github.com/SEC-bench/SEC-bench -->
<!-- Data URL: https://huggingface.co/datasets/SEC-bench/SEC-bench -->

## Citation

### BibTeX

If you use SEC-bench in your research, please cite our paper:
```bibtex
@inproceedings{...}
```

### Acknowledgement

...
```

The `<!-- Paper URL: ... -->` and `<!-- Code URL: ... -->` comments are used to populate the sidebar links.

### 5. Adding Info Sections Below the Table

Each leaderboard can have multiple info sections displayed below the results table:

```yaml
info_sections:
  - title: '📣 News'
    content: |
      <ul>
        <li><b>Date:</b> News item here</li>
      </ul>
      
  - title: 'About This Benchmark'
    content: |
      Plain text or HTML content describing the benchmark.
      <br><br>
      Supports line breaks and HTML formatting.
```

## Deployment

After making changes:

1. Build the site: `make build`
2. Test locally: `make serve`
3. Deploy the `dist/` folder to your hosting service

For GitHub Pages, the `dist/` folder contents should be deployed to the `gh-pages` branch or configured as the source.

## Customization

### Changing Colors

Edit `css/core.css` to modify the color theme. The primary colors are:
- `--color-primary: #FF5F05` (SEC-bench orange)
- `--color-primary-hover: #E54D00`

### Changing Fonts

The site uses [Inter](https://fonts.google.com/specimen/Inter) font. To change it, edit the `@import` statement and `--font-family` variable in `css/core.css`.

### Modifying Sidebar Links

Edit `templates/base.html` to add/remove sidebar navigation items.

## Password-Protected Section

The `/chromium` directory contains a password-protected section that uses client-side encryption. Access it via the `/chromium` URI directly. The encrypted data files are stored in `data/chromium/`.

