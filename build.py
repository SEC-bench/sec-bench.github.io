#!/usr/bin/env python3
"""
Static site generator for the SEC-bench leaderboard site
Converts YAML data to static HTML using Jinja2 templates
"""

import json
import html
import re
import shutil
from datetime import datetime
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader
except ModuleNotFoundError:
    Environment = None
    FileSystemLoader = None

try:
    import yaml
except ModuleNotFoundError:
    yaml = None

try:
    import markdown
except ModuleNotFoundError:
    markdown = None

# ==============================================================================
# Citation Formats
# ==============================================================================

CITATION_FORMATS = (
    ("bibtex", "BibTeX"),
    ("apa", "APA"),
    ("mla", "MLA"),
)

RESOURCE_LINK_KEYS = ("paper_url", "code_url", "data_url", "submit_url")
RESOURCE_LINK_MODES = ("pro", "classic")


def normalize_resource_links(site_config: dict) -> dict:
    """Return per-mode navigation resource links from leaderboards.yaml."""
    configured = site_config.get("resource_links") or {}
    links = {}
    for mode in RESOURCE_LINK_MODES:
        values = configured.get(mode) or {}
        links[mode] = {key: values.get(key) for key in RESOURCE_LINK_KEYS}
    return links


def default_markdown_content(resource_links: dict) -> dict:
    """Resource links and small content fallbacks when Markdown is unavailable."""
    return {
        "about": (
            "<p>SEC-bench Pro expands the SEC-bench benchmark family toward harder, "
            "project-specific security evaluations across Chromium V8, Firefox SpiderMonkey, and Linux.</p>"
        ),
        "resource_links": resource_links,
        "paper_url": resource_links["classic"]["paper_url"],
        "code_url": resource_links["classic"]["code_url"],
        "data_url": resource_links["classic"]["data_url"],
    }


def load_citations_data(citations_file: Path) -> list:
    """Load citation tabs and normalize citation formats for template rendering."""
    if yaml is None:
        raise SystemExit("PyYAML is required to read data/citations.yaml. Run `make install`.")

    if not citations_file.exists():
        print(f"⚠ Warning: citations file not found: {citations_file}")
        return []

    with open(citations_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    citations = []
    for entry in data.get("citation_tabs", []):
        citation_id = entry.get("id")
        raw_formats = entry.get("citations") or {}
        formats = [
            {"id": format_id, "label": label, "text": raw_formats[format_id].strip()}
            for format_id, label in CITATION_FORMATS
            if raw_formats.get(format_id)
        ]

        if not citation_id or not formats:
            print(f"⚠ Warning: Skipping malformed citation entry: {entry}")
            continue

        citations.append(
            {
                "id": citation_id,
                "label": entry.get("label") or citation_id,
                "heading": entry.get("heading") or entry.get("label") or citation_id,
                "description": entry.get("description", ""),
                "formats": formats,
            }
        )

    return citations

# ==============================================================================
# Organization Logo Mapping
# ==============================================================================
# Maps organization names to their logo image URLs.
# Add new organizations here as they submit to the leaderboard.
# ==============================================================================
ORG_LOGOS = {
    # Agent/Tool Organizations
    "All Hands": "https://avatars.githubusercontent.com/u/169105795?s=200&v=4",  # OpenHands
    "OpenHands": "https://avatars.githubusercontent.com/u/169105795?s=200&v=4",
    "SWE-agent": "https://avatars.githubusercontent.com/u/166046056?s=200&v=4",
    "Princeton": "https://avatars.githubusercontent.com/u/166046056?s=200&v=4",  # SWE-agent is from Princeton
    "University of Melbourne": "/img/unimelb-logo.svg",
    "Aider": "https://avatars.githubusercontent.com/u/172139148?s=48&v=4",
    "Agentless": "https://avatars.githubusercontent.com/u/104632009?s=200&v=4",  # UIUC
    "UIUC": "https://avatars.githubusercontent.com/u/104632009?s=200&v=4",
    # AI Model Providers
    "Anthropic": "https://avatars.githubusercontent.com/u/76263028?s=200&v=4",
    "OpenAI": "https://avatars.githubusercontent.com/u/14957082?s=200&v=4",
    "Google": "https://avatars.githubusercontent.com/u/1342004?s=200&v=4",
    "Gemini": "https://avatars.githubusercontent.com/u/1342004?s=200&v=4",
    "Moonshot": "https://avatars.githubusercontent.com/u/129152888?s=200&v=4",
    "Kimi": "https://avatars.githubusercontent.com/u/129152888?s=200&v=4",
    "Moonshot AI": "https://statics.moonshot.cn/moonshot-ai/assets/static/kimi-icon.ByIGCGon.webp",
    "MiniMax": "/img/minimax-color.svg",
    "Z.ai": "https://upload.wikimedia.org/wikipedia/commons/f/f4/Z.ai_%28company_logo%29.svg",
    "Zhipu": "https://upload.wikimedia.org/wikipedia/commons/f/f4/Z.ai_%28company_logo%29.svg",
    "NVIDIA": "https://avatars.githubusercontent.com/u/1728152?s=200&v=4",
    # Cloud/Enterprise
    "Amazon": "https://avatars.githubusercontent.com/u/2232217?s=200&v=4",
    "AWS": "https://avatars.githubusercontent.com/u/2232217?s=200&v=4",
    "Microsoft": "https://avatars.githubusercontent.com/u/6154722?s=200&v=4",
    "Meta": "https://avatars.githubusercontent.com/u/69631?s=200&v=4",
    "Alibaba": "https://avatars.githubusercontent.com/u/1961952?s=200&v=4",
    "Bytedance": "https://avatars.githubusercontent.com/u/20225159?s=200&v=4",
    # Research Labs
    "NUS": "https://avatars.githubusercontent.com/u/28691550?s=200&v=4",  # AutoCodeRover
    "Stanford": "https://avatars.githubusercontent.com/u/6937093?s=200&v=4",
    # Other Organizations
    "Factory": "https://avatars.githubusercontent.com/u/121155557?s=200&v=4",
    "AppMap": "https://avatars.githubusercontent.com/u/48058882?s=200&v=4",
    "Moatless": "https://avatars.githubusercontent.com/u/172453067?s=200&v=4",
    "CodeStory": "https://avatars.githubusercontent.com/u/132aboratory?s=200&v=4",
    "AbanteAI": "https://avatars.githubusercontent.com/u/128949612?s=200&v=4",
}

# Default logo for unknown organizations
DEFAULT_ORG_LOGO = "https://avatars.githubusercontent.com/u/0?s=200&v=4"


RESULTS_DATA_FILE = "results.json"


def org_logo_filter(org_name: str) -> str:
    """Convert organization name to logo URL"""
    return ORG_LOGOS.get(org_name, DEFAULT_ORG_LOGO)


def auto_name_from_display(display_name: str) -> str:
    """Convert a display name to the generated leaderboard identifier."""
    auto_name = display_name.lower().replace(" ", "_").replace("-", "_")
    return "".join(c if c.isalnum() or c == "_" else "" for c in auto_name)


def format_number_filter(value) -> str:
    """Format numeric values for display."""
    if value is None or value == "":
        return "N/A"

    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)

    if number.is_integer():
        return f"{int(number):,}"
    return f"{number:,.1f}"


def format_currency_filter(value) -> str:
    """Format a number as USD."""
    if value is None or value == "":
        return "N/A"

    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)

    if number >= 1000:
        return f"${number:,.0f}"
    return f"${number:,.2f}"


def token_count_value(value):
    """Parse compact token labels such as 2.6B, 10.4M, or 276K into counts."""
    if value in (None, ""):
        return None

    raw = str(value).strip().replace(",", "")
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)([bBkKmM]?)", raw)
    if not match:
        return None

    number = float(match.group(1))
    suffix = match.group(2).upper()
    if suffix == "B":
        number *= 1_000_000_000
    elif suffix == "M":
        number *= 1_000_000
    elif suffix == "K":
        number *= 1_000
    return number


def format_token_count(value) -> str:
    """Format token counts with K/M/B suffixes, up to one decimal place."""
    if value in (None, ""):
        return ""

    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""

    suffix = ""
    if not suffix:
        if number >= 1_000_000_000:
            number /= 1_000_000_000
            suffix = "B"
        elif number >= 1_000_000:
            number /= 1_000_000
            suffix = "M"
        elif number >= 1_000:
            number /= 1_000
            suffix = "K"

    compact = f"{number:,.1f}".rstrip("0").rstrip(".")
    return f"{compact}{suffix}"


def format_token_label(value) -> str:
    """Normalize compact token labels to one decimal with K/M/B suffixes."""
    count = token_count_value(value)
    if count is None:
        return "" if value in (None, "") else str(value).replace("k", "K")
    return format_token_count(count)


def token_pair_label(instance: dict) -> str:
    """Render input/output token usage for a detail-table row."""
    token_input = format_token_label(instance.get("tokens_input"))
    token_output = format_token_label(instance.get("tokens_output"))
    if token_input and token_output:
        return f"{token_input}/{token_output}"
    if token_input:
        return token_input
    if token_output:
        return token_output
    return ""


def display_result_label(instance: dict) -> str:
    """Normalize visible result labels without changing scoring fields."""
    if instance.get("result") in ("Timed out", "TIMEOUT"):
        return "TIMEOUT"
    return instance.get("result", "")


def display_result_class(instance: dict) -> str:
    label = display_result_label(instance)
    return str(label).lower().replace(" ", "-")


def token_pair_from_counts(input_count, output_count) -> str:
    token_input = format_token_count(input_count)
    token_output = format_token_count(output_count)
    if token_input and token_output:
        return f"{token_input}/{token_output}"
    return token_input or token_output


def format_runtime_minutes(value) -> str:
    if value in (None, ""):
        return "N/A"
    try:
        minutes = float(value)
    except (TypeError, ValueError):
        return str(value)
    if minutes < 60:
        return f"{minutes:.1f}".rstrip("0").rstrip(".") + "m"
    hours = minutes / 60
    return f"{hours:.1f}".rstrip("0").rstrip(".") + "h"


def format_percent_filter(value) -> str:
    """Format a percent with one decimal place unless it is whole."""
    if value is None or value == "":
        return "N/A"

    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)

    return f"{number:.0f}%" if number.is_integer() else f"{number:.1f}%"


def load_yaml_data(yaml_file: Path) -> dict:
    """Load leaderboard data from YAML file and auto-generate names"""
    if yaml is None:
        raise SystemExit("PyYAML is required to read data/leaderboards.yaml. Run `make install`.")

    with open(yaml_file, "r") as f:
        data = yaml.safe_load(f)

    # Auto-generate 'name' from 'display_name' if not provided
    leaderboard_groups = [data.get("leaderboards", [])]
    if isinstance(data.get("legacy"), dict):
        leaderboard_groups.append(data["legacy"].get("leaderboards", []))

    for leaderboard in [item for group in leaderboard_groups for item in group]:
        if "name" not in leaderboard and "display_name" in leaderboard:
            leaderboard["name"] = auto_name_from_display(leaderboard["display_name"])

    return data


def normalize_run_detail_summary_metrics(run_details: dict):
    """Ensure detail summaries have token and average labels for rendering."""
    for detail in run_details.values():
        instances = detail.get("instances", [])
        summary = detail.setdefault("summary", {})
        total = int_value(summary.get("instances"), len(instances)) or len(instances)

        total_tokens_input = sum(
            instance.get("tokens_input_count")
            if instance.get("tokens_input_count") is not None
            else (token_count_value(instance.get("tokens_input")) or 0)
            for instance in instances
        )
        total_tokens_output = sum(
            instance.get("tokens_output_count")
            if instance.get("tokens_output_count") is not None
            else (token_count_value(instance.get("tokens_output")) or 0)
            for instance in instances
        )
        total_tokens = sum(
            instance.get("tokens_total_count")
            if instance.get("tokens_total_count") is not None
            else (token_count_value(instance.get("tokens_total")) or 0)
            for instance in instances
        )
        if not total_tokens and (total_tokens_input or total_tokens_output):
            total_tokens = total_tokens_input + total_tokens_output

        total_runtime = summary.get("total_runtime_min")
        if total_runtime in (None, ""):
            total_runtime = sum(instance.get("runtime_min") or 0 for instance in instances)
        total_runtime = float_value(total_runtime, 0) or 0

        total_tools = summary.get("total_tool_calls")
        if total_tools in (None, ""):
            total_tools = sum(instance.get("tool_calls") or 0 for instance in instances)
        total_tools = float_value(total_tools, 0) or 0

        summary["total_tokens"] = total_tokens
        summary["total_tokens_input"] = total_tokens_input
        summary["total_tokens_output"] = total_tokens_output
        summary["total_tokens_label"] = token_pair_from_counts(
            total_tokens_input, total_tokens_output
        )
        summary["average_tokens"] = round(total_tokens / total, 1) if total else 0
        summary["average_tokens_input"] = (
            round(total_tokens_input / total, 1) if total else 0
        )
        summary["average_tokens_output"] = (
            round(total_tokens_output / total, 1) if total else 0
        )
        summary["average_tokens_label"] = token_pair_from_counts(
            total_tokens_input / total if total else 0,
            total_tokens_output / total if total else 0,
        )
        summary["average_tool_calls"] = round(total_tools / total, 1) if total else 0
        summary["average_runtime_min"] = round(total_runtime / total, 1) if total else 0
        summary["total_runtime_min"] = round(total_runtime, 1)
        summary["total_runtime_label"] = format_runtime_minutes(total_runtime)
        summary["average_runtime_label"] = format_runtime_minutes(
            total_runtime / total if total else 0
        )


def percent(solved: int, total: int) -> float:
    """Return a one-decimal percentage for scoreboard display."""
    if not total:
        return 0.0
    return round(solved / total * 100, 1)


def int_value(value, default: int = 0) -> int:
    """Best-effort integer parsing for CSV fields."""
    if value in (None, ""):
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def float_value(value, default=None):
    """Best-effort float parsing for CSV fields."""
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_results_data(data_dir: Path) -> dict | None:
    """Load a trajectory-derived generated snapshot for CI builds without siblings."""
    path = data_dir / RESULTS_DATA_FILE
    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"⚠ Warning: Could not parse {path}: {exc}")
        return None

    details = {}
    for key, detail in data.get("run_details", {}).items():
        if "/" not in key:
            continue
        target, slug = key.split("/", 1)
        details[(target, slug)] = detail

    return {
        "leaderboards": data.get("leaderboards", []),
        "target_tabs": data.get("target_tabs", []),
        "run_details": details,
    }


def normalize_footnotes(value) -> list[str]:
    """Normalize YAML footnote lists while tolerating strings and {text: ...} items."""
    if not value:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []

    footnotes = []
    for item in value:
        text = item.get("text") if isinstance(item, dict) else item
        if text in (None, ""):
            continue
        footnotes.append(str(text))
    return footnotes


def merge_footnotes(*groups) -> list[str]:
    """Merge footnote groups, preserving order and removing duplicates."""
    merged = []
    seen = set()
    for group in groups:
        for footnote in normalize_footnotes(group):
            if footnote in seen:
                continue
            seen.add(footnote)
            merged.append(footnote)
    return merged


def merge_generated_target_tabs(configured_tabs: list, generated_tabs: list) -> list:
    """Overlay YAML-owned tab metadata onto generated target tabs."""
    configured_by_name = {
        tab.get("name"): tab for tab in configured_tabs if tab.get("name")
    }
    metadata_keys = ("display_name", "logo", "leaderboard", "status", "description")
    merged = []

    for tab in generated_tabs:
        name = tab.get("name")
        configured = configured_by_name.get(name, {})
        item = dict(tab)
        for key in metadata_keys:
            if key in configured:
                item[key] = configured[key]
        if "instances" not in item and "instances" in configured:
            item["instances"] = configured["instances"]
        merged.append(item)

    return merged


def apply_results_data(
    leaderboards_data: dict,
    run_details: dict,
    generated: dict,
):
    """Merge results.json data into the rendered Pro site data."""
    configured_leaderboards = {
        leaderboard.get("name"): leaderboard
        for leaderboard in leaderboards_data.get("leaderboards", [])
        if leaderboard.get("name")
    }
    common_footnotes = leaderboards_data.get("pro_common_footnotes", [])
    metadata_keys = ("display_name", "description", "is_overall")

    for leaderboard in generated["leaderboards"]:
        configured = configured_leaderboards.get(leaderboard.get("name"), {})
        for key in metadata_keys:
            if key in configured:
                leaderboard[key] = configured[key]

        if configured.get("info_sections"):
            leaderboard["info_sections"] = configured["info_sections"]
        elif not leaderboard.get("info_sections"):
            leaderboard["info_sections"] = leaderboards_data.get(
                "pro_common_info_sections", []
            )
        footnotes = merge_footnotes(
            common_footnotes,
            configured.get("footnotes", []),
            leaderboard.get("footnotes", []),
        )
        if footnotes:
            leaderboard["footnotes"] = footnotes

    leaderboards_data["leaderboards"] = generated["leaderboards"]
    leaderboards_data["target_tabs"] = merge_generated_target_tabs(
        leaderboards_data.get("target_tabs", []),
        generated["target_tabs"],
    )
    normalize_run_detail_summary_metrics(generated["run_details"])
    run_details.update(generated["run_details"])


def normalize_legacy_leaderboards(site_config: dict) -> dict:
    """Normalize classic SEC-bench rows for the shared leaderboard template."""
    if not isinstance(site_config, dict):
        return {}

    for leaderboard in site_config.get("leaderboards", []):
        results = [
            result
            for result in leaderboard.get("results", [])
            if result.get("resolved") is not None
        ]
        ranked = sorted(
            results,
            key=lambda result: float(result.get("resolved") or 0),
            reverse=True,
        )
        rank_by_id = {id(result): index + 1 for index, result in enumerate(ranked)}

        for result in leaderboard.get("results", []):
            result["rank"] = rank_by_id.get(id(result))
            result["score_label"] = "SEC-bench score"
            result.setdefault("open_source", False)
            result.setdefault("verified", False)
            result.setdefault("date", "")

    return site_config


def leaderboard_mode_stats(site_config: dict, mode: str) -> list[dict]:
    """Build compact hero stats for one leaderboard mode."""
    leaderboards = site_config.get("leaderboards", [])
    total_entries = sum(len(board.get("results", [])) for board in leaderboards)

    if mode == "pro":
        tabs = [
            target
            for target in available_target_tabs(site_config)
            if target.get("name") != "overall"
        ]
        return [
            {
                "value": leaderboards[0].get("instances", 0) if leaderboards else 0,
                "label": "instances",
            },
            {
                "value": len(leaderboards[0].get("results", [])) if leaderboards else 0,
                "label": "runs",
            },
            {"value": len(tabs), "label": "projects"},
            {"value": 2, "label": "score views"},
        ]

    return [
        {"value": len(leaderboards), "label": "tasks"},
        {"value": total_entries, "label": "entries"},
        {"value": "PoC", "label": "generation"},
        {"value": "Patch", "label": "repair"},
    ]


def available_target_tabs(site_config: dict) -> list:
    """Return Pro target tabs that have published leaderboard pages."""
    return [
        target
        for target in site_config.get("target_tabs", [])
        if target.get("status") == "available" and target.get("leaderboard")
    ]


def target_for_leaderboard(site_config: dict) -> dict:
    """Map leaderboard names to their Pro target tab config."""
    mapping = {}
    for target in available_target_tabs(site_config):
        mapping[target.get("leaderboard") or target.get("name")] = target
    return mapping


def attach_run_detail_urls(site_config: dict, run_details: dict):
    """Annotate leaderboard rows with clean detail URLs when detail data exists."""
    target_by_leaderboard = target_for_leaderboard(site_config)

    for leaderboard in site_config.get("leaderboards", []):
        target = target_by_leaderboard.get(leaderboard.get("name"))
        if not target:
            continue

        scored_results = [
            result
            for result in leaderboard.get("results", [])
            if result.get("resolved") is not None
        ]
        ranked_results = sorted(
            scored_results,
            key=lambda result: float(result.get("resolved") or 0),
            reverse=True,
        )
        rank_by_id = {
            id(result): index + 1 for index, result in enumerate(ranked_results)
        }

        for result in leaderboard.get("results", []):
            result["rank"] = rank_by_id.get(id(result))
            details = (
                result.get("details")
                if isinstance(result.get("details"), dict)
                else None
            )
            if not details:
                continue

            slug = details.get("slug")
            detail = run_details.get((target["name"], slug))
            if not slug or not detail:
                print(f"⚠ Warning: Missing run detail data for {target['name']}/{slug}")
                continue

            result["details_available"] = True
            result["details_url"] = f"/{target['name']}/runs/{slug}"
            result["details_summary"] = detail.get("summary", {})


def load_markdown_content(content_dir: Path, resource_links: dict) -> dict:
    """Load about.md and split by H2 sections; extract sidebar resource URLs."""
    import re

    if markdown is None:
        print("⚠ Markdown package not available; using content fallback")
        return default_markdown_content(resource_links)

    md = markdown.Markdown(extensions=["fenced_code", "tables", "nl2br"])
    content = {}

    about_file = content_dir / "about.md"

    if about_file.exists():
        with open(about_file, "r", encoding="utf-8") as f:
            md_text = f.read()

        content["resource_links"] = resource_links
        classic_urls = content["resource_links"]["classic"]
        content["paper_url"] = classic_urls["paper_url"]
        content["code_url"] = classic_urls["code_url"]
        content["data_url"] = classic_urls["data_url"]

        # Split by H2 headers (## Title)
        # Pattern: ## Section Title
        sections = re.split(r"\n## ", md_text)

        # First section is the main About content (before first ##)
        if sections:
            main_content = sections[0].replace("# About\n\n", "")
            # Remove resource URL HTML comments from rendered About intro
            main_content = re.sub(
                r"<!--\s*(?:Pro|Classic|Paper|Code|Data|Submit)\s+URL:\s*.*?-->\s*\n?",
                "",
                main_content,
                flags=re.IGNORECASE | re.DOTALL,
            )
            if main_content.strip():
                content["about"] = md.convert(main_content)
                md.reset()

        # Process each H2 section
        for section in sections[1:]:
            # Extract section title (first line)
            lines = section.split("\n", 1)
            if len(lines) >= 1:
                title = lines[0].strip().lower()  # e.g., "Code" -> "code"
                section_content = lines[1] if len(lines) > 1 else ""

                # Add the H2 header back for proper rendering
                full_section = f"## {lines[0]}\n{section_content}"
                content[title] = md.convert(full_section)
                md.reset()
    else:
        print(f"⚠ Warning: about.md not found")
        content["about"] = ""
        content["data"] = ""
        content["code"] = ""
        content["citation"] = ""
        content["resource_links"] = resource_links
        content["paper_url"] = resource_links["classic"]["paper_url"]
        content["code_url"] = resource_links["classic"]["code_url"]
        content["data_url"] = resource_links["classic"]["data_url"]

    return content


def copy_static_files(src_dir: Path, dest_dir: Path):
    """Copy static files (CSS, JS, images) to dist directory"""
    static_dirs = ["css", "js", "img"]

    for dirname in static_dirs:
        src = src_dir / dirname
        dest = dest_dir / dirname

        if src.exists():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
            print(f"✓ Copied {dirname}/")


def copy_chromium_files(src_dir: Path, dest_dir: Path):
    """Copy chromium directory to dist"""
    chromium_src = src_dir / "chromium"
    chromium_dest = dest_dir / "chromium"

    if chromium_src.exists():
        if chromium_dest.exists():
            shutil.rmtree(chromium_dest)
        shutil.copytree(chromium_src, chromium_dest)
        print(f"✓ Copied chromium/")

    # Also copy the encrypted data files
    data_src = src_dir / "data"
    data_dest = dest_dir / "data"

    if data_src.exists():
        if data_dest.exists():
            shutil.rmtree(data_dest)
        shutil.copytree(data_src, data_dest)
        print(f"✓ Copied data/")


def esc(value) -> str:
    """HTML-escape a value for stdlib rendering."""
    return html.escape("" if value is None else str(value), quote=True)


def highlight_bibtex_value(value: str) -> str:
    parts = []
    index = 0
    while index < len(value):
        char = value[index]
        if char in "{}":
            parts.append(f'<span class="bib-punct">{esc(char)}</span>')
            index += 1
        elif char == "\\":
            match = re.match(r"\\[A-Za-z]+", value[index:])
            if match:
                command = match.group(0)
                parts.append(f'<span class="bib-command">{esc(command)}</span>')
                index += len(command)
            else:
                parts.append(f'<span class="bib-value">{esc(char)}</span>')
                index += 1
        else:
            start = index
            while index < len(value) and value[index] not in "{}\\":
                index += 1
            parts.append(f'<span class="bib-value">{esc(value[start:index])}</span>')
    return "".join(parts)


def highlight_bibtex(value) -> str:
    lines = str(value or "").splitlines()
    highlighted = []
    entry_re = re.compile(r"^(@[A-Za-z]+)(\{)([^,]+)(,?)$")
    field_re = re.compile(r"^(\s*)([A-Za-z][A-Za-z0-9_:-]*)(\s*=\s*)(.*?)(,?)$")

    for line in lines:
        entry_match = entry_re.match(line)
        if entry_match:
            entry_type, open_brace, key, comma = entry_match.groups()
            comma_html = f'<span class="bib-punct">{esc(comma)}</span>' if comma else ""
            highlighted.append(
                f'<span class="bib-type">{esc(entry_type)}</span>'
                f'<span class="bib-punct">{esc(open_brace)}</span>'
                f'<span class="bib-key">{esc(key)}</span>'
                f"{comma_html}"
            )
            continue

        field_match = field_re.match(line)
        if field_match:
            indent, field, operator, field_value, comma = field_match.groups()
            comma_html = f'<span class="bib-punct">{esc(comma)}</span>' if comma else ""
            highlighted.append(
                esc(indent)
                + f'<span class="bib-field">{esc(field)}</span>'
                + f'<span class="bib-op">{esc(operator)}</span>'
                + highlight_bibtex_value(field_value)
                + comma_html
            )
            continue

        highlighted.append(
            "".join(
                f'<span class="bib-punct">{esc(char)}</span>' if char in "{}," else esc(char)
                for char in line
            )
        )

    return "\n".join(highlighted)


def highlight_citation_text(value, format_id: str) -> str:
    if format_id == "bibtex":
        return highlight_bibtex(value)
    return esc(value)


def json_script(data) -> str:
    """Serialize JSON safely inside a script tag."""
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def is_external_url(url: str) -> bool:
    return str(url or "").startswith(("http://", "https://", "//", "mailto:"))


def nav_resource_link(url: str, label: str) -> str:
    if url:
        return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>'
    return f'<span class="nav-pending" title="Coming soon">{esc(label)}</span>'


def nav_mode_resource_link(pro_url: str, classic_url: str, label: str) -> str:
    href = pro_url or classic_url
    if not href:
        return f'<span class="nav-pending" title="Coming soon">{esc(label)}</span>'

    target_attrs = ' target="_blank" rel="noopener noreferrer"' if is_external_url(href) else ""
    return (
        f'<a href="{esc(href)}" data-mode-nav-link '
        f'data-pro-href="{esc(pro_url or "")}" '
        f'data-classic-href="{esc(classic_url or "")}"{target_attrs}>{esc(label)}</a>'
    )


def render_base_html_stdlib(
    page_title: str,
    body_html: str,
    markdown_content: dict,
    footer_links: list,
    current_year: int,
    asset_prefix: str = "",
    site_root: str = "/",
    scripts_extra: str = "",
    website_subtitle: str | None = None,
) -> str:
    """Render the shared shell without Jinja."""
    resource_links = markdown_content.get("resource_links") or {}
    pro_links = resource_links.get("pro") or {}
    classic_links = resource_links.get("classic") or {}
    footer = ""
    if footer_links:
        footer_items = "".join(
            f'<a href="{esc(link.get("url"))}" target="_blank" rel="noopener noreferrer">{esc(link.get("name"))}</a>'
            for link in footer_links
        )
        footer = f'<div class="footer-links">{footer_items}</div>'

    return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="theme-color" content="#121312">
    <title>{esc(page_title)}</title>
    <meta name="description" content="{esc(website_subtitle or page_title)}">
    <link rel="icon" type="image/png" href="{asset_prefix}img/secbench.png">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{asset_prefix}css/core.css?v=6">
    <link rel="stylesheet" href="{asset_prefix}css/layout.css?v=15">
    <link rel="stylesheet" href="{asset_prefix}css/components.css?v=17">
    <link rel="stylesheet" href="{asset_prefix}css/filters.css?v=3">
    <link rel="stylesheet" href="{asset_prefix}css/sidebar.css?v=5">
</head>
<body data-leaderboard-mode="pro">
    <header class="topnav">
        <div class="topnav-inner">
            <a class="brand" href="{site_root}" aria-label="{esc(page_title)}">
                <span>SEC-bench</span>
            </a>
            <button type="button" class="pro-mode-toggle active" id="pro-toggle" aria-label="SEC-bench Pro mode" aria-pressed="true" data-state="on" title="PRO mode on">PRO</button>
            <nav class="nav-links" aria-label="Primary navigation">
                {nav_mode_resource_link(pro_links.get("paper_url"), classic_links.get("paper_url"), "Paper")}
                {nav_mode_resource_link(pro_links.get("code_url"), classic_links.get("code_url"), "Code")}
                {nav_mode_resource_link(pro_links.get("data_url"), classic_links.get("data_url"), "Data")}
                <a href="{site_root}citations.html">Cite</a>
                {nav_mode_resource_link(f"{site_root}submit.html", f"{site_root}submit.html?mode=classic", "Submit")}
            </nav>
            <button type="button" class="theme-toggle" id="dark-mode-toggle" data-theme-toggle data-theme-state="dark" aria-label="Switch to light mode" aria-pressed="true" title="Switch to light mode">
                <svg class="theme-icon theme-icon-moon" viewBox="0 0 384 512" aria-hidden="true" focusable="false">
                    <path d="M223.5 32C100 32 0 132.3 0 256s100.3 224 224 224c62.7 0 119.3-25.8 160-67.3 5-5.1 6.3-12.8 3.1-19.2s-10.5-9.7-17.8-8.5c-8.2 1.4-16.5 2.1-25 2.1-82.8 0-150-67.2-150-150 0-69.4 47.1-127.8 111.1-145 7.4-2 12.9-8.2 13.6-15.8s-3.7-14.8-10.5-18.4C284.9 43.6 255.5 32 223.5 32z"></path>
                </svg>
                <svg class="theme-icon theme-icon-sun" viewBox="0 0 512 512" aria-hidden="true" focusable="false">
                    <path d="M256 118a138 138 0 1 0 0 276 138 138 0 1 0 0-276zM256 0c-13.3 0-24 10.7-24 24v48c0 13.3 10.7 24 24 24s24-10.7 24-24V24c0-13.3-10.7-24-24-24zm0 416c-13.3 0-24 10.7-24 24v48c0 13.3 10.7 24 24 24s24-10.7 24-24v-48c0-13.3-10.7-24-24-24zM488 232h-48c-13.3 0-24 10.7-24 24s10.7 24 24 24h48c13.3 0 24-10.7 24-24s-10.7-24-24-24zM96 256c0-13.3-10.7-24-24-24H24c-13.3 0-24 10.7-24 24s10.7 24 24 24h48c13.3 0 24-10.7 24-24zM411.7 100.3c-9.4-9.4-24.6-9.4-33.9 0l-33.9 33.9c-9.4 9.4-9.4 24.6 0 33.9s24.6 9.4 33.9 0l33.9-33.9c9.4-9.4 9.4-24.6 0-33.9zM168.1 343.9c-9.4-9.4-24.6-9.4-33.9 0l-33.9 33.9c-9.4 9.4-9.4 24.6 0 33.9s24.6 9.4 33.9 0l33.9-33.9c9.4-9.4 9.4-24.6 0-33.9zM411.7 411.7c9.4-9.4 9.4-24.6 0-33.9l-33.9-33.9c-9.4-9.4-24.6-9.4-33.9 0s-9.4 24.6 0 33.9l33.9 33.9c9.4 9.4 24.6 9.4 33.9 0zM168.1 168.1c9.4-9.4 9.4-24.6 0-33.9l-33.9-33.9c-9.4-9.4-24.6-9.4-33.9 0s-9.4 24.6 0 33.9l33.9 33.9c9.4 9.4 24.6 9.4 33.9 0z"></path>
                </svg>
            </button>
        </div>
    </header>
    <main class="main-content">{body_html}</main>
    <footer class="footer">
        <div class="footer-content">
            <p>&copy; {current_year} {esc(page_title)}</p>
            {footer}
        </div>
    </footer>
    <script src="{asset_prefix}js/dark-mode.js?v=4"></script>
    <script src="{asset_prefix}js/multiselect-dropdown.js?v=2"></script>
    <script src="{asset_prefix}js/leaderboard.js?v=4"></script>
    <script src="{asset_prefix}js/filters.js?v=3"></script>
    <script src="{asset_prefix}js/footnotes.js?v=2"></script>
    <script src="{asset_prefix}js/sidebar.js?v=5"></script>
    {scripts_extra}
</body>
</html>"""


def render_stats_stdlib(stats: list[dict]) -> str:
    items = "".join(
        f'<div class="stat"><div class="stat-num">{esc(stat.get("value"))}</div><div class="stat-label">{esc(stat.get("label"))}</div></div>'
        for stat in stats
    )
    return f'<div class="stats-strip" aria-label="Benchmark summary">{items}</div>'


def render_score_bar_stdlib(result: dict, leaderboard: dict, supports_score_modes: bool) -> str:
    if not supports_score_modes:
        score = float_value(result.get("resolved"), 0) or 0
        return (
            '<div class="score-cell">'
            f'<div class="score-number">{format_percent_filter(score)}</div>'
            f'<div class="score-count">{esc(result.get("score_label") or "SEC-bench score")}</div>'
            '<div class="score-bar-track">'
            f'<span class="score-bar-fill" style="width: {max(0, min(100, score))}%"></span>'
            '</div></div>'
        )

    headline = result["score_modes"]["headline"]
    parts = [
        '<div class="score-cell">',
        f'<div class="score-number" data-score-value>{esc(headline["score"])}%</div>',
        f'<div class="score-count" data-count-value>{esc(headline["solved"])}/{esc(headline["total"])}</div>',
    ]
    if leaderboard.get("is_overall") and result.get("projects"):
        parts.append('<div class="split-score-bar" aria-label="Project contribution split">')
        for part in result["projects"]:
            h = part["score_modes"]["headline"]
            c = part["score_modes"]["completed"]
            parts.append(
                f'<span class="score-segment score-segment-{esc(part["name"])}" '
                f'style="width: {esc(h["width"])}%" '
                f'data-headline-width="{esc(h["width"])}" '
                f'data-completed-width="{esc(c["width"])}" '
                f'data-headline-title="{esc(part["label"] + ": " + h["score_label"])}" '
                f'data-completed-title="{esc(part["label"] + ": " + c["score_label"])}" '
                f'title="{esc(part["label"] + ": " + h["score_label"])}"></span>'
            )
        parts.append("</div><div class=\"split-legend\">")
        for part in result["projects"]:
            parts.append(
                f'<span><i class="legend-dot score-segment-{esc(part["name"])}"></i>{esc(part["label"])}</span>'
            )
        parts.append("</div>")
    else:
        parts.append(
            '<div class="score-bar-track">'
            f'<span class="score-bar-fill" style="width: {esc(headline["score"])}%"></span>'
            "</div>"
        )
    parts.append("</div>")
    return "".join(parts)


def render_info_panels_stdlib(leaderboards: list[dict], active_leaderboard: str) -> str:
    panels = []
    for leaderboard in leaderboards:
        sections = leaderboard.get("info_sections") or []
        if not sections:
            continue
        style = "" if leaderboard.get("name") == active_leaderboard else ' style="display: none;"'
        articles = "".join(
            f'<article class="leaderboard-info"><h3>{esc(info.get("title"))}</h3><div class="leaderboard-info-content">{info.get("content", "")}</div></article>'
            for info in sections
        )
        panels.append(
            f'<div class="leaderboard-info-grid" data-info-panel="{esc(leaderboard.get("name"))}"{style}>{articles}</div>'
        )
    return f'<div class="leaderboard-info-panels">{"".join(panels)}</div>'


def render_leaderboard_panel_stdlib(
    mode: str,
    leaderboards: list[dict],
    target_tabs: list[dict],
    default_leaderboard: str | None,
    panel_title: str,
    panel_subtitle: str,
    panel_section_title: str,
    panel_section_description: str,
    stats: list[dict],
    supports_score_modes: bool,
) -> str:
    active = default_leaderboard or (leaderboards[0]["name"] if leaderboards else "")
    tab_buttons = []
    active_description = ""
    for target in target_tabs:
        tab_name = target.get("leaderboard") or target.get("name")
        if tab_name == active:
            active_description = target.get("description", "")
        active_class = " active" if tab_name == active else ""
        url_attr = ""
        if mode == "pro":
            url = "/" if target.get("name") == "overall" else f'/{target.get("name")}'
            url_attr = f' data-target-url="{esc(url)}"'
        logo = ""
        if target.get("logo"):
            logo = f'<img class="target-tab-logo" src="{esc(target["logo"])}" alt="" aria-hidden="true">'
        tab_buttons.append(
            f'<button class="tab-button target-tab-button{active_class}" data-tab="{esc(tab_name)}" '
            f'data-target-description="{esc(target.get("description", ""))}"{url_attr} role="tab">'
            f'{logo}<span>{esc(target.get("display_name"))}</span></button>'
        )

    score_tabs = ""
    if supports_score_modes:
        score_tabs = """
        <div class="score-mode-tabs" aria-label="Score basis">
            <button type="button" class="score-mode-tab active" data-score-mode="headline" aria-pressed="true"><span>Headline</span><small>fixed budget</small></button>
            <button type="button" class="score-mode-tab" data-score-mode="completed" aria-pressed="false"><span>Completed</span><small>within timeout</small></button>
        </div>"""

    panels = []
    for leaderboard in leaderboards:
        lb_name = leaderboard.get("name")
        style = "" if lb_name == active else ' style="display: none;"'
        has_open = any(result.get("open_source") for result in leaderboard.get("results", []))
        has_prop = any(not result.get("open_source") for result in leaderboard.get("results", []))
        filters = ""
        if has_open and has_prop:
            filters = f"""
            <div class="filter-controls">
                <div class="filter-group">
                    <label class="filter-label">Model Type</label>
                    <div class="filter-buttons" id="{esc(lb_name)}-type-filter">
                        <button class="filter-btn active" data-filter="all">All</button>
                        <button class="filter-btn" data-filter="proprietary">Proprietary</button>
                        <button class="filter-btn" data-filter="open-source">Open model</button>
                    </div>
                </div>
            </div>"""

        extra_headers = '<th class="completed-col sortable" data-sort="completed">Completed</th>' if supports_score_modes else ""
        logs_header = "" if supports_score_modes else '<th class="logs-col">Artifacts</th>'
        rows = []
        for result in leaderboard.get("results", []):
            details_url = result.get("details_url")
            clickable = " leaderboard-row-clickable" if details_url else ""
            if supports_score_modes:
                model_label = result.get("model", "")
                if result.get("effort"):
                    model_label += f' ({result.get("effort")})'
                model_data = f'{model_label} {result.get("agent", "")}'
            else:
                model_label = result.get("model", "")
                model_data = model_label
            score_value = result["score_modes"]["headline"]["score"] if supports_score_modes else result.get("resolved", 0)
            row_attrs = [
                f'class="leaderboard-row{clickable}"',
                'data-scored="true"',
                f'data-type="{"open-source" if result.get("open_source") else "proprietary"}"',
                f'data-model="{esc(model_data)}"',
                f'data-resolved="{esc(score_value)}"',
                f'data-rank="{esc(result.get("rank", ""))}"',
                f'data-org="{esc(result.get("org", ""))}"',
                f'data-date="{esc(result.get("date", ""))}"',
            ]
            if supports_score_modes:
                row_attrs.append(f'data-completed="{esc(result.get("completed_instances", ""))}"')
                for mode_name in ("headline", "completed"):
                    mode_data = result["score_modes"][mode_name]
                    row_attrs.extend(
                        [
                            f'data-{mode_name}-score="{esc(mode_data["score"])}"',
                            f'data-{mode_name}-rank="{esc(mode_data["rank"])}"',
                            f'data-{mode_name}-score-label="{esc(mode_data["score_label"])}"',
                            f'data-{mode_name}-count="{esc(mode_data["solved"])}/{esc(mode_data["total"])}"',
                            f'data-{mode_name}-completed="{esc(result.get("completed_instances", ""))}/{esc(result["score_modes"]["headline"]["total"])}"',
                        ]
                    )
            if details_url:
                row_attrs.append(f'data-details-url="{esc(details_url)}" tabindex="0" role="link" aria-label="View run details for {esc(model_label)}"')

            if supports_score_modes:
                name_html = (
                    f'<a class="model-name-text model-detail-link" href="{esc(details_url)}">{esc(model_label)}</a>'
                    if details_url
                    else f'<span class="model-name-text">{esc(model_label)}</span>'
                )
                name_html += f'<span class="model-meta">{esc(result.get("agent", ""))}</span>'
            else:
                name_html = f'<span class="model-name-text">{esc(result.get("model"))}</span>'

            badges = ""
            if result.get("open_source"):
                badges += '<span class="badge badge-oss" title="Open model">Open</span>'
            if not supports_score_modes and result.get("verified"):
                badges += '<span class="badge badge-verified" title="Verified">Verified</span>'

            completed_cell = ""
            if supports_score_modes:
                completed_cell = (
                    '<td class="completed-col" data-label="Completed">'
                    f'<strong data-completed-value>{esc(result.get("completed_instances"))}/{esc(result["score_modes"]["headline"]["total"])}</strong>'
                    f'<span>{esc(result.get("timeouts", 0))} timed out</span></td>'
                )

            logs_cell = ""
            if not supports_score_modes:
                if result.get("logs_link"):
                    logs = f'<a class="logs-link" href="{esc(result["logs_link"])}" target="_blank" rel="noopener noreferrer">Logs</a>'
                else:
                    logs = '<span class="table-muted">N/A</span>'
                logs_cell = f'<td class="logs-col" data-label="Artifacts">{logs}</td>'

            rows.append(
                f'<tr {" ".join(row_attrs)}>'
                f'<td class="rank-col" data-label="#"><span class="rank-badge" data-rank-value>{esc(result.get("rank", ""))}</span></td>'
                f'<td class="model-col" data-label="{"Model" if supports_score_modes else "System"}">'
                '<div class="model-name">'
                f'<img class="org-logo" src="{esc(org_logo_filter(result.get("org", "")))}" alt="{esc(result.get("org", ""))}" title="{esc(result.get("org", ""))}">'
                f'<div class="model-name-stack">{name_html}</div>{badges}</div></td>'
                f'<td class="resolved-col" data-label="{"Success" if supports_score_modes else "Score"}">{render_score_bar_stdlib(result, leaderboard, supports_score_modes)}</td>'
                f'{completed_cell}<td class="org-col" data-label="Provider"><span>{esc(result.get("org"))}</span></td>'
                f'<td class="date-col" data-label="Date">{esc(result.get("date"))}</td>{logs_cell}</tr>'
            )

        static_notes = ""
        footnotes = normalize_footnotes(leaderboard.get("footnotes", []))
        if footnotes:
            static_notes = (
                '<div class="leaderboard-static-notes">'
                + "".join(
                    f'<p class="leaderboard-static-note"><span aria-hidden="true">*</span> {esc(footnote)}</p>'
                    for footnote in footnotes
                )
                + "</div>"
            )

        table = f"""
        {filters}
        <div class="table-container">
            <table class="leaderboard-table" id="{esc(lb_name)}-table">
                <thead>
                    <tr>
                        <th class="rank-col sortable active asc" data-sort="rank">#</th>
                        <th class="model-col sortable" data-sort="model">{"Model" if supports_score_modes else "System"}</th>
                        <th class="resolved-col sortable active desc" data-sort="resolved">{"Success" if supports_score_modes else "Score"}</th>
                        {extra_headers}
                        <th class="org-col sortable" data-sort="org">Provider</th>
                        <th class="date-col sortable" data-sort="date">Date</th>
                        {logs_header}
                    </tr>
                </thead>
                <tbody>{''.join(rows)}</tbody>
            </table>
        </div>
        <div class="no-results" style="display: none;"><p>No models match the selected filters.</p></div>
        {static_notes}
        <div class="leaderboard-footnotes" id="{esc(lb_name)}-footnotes"></div>"""
        panels.append(
            f'<div class="leaderboard-content" id="{esc(lb_name)}-content" data-leaderboard-panel="{esc(lb_name)}"{style}>{table}</div>'
        )

    return f"""
<section class="hero">
    <div class="container wide">
        <h1 class="title">{esc(panel_title)}</h1>
        <p class="lede">{esc(panel_subtitle)}</p>
    </div>
</section>
<section class="leaderboard-section">
    <div class="container wide">
        <div class="section-head">
            <h2 class="section-title">{esc(panel_section_title)}</h2>
        </div>
        <p class="section-note">{panel_section_description}</p>
        <div class="leaderboard-shell">
            <div class="leaderboard-toolbar">
                <div class="target-tabs" role="tablist" aria-label="{esc(panel_title)} leaderboards">{''.join(tab_buttons)}</div>
                {score_tabs}
            </div>
            <p class="target-description" data-target-description-container>{active_description}</p>
            <div class="leaderboard-container">{''.join(panels)}</div>
        </div>
        {render_info_panels_stdlib(leaderboards, active)}
    </div>
</section>"""


def render_index_body_stdlib(
    leaderboards_data: dict,
    legacy_config: dict,
    section_title: str,
    section_description: str,
    initial_leaderboard: str | None,
    pro_stats: list[dict],
    legacy_stats: list[dict],
    all_leaderboards: list[dict],
) -> str:
    legacy_leaderboards = legacy_config.get("leaderboards", [])

    pro_default = initial_leaderboard or leaderboards_data["leaderboards"][0]["name"]
    pro_panel = render_leaderboard_panel_stdlib(
        "pro",
        leaderboards_data["leaderboards"],
        leaderboards_data["target_tabs"],
        pro_default,
        leaderboards_data.get("website_title", "SEC-bench Pro"),
        leaderboards_data.get("website_subtitle", ""),
        section_title,
        section_description,
        pro_stats,
        True,
    )
    classic_panel = ""
    if legacy_leaderboards:
        classic_panel = (
            '<div class="mode-panel" data-mode-panel="classic" '
            f'data-default-leaderboard="{esc(legacy_leaderboards[0]["name"])}" hidden>'
            + render_leaderboard_panel_stdlib(
                "classic",
                legacy_leaderboards,
                legacy_config.get("target_tabs", []),
                legacy_leaderboards[0]["name"],
                legacy_config.get("website_title", "SEC-bench"),
                legacy_config.get("website_subtitle", ""),
                legacy_config.get("section_title", "Leaderboard"),
                legacy_config.get("section_description", ""),
                legacy_stats,
                False,
            )
            + "</div>"
        )

    return (
        '<div class="mode-panels">'
        + f'<div class="mode-panel mode-panel-active" data-mode-panel="pro" data-default-leaderboard="{esc(pro_default)}">{pro_panel}</div>'
        + classic_panel
        + "</div>"
        + f'<script type="application/json" id="leaderboard-data">{json_script(all_leaderboards)}</script>'
    )


def instance_link(detail: dict, instance: dict) -> str:
    instance_id = esc(instance.get("id"))
    if detail.get("target") == "v8":
        return f'<a href="https://issues.chromium.org/issues/{instance_id}" target="_blank" rel="noopener noreferrer">{instance_id}</a>'
    if detail.get("target") == "firefox":
        return f'<a href="https://bugzilla.mozilla.org/show_bug.cgi?id={instance_id}" target="_blank" rel="noopener noreferrer">{instance_id}</a>'
    if detail.get("target") == "linux":
        return f'<a href="https://nvd.nist.gov/vuln/detail/{instance_id}" target="_blank" rel="noopener noreferrer">{instance_id}</a>'
    return f"<span>{instance_id}</span>"


def render_run_detail_body_stdlib(detail: dict, target: dict, result: dict) -> str:
    summary = detail["summary"]
    headline = summary["score_modes"]["headline"]
    completed = summary["score_modes"]["completed"]
    show_bounty = detail.get("target") == "v8"
    rows = []
    for index, instance in enumerate(detail.get("instances", []), 1):
        solved_class = " instance-row-solved" if instance.get("success") else ""
        result_label = display_result_label(instance)
        result_class = esc(display_result_class(instance))
        description = instance.get("result_description", "")
        result_title = (
            f' title="{esc(description)}" aria-label="{esc(result_label)}: {esc(description)}"'
            if description
            else ""
        )
        expected = (
            f'<code>{esc(instance.get("expected_type"))}</code>'
            if instance.get("expected_type")
            else '<span class="table-muted">Unknown</span>'
        )
        vuln_type = (
            f'<span>{esc(instance.get("vulnerability_type"))}</span>'
            if instance.get("vulnerability_type")
            else '<span class="table-muted">Unknown</span>'
        )
        runtime = esc(instance.get("runtime_label")) if instance.get("runtime_label") else '<span class="table-muted">N/A</span>'
        tools = format_number_filter(instance.get("tool_calls")) if instance.get("tool_calls") else '<span class="table-muted">N/A</span>'
        token_pair = token_pair_label(instance)
        tokens = (
            f'<span title="Total: {esc(format_token_label(instance.get("tokens_total")))}">{esc(token_pair)}</span>'
            if token_pair
            else '<span class="table-muted">N/A</span>'
        )
        bounty_cell = ""
        if show_bounty:
            bounty = (
                format_currency_filter(instance.get("bounty"))
                if instance.get("bounty") is not None
                else '<span class="table-muted">N/A</span>'
            )
            bounty_cell = f'<td class="run-num-cell run-bounty-cell">{bounty}</td>'
        rows.append(
            f'<tr class="run-instance-row{solved_class}" data-completed="{str(bool(instance.get("completed"))).lower()}" '
            f'data-timedout="{str(bool(instance.get("timed_out"))).lower()}" data-solved="{str(bool(instance.get("success"))).lower()}">'
            f'<td class="run-index">{index}</td>'
            f'<td class="instance-cell">{instance_link(detail, instance)}</td>'
            f'{bounty_cell}'
            f'<td class="run-result-cell"><span class="result-pill result-pill-{result_class}"{result_title}>{esc(result_label)}</span></td>'
            f'<td class="run-type-cell run-error-cell">{expected}</td>'
            f'<td class="run-type-cell run-bug-cell">{vuln_type}</td>'
            f'<td class="run-num-cell run-poc-cell"><strong>{format_number_filter(instance.get("verified_pocs"))}</strong><span>/ {format_number_filter(instance.get("poc_total"))}</span></td>'
            f'<td class="run-num-cell">{runtime}</td>'
            f'<td class="run-num-cell run-token-cell">{tokens}</td>'
            f'<td class="run-num-cell">{tools}</td></tr>'
        )

    bounty_header = "<th>Bounty</th>" if show_bounty else ""
    total_runtime_label = summary.get("total_runtime_label") or "N/A"
    total_tokens_label = summary.get("total_tokens_label") or "N/A"
    average_tokens_label = summary.get("average_tokens_label") or "N/A"
    average_runtime_label = summary.get("average_runtime_label") or "N/A"

    return f"""
<div class="run-detail-page">
    <section class="run-page-top"><a class="run-back-link" href="/{esc(target.get("name"))}">Back to {esc(target.get("display_name"))}</a></section>
    <header class="run-hero">
        <div class="run-hero-main">
            <img class="run-org-logo" src="{esc(org_logo_filter(detail.get("org")))}" alt="{esc(detail.get("org"))}">
            <div class="run-hero-copy">
                <p class="section-no">{esc(detail.get("target_display_name"))} / run detail</p>
                <h1 class="run-hero-title">{esc(detail.get("agent"))} · {esc(detail.get("model"))}</h1>
                <p class="run-hero-meta">{esc(detail.get("org"))}{' · ' + esc(detail.get("effort")) if detail.get("effort") else ''}{' · Rank #' + esc(result.get("rank")) if result.get("rank") else ''}</p>
                <p class="run-hero-submeta">{esc(detail.get("date"))} · {esc(detail.get("source_run"))}</p>
            </div>
        </div>
        <div class="score-mode-tabs run-score-tabs" aria-label="Score basis">
            <button type="button" class="score-mode-tab active" data-run-score-mode="headline" aria-pressed="true"><span>Headline</span><small>all instances</small></button>
            <button type="button" class="score-mode-tab" data-run-score-mode="completed" aria-pressed="false"><span>Completed</span><small>exclude timeout markers</small></button>
        </div>
        <section class="run-metrics" aria-label="Run summary">
            <article class="run-metric"><strong data-run-mode-value data-headline="{esc(headline["score"])}%" data-completed="{esc(completed["score"])}%">{esc(headline["score"])}%</strong><span>Success</span></article>
            <article class="run-metric"><strong data-run-mode-value data-headline="{esc(headline["solved"])} / {esc(headline["total"])}" data-completed="{esc(completed["solved"])} / {esc(completed["total"])}">{esc(headline["solved"])} / {esc(headline["total"])}</strong><span>Solved Instances</span></article>
            <article class="run-metric"><strong>{esc(total_runtime_label)}</strong><span>Total Runtime</span></article>
            <article class="run-metric"><strong>{esc(total_tokens_label)}</strong><span>Total Tokens (IN/OUT)</span></article>
        </section>
        <div class="run-secondary-stats" aria-label="Additional run summary">
            <span><strong>{format_number_filter(summary.get("average_tool_calls"))}</strong> Avg. tool calls</span>
            <span><strong>{esc(average_tokens_label)}</strong> Avg. tokens</span>
            <span><strong>{esc(average_runtime_label)}</strong> Avg. runtime</span>
        </div>
    </header>
    <section class="run-detail-section">
        <div class="run-section-header">
            <div><h2>Per-Instance Results</h2><p>Timeout uses the per-instance marker under the trajectory artifact. Completed-only scoring excludes rows with that marker.</p></div>
            <div class="instance-filter-tabs" aria-label="Instance filter">
                <button type="button" class="filter-btn active" data-instance-filter="all">All</button>
                <button type="button" class="filter-btn" data-instance-filter="completed">Completed</button>
                <button type="button" class="filter-btn" data-instance-filter="timedout">Timed out</button>
                <button type="button" class="filter-btn" data-instance-filter="solved">Solved</button>
            </div>
        </div>
        <div class="table-container run-table-container">
            <table class="run-results-table" id="run-results-table">
                <thead><tr><th>#</th><th>Instance</th>{bounty_header}<th>Result</th><th>Error Type</th><th>Bug Type</th><th>PoCs</th><th>Runtime</th><th>Tokens</th><th>Tools</th></tr></thead>
                <tbody>{''.join(rows)}</tbody>
            </table>
        </div>
    </section>
</div>
<script>
(function () {{
    function setMode(mode) {{
        document.querySelectorAll('[data-run-score-mode]').forEach((button) => {{
            const active = button.dataset.runScoreMode === mode;
            button.classList.toggle('active', active);
            button.setAttribute('aria-pressed', String(active));
        }});
        document.querySelectorAll('[data-run-mode-value]').forEach((node) => {{
            node.textContent = node.dataset[mode] || '';
        }});
    }}
    function applyInstanceFilter(filter) {{
        document.querySelectorAll('[data-instance-filter]').forEach((button) => {{
            button.classList.toggle('active', button.dataset.instanceFilter === filter);
        }});
        document.querySelectorAll('.run-instance-row').forEach((row) => {{
            const show = filter === 'all' ||
                (filter === 'completed' && row.dataset.completed === 'true') ||
                (filter === 'timedout' && row.dataset.timedout === 'true') ||
                (filter === 'solved' && row.dataset.solved === 'true');
            row.classList.toggle('hidden', !show);
        }});
    }}
    document.addEventListener('DOMContentLoaded', () => {{
        document.querySelectorAll('[data-run-score-mode]').forEach((button) => {{
            button.addEventListener('click', () => setMode(button.dataset.runScoreMode));
        }});
        document.querySelectorAll('[data-instance-filter]').forEach((button) => {{
            button.addEventListener('click', () => applyInstanceFilter(button.dataset.instanceFilter));
        }});
    }});
}})();
</script>"""


def render_contact_body_stdlib() -> str:
    return """
<div class="content-wrapper">
    <header class="section-head"><h1 class="section-title">Contact Us</h1></header>
    <section class="content-section">
        <div class="leaderboard-shell">
            <p>For general inquiries about SEC-bench (Pro), please email:</p>
            <p><a href="mailto:hwiwonl2@illinois.edu">hwiwonl2@illinois.edu</a></p>
        </div>
    </section>
</div>"""


def render_submit_body_stdlib() -> str:
    return """
<div class="content-wrapper submit-page mode-panels">
    <div class="mode-panel mode-panel-active" data-mode-panel="pro">
        <header class="section-head">
            <h1 class="section-title">Submit to SEC-bench Pro</h1>
            <p class="section-note">Submission workflow for the SEC-bench Pro leaderboard.</p>
        </header>
        <section class="content-section">
            <div class="leaderboard-shell submit-content">
                <div class="submit-callout">
                    <strong>Submission path is lightweight for now.</strong>
                    Send us the checker summary, harness config, and artifact bundle for your <code>source_files</code> run.
                </div>
                <p>If you want your system added to the SEC-bench Pro leaderboard, please prepare the following:</p>
                <ol>
                    <li>Run the official SEC-bench Pro harness against the target project in <code>source_files</code> mode.</li>
                    <li>Keep the exact harness config you used, including the model identifier, reasoning settings, and timeout.</li>
                    <li>
                        Share the following artifacts with the SEC-bench team:
                        <ul>
                            <li><code>summary.csv</code> or equivalent checker summary covering the evaluated target instances</li>
                            <li><code>config.toml</code> for the exact run configuration</li>
                            <li><code>logs/</code> or an artifact directory with reproducible run outputs</li>
                            <li>Optional metadata such as project URL, organization icon, and whether the system is open-source</li>
                        </ul>
                    </li>
                    <li>Open an issue or send the bundle to <a href="mailto:hwiwonl2@illinois.edu">hwiwonl2@illinois.edu</a> so the official score import can be verified and published.</li>
                </ol>
                <h3>Contact</h3>
                <p>
                    For questions about submissions, evaluation, or the benchmark itself, please contact us at
                    <a href="mailto:hwiwonl2@illinois.edu">hwiwonl2@illinois.edu</a> or open an issue on GitHub.
                </p>
            </div>
        </section>
    </div>
    <div class="mode-panel" data-mode-panel="classic" hidden>
        <header class="section-head">
            <h1 class="section-title">Submit to SEC-bench</h1>
            <p class="section-note">Guidelines for contributing your model's results to the original SEC-bench leaderboard.</p>
        </header>
        <section class="content-section">
            <div class="leaderboard-shell submit-content">
                <p>If you are interested in submitting your model to the SEC-bench leaderboard, please do the following:</p>
                <ol>
                    <li>Fork the <a href="https://github.com/SEC-bench/experiments" target="_blank" rel="noopener noreferrer">SEC-bench/experiments</a> repository.</li>
                    <li>Clone the repository. Due to this repository's large diff history, consider using <code>git clone --depth 1</code> if cloning takes too long.</li>
                    <li>Under the task that you evaluate on, such as <code>evaluation/Patch/</code>, create a new folder with the model name, such as <code>swea_o3-mini</code>.</li>
                    <li>
                        Within the folder, include the following files:
                        <ul>
                            <li><code>report.jsonl</code>: a report file that summarizes the evaluation results</li>
                            <li>
                                <code>metadata.yaml</code>: metadata for how the result is shown on the website, including:
                                <ul>
                                    <li><strong>name</strong>: the name of your leaderboard entry</li>
                                    <li><strong>orgIcon</strong> (optional): URL or link to an icon representing your organization</li>
                                    <li><strong>oss</strong>: <code>true</code> if your system is open-source</li>
                                    <li><strong>site</strong>: URL or link to more information about your system</li>
                                    <li><strong>verified</strong>: <code>false</code>; see results verification below</li>
                                    <li><strong>date</strong>: date of submission</li>
                                </ul>
                            </li>
                            <li><code>trajs/</code>: reasoning traces reflecting how your system solved the problems</li>
                            <li><code>logs/</code>: SEC-bench evaluation artifact dump</li>
                        </ul>
                    </li>
                    <li>Create a pull request to the <a href="https://github.com/SEC-bench/experiments" target="_blank" rel="noopener noreferrer">SEC-bench/experiments</a> repository with the new folder.</li>
                </ol>
                <h3>Results Verification</h3>
                <p>
                    Submissions marked with the <span class="badge badge-verified" title="Verified">Verified</span> badge have been verified by the SEC-bench team through artifact reproduction.
                    We run your agent in our controlled environment to confirm the reported results.
                </p>
                <h3>Contact</h3>
                <p>
                    For questions about submissions, evaluation, or the benchmark itself, please contact us at
                    <a href="mailto:hwiwonl2@illinois.edu">hwiwonl2@illinois.edu</a> or open an issue on GitHub.
                </p>
            </div>
        </section>
    </div>
</div>"""


def render_citations_body_stdlib(citations: list[dict]) -> tuple[str, str]:
    tabs = []
    panels = []
    for index, citation in enumerate(citations):
        active = index == 0
        tabs.append(
            f'<button class="citation-tab-btn {"active" if active else ""}" id="{esc(citation["id"])}-tab" '
            f'data-citation-tab="{esc(citation["id"])}" type="button" role="tab" aria-selected="{str(active).lower()}" '
            f'aria-controls="{esc(citation["id"])}-panel">{esc(citation["label"])}</button>'
        )
        format_buttons = []
        format_panels = []
        for format_index, fmt in enumerate(citation.get("formats", [])):
            fmt_active = format_index == 0
            format_buttons.append(
                f'<button class="citation-format-btn {"active" if fmt_active else ""}" data-format="{esc(fmt["id"])}" '
                f'data-target="{esc(citation["id"])}-citation" type="button">{esc(fmt["label"])}</button>'
            )
            highlighted = highlight_citation_text(fmt["text"], fmt["id"])
            copy_button = (
                '<button class="copy-btn" type="button" aria-label="Copy citation" title="Copy citation">'
                '<svg class="copy-icon copy-icon-copy" aria-hidden="true" viewBox="0 0 24 24">'
                '<rect x="9" y="9" width="10" height="10" rx="1.5"></rect>'
                '<path d="M5 15V6.5A1.5 1.5 0 0 1 6.5 5H15"></path>'
                '</svg>'
                '<svg class="copy-icon copy-icon-check" aria-hidden="true" viewBox="0 0 24 24">'
                '<path d="M5 12.5 10 17l9-10"></path>'
                '</svg>'
                '<span class="sr-only copy-status" aria-live="polite">Copy citation</span>'
                '</button>'
            )
            format_panels.append(
                f'<div class="citation-container citation-block {"display-none" if not fmt_active else ""}" '
                f'id="{esc(citation["id"])}-citation-{esc(fmt["id"])}" data-citation-target="{esc(citation["id"])}-citation" data-format="{esc(fmt["id"])}">'
                f'{copy_button}<div class="citation-scroll"><pre><code class="language-{esc(fmt["id"])}">{highlighted}</code></pre></div></div>'
            )
        panels.append(
            f'<section class="citation-section citation-tab-panel {"display-none" if not active else ""}" id="{esc(citation["id"])}-panel" '
            f'data-citation-panel="{esc(citation["id"])}" role="tabpanel" aria-labelledby="{esc(citation["id"])}-tab">'
            f'<div class="citation-section-head"><div><h2>{esc(citation["heading"])}</h2>'
            f'<p class="citation-section-description">{esc(citation.get("description"))}</p></div>'
            f'<div class="citation-type" data-citation-format-group="{esc(citation["id"])}">{"".join(format_buttons)}</div></div>'
            f'{"".join(format_panels)}</section>'
        )

    tabs_html = (
        f'<div class="citation-tabs" role="tablist" aria-label="Citation targets">{"".join(tabs)}</div>'
        if tabs
        else ""
    )
    panels_html = "".join(panels) or (
        '<section class="citation-section"><div class="citation-section-head"><div>'
        '<h2>Citations unavailable</h2>'
        '<p class="citation-section-description">No citation data is configured for this site build.</p>'
        "</div></div></section>"
    )

    body = f"""
<div class="content-wrapper citations-page">
    <header class="section-head citation-page-head">
        <h1 class="section-title">Citations</h1>
        <p class="section-note">Use the SEC-bench Pro citation for Pro results and the SEC-bench citation for legacy benchmark-family results.</p>
    </header>
    {tabs_html}
    {panels_html}
</div>"""
    return body, '<script src="js/citation.js?v=2"></script>'


def prepare_site_data(base_dir: Path):
    """Load and normalize all data shared by both renderers."""
    data_dir = base_dir / "data"
    content_dir = base_dir / "content"

    leaderboards_data = load_yaml_data(data_dir / "leaderboards.yaml")
    citations_data = load_citations_data(data_dir / "citations.yaml")
    resource_links = normalize_resource_links(leaderboards_data)
    markdown_content = load_markdown_content(content_dir, resource_links)
    run_details = {}
    generated = load_results_data(data_dir)
    if generated:
        apply_results_data(
            leaderboards_data,
            run_details,
            generated,
        )
    normalize_run_detail_summary_metrics(run_details)
    attach_run_detail_urls(leaderboards_data, run_details)
    legacy_config = normalize_legacy_leaderboards(
        leaderboards_data.get("legacy", {})
        if isinstance(leaderboards_data.get("legacy"), dict)
        else {}
    )
    pro_stats = leaderboard_mode_stats(leaderboards_data, "pro")
    legacy_stats = leaderboard_mode_stats(legacy_config, "classic")
    all_leaderboards = leaderboards_data["leaderboards"] + legacy_config.get(
        "leaderboards", []
    )

    return {
        "leaderboards_data": leaderboards_data,
        "citations_data": citations_data,
        "markdown_content": markdown_content,
        "run_details": run_details,
        "legacy_config": legacy_config,
        "pro_stats": pro_stats,
        "legacy_stats": legacy_stats,
        "all_leaderboards": all_leaderboards,
    }


def build_site_stdlib():
    """Template-free renderer used when Jinja2 or Markdown are absent."""
    print("Building SEC-bench Pro leaderboard site with stdlib renderer...")

    base_dir = Path(__file__).parent
    dist_dir = base_dir / "dist"

    print("\nLoading data...")
    data = prepare_site_data(base_dir)
    leaderboards_data = data["leaderboards_data"]
    citations_data = data["citations_data"]
    markdown_content = data["markdown_content"]
    run_details = data["run_details"]
    legacy_config = data["legacy_config"]
    pro_stats = data["pro_stats"]
    legacy_stats = data["legacy_stats"]
    all_leaderboards = data["all_leaderboards"]

    leaderboard_count = len(leaderboards_data["leaderboards"]) + len(
        legacy_config.get("leaderboards", [])
    )
    print(f"✓ Loaded {leaderboard_count} leaderboards")
    print(f"✓ Loaded {len(citations_data)} citation tabs")
    print(f"✓ Loaded {len(run_details)} run detail files")

    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir(exist_ok=True)

    print("\nCopying static files...")
    copy_static_files(base_dir, dist_dir)
    copy_chromium_files(base_dir, dist_dir)

    website_title = leaderboards_data.get("website_title", "SEC-bench Leaderboard")
    website_subtitle = leaderboards_data.get("website_subtitle", None)
    section_title = leaderboards_data.get("section_title", "Leaderboard")
    section_description = leaderboards_data.get(
        "section_description",
        "Performance of various LLM agents on SEC-bench security engineering tasks.",
    )
    footer_links = leaderboards_data.get("footer_links") or []
    current_year = datetime.now().year

    print("\nRendering pages...")

    def render_leaderboard_page(output_file: Path, initial_leaderboard: str | None, asset_prefix: str):
        body = render_index_body_stdlib(
            leaderboards_data,
            legacy_config,
            section_title,
            section_description,
            initial_leaderboard,
            pro_stats,
            legacy_stats,
            all_leaderboards,
        )
        html_text = render_base_html_stdlib(
            website_title,
            body,
            markdown_content,
            footer_links,
            current_year,
            asset_prefix=asset_prefix,
            website_subtitle=website_subtitle,
        )
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(html_text, encoding="utf-8")
        print(f"✓ Rendered {output_file.relative_to(dist_dir)}")

    default_leaderboard = (
        leaderboards_data["leaderboards"][0]["name"]
        if leaderboards_data["leaderboards"]
        else None
    )
    render_leaderboard_page(dist_dir / "index.html", default_leaderboard, "")

    for target in available_target_tabs(leaderboards_data):
        if target["name"] == "overall":
            continue
        render_leaderboard_page(
            dist_dir / target["name"] / "index.html",
            target.get("leaderboard") or target.get("name"),
            "../",
        )

    target_by_name = {
        target["name"]: target for target in available_target_tabs(leaderboards_data)
    }
    for leaderboard in leaderboards_data.get("leaderboards", []):
        target = target_by_name.get(leaderboard.get("name"))
        if not target:
            continue
        for result in leaderboard.get("results", []):
            details = result.get("details") if isinstance(result.get("details"), dict) else None
            if not details or not result.get("details_available"):
                continue
            slug = details.get("slug")
            detail = run_details.get((target["name"], slug))
            if not detail:
                continue
            body = render_run_detail_body_stdlib(detail, target, result)
            html_text = render_base_html_stdlib(
                f"{detail['model']} - {target['display_name']}",
                body,
                markdown_content,
                footer_links,
                current_year,
                asset_prefix="../../../",
                website_subtitle=website_subtitle,
            )
            output_file = dist_dir / target["name"] / "runs" / slug / "index.html"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(html_text, encoding="utf-8")
            print(f"✓ Rendered {output_file.relative_to(dist_dir)}")

    citation_body, citation_script = render_citations_body_stdlib(citations_data)
    pages = {
        "contact.html": ("Contact SEC-bench Pro", render_contact_body_stdlib(), ""),
        "submit.html": ("Submit to SEC-bench", render_submit_body_stdlib(), ""),
        "citations.html": ("SEC-bench Citations", citation_body, citation_script),
    }
    for page_name, (title, body, scripts_extra) in pages.items():
        html_text = render_base_html_stdlib(
            title,
            body,
            markdown_content,
            footer_links,
            current_year,
            scripts_extra=scripts_extra,
            website_subtitle=website_subtitle,
        )
        output_file = dist_dir / page_name
        output_file.write_text(html_text, encoding="utf-8")
        print(f"✓ Rendered {page_name}")

    print("\n✅ Build complete! Output in dist/")
    print(f"   Run: python3 -m http.server --directory dist/ 8000")


def build_site():
    """Main build function"""
    if yaml is None:
        raise SystemExit("PyYAML is required to read data/*.yaml. Run `make install`.")

    if Environment is None or FileSystemLoader is None or markdown is None:
        missing = []
        if Environment is None or FileSystemLoader is None:
            missing.append("Jinja2")
        if markdown is None:
            missing.append("Markdown")
        print(f"⚠ Missing optional build dependencies: {', '.join(missing)}")
        return build_site_stdlib()

    print("Building SEC-bench Pro leaderboard site...")

    # Setup paths
    base_dir = Path(__file__).parent
    templates_dir = base_dir / "templates"
    dist_dir = base_dir / "dist"

    # Load data
    print("\nLoading data...")
    data = prepare_site_data(base_dir)
    leaderboards_data = data["leaderboards_data"]
    citations_data = data["citations_data"]
    markdown_content = data["markdown_content"]
    run_details = data["run_details"]
    legacy_config = data["legacy_config"]
    pro_stats = data["pro_stats"]
    legacy_stats = data["legacy_stats"]
    all_leaderboards = data["all_leaderboards"]

    leaderboard_count = len(leaderboards_data["leaderboards"])
    leaderboard_count += len(legacy_config.get("leaderboards", []))

    print(f"✓ Loaded {leaderboard_count} leaderboards")
    print(f"✓ Loaded {len(citations_data)} citation tabs")
    print(f"✓ Loaded {len(markdown_content)} markdown content files")
    print(f"✓ Loaded {len(run_details)} run detail files")

    # Setup Jinja2 environment
    env = Environment(loader=FileSystemLoader(templates_dir))

    # Register custom filters
    env.filters["org_logo"] = org_logo_filter
    env.filters["format_number"] = format_number_filter
    env.filters["format_currency"] = format_currency_filter
    env.filters["format_percent"] = format_percent_filter
    env.filters["format_token_label"] = format_token_label
    env.filters["token_pair"] = token_pair_label
    env.filters["result_label"] = display_result_label
    env.filters["result_class"] = display_result_class
    env.filters["highlight_citation"] = highlight_citation_text

    # Create dist directory
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir(exist_ok=True)

    # Copy static files
    print("\nCopying static files...")
    copy_static_files(base_dir, dist_dir)
    copy_chromium_files(base_dir, dist_dir)

    # Render pages
    print("\nRendering pages...")

    # Optional extra links in the site footer (sidebar carries Paper/Code/Data).
    footer_links = leaderboards_data.get("footer_links") or []

    # Extract website title, subtitle, section title and description
    website_title = leaderboards_data.get("website_title", "SEC-bench Leaderboard")
    website_subtitle = leaderboards_data.get("website_subtitle", None)
    section_title = leaderboards_data.get("section_title", "Leaderboard")
    section_description = leaderboards_data.get(
        "section_description",
        "Performance of various LLM agents on SEC-bench security engineering tasks.",
    )

    # Common template context
    common_context = {
        "content": markdown_content,
        "footer_links": footer_links,
        "website_title": website_title,
        "website_subtitle": website_subtitle,
        "leaderboard_items": leaderboards_data["leaderboards"],
        "site_config": leaderboards_data,
        "legacy_config": legacy_config,
        "all_leaderboards": all_leaderboards,
        "pro_stats": pro_stats,
        "legacy_stats": legacy_stats,
        "citations": citations_data,
        "current_year": datetime.now().year,
        "asset_prefix": "",
        "site_root": "/",
    }

    # Render leaderboard pages
    template = env.get_template("index.html")

    def render_leaderboard_page(
        output_file: Path, initial_leaderboard: str | None, asset_prefix: str
    ):
        html = template.render(
            leaderboards=leaderboards_data["leaderboards"],
            legacy_leaderboards=legacy_config.get("leaderboards", []),
            section_title=section_title,
            section_description=section_description,
            initial_leaderboard=initial_leaderboard,
            asset_prefix=asset_prefix,
            **{k: v for k, v in common_context.items() if k != "asset_prefix"},
        )
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(html)
        print(f"✓ Rendered {output_file.relative_to(dist_dir)}")

    default_leaderboard = (
        leaderboards_data["leaderboards"][0]["name"]
        if leaderboards_data["leaderboards"]
        else None
    )
    render_leaderboard_page(dist_dir / "index.html", default_leaderboard, "")

    for target in available_target_tabs(leaderboards_data):
        if target["name"] == "overall":
            continue
        render_leaderboard_page(
            dist_dir / target["name"] / "index.html",
            target.get("leaderboard") or target.get("name"),
            "../",
        )

    # Render run detail pages
    detail_template = env.get_template("run_detail.html")
    target_by_name = {
        target["name"]: target for target in available_target_tabs(leaderboards_data)
    }
    for leaderboard in leaderboards_data.get("leaderboards", []):
        target = target_by_name.get(leaderboard.get("name"))
        if not target:
            continue

        for result in leaderboard.get("results", []):
            details = (
                result.get("details")
                if isinstance(result.get("details"), dict)
                else None
            )
            if not details or not result.get("details_available"):
                continue

            slug = details.get("slug")
            detail = run_details.get((target["name"], slug))
            if not detail:
                continue

            html = detail_template.render(
                detail=detail,
                target=target,
                result=result,
                page_title=f"{detail['model']} - {target['display_name']}",
                asset_prefix="../../../",
                **{k: v for k, v in common_context.items() if k != "asset_prefix"},
            )
            output_file = dist_dir / target["name"] / "runs" / slug / "index.html"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(html)
            print(f"✓ Rendered {output_file.relative_to(dist_dir)}")

    # Render additional pages
    additional_pages = ["citations.html", "contact.html", "submit.html"]
    for page_name in additional_pages:
        try:
            template = env.get_template(f"pages/{page_name}")
            html = template.render(**common_context)
            output_file = dist_dir / page_name
            output_file.write_text(html)
            print(f"✓ Rendered {page_name}")
        except Exception as e:
            print(f"⚠ Warning: Could not render {page_name}: {e}")

    print("\n✅ Build complete! Output in dist/")
    print(f"   Run: python3 -m http.server --directory dist/ 8000")


if __name__ == "__main__":
    build_site()
