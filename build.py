#!/usr/bin/env python3
"""
Static site generator for SEC-bench leaderboard
Converts YAML data to static HTML using Jinja2 templates
"""

import json
import shutil
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
    'Aider': 'https://avatars.githubusercontent.com/u/172139148?s=48&v=4',
    'Agentless': 'https://avatars.githubusercontent.com/u/104632009?s=200&v=4',  # UIUC
    'UIUC': 'https://avatars.githubusercontent.com/u/104632009?s=200&v=4',
    
    # AI Model Providers
    'Anthropic': 'https://avatars.githubusercontent.com/u/76263028?s=200&v=4',
    'OpenAI': 'https://avatars.githubusercontent.com/u/14957082?s=200&v=4',
    'Google': 'https://avatars.githubusercontent.com/u/1342004?s=200&v=4',
    'Gemini': 'https://avatars.githubusercontent.com/u/1342004?s=200&v=4',
    'Moonshot': 'https://avatars.githubusercontent.com/u/129aboratory?s=200&v=4',
    'Kimi': 'https://avatars.githubusercontent.com/u/149329654?s=200&v=4',
    
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


def load_yaml_data(yaml_file: Path) -> dict:
    """Load leaderboard data from YAML file and auto-generate names"""
    with open(yaml_file, 'r') as f:
        data = yaml.safe_load(f)

    # Auto-generate 'name' from 'display_name' if not provided
    for leaderboard in data.get('leaderboards', []):
        if 'name' not in leaderboard and 'display_name' in leaderboard:
            # Convert to lowercase and replace spaces/special chars with underscores
            display_name = leaderboard['display_name']
            auto_name = display_name.lower().replace(' ', '_').replace('-', '_')
            # Remove any non-alphanumeric characters except underscores
            auto_name = ''.join(c if c.isalnum() or c == '_' else '' for c in auto_name)
            leaderboard['name'] = auto_name

    return data


def load_markdown_content(content_dir: Path) -> dict:
    """Load about.md and split by H2 sections, extract Paper URL"""
    import re

    md = markdown.Markdown(extensions=['fenced_code', 'tables', 'nl2br'])
    content = {}

    about_file = content_dir / 'about.md'

    if about_file.exists():
        with open(about_file, 'r', encoding='utf-8') as f:
            md_text = f.read()

        # Extract Paper URL from HTML comment
        paper_url_match = re.search(r'<!-- Paper URL: (.+?) -->', md_text)
        if paper_url_match:
            content['paper_url'] = paper_url_match.group(1).strip()
        else:
            content['paper_url'] = 'https://arxiv.org/abs/2506.11791'  # Default
        
        # Extract Data URL from HTML comment
        data_url_match = re.search(r'<!-- Data URL: (.+?) -->', md_text)
        if data_url_match:
            content['data_url'] = data_url_match.group(1).strip()
        else:
            content['data_url'] = 'https://huggingface.co/datasets/SEC-bench/SEC-bench'  # Default

        # Extract Code URL from HTML comment
        code_url_match = re.search(r'<!-- Code URL: (.+?) -->', md_text)
        if code_url_match:
            content['code_url'] = code_url_match.group(1).strip()
        else:
            content['code_url'] = 'https://github.com/SEC-bench/SEC-bench'  # Default

        # Split by H2 headers (## Title)
        # Pattern: ## Section Title
        sections = re.split(r'\n## ', md_text)

        # First section is the main About content (before first ##)
        if sections:
            main_content = sections[0].replace('# About\n\n', '')
            # Remove the Paper URL comment
            main_content = re.sub(r'<!-- Paper URL: .+? -->\n\n', '', main_content)
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
        content['paper_url'] = 'https://arxiv.org/abs/2506.11791'
        content['code_url'] = 'https://github.com/SEC-bench/SEC-bench'
        content['data_url'] = 'https://huggingface.co/datasets/SEC-bench/SEC-bench'

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
    print("Building SEC-bench leaderboard site...")

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

    print(f"✓ Loaded {len(leaderboards_data['leaderboards'])} leaderboards")
    print(f"✓ Loaded {len(markdown_content)} markdown content files")

    # Setup Jinja2 environment
    env = Environment(loader=FileSystemLoader(templates_dir))
    
    # Register custom filters
    env.filters['org_logo'] = org_logo_filter

    # Create dist directory
    dist_dir.mkdir(exist_ok=True)

    # Copy static files
    print("\nCopying static files...")
    copy_static_files(base_dir, dist_dir)
    copy_chromium_files(base_dir, dist_dir)

    # Render pages
    print("\nRendering pages...")

    # Extract footer links from YAML, use defaults if not present
    footer_links = leaderboards_data.get('footer_links', [
        {'name': 'GitHub', 'url': 'https://github.com/SEC-bench/SEC-bench'},
        {'name': 'Data', 'url': 'https://huggingface.co/datasets/SEC-bench/SEC-bench'},
        {'name': 'Paper', 'url': 'https://arxiv.org/abs/2506.11791'}
    ])

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
    }

    # Render index page
    template = env.get_template('index.html')
    html = template.render(
        leaderboards=leaderboards_data['leaderboards'],
        section_title=section_title,
        section_description=section_description,
        **common_context
    )
    output_file = dist_dir / 'index.html'
    output_file.write_text(html)
    print(f"✓ Rendered index.html")

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

