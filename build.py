#!/usr/bin/env python3
"""
Static site generator for the SEC-bench leaderboard site
Converts YAML data to static HTML using Jinja2 templates
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import yaml
import markdown


# ==============================================================================
# Organization Logo Mapping
# ==============================================================================
# Maps organization names to their logo image URLs.
# Add new organizations here as they submit to the leaderboard.
# ==============================================================================
ORG_LOGOS = {
    # Agent/Tool Organizations
    'All Hands': 'https://avatars.githubusercontent.com/u/169105795?s=200&v=4',  # OpenHands
    'OpenHands': 'https://avatars.githubusercontent.com/u/169105795?s=200&v=4',
    'SWE-agent': 'https://avatars.githubusercontent.com/u/166046056?s=200&v=4',
    'Princeton': 'https://avatars.githubusercontent.com/u/166046056?s=200&v=4',  # SWE-agent is from Princeton
    'University of Melbourne': 'https://raw.githubusercontent.com/MichaelFu1998-create/MichaelFu1998-create.github.io/main/img/unimelb_logo.png',  # AgentMem
    'Aider': 'https://avatars.githubusercontent.com/u/172139148?s=48&v=4',
    'Agentless': 'https://avatars.githubusercontent.com/u/104632009?s=200&v=4',  # UIUC
    'UIUC': 'https://avatars.githubusercontent.com/u/104632009?s=200&v=4',
    
    # AI Model Providers
    'Anthropic': 'https://avatars.githubusercontent.com/u/76263028?s=200&v=4',
    'OpenAI': 'https://avatars.githubusercontent.com/u/14957082?s=200&v=4',
    'Google': 'https://avatars.githubusercontent.com/u/1342004?s=200&v=4',
    'Gemini': 'https://avatars.githubusercontent.com/u/1342004?s=200&v=4',
    'Moonshot': 'https://avatars.githubusercontent.com/u/129152888?s=200&v=4',
    'Kimi': 'https://avatars.githubusercontent.com/u/129152888?s=200&v=4',
    'MiniMax': 'https://avatars.githubusercontent.com/u/194880281?s=200&v=4',
    'NVIDIA': 'https://avatars.githubusercontent.com/u/1728152?s=200&v=4',
    
    # Cloud/Enterprise
    'Amazon': 'https://avatars.githubusercontent.com/u/2232217?s=200&v=4',
    'AWS': 'https://avatars.githubusercontent.com/u/2232217?s=200&v=4',
    'Microsoft': 'https://avatars.githubusercontent.com/u/6154722?s=200&v=4',
    'Meta': 'https://avatars.githubusercontent.com/u/69631?s=200&v=4',
    'Alibaba': 'https://avatars.githubusercontent.com/u/1961952?s=200&v=4',
    'Bytedance': 'https://avatars.githubusercontent.com/u/20225159?s=200&v=4',
    
    # Research Labs
    'NUS': 'https://avatars.githubusercontent.com/u/28691550?s=200&v=4',  # AutoCodeRover
    'Stanford': 'https://avatars.githubusercontent.com/u/6937093?s=200&v=4',
    
    # Other Organizations  
    'Factory': 'https://avatars.githubusercontent.com/u/121155557?s=200&v=4',
    'AppMap': 'https://avatars.githubusercontent.com/u/48058882?s=200&v=4',
    'Moatless': 'https://avatars.githubusercontent.com/u/172453067?s=200&v=4',
    'CodeStory': 'https://avatars.githubusercontent.com/u/132aboratory?s=200&v=4',
    'AbanteAI': 'https://avatars.githubusercontent.com/u/128949612?s=200&v=4',
}

# Default logo for unknown organizations
DEFAULT_ORG_LOGO = 'https://avatars.githubusercontent.com/u/0?s=200&v=4'


def org_logo_filter(org_name: str) -> str:
    """Convert organization name to logo URL"""
    return ORG_LOGOS.get(org_name, DEFAULT_ORG_LOGO)


def auto_name_from_display(display_name: str) -> str:
    """Convert a display name to the generated leaderboard identifier."""
    auto_name = display_name.lower().replace(' ', '_').replace('-', '_')
    return ''.join(c if c.isalnum() or c == '_' else '' for c in auto_name)


def format_number_filter(value) -> str:
    """Format numeric values for display."""
    if value is None or value == '':
        return 'N/A'

    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)

    if number.is_integer():
        return f'{int(number):,}'
    return f'{number:,.1f}'


def format_currency_filter(value) -> str:
    """Format a number as USD."""
    if value is None or value == '':
        return 'N/A'

    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)

    if number >= 1000:
        return f'${number:,.0f}'
    return f'${number:,.2f}'


def format_percent_filter(value) -> str:
    """Format a percent with one decimal place unless it is whole."""
    if value is None or value == '':
        return 'N/A'

    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)

    return f'{number:.0f}%' if number.is_integer() else f'{number:.1f}%'


def load_yaml_data(yaml_file: Path) -> dict:
    """Load leaderboard data from YAML file and auto-generate names"""
    with open(yaml_file, 'r') as f:
        data = yaml.safe_load(f)

    # Auto-generate 'name' from 'display_name' if not provided
    leaderboard_groups = [data.get('leaderboards', [])]
    if isinstance(data.get('legacy'), dict):
        leaderboard_groups.append(data['legacy'].get('leaderboards', []))

    for leaderboard in [item for group in leaderboard_groups for item in group]:
        if 'name' not in leaderboard and 'display_name' in leaderboard:
            leaderboard['name'] = auto_name_from_display(leaderboard['display_name'])

    return data


def load_run_details(data_dir: Path) -> dict:
    """Load compact run-detail JSON files checked into data/run_details."""
    details_root = data_dir / 'run_details'
    run_details = {}

    if not details_root.exists():
        return run_details

    for path in sorted(details_root.glob('*/*.json')):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                detail = json.load(f)
        except json.JSONDecodeError as exc:
            print(f"⚠ Warning: Could not parse {path}: {exc}")
            continue

        target = detail.get('target')
        slug = detail.get('slug')
        if target and slug:
            run_details[(target, slug)] = detail

    return run_details


def available_target_tabs(site_config: dict) -> list:
    """Return Pro target tabs that have published leaderboard pages."""
    return [
        target
        for target in site_config.get('target_tabs', [])
        if target.get('status') == 'available' and target.get('leaderboard')
    ]


def target_for_leaderboard(site_config: dict) -> dict:
    """Map leaderboard names to their Pro target tab config."""
    mapping = {}
    for target in available_target_tabs(site_config):
        mapping[target.get('leaderboard') or target.get('name')] = target
    return mapping


def attach_run_detail_urls(site_config: dict, run_details: dict):
    """Annotate leaderboard rows with clean detail URLs when detail data exists."""
    target_by_leaderboard = target_for_leaderboard(site_config)

    for leaderboard in site_config.get('leaderboards', []):
        target = target_by_leaderboard.get(leaderboard.get('name'))
        if not target:
            continue

        scored_results = [
            result for result in leaderboard.get('results', [])
            if result.get('resolved') is not None
        ]
        ranked_results = sorted(
            scored_results,
            key=lambda result: float(result.get('resolved') or 0),
            reverse=True,
        )
        rank_by_id = {id(result): index + 1 for index, result in enumerate(ranked_results)}

        for result in leaderboard.get('results', []):
            result['rank'] = rank_by_id.get(id(result))
            details = result.get('details') if isinstance(result.get('details'), dict) else None
            if not details:
                continue

            slug = details.get('slug')
            detail = run_details.get((target['name'], slug))
            if not slug or not detail:
                print(f"⚠ Warning: Missing run detail data for {target['name']}/{slug}")
                continue

            result['details_available'] = True
            result['details_url'] = f"/{target['name']}/runs/{slug}"
            result['details_summary'] = detail.get('summary', {})


# Sidebar resource URLs when comments omit a mode (Classic still inherits generic <!-- X URL -->).
RESOURCE_DEFAULTS = {
    'pro': {
        'paper_url': None,
        'code_url': 'https://github.com/SEC-bench/SEC-bench-Pro',
        'data_url': None,
    },
    'classic': {
        'paper_url': 'https://arxiv.org/abs/2506.11791',
        'code_url': 'https://github.com/SEC-bench/SEC-bench',
        'data_url': 'https://huggingface.co/datasets/SEC-bench/SEC-bench',
    },
}

_RESOURCE_COMMENT_MISSING = object()


def _parse_resource_url_comment(md_text: str, mode: str, label: str):
    """Return URL string, None if explicitly empty, or _RESOURCE_COMMENT_MISSING."""
    import re

    pattern = rf'<!--\s*{re.escape(mode)}\s+{re.escape(label)}\s+URL:\s*(.*?)\s*-->'
    m = re.search(pattern, md_text, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return _RESOURCE_COMMENT_MISSING
    raw = (m.group(1) or '').strip()
    return raw if raw else None


def _parse_generic_resource_url_comment(md_text: str, label: str):
    """Legacy <!-- Paper URL: ... --> style (shared fallback for Classic; Pro uses only for Code)."""
    import re

    pattern = rf'<!--\s*{re.escape(label)}\s+URL:\s*(.*?)\s*-->'
    m = re.search(pattern, md_text, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return _RESOURCE_COMMENT_MISSING
    raw = (m.group(1) or '').strip()
    return raw if raw else None


def build_resource_links(md_text: str) -> dict:
    """Per-mode Paper/Code/Data URLs for the sidebar (None => coming soon in UI)."""
    pro = {}
    classic = {}
    for key_root in ('paper', 'code', 'data'):
        label = key_root.capitalize()
        py_key = f'{key_root}_url'

        pv = _parse_resource_url_comment(md_text, 'Pro', label)
        if pv is not _RESOURCE_COMMENT_MISSING:
            pro[py_key] = pv
        elif py_key == 'code_url':
            gv = _parse_generic_resource_url_comment(md_text, label)
            if gv is not _RESOURCE_COMMENT_MISSING:
                pro[py_key] = gv
            else:
                pro[py_key] = RESOURCE_DEFAULTS['pro'][py_key]
        else:
            pro[py_key] = RESOURCE_DEFAULTS['pro'][py_key]

        cv = _parse_resource_url_comment(md_text, 'Classic', label)
        if cv is not _RESOURCE_COMMENT_MISSING:
            classic[py_key] = cv
        else:
            gv = _parse_generic_resource_url_comment(md_text, label)
            if gv is not _RESOURCE_COMMENT_MISSING:
                classic[py_key] = gv
            else:
                classic[py_key] = RESOURCE_DEFAULTS['classic'][py_key]

    return {'pro': pro, 'classic': classic}


def load_markdown_content(content_dir: Path) -> dict:
    """Load about.md and split by H2 sections; extract sidebar resource URLs."""
    import re

    md = markdown.Markdown(extensions=['fenced_code', 'tables', 'nl2br'])
    content = {}

    about_file = content_dir / 'about.md'

    if about_file.exists():
        with open(about_file, 'r', encoding='utf-8') as f:
            md_text = f.read()

        content['resource_links'] = build_resource_links(md_text)
        classic_urls = content['resource_links']['classic']
        content['paper_url'] = classic_urls['paper_url']
        content['code_url'] = classic_urls['code_url']
        content['data_url'] = classic_urls['data_url']

        # Split by H2 headers (## Title)
        # Pattern: ## Section Title
        sections = re.split(r'\n## ', md_text)

        # First section is the main About content (before first ##)
        if sections:
            main_content = sections[0].replace('# About\n\n', '')
            # Remove resource URL HTML comments from rendered About intro
            main_content = re.sub(
                r'<!--\s*(?:Pro|Classic|Paper|Code|Data)\s+URL:\s*.*?-->\s*\n?',
                '',
                main_content,
                flags=re.IGNORECASE | re.DOTALL,
            )
            if main_content.strip():
                content['about'] = md.convert(main_content)
                md.reset()

        # Process each H2 section
        for section in sections[1:]:
            # Extract section title (first line)
            lines = section.split('\n', 1)
            if len(lines) >= 1:
                title = lines[0].strip().lower()  # e.g., "Code" -> "code"
                section_content = lines[1] if len(lines) > 1 else ''

                # Add the H2 header back for proper rendering
                full_section = f'## {lines[0]}\n{section_content}'
                content[title] = md.convert(full_section)
                md.reset()
    else:
        print(f"⚠ Warning: about.md not found")
        content['about'] = ''
        content['data'] = ''
        content['code'] = ''
        content['citation'] = ''
        content['resource_links'] = {
            'pro': dict(RESOURCE_DEFAULTS['pro']),
            'classic': dict(RESOURCE_DEFAULTS['classic']),
        }
        content['paper_url'] = RESOURCE_DEFAULTS['classic']['paper_url']
        content['code_url'] = RESOURCE_DEFAULTS['classic']['code_url']
        content['data_url'] = RESOURCE_DEFAULTS['classic']['data_url']

    return content


def copy_static_files(src_dir: Path, dest_dir: Path):
    """Copy static files (CSS, JS, images) to dist directory"""
    static_dirs = ['css', 'js', 'img']

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
    chromium_src = src_dir / 'chromium'
    chromium_dest = dest_dir / 'chromium'

    if chromium_src.exists():
        if chromium_dest.exists():
            shutil.rmtree(chromium_dest)
        shutil.copytree(chromium_src, chromium_dest)
        print(f"✓ Copied chromium/")
    
    # Also copy the encrypted data files
    data_src = src_dir / 'data'
    data_dest = dest_dir / 'data'
    
    if data_src.exists():
        if data_dest.exists():
            shutil.rmtree(data_dest)
        shutil.copytree(data_src, data_dest)
        print(f"✓ Copied data/")


def build_site():
    """Main build function"""
    print("Building SEC-bench Pro leaderboard site...")

    # Setup paths
    base_dir = Path(__file__).parent
    templates_dir = base_dir / 'templates'
    data_dir = base_dir / 'data'
    content_dir = base_dir / 'content'
    dist_dir = base_dir / 'dist'

    # Load data
    print("\nLoading data...")
    leaderboards_data = load_yaml_data(data_dir / 'leaderboards.yaml')
    markdown_content = load_markdown_content(content_dir)
    run_details = load_run_details(data_dir)
    attach_run_detail_urls(leaderboards_data, run_details)

    leaderboard_count = len(leaderboards_data['leaderboards'])
    if isinstance(leaderboards_data.get('legacy'), dict):
        leaderboard_count += len(leaderboards_data['legacy'].get('leaderboards', []))

    print(f"✓ Loaded {leaderboard_count} leaderboards")
    print(f"✓ Loaded {len(markdown_content)} markdown content files")
    print(f"✓ Loaded {len(run_details)} run detail files")

    # Setup Jinja2 environment
    env = Environment(loader=FileSystemLoader(templates_dir))
    
    # Register custom filters
    env.filters['org_logo'] = org_logo_filter
    env.filters['format_number'] = format_number_filter
    env.filters['format_currency'] = format_currency_filter
    env.filters['format_percent'] = format_percent_filter

    # Create dist directory
    dist_dir.mkdir(exist_ok=True)

    # Copy static files
    print("\nCopying static files...")
    copy_static_files(base_dir, dist_dir)
    copy_chromium_files(base_dir, dist_dir)

    # Render pages
    print("\nRendering pages...")

    # Optional extra links in the site footer (sidebar carries Paper/Code/Data).
    footer_links = leaderboards_data.get('footer_links') or []

    # Extract website title, subtitle, section title and description
    website_title = leaderboards_data.get('website_title', 'SEC-bench Leaderboard')
    website_subtitle = leaderboards_data.get('website_subtitle', None)
    section_title = leaderboards_data.get('section_title', 'Leaderboard')
    section_description = leaderboards_data.get('section_description',
        'Performance of various LLM agents on SEC-bench security engineering tasks.')

    # Common template context
    common_context = {
        'content': markdown_content,
        'footer_links': footer_links,
        'website_title': website_title,
        'website_subtitle': website_subtitle,
        'leaderboard_items': leaderboards_data['leaderboards'],
        'site_config': leaderboards_data,
        'current_year': datetime.now().year,
        'asset_prefix': '',
        'site_root': '/',
    }

    # Render leaderboard pages
    template = env.get_template('index.html')

    def render_leaderboard_page(output_file: Path, initial_leaderboard: str | None, asset_prefix: str):
        html = template.render(
            leaderboards=leaderboards_data['leaderboards'],
            section_title=section_title,
            section_description=section_description,
            initial_leaderboard=initial_leaderboard,
            asset_prefix=asset_prefix,
            **{k: v for k, v in common_context.items() if k != 'asset_prefix'}
        )
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(html)
        print(f"✓ Rendered {output_file.relative_to(dist_dir)}")

    default_leaderboard = leaderboards_data['leaderboards'][0]['name'] if leaderboards_data['leaderboards'] else None
    render_leaderboard_page(dist_dir / 'index.html', default_leaderboard, '')

    for target in available_target_tabs(leaderboards_data):
        render_leaderboard_page(
            dist_dir / target['name'] / 'index.html',
            target.get('leaderboard') or target.get('name'),
            '../',
        )

    # Render run detail pages
    detail_template = env.get_template('run_detail.html')
    target_by_name = {target['name']: target for target in available_target_tabs(leaderboards_data)}
    for leaderboard in leaderboards_data.get('leaderboards', []):
        target = target_by_name.get(leaderboard.get('name'))
        if not target:
            continue

        for result in leaderboard.get('results', []):
            details = result.get('details') if isinstance(result.get('details'), dict) else None
            if not details or not result.get('details_available'):
                continue

            slug = details.get('slug')
            detail = run_details.get((target['name'], slug))
            if not detail:
                continue

            html = detail_template.render(
                detail=detail,
                target=target,
                result=result,
                page_title=f"{detail['model']} - {target['display_name']}",
                asset_prefix='../../../',
                **{k: v for k, v in common_context.items() if k != 'asset_prefix'}
            )
            output_file = dist_dir / target['name'] / 'runs' / slug / 'index.html'
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(html)
            print(f"✓ Rendered {output_file.relative_to(dist_dir)}")

    # Render additional pages
    additional_pages = ['citations.html', 'contact.html', 'submit.html']
    for page_name in additional_pages:
        try:
            template = env.get_template(f'pages/{page_name}')
            html = template.render(**common_context)
            output_file = dist_dir / page_name
            output_file.write_text(html)
            print(f"✓ Rendered {page_name}")
        except Exception as e:
            print(f"⚠ Warning: Could not render {page_name}: {e}")

    print("\n✅ Build complete! Output in dist/")
    print(f"   Run: python3 -m http.server --directory dist/ 8000")


if __name__ == '__main__':
    build_site()
