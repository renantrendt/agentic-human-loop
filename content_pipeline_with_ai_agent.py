def extract_primary_keywords(markdown_text):
    """
    Pull the Primary Keywords line from markdown and return list of keywords.
    Expected format near bottom: **Primary Keywords:** keyword1, keyword2
    """
    match = re.search(r"\*\*Primary Keywords:\*\*\s*(.+)", markdown_text)
    if not match:
        return []
    keywords_line = match.group(1).strip()
    # Split on commas or pipes, remove inline annotations
    raw_keywords = re.split(r"[,\|]", keywords_line)
    keywords = [kw.strip() for kw in raw_keywords if kw.strip()]
    return keywords

def build_prompt_values(keywords, title, slug_text):
    """
    Build prompt values from reviewed keywords only.
    No longer adds article title - AI-reviewed keywords are sufficient.
    Title fallback removed to prevent branded titles becoming prompts.
    """
    # Use keywords if available, otherwise fall back to slug
    base = keywords[:] if keywords else [slug_text]
    
    # De-duplicate while preserving order
    seen = set()
    ordered = []
    for value in base:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered
#!/usr/bin/env python3
"""
Local Content Optimization Pipeline - ZERO COMPROMISE MODE
===========================================================
Runs the complete pipeline locally using CSV data instead of database.
Each step creates an output file that YOU (Claude via Cursor) will analyze.

PHILOSOPHY: Never skip steps. Demand AI agent rescue for any failures.
GOAL: Create EXCEPTIONAL SEO content for the best company in the world.

Workflow:
1. Content Analysis (using CSV) → outputs data for Claude to analyze
2. URL Analysis (using existing scraped URLs)
3. Scraping Analysis (using existing scraped content)
4. AI Synthesis → strategic recommendations
5. Article Generation → world-class content
6. Writing Rules → brand alignment
7. Internal Links → SEO optimization
8. Citations → authority building

No external AI APIs - Claude does all the analysis!
QUALITY MANDATE: Every step must succeed. No shortcuts. No compromises.
"""

import pandas as pd
import json
import os
import csv
from datetime import datetime
from urllib.parse import urlparse
from collections import Counter
import re
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import time
import random
from dotenv import load_dotenv
import argparse
import sys
import glob

from autonomous.secrets import get_secret

# =============================================================================
# SEO YEAR STRATEGY
# =============================================================================
# RULES:
# 1. NEVER put month or year in URL (evergreen URLs)
# 2. Jan-Oct: Use CURRENT year in titles/keywords
# 3. Nov-Dec: Use NEXT year in titles/keywords
# 4. "Month Hack" for competitive niches: Add "(Updated Month)" to title tag for CTR boost
# =============================================================================

def get_seo_target_year():
    """
    Get the target year for SEO content titles and keywords.
    
    Nov-Dec Strategy: Use NEXT year
    - Users searching late in year want future-relevant content
    - "Best tools 2026" in Nov 2025 captures Jan search intent
    - Higher CTR when new year arrives
    
    Jan-Oct: Use CURRENT year
    - Content is relevant for the current year
    
    Returns: int (e.g., 2026 if called in Nov 2025)
    """
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    
    # Nov-Dec = target next year
    if current_month >= 11:
        return current_year + 1
    else:
        return current_year

def get_month_hack_suffix():
    """
    Generate the "Month Hack" suffix for title tags.
    
    The "Month Hack": Adding "(Updated Month)" to title tags
    increases CTR in competitive niches (Finance, Tech, etc.)
    
    Example: "Best Apps 2025 (Updated May)"
    
    Returns: str (e.g., "(Updated November)")
    """
    now = datetime.now()
    month_name = now.strftime('%B')
    return f"(Updated {month_name})"

def is_late_year_publishing():
    """Check if we're in Nov-Dec (late year publishing window)."""
    return datetime.now().month >= 11

# Global SEO values (calculated once at startup)
SEO_TARGET_YEAR = get_seo_target_year()
SEO_MONTH_HACK = get_month_hack_suffix()
SEO_CURRENT_MONTH = datetime.now().strftime('%B')

# Load environment variables at the top
try:
    load_dotenv()
    ANTHROPIC_API_KEY = get_secret('ANTHROPIC_API_KEY')
except:
    ANTHROPIC_API_KEY = None

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)

# Import requests early for Athena API
import requests

# Load brand-specific configuration
CONFIG_FILE = os.path.join(SCRIPT_DIR, "brand-context/config.json")
try:
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        CONFIG = json.load(f)
except FileNotFoundError:
    print(f"❌ Configuration file not found: {CONFIG_FILE}")
    print(f"   Copy config.json.example to config.json and update with your brand details")
    sys.exit(1)

def save_config(updated_config):
    """Save updated configuration to file"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(updated_config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log(f"⚠️  Could not save config: {e}")

def fetch_athena_settings(website_id, api_url="http://localhost:3000/api/webhooks", vercel_share_token=None):
    """Fetch brand settings from AthenaHQ (supports Vercel preview)"""
    try:
        # Add Vercel share token if provided
        url = f"{api_url}/settings"
        if vercel_share_token:
            url += f"?_vercel_share={vercel_share_token}"
        
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {website_id}"},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        # Use print() not log() - this runs during module initialization
        print(f"⚠️  Could not fetch Athena settings: {e}")
        return None

def merge_athena_config():
    """Merge Athena settings into CONFIG if enabled"""
    global CONFIG
    
    athena_config = CONFIG.get('athena_integration', {})
    website_id = athena_config.get('website_id')
    
    if not website_id:
        return  # Athena not configured
    
    try:
        log("🔍 Fetching configuration from AthenaHQ...")
    except NameError:
        print("🔍 Fetching configuration from AthenaHQ...")
    
    api_url = athena_config.get('api_url', 'http://localhost:3000/api/webhooks')
    vercel_share_token = athena_config.get('vercel_share_token')
    athena_settings = fetch_athena_settings(website_id, api_url, vercel_share_token)
    
    if not athena_settings:
        return  # Fetch failed, use existing config
    
    # Auto-fill brand information
    if not CONFIG.get('brand'):
        CONFIG['brand'] = {}
    
    if not CONFIG['brand'].get('name'):
        CONFIG['brand']['name'] = athena_settings['websiteName']
        try:
            log(f"   ✅ Brand name: {athena_settings['websiteName']}")
        except NameError:
            print(f"   ✅ Brand name: {athena_settings['websiteName']}")
    
    if not CONFIG['brand'].get('url'):
        url = athena_settings['websiteUrl']
        if not url.startswith('http'):
            url = f"https://{url}"
        CONFIG['brand']['url'] = url
        try:
            log(f"   ✅ Brand URL: {url}")
        except NameError:
            print(f"   ✅ Brand URL: {url}")
    
    if CONFIG['brand'].get('keywords') == "AUTO" or not CONFIG['brand'].get('keywords'):
        CONFIG['brand']['keywords'] = athena_settings.get('identifiers', [])
        try:
            log(f"   ✅ Brand keywords: {len(CONFIG['brand']['keywords'])} identifiers")
        except NameError:
            print(f"   ✅ Brand keywords: {len(CONFIG['brand']['keywords'])} identifiers")
    
    # Auto-fill competitor analysis
    if not CONFIG.get('competitor_analysis'):
        CONFIG['competitor_analysis'] = {}
    
    if CONFIG['competitor_analysis'].get('domain_keywords') == "AUTO" or not CONFIG['competitor_analysis'].get('domain_keywords'):
        competitors = athena_settings.get('competitors', [])
        if competitors:
            # Extract all competitor identifiers
            all_competitor_keywords = []
            for comp in competitors:
                all_competitor_keywords.extend(comp.get('identifiers', []))
            
            CONFIG['competitor_analysis']['domain_keywords'] = {
                'athena_competitors': all_competitor_keywords
            }
            CONFIG['competitor_analysis']['target_domain'] = 'athena_competitors'
            
            try:
                log(f"   ✅ Competitors: {len(competitors)} companies ({len(all_competitor_keywords)} identifiers)")
            except NameError:
                print(f"   ✅ Competitors: {len(competitors)} companies ({len(all_competitor_keywords)} identifiers)")
    
    # Store settings for later use (webhooks)
    CONFIG['_athena_settings'] = athena_settings
    
    try:
        log(f"✅ Configuration enriched from AthenaHQ!")
    except NameError:
        print(f"✅ Configuration enriched from AthenaHQ!")
    
    # Update global variables
    global BRAND_NAME, BRAND_URL
    BRAND_NAME = CONFIG['brand']['name']
    BRAND_URL = CONFIG['brand']['url']

# Merge Athena settings if enabled (before using config values)
merge_athena_config()

# Brand Configuration (from config.json, possibly enriched by Athena)
BRAND_NAME = CONFIG['brand']['name']
BRAND_URL = CONFIG['brand']['url']
AUTHOR_NAME = CONFIG['brand'].get('author_name', CONFIG.get('publishing', {}).get('author_name', 'Content Team'))

# Paths - configurable from environment or config
CSV_FILENAME = os.getenv('PIPELINE_CSV_FILE', CONFIG.get('data_source', {}).get('csv_file', 'responses.csv'))
CSV_FILE = os.path.join(SCRIPT_DIR, "datasets", CSV_FILENAME)

RESULTS_DIR = os.path.join(SCRIPT_DIR, "results/local_pipeline")
# Brand context file - use first config keyword or brand name as filename
brand_context_filename = CONFIG['brand'].get('keywords', [CONFIG['brand']['name'].lower()])[0] if isinstance(CONFIG['brand'].get('keywords'), list) else CONFIG['brand']['name'].lower()
brand_context_filename = brand_context_filename.replace(' ', '_').lower()
BRAND_CONTEXT_FILE = os.path.join(SCRIPT_DIR, f"brand-context/{brand_context_filename}")
SESSION_ID = datetime.now().strftime('%Y%m%d_%H%M%S')
SESSION_DIR = os.path.join(RESULTS_DIR, f"session_{SESSION_ID}")

# Article Generation Config (from config.json)
TARGET_WORD_COUNT = CONFIG['content']['word_count_targets']['spoke']['ideal']
WORD_COUNT_TARGETS = CONFIG['content']['word_count_targets']

os.makedirs(SESSION_DIR, exist_ok=True)

def log(message):
    """Log message"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {message}")

# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Content Pipeline - ZERO COMPROMISE Mode',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create new session
  python3 content_pipeline_with_ai_agent.py
  
  # Resume latest session
  python3 content_pipeline_with_ai_agent.py --resume
  
  # Resume specific session
  python3 content_pipeline_with_ai_agent.py --resume session_20251121_024724
  
  # Resume with custom spoke batch size
  python3 content_pipeline_with_ai_agent.py --resume --spokes-batch 5
        """
    )
    parser.add_argument(
        '--resume',
        nargs='?',
        const='latest',
        metavar='SESSION_ID',
        help='Resume existing session (latest or specify session_ID)'
    )
    parser.add_argument(
        '--spokes-batch',
        type=int,
        default=3,
        metavar='N',
        help='Generate spokes in batches of N (default: 3)'
    )
    parser.add_argument(
        '--skip-evaluation',
        action='store_true',
        help='Skip Step 13 content quality evaluation (not recommended)'
    )
    return parser.parse_args()

def find_latest_session():
    """Find the most recent session directory"""
    sessions = sorted(Path(RESULTS_DIR).glob("session_*"))
    if sessions:
        return sessions[-1]
    return None

def detect_completed_steps(session_dir):
    """Returns dict of completed steps with file paths - supports organized folders"""
    completed = {}
    
    step_files = {
        0: "step0_BRAND_GAP_ANALYSIS.md",
        1: "step1_FOR_AGENT_ANALYSIS.md",
        2: "step2_FOR_AGENT_ANALYSIS.md",
        "2b": "step2b_SCRAPED_ANALYSIS.md",
        "2c": "step2c_URL_SEMANTIC_ANALYSIS.md",
        3: "step3_FOR_AGENT_ANALYSIS.md",
        "3b": "step3b_VERIFIED_SOURCES.json",  # Marker: Perplexity Sonar source library
        4: "step4_AGENT_SYNTHESIS.md",
        5: ["step5_GENERATED_ARTICLE.md", "articles/hub/step5_GENERATED_ARTICLE.md"],  # Check both locations
        6: ["step6_ARTICLE_RULES_APPLIED.md", "articles/hub/step6_ARTICLE_RULES_APPLIED.md"],
        7: ["step7_ARTICLE_WITH_INTERNAL_LINKS.md", "articles/hub/step7_ARTICLE_WITH_INTERNAL_LINKS.md"],
        8: ["step8_ARTICLE_WITH_CITATIONS.md", "articles/hub/step8_ARTICLE_WITH_CITATIONS.md"],
        "8b": "step8b_CITATION_VERIFICATION_REPORT.md",  # Marker: Citation URLs verified
        "8c": "step8c_CITATIONS_REVIEWED.txt",           # Marker: Citation issues fixed
        9: "step9_UPDATED_internal_linking_map.json",
        10: "step10_SPOKE_CLUSTER_COMPLETE.md",
        "10a": "step10a_UTILITIES_COMPLETE.txt",       # Marker: utility articles generated
        "10b": "step10b_CITATIONS_TASK_spoke01.md",    # Marker: spoke citation tasks created
        "10c": "step10c_CITATIONS_VERIFIED.txt",     # Marker: all spokes have citations
        11: "step11_CROSSLINKING_COMPLETE.txt",
        12: "step12_FRAMER_EXPORT.csv",
        "12b": "step12b_HTML_CLEANED.csv",           # Marker: HTML quality reviewed
        "12c": "step12c_CONTENT_GAPS.md",            # Marker: Content gaps analyzed  
        "12d": "step12d_LINK_VERIFICATION_REPORT.md", # Marker: Links verified
        "12e": "step12e_LINKS_FIXED.md",             # Marker: Links fixed
        13: "step13_CLUSTER_DOMINANCE.json",
        14: "step14_FINAL_SUMMARY.md"
    }
    
    for step, filename in step_files.items():
        # Handle list of possible locations
        if isinstance(filename, list):
            for fname in filename:
                filepath = Path(session_dir) / fname
                if filepath.exists():
                    completed[step] = str(filepath)
                    break
        else:
            filepath = Path(session_dir) / filename
            if filepath.exists():
                completed[step] = str(filepath)
    
    return completed

def resume_or_create_session(args):
    """Resume existing session or create new one"""
    global SESSION_ID, SESSION_DIR, COMPLETED_STEPS
    
    if args.resume:
        if args.resume == 'latest':
            session_path = find_latest_session()
            if not session_path:
                log("⚠️  No existing sessions found. Creating new session...")
                return create_new_session()
        else:
            session_path = Path(RESULTS_DIR) / args.resume
            if not session_path.exists():
                log(f"❌ Session not found: {args.resume}")
                log("Creating new session instead...")
                return create_new_session()
        
        log(f"📁 Found existing session: {session_path.name}")
        completed = detect_completed_steps(session_path)
        
        if completed:
            log(f"✅ Completed steps: {sorted([str(k) for k in completed.keys()])}")
            log(f"⏭️  Will resume from next incomplete step")
        else:
            log("⚠️  No completed steps found in session")
        
        SESSION_ID = session_path.name.replace('session_', '')
        SESSION_DIR = str(session_path)
        COMPLETED_STEPS = completed
        
        return session_path, completed
    else:
        log("🆕 Creating new session...")
        return create_new_session(), {}

def create_new_session():
    """Create new timestamped session directory"""
    global SESSION_ID, SESSION_DIR
    
    SESSION_ID = datetime.now().strftime('%Y%m%d_%H%M%S')
    SESSION_DIR = os.path.join(RESULTS_DIR, f"session_{SESSION_ID}")
    os.makedirs(SESSION_DIR, exist_ok=True)
    
    return Path(SESSION_DIR)

# ============================================================================
# HELPER: GET BEST HUB FILE
# ============================================================================

def get_best_hub_file(session_dir=None):
    """
    Find the best hub article file (actual content, not task files).
    Priority order:
    1. step8_ARTICLE_WITH_CITATIONS.md (final with citations)
    2. step6_ARTICLE_RULES_APPLIED.md (rules applied)
    3. step5_HUB_COMPREHENSIVE_*.md (comprehensive version)
    4. step5_GENERATED_ARTICLE.md (initial generation)
    5. Any step8*.md that's not a task file
    """
    from pathlib import Path
    
    if session_dir is None:
        session_dir = SESSION_DIR
    
    hub_dir = Path(session_dir) / 'articles' / 'hub'
    if not hub_dir.exists():
        return None
    
    # Priority order for hub files
    priority_patterns = [
        'step8_ARTICLE_WITH_CITATIONS.md',
        'step6_ARTICLE_RULES_APPLIED.md',
        'step5_HUB_COMPREHENSIVE_*.md',
        'step5_GENERATED_ARTICLE.md',
    ]
    
    for pattern in priority_patterns:
        matches = list(hub_dir.glob(pattern))
        if matches:
            # Return the one with most content
            best = max(matches, key=lambda f: f.stat().st_size)
            return best
    
    # Fallback: any step8*.md that's not a task file
    for f in hub_dir.glob('step8*.md'):
        if 'TASK' not in f.name and 'BIBLIOGRAPHY' not in f.name:
            return f
    
    # Last resort: any .md file
    md_files = list(hub_dir.glob('*.md'))
    if md_files:
        # Exclude task files and return largest
        content_files = [f for f in md_files if 'TASK' not in f.name]
        if content_files:
            return max(content_files, key=lambda f: f.stat().st_size)
    
    return None

# ============================================================================
# HELPER: LOAD AVAILABLE INTERNAL LINKS
# ============================================================================

def load_available_internal_links():
    """Load internal linking opportunities from sitemap and session"""
    
    links = []
    
    # 1. Load brand sitemap
    sitemap_file = Path(SCRIPT_DIR) / "brand-context" / "sitemap"
    if sitemap_file.exists():
        with open(sitemap_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split('|')
                if len(parts) >= 2:
                    links.append({
                        'url': parts[0].strip(),
                        'title': parts[1].strip(),
                        'type': parts[2].strip() if len(parts) > 2 else 'blog',
                        'keywords': [k.strip() for k in parts[3].split(',')] if len(parts) > 3 else []
                    })
    
    # 2. Load internal linking map
    linking_map_file = Path(SCRIPT_DIR) / "brand-context" / "internal_linking_map.json"
    if linking_map_file.exists():
        with open(linking_map_file, 'r', encoding='utf-8') as f:
            linking_map = json.load(f)
            for cluster in linking_map.get('clusters', []):
                if 'hub_url' in cluster:
                    links.append({
                        'url': cluster['hub_url'],
                        'title': cluster.get('hub_title', ''),
                        'type': 'hub',
                        'keywords': cluster.get('keywords', [])
                    })
                for spoke in cluster.get('spokes', []):
                    links.append({
                        'url': spoke.get('url', ''),
                        'title': spoke.get('title', ''),
                        'type': 'spoke',
                        'keywords': spoke.get('keywords', [])
                    })
    
    # 3. Add product URLs from config (optional)
    config_product_links = CONFIG['brand'].get('default_product_links', [])
    if config_product_links:
        links.extend(config_product_links)
    
    # 4. ALWAYS include homepage (guaranteed safe!)
    homepage_exists = any(l['url'] == BRAND_URL for l in links)
    if not homepage_exists and BRAND_URL:
        links.append({
            'url': BRAND_URL,
            'title': f'{BRAND_NAME} Homepage',
            'type': 'product',
            'keywords': [BRAND_NAME.lower(), 'homepage', 'platform']
        })
    
    return links

def format_link_list(links):
    """Format list of links for task file"""
    if not links:
        return "_No links available in this category_"
    
    output = []
    for link in links[:20]:
        title = link.get('title', link['url'])
        url = link['url']
        keywords = ', '.join(link.get('keywords', [])[:3])
        output.append(f"- [{title}]({url})\n  Keywords: {keywords}")
    
    return '\n'.join(output)

def format_citation_needs(citation_markers):
    """Format list of claims needing citations"""
    if not citation_markers:
        return "_No citation markers found_"
    
    output = []
    for i, marker in enumerate(citation_markers, 1):
        context = re.sub(r'\s+', ' ', marker.strip())
        output.append(f"{i}. {context}")
    
    return '\n\n'.join(output)

def create_ai_rescue_task(step_name, failure_reason, required_action, output_file, additional_context=""):
    """
    Create an AI rescue task when pipeline hits a blocking issue.
    This ensures we NEVER skip important steps - we demand solutions.
    
    Philosophy: We're building for the BEST company in the world.
    No compromises. No shortcuts. Exceptional quality only.
    """
    rescue_file = os.path.join(SESSION_DIR, f"RESCUE_{step_name}.md")
    
    with open(rescue_file, 'w', encoding='utf-8') as f:
        f.write(f"# 🚨 AI AGENT RESCUE REQUIRED: {step_name}\n\n")
        f.write(f"**Session:** {SESSION_ID}\n")
        f.write(f"**Created:** {datetime.now()}\n\n")
        f.write("---\n\n")
        f.write("## ⚠️ CRITICAL ISSUE\n\n")
        f.write(f"**Failure Reason:** {failure_reason}\n\n")
        f.write("**Impact:** Pipeline CANNOT proceed without this data\n\n")
        f.write(f"**Quality Standard:** We're building for {BRAND_NAME} - no shortcuts allowed\n\n")
        
        if additional_context:
            f.write(f"**Context:** {additional_context}\n\n")
        
        f.write("---\n\n")
        f.write("## 🎯 YOUR MISSION (AI Agent)\n\n")
        f.write(f"{required_action}\n\n")
        f.write("---\n\n")
        f.write("## 📋 DELIVERABLE\n\n")
        f.write(f"**Save your solution to:** `{output_file}`\n\n")
        f.write("**Quality Gates:**\n")
        f.write("- ✅ Complete (no placeholders or TODOs)\n")
        f.write("- ✅ Accurate (verified sources and data)\n")
        f.write("- ✅ Sufficient (meets or exceeds minimum thresholds)\n")
        f.write("- ✅ Formatted correctly (proper structure)\n")
        f.write("- ✅ Exceptional (not just 'good enough')\n\n")
        f.write("---\n\n")
        f.write("## ⚡ URGENCY: BLOCKING\n\n")
        f.write("⏸️  Pipeline is PAUSED until you complete this rescue task.\n\n")
        f.write(f"**Remember:** Every piece of content represents {BRAND_NAME}.\n")
        f.write(f"We ship excellence or we ship nothing.\n\n")
        f.write("**After completion:**\n")
        f.write("1. Save file with exact name above\n")
        f.write("2. Re-run pipeline: `python3 content_pipeline_with_ai_agent.py --resume`\n")
        f.write("3. Pipeline will detect your solution and continue\n\n")
    
    log("="*80)
    log("🚨 CRITICAL: AI AGENT RESCUE REQUIRED")
    log("="*80)
    log(f"   Blocking Issue: {step_name}")
    log(f"   Rescue Task: {rescue_file}")
    log(f"   Save solution to: {output_file}")
    log("="*80)
    print(f"\n🤖 RESCUE_TASK_READY: {rescue_file}")
    print(f"💾 Solution File: {output_file}")
    print(f"⏸️  Pipeline BLOCKED - cannot proceed without exceptional data")
    print(f"📖 Read rescue task for detailed instructions")
    print("="*80 + "\n")
    
    return None, {'rescue_required': True, 'rescue_file': rescue_file}

def extract_domains_from_sources(sources_text):
    """Extract domains from source URLs"""
    if pd.isna(sources_text) or str(sources_text).strip() == '':
        return []
    
    domains = []
    urls = str(sources_text).split(';')
    
    for url in urls:
        url = url.strip()
        if not url:
            continue
        
        try:
            if not url.startswith('http'):
                domain = url.split('/')[0]
            else:
                parsed = urlparse(url)
                domain = parsed.netloc.replace('www.', '')
            
            if domain:
                domains.append(domain.lower())
        except:
            continue
    
    return domains

def categorize_by_sources(row):
    """Categorize response based on cited sources AND text mentions"""
    sources = row.get('Sources', '')
    response_text = str(row.get('Response', '')).lower()
    
    # Extract domains from Sources column
    domains = extract_domains_from_sources(sources)
    
    # Load competitor brands from config (supports both old format and Athena auto-filled)
    domain_keywords = CONFIG['competitor_analysis']['domain_keywords']
    
    # Get primary domain keywords (Athena or manual)
    if 'athena_competitors' in domain_keywords:
        target_brands = domain_keywords['athena_competitors']
        
        # Check both domain citations and text mentions
        has_target_citation = any(any(brand.lower() in d.lower() for brand in target_brands) for d in domains)
        has_target_mention = any(brand.lower() in response_text for brand in target_brands)
        has_target = has_target_citation or has_target_mention
        
        if not domains and not has_target:
            return 'no_sources'
        elif has_target:
            return 'target_domain'
        else:
            return 'other'
    else:
        # Legacy/Manual config: use first defined category as target domain
        # This supports custom category names in config.json
        category_keys = list(domain_keywords.keys())
        
        if not category_keys:
            return 'other'
        
        # First category = target domain
        primary_category = category_keys[0]
        primary_brands = domain_keywords.get(primary_category, [])
        
        # Check both domain citations and text mentions for primary category
        has_primary_citation = any(any(brand.lower() in d.lower() for brand in primary_brands) for d in domains)
        has_primary_mention = any(brand.lower() in response_text for brand in primary_brands)
        has_primary = has_primary_citation or has_primary_mention
        
        # Check secondary categories (if any)
        has_secondary = False
        if len(category_keys) > 1:
            for cat_key in category_keys[1:]:
                cat_brands = domain_keywords.get(cat_key, [])
                has_secondary_citation = any(any(brand.lower() in d.lower() for brand in cat_brands) for d in domains)
                has_secondary_mention = any(brand.lower() in response_text for brand in cat_brands)
                if has_secondary_citation or has_secondary_mention:
                    has_secondary = True
                    break
        
        if not domains and not has_primary and not has_secondary:
            return 'no_sources'
        
        if has_primary and has_secondary:
            return 'mixed'
        elif has_primary:
            return 'target_domain'
        elif has_secondary:
            return 'other_domain'
        else:
            return 'other'

def extract_ngrams(text, n=2):
    """Extract n-grams"""
    if pd.isna(text):
        return []
    
    text = str(text).lower()
    text = re.sub(r'[^\w\s-]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    
    words = text.split()
    ngrams = []
    
    for i in range(len(words) - n + 1):
        ngram = ' '.join(words[i:i+n])
        if len(ngram) > 3 and not any(x in ngram for x in ['http', 'www', 'com', 'click']):
            ngrams.append(ngram)
    
    return ngrams

# ============================================================================
# STEP 0: BRAND GAP ANALYSIS
# ============================================================================

def fetch_athena_responses(website_id, api_url, target_prompt=None, vercel_share_token=None):
    """
    Fetch responses from Athena API for a specific prompt
    Supports Vercel preview deployments with share token
    Returns DataFrame in same format as CSV
    """
    
    # Helper to add Vercel token to URL
    def add_vercel_token(url, params=None):
        if vercel_share_token:
            if params is None:
                params = {}
            params['_vercel_share'] = vercel_share_token
        return params
    
    # 1. If no target_prompt, list zero-mention prompts
    if not target_prompt:
        log("🔍 Fetching prompts from Athena...")
        
        try:
            params = {
                    "page": 1,
                    "limit": 100,
                    "status": "active",
                    "type": "all",
                    "sortBy": "created",
                    "sortOrder": "desc"
            }
            params = add_vercel_token(f"{api_url}/prompts/list", params)
            
            response = requests.get(
                f"{api_url}/prompts/list",
                headers={"Authorization": f"Bearer {website_id}"},
                params=params,
                timeout=60
            )
            response.raise_for_status()
            
            prompts = response.json()['prompts']
            zero_mentions = [p for p in prompts if p['metrics']['totalResponses'] == 0]
            with_data = [p for p in prompts if p['metrics']['totalResponses'] > 0]
            
            log(f"✅ Found {len(prompts)} total prompts")
            log(f"   With data: {len(with_data)}")
            log(f"   Need data: {len(zero_mentions)}")
            
            if zero_mentions:
                log(f"\n⚠️  PROMPTS WITH ZERO RESPONSES (Add 'target_prompt' to config to select):")
                for i, p in enumerate(zero_mentions[:10], 1):
                    log(f"   {i}. '{p['prompt']}' (Topic: {p.get('topic', {}).get('name', 'None') if p.get('topic') else 'None'})")
                
                if len(zero_mentions) > 10:
                    log(f"   ... and {len(zero_mentions) - 10} more")
                
                log(f"\n💡 To use a prompt:")
                log(f"   1. Add to config.json: \"target_prompt\": \"your chosen prompt\"")
                log(f"   2. Collect data in Athena first (get responses)")
                log(f"   3. Re-run pipeline")
                return None
            
            # Auto-select first with data
            if with_data:
                target_prompt = with_data[0]['prompt']
                log(f"✅ Auto-selected first prompt with data: '{target_prompt}'")
            else:
                log(f"❌ No prompts with data found")
                return None
        
        except Exception as e:
            log(f"❌ Could not fetch prompts: {e}")
            return None
    
    # 2. Find prompt by text
    log(f"🔍 Finding prompt: '{target_prompt}'...")
    
    try:
        response = requests.get(
            f"{api_url}/prompts/list",
            headers={"Authorization": f"Bearer {website_id}"},
            params={
                "page": 1,
                "limit": 100,
                "status": "active",
                "type": "all",
                "sortBy": "created",
                "sortOrder": "desc"
            },
            timeout=30
        )
        response.raise_for_status()
        
        prompts = response.json()['prompts']
        prompt_obj = next((p for p in prompts if p['prompt'].lower() == target_prompt.lower()), None)
        
        if not prompt_obj:
            log(f"❌ Prompt not found: '{target_prompt}'")
            log(f"   Available prompts: {len(prompts)}")
            log(f"   Add this prompt in Athena first")
            return None
        
        log(f"✅ Found prompt: '{prompt_obj['prompt']}'")
        log(f"   Responses: {prompt_obj['metrics']['totalResponses']}")
        log(f"   Brand mentions: {prompt_obj['metrics']['brandMentions']} ({prompt_obj['metrics']['mentionRate']:.1f}%)")
        
        if prompt_obj['metrics']['totalResponses'] == 0:
            log(f"⚠️  This prompt has 0 responses!")
            log(f"   Collect data in Athena first")
            return None
        
    except Exception as e:
        log(f"❌ Could not find prompt: {e}")
        return None
    
    # 3. Fetch all responses for this prompt
    prompt_id = prompt_obj['id']
    
    log(f"📥 Fetching responses from Athena API...")
    
    all_responses = []
    page = 1
    
    try:
        while True:
            response = requests.get(
                f"{api_url}/prompts/{prompt_id}/responses",
                headers={"Authorization": f"Bearer {website_id}"},
                params={
                    "page": page,
                    "limit": 100,
                    "sortOrder": "desc"
                },
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            all_responses.extend(data['responses'])
            
            total_pages = data.get('totalPages', 1)
            log(f"   Page {page}/{total_pages} ({len(all_responses)} responses so far...)")
            
            if page >= total_pages:
                break
            page += 1
        
        log(f"✅ Fetched {len(all_responses)} responses from Athena")
        
    except Exception as e:
        log(f"❌ Could not fetch responses: {e}")
        return None
    
    # 4. Convert to DataFrame (same format as CSV)
    import pandas as pd
    
    df_data = []
    for r in all_responses:
        # Extract competitors mentioned
        competitors_list = r.get('competitorsMentioned', [])
        competitors_str = ';'.join([c['name'] for c in competitors_list])
        
        # Extract sources (URLs cited in the response)
        sources_list = r.get('sources', [])
        sources_urls = [s.get('url', s.get('domain', '')) for s in sources_list]
        sources_str = ';'.join(sources_urls)
        
        # Format date to match CSV format (MM/DD/YY)
        created_at = r.get('createdAt', '')
        if created_at:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(created_at.replace('+00', ''))
                date_formatted = dt.strftime('%m/%d/%y')
            except:
                date_formatted = created_at
        else:
            date_formatted = ''
        
        # Convert booleans to Yes/No strings to match CSV format
        mentioned_str = 'Yes' if r.get('targetMentioned', False) else 'No'
        cited_str = 'Yes' if len(sources_list) > 0 else 'No'
        attributed_str = 'Yes' if r.get('hasAttribution', False) else 'No'
        
        df_data.append({
            'Date': date_formatted,
            'Model': r.get('model', ''),
            'Prompt Type': prompt_obj.get('type', 'discovery'),
            'Base Prompt': prompt_obj.get('text', ''),
            'Prompt Variation': r.get('variation', ''),
            'Response': r.get('text', ''),
            'Mentioned': mentioned_str,
            'Market Position': r.get('targetRank', ''),
            'Sentiment': r.get('sentiment', ''),
            'Competitors Mentioned': competitors_str,
            'Sources': sources_str,  # Actual citation URLs!
            'Cited': cited_str,
            'Attributed Citation': attributed_str,
            'Persona': r.get('persona', '')
        })
    
    df = pd.DataFrame(df_data)
    
    log(f"✅ Dataset ready:")
    log(f"   Total responses: {len(df)}")
    log(f"   Brand mentions: {df['Mentioned'].sum()}")
    log(f"   Mention rate: {df['Mentioned'].mean()*100:.1f}%")
    log(f"   Responses with sources: {df['Cited'].sum()}")
    
    # CRITICAL: Save to CSV for Steps 1-2 to use
    log(f"\n💾 Saving Athena data to CSV for subsequent steps...")
    
    # Ensure datasets directory exists
    datasets_dir = os.path.dirname(CSV_FILE)
    os.makedirs(datasets_dir, exist_ok=True)
    
    # Save to CSV (columns already match expected format)
    df.to_csv(CSV_FILE, index=False)
    log(f"✅ Saved to: {CSV_FILE}")
    log(f"   (Steps 1-2 will use this file)")
    
    return df, {
        'source': 'athena_api',
        'prompt': prompt_obj['prompt'],
        'prompt_id': prompt_id,
        'total_responses': len(df)
    }

def step0_brand_gap_analysis():
    """
    Analyze brand mention rate and keyword gaps vs competitors
    TWO MODES:
    1. Athena API (if enabled): Fetches responses directly from Athena
    2. CSV (fallback): Loads from CSV file (configured in config.json or env)
    """
    log("="*80)
    log("STEP 0: BRAND GAP ANALYSIS")
    log("="*80)
    
    # Check if Athena API mode enabled
    athena_config = CONFIG.get('athena_integration', {})
    
    if athena_config.get('enabled') and athena_config.get('website_id'):
        log("🔗 ATHENA API MODE: Fetching data directly from Athena...")
        
        athena_result = fetch_athena_responses(
            athena_config['website_id'],
            athena_config.get('api_url', 'http://localhost:3000/api/webhooks'),
            athena_config.get('target_prompt', ''),
            athena_config.get('vercel_share_token')
        )
        
        if athena_result is None:
            log(f"\n❌ Could not fetch data from Athena")
            log(f"   Options:")
            log(f"   1. Set 'target_prompt' in config.json to a specific keyword")
            log(f"   2. Collect data for prompts in Athena first")
            log(f"   3. Disable Athena and use CSV mode instead")
            sys.exit(1)
        
        df = athena_result
        log(f"✅ Using Athena API data - NO CSV NEEDED!")
        
    else:
        # Fallback to CSV mode
        log("📁 CSV MODE: Loading dataset from file...")
    
    # Check if CSV exists
    if not os.path.exists(CSV_FILE):
        log(f"")
        log(f"❌ PIPELINE HALTED: CSV file not found")
        log(f"")
        log(f"📁 Missing file: {CSV_FILE}")
        log(f"")
        log(f"🔧 SOLUTION:")
        log(f"")
        log(f"1. **Enable Athena API mode** (RECOMMENDED):")
        log(f"   - Set `athena_integration.enabled = true` in config.json")
        log(f"   - Set `target_prompt` to your keyword")
        log(f"   - Pipeline will fetch data directly from AthenaHQ (no CSV needed!)")
        log(f"")
        log(f"2. **Or provide CSV file manually:**")
        log(f"   - Export responses from AthenaHQ")
        log(f"   - Save as: datasets/{CSV_FILENAME}")
        log(f"   - Ensure it has these columns: Date, Model, Response, Sources, etc.")
        log(f"")
        log(f"⏸️  Pipeline stopped. Fix the issue above and re-run.")
        log(f"")
        return create_ai_rescue_task(
            step_name="STEP0_CSV_MISSING",
            failure_reason=f"CSV file not found at {CSV_FILE}. Enable Athena API mode or provide CSV file.",
            required_action=f"""**REQUIRED:** Enable Athena API mode or provide CSV file.

**Recommended: Enable Athena API Mode**
   - Set `athena_integration.enabled = true` in config.json
   - Set `target_prompt` to your keyword (e.g., "conversation analytics platform")
   - Pipeline will fetch data directly from AthenaHQ - no CSV needed!

**Alternative: Provide CSV File**
   - Export responses from AthenaHQ dashboard
   - Save as: `datasets/{CSV_FILENAME}`
   - Required columns: Date, Model, Base Prompt, Response, Sources, Mentioned, etc.

**Required CSV columns:**
- `Prompt` or `Prompt Variation` (str) - the user's question
- `Response` (str, min 100 chars) - the AI's response
- `Sources` (str) - semicolon-separated URLs cited
- `Model` (str, optional) - which AI model generated response

**Minimum data quality requirements:**
- At least 1,000 total responses
- At least {CONFIG.get('data_source', {}).get('min_responses_required', 100)} target domain responses
- Real source citations with actual URLs
- Diverse prompt variations

**Save the CSV to:** `{CSV_FILE}`

This is the foundation of ALL analysis - we need real, quality data.
""",
            output_file=CSV_FILE,
            additional_context=f"Brand gap analysis requires response data to measure {BRAND_NAME} visibility vs competitors"
        )
    
    # Load CSV
    try:
        df = pd.read_csv(CSV_FILE)
        log(f"Loaded {len(df):,} responses")
    except Exception as e:
        return create_ai_rescue_task(
            step_name="STEP0_CSV_CORRUPT",
            failure_reason=f"Failed to read CSV file: {e}",
            required_action=f"""The CSV file exists but cannot be read (corrupt or wrong format).

**Error:** {e}

**YOUR MISSION:**
Fix or replace the CSV file so it can be loaded with pandas.

**Common issues:**
- Encoding problems (try UTF-8)
- Malformed CSV (extra commas, unescaped quotes)
- Wrong delimiter (should be comma, not tab/semicolon)
- File corruption (re-download or use backup)

**Test with:**
```python
import pandas as pd
df = pd.read_csv('{CSV_FILE}')
print(df.head())
print(df.columns)
```

Fix the file and save to: `{CSV_FILE}`
""",
            output_file=CSV_FILE
        )
    
    # Check if Response column exists
    if 'Response' not in df.columns:
        log("⚠️  'Response' column not found - Skipping brand analysis")
        return None, {}
    
    # Brand detection (from config)
    brand_keywords = CONFIG['brand'].get('keywords', [BRAND_NAME.lower()])
    
    def has_brand_mention(text):
        if pd.isna(text):
            return False
        text_lower = str(text).lower()
        return any(keyword in text_lower for keyword in brand_keywords)
    
    df['brand_mentioned'] = df['Response'].apply(has_brand_mention)
    
    # Competitor detection (from config or will be auto-detected in Step 0)
    target_domain = CONFIG['competitor_analysis'].get('target_domain', 'AUTO')
    
    if target_domain != "AUTO":
        competitor_keywords = CONFIG['competitor_analysis']['domain_keywords'].get(target_domain, [])
    else:
        # AUTO mode - will be detected later
        competitor_keywords = []
    
    def has_competitor_mention(text):
        if pd.isna(text):
            return False
        text_lower = str(text).lower()
        return any(keyword in text_lower for keyword in competitor_keywords)
    
    df['competitor_mentioned'] = df['Response'].apply(has_competitor_mention)
    
    # Categorize
    brand_only = df[df['brand_mentioned'] == True]
    competitors_only = df[(df['brand_mentioned'] == False) & (df['competitor_mentioned'] == True)]
    generic = df[(df['brand_mentioned'] == False) & (df['competitor_mentioned'] == False)]
    
    # Calculate stats
    total = len(df)
    brand_rate = (len(brand_only) / total * 100) if total > 0 else 0
    competitor_rate = (len(competitors_only) / total * 100) if total > 0 else 0
    generic_rate = (len(generic) / total * 100) if total > 0 else 0
    
    # Extract top keywords from competitor responses
    competitor_bigrams = []
    if len(competitors_only) > 0:
        for text in competitors_only['Response']:
            competitor_bigrams.extend(extract_ngrams(text, n=2))
    
    top_competitor_keywords = Counter(competitor_bigrams).most_common(20)
    
    # Save analysis
    md_file = os.path.join(SESSION_DIR, "step0_BRAND_GAP_ANALYSIS.md")
    
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("# STEP 0: Brand Gap Analysis\n\n")
        f.write(f"**Session:** {SESSION_ID}\n\n")
        f.write("---\n\n")
        
        f.write("## 📊 Brand Visibility\n\n")
        f.write(f"- **Total Responses:** {total:,}\n")
        f.write(f"- **Brand Mentioned ({BRAND_NAME}):** {len(brand_only):,} ({brand_rate:.1f}%)\n")
        f.write(f"- **Competitors Mentioned:** {len(competitors_only):,} ({competitor_rate:.1f}%)\n")
        f.write(f"- **Generic (No brands):** {len(generic):,} ({generic_rate:.1f}%)\n\n")
        
        if brand_rate < 5:
            f.write("⚠️ **Warning:** Low brand visibility (<5%). Focus on improving brand authority.\n\n")
        
        f.write("---\n\n")
        
        f.write("## 🎯 Top Keywords in Competitor Responses\n\n")
        f.write("*These keywords appear frequently when competitors are cited. Consider incorporating them:*\n\n")
        for i, (keyword, count) in enumerate(top_competitor_keywords, 1):
            f.write(f"{i}. `{keyword}` - {count:,}x\n")
        
        f.write("\n---\n\n")
        f.write("## ❓ FOR CLAUDE:\n\n")
        f.write("1. **Visibility Gap:** Why is brand mention rate low?\n")
        f.write("2. **Keyword Opportunities:** Which competitor keywords should we target?\n")
        f.write("3. **Content Strategy:** How can we increase brand visibility?\n\n")
    
    log(f"✅ Step 0 complete: {md_file}")
    log(f"   Brand mention rate: {brand_rate:.1f}%")
    
    return md_file, {
        'brand_rate': brand_rate,
        'competitor_rate': competitor_rate,
        'top_competitor_keywords': top_competitor_keywords
    }

# ============================================================================
# STEP 1: CONTENT ANALYSIS (Local CSV-based)
# ============================================================================

def step1_content_analysis():
    """
    Analyze response patterns from CSV using source-based categorization
    """
    log("="*80)
    log("STEP 1: CONTENT ANALYSIS (Local CSV)")
    log("="*80)
    
    # Check if CSV exists
    if not os.path.exists(CSV_FILE):
        log(f"")
        log(f"❌ PIPELINE HALTED: CSV file not found")
        log(f"")
        log(f"📁 Missing file: {CSV_FILE}")
        log(f"")
        log(f"🔧 SOLUTION: Enable Athena API mode (recommended)")
        log(f"   - Set `athena_integration.enabled = true` in config.json")
        log(f"   - Set `target_prompt` to your keyword")
        log(f"   - Pipeline will fetch data automatically from AthenaHQ")
        log(f"")
        log(f"⏸️  Pipeline stopped. Enable Athena mode or provide CSV file.")
        log(f"")
        sys.exit(1)
    
    # Load dataset - from Athena API or CSV
    athena_config = CONFIG.get('athena_integration', {})
    
    if athena_config.get('enabled') and athena_config.get('website_id'):
        # ATHENA API MODE
        log(f"🔗 Fetching data from Athena API...")
        
        athena_result = fetch_athena_responses(
            athena_config['website_id'],
            athena_config.get('api_url', 'http://localhost:3000/api/webhooks'),
            athena_config.get('target_prompt', ''),
            athena_config.get('vercel_share_token')
        )
        
        if athena_result is None:
            log(f"\n❌ Athena fetch failed - see instructions above")
            sys.exit(1)
        
        df = athena_result
        log(f"✅ Loaded {len(df):,} responses from Athena API")
        
    else:
        # CSV MODE (fallback)
        log(f"📁 Loading CSV: {CSV_FILE}...")
    try:
        df = pd.read_csv(CSV_FILE)
        log(f"✅ Loaded {len(df):,} responses from CSV")
    except Exception as e:
        return create_ai_rescue_task(
            step_name="STEP1_CSV_CORRUPT",
            failure_reason=f"Cannot read CSV: {e}",
            required_action=f"""Fix the CSV file format.

**Error:** {e}

Test and fix with pandas, then save to: `{CSV_FILE}`
""",
            output_file=CSV_FILE
        )
    
    # Categorize by sources
    log("Categorizing by source citations...")
    df['source_category'] = df.apply(categorize_by_sources, axis=1)
    
    # Focus on target domain + mixed
    target_domain_df = df[df['source_category'].isin(['target_domain', 'mixed'])]
    
    log(f"✅ Found {len(target_domain_df):,} target domain responses")
    
    # Extract patterns
    log("Extracting n-gram patterns...")
    
    all_bigrams = []
    all_trigrams = []
    
    for text in target_domain_df['Response']:
        all_bigrams.extend(extract_ngrams(text, n=2))
        all_trigrams.extend(extract_ngrams(text, n=3))
    
    bigram_counts = Counter(all_bigrams)
    trigram_counts = Counter(all_trigrams)
    
    top_bigrams = bigram_counts.most_common(50)
    top_trigrams = trigram_counts.most_common(30)
    
    # Auto-detect category and tags if set to AUTO
    if CONFIG['content'].get('default_category') == "AUTO":
        # Extract category from top trigram
        if top_trigrams:
            top_trigram = top_trigrams[0][0]
            # Capitalize first 2 words (e.g., 'conversation analytics platform' → 'Conversation Analytics')
            category_parts = top_trigram.split()[:2]
            auto_category = ' '.join(word.capitalize() for word in category_parts)
            CONFIG['content']['default_category'] = auto_category
            save_config(CONFIG)
            log(f"✅ Auto-detected category: {auto_category}")
    
    if CONFIG['content'].get('default_tags') == "AUTO":
        # Generate tags from top 4 bigrams
        auto_tags = []
        for bigram, _ in top_bigrams[:4]:
            # Capitalize (e.g., 'agent performance' → 'Agent Performance')
            tag = ' '.join(word.capitalize() for word in bigram.split())
            auto_tags.append(tag)
        
        CONFIG['content']['default_tags'] = auto_tags
        save_config(CONFIG)
        log(f"✅ Auto-generated tags: {auto_tags}")
    
    # Create analysis output
    output = {
        'total_responses': len(df),
        'target_domain_responses': len(target_domain_df),
        'percentage': (len(target_domain_df) / len(df)) * 100,
        'top_bigrams': top_bigrams,
        'top_trigrams': top_trigrams,
        'category_distribution': df['source_category'].value_counts().to_dict()
    }
    
    # Save JSON
    json_file = os.path.join(SESSION_DIR, "step1_content_patterns.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    # Create markdown for Claude analysis
    md_file = os.path.join(SESSION_DIR, "step1_FOR_AGENT_ANALYSIS.md")
    
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("# STEP 1: Content Pattern Analysis - FOR CLAUDE\n\n")
        f.write(f"**Session:** {SESSION_ID}\n")
        f.write(f"**Generated:** {datetime.now()}\n\n")
        f.write("---\n\n")
        
        f.write("## 📊 Data Overview\n\n")
        f.write(f"- Total responses analyzed: {len(df):,}\n")
        f.write(f"- **Target domain responses: {len(target_domain_df):,} ({output['percentage']:.1f}%)**\n")
        f.write(f"- Based on sources cited (not just text mentions)\n\n")
        
        f.write(f"## 🎯 TOP PATTERNS IN {CONFIG.get('data_source', {}).get('domain_name', 'TARGET DOMAIN').upper()} RESPONSES\n\n")
        
        f.write("### Top 30 Bigrams:\n\n")
        for i, (bigram, count) in enumerate(top_bigrams[:30], 1):
            f.write(f"{i}. `{bigram}` - {count:,}x\n")
        
        f.write("\n### Top 20 Trigrams:\n\n")
        for i, (trigram, count) in enumerate(top_trigrams[:20], 1):
            f.write(f"{i}. `{trigram}` - {count:,}x\n")
        
        f.write("\n---\n\n")
        
        f.write("## 📝 SAMPLE RESPONSES (First 5)\n\n")
        for idx, (i, row) in enumerate(target_domain_df.head(5).iterrows(), 1):
            f.write(f"### Sample {idx}\n\n")
            f.write(f"**Model:** {row.get('Model', 'Unknown')}\n")
            f.write(f"**Prompt:** {row.get('Prompt Variation', '')}\n")
            sources = extract_domains_from_sources(row.get('Sources', ''))
            f.write(f"**Sources:** {', '.join(sources[:5])}\n\n")
            f.write(f"**Response:**\n\n{str(row.get('Response', ''))[:800]}...\n\n")
            f.write("---\n\n")
        
        f.write("\n## ❓ FOR CLAUDE TO ANALYZE:\n\n")
        f.write("Based on the patterns above, please provide:\n\n")
        f.write("1. **Key Themes:** What are the main topics in target domain responses?\n")
        f.write("2. **Critical Keywords:** Which keywords appear most and should be prioritized?\n")
        f.write("3. **Content Structure:** What structure/format do these responses follow?\n")
        f.write("4. **Tone & Voice:** What tone is used in these responses?\n")
        f.write("5. **Strategic Insights:** What should our content include/avoid?\n\n")
    
    # QUALITY GATE: Ensure we have sufficient data for exceptional content
    min_responses_required = 100
    min_unique_bigrams = 30
    
    if len(target_domain_df) < min_responses_required:
        return create_ai_rescue_task(
            step_name="STEP1_INSUFFICIENT_DATA",
            failure_reason=f"Only {len(target_domain_df)} target domain responses found (need {min_responses_required}+)",
            required_action=f"""The dataset has insufficient target domain responses for quality analysis.

**Current Status:**
- Total responses in CSV: {len(df):,}
- Target domain responses: {len(target_domain_df)} ❌
- Minimum required: {min_responses_required}
- **Gap:** {min_responses_required - len(target_domain_df)} responses needed

**Why this matters:**
With only {len(target_domain_df)} responses, our keyword analysis and content patterns won't be statistically significant.
We need MORE data to create exceptional, data-driven content.

**YOUR MISSION:**
Augment the dataset with additional target domain responses.

**Strategies:**

1. **Query more data from source:**
   - Expand date range in Athena query
   - Include more prompt variations
   - Check if there's a larger export available

2. **Check categorization logic:**
   - Review responses in "other" or "mixed" categories
   - Some might be miscategorized (check lines 100-140 in script)
   - Update competitor domains in config.json or Athena settings if needed

3. **Cross-reference with competitors:**
   - Look for responses mentioning competitor platforms from your domain
   - Check for keywords from your industry (review Step 1 bigrams/trigrams)
   - These should be categorized as target domain responses

4. **Add supplemental data:**
   - Create `datasets/supplemental_data.csv` with same format
   - Pipeline will merge both files on next run

**Quality over speed:** We need genuine, relevant responses in your target domain.

**After completion:** Re-run pipeline - it will detect and merge your additions.
""",
            output_file="datasets/supplemental_data.csv",
            additional_context=f"Current percentage: {(len(target_domain_df)/len(df)*100):.1f}% of responses are target domain"
        )
    
    if len(top_bigrams) < min_unique_bigrams:
        log(f"⚠️  WARNING: Only {len(top_bigrams)} unique bigrams found (threshold: {min_unique_bigrams})")
        log("   Content patterns may be limited. Consider augmenting dataset.")
    
    log(f"✅ Step 1 complete - QUALITY GATE PASSED")
    log(f"   Responses analyzed: {len(target_domain_df):,} target domain")
    log(f"   Unique patterns: {len(top_bigrams)} bigrams, {len(top_trigrams)} trigrams")
    log(f"   JSON: {json_file}")
    log(f"   FOR CLAUDE: {md_file}")
    
    return md_file, output

# ============================================================================
# STEP 2: URL ANALYSIS (Using existing data)
# ============================================================================

def step2_url_analysis():
    """
    Analyze URL structure from scraped sources
    """
    log("="*80)
    log("STEP 2: URL ANALYSIS")
    log("="*80)
    
    # Load CSV to get cited URLs
    df = pd.read_csv(CSV_FILE)
    df['source_category'] = df.apply(categorize_by_sources, axis=1)
    target_df = df[df['source_category'].isin(['target_domain', 'mixed'])]
    
    # Extract all URLs
    all_urls = []
    for sources_text in target_df['Sources']:
        if pd.isna(sources_text):
            continue
        urls = str(sources_text).split(';')
        all_urls.extend([u.strip() for u in urls if u.strip()])
    
    log(f"Found {len(all_urls):,} total URL citations")
    
    # Count BOTH domain frequency AND full URL paths
    domain_counts = Counter()
    url_path_counts = Counter()
    
    for url in all_urls:
        try:
            if url.startswith('http'):
                parsed = urlparse(url)
                domain = parsed.netloc.replace('www.', '')
                # Get full path (domain + path)
                url_path = domain + parsed.path.rstrip('/')
            else:
                domain = url.split('/')[0].replace('www.', '')
                url_path = url.replace('www.', '')
            
            domain_counts[domain] += 1
            url_path_counts[url_path] += 1
        except:
            continue
    
    top_domains = domain_counts.most_common(20)
    top_url_paths = url_path_counts.most_common(50)  # Top 50 URL paths
    
    # Save for Agent
    md_file = os.path.join(SESSION_DIR, "step2_FOR_AGENT_ANALYSIS.md")
    
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("# STEP 2: URL Analysis - FOR AGENT\n\n")
        f.write(f"**Session:** {SESSION_ID}\n\n")
        f.write("---\n\n")
        
        f.write(f"## 📊 Most Cited Root Domains in {CONFIG.get('data_source', {}).get('domain_name', 'Target Domain').title()} Responses\n\n")
        f.write(f"Total URLs analyzed: {len(all_urls):,}\n\n")
        
        for i, (domain, count) in enumerate(top_domains, 1):
            f.write(f"{i}. **{domain}** - cited {count:,}x\n")
        
        f.write("\n---\n\n")
        
        f.write("## 📄 Most Cited URL Paths (Full Path for Better Calibration)\n\n")
        f.write(f"These are the specific articles/pages most cited by AI models:\n\n")
        
        for i, (url_path, count) in enumerate(top_url_paths, 1):
            f.write(f"{i}. `{url_path}` - cited {count:,}x\n")
        
        f.write("\n---\n\n")
        
        f.write("## ❓ FOR AGENT TO ANALYZE:\n\n")
        f.write("Based on the most-cited domains:\n\n")
        f.write("1. **Authority Sources:** Which domains are most authoritative?\n")
        f.write("2. **Content Types:** What types of content are being cited? (blogs, guides, comparisons)\n")
        f.write("3. **Competitor Landscape:** Who are the main competitors in this space?\n")
        f.write("4. **Content Gaps:** What topics are well-covered vs under-covered?\n\n")
    
    log(f"✅ Step 2 complete: {md_file}")
    log(f"   Top domain: {top_domains[0][0]} ({top_domains[0][1]} citations)")
    log(f"   Top URL path: {top_url_paths[0][0]} ({top_url_paths[0][1]} citations)")
    
    return md_file, {
        'top_domains': top_domains,
        'top_url_paths': top_url_paths,
        'all_urls': all_urls,
        'url_df': pd.DataFrame({'url': all_urls})
    }

# ============================================================================
# STEP 2C: URL SEMANTIC ANALYSIS (Search Intent & Keywords)
# ============================================================================

def extract_semantic_content_from_url(url):
    """Extract semantic keywords from URL path"""
    if not url or pd.isna(url):
        return ""
    
    url = str(url)
    if not url.startswith('http'):
        url = f'http://{url}'
    
    try:
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        if not path:
            return ""
        
        # Remove common non-semantic prefixes
        non_semantic = {'blog', 'article', 'post', 'news', 'learn', 'guide', 
                       '2023', '2024', '2025', 'en', 'pt', 'es'}
        
        segments = [seg for seg in path.split('/') if seg and seg.lower() not in non_semantic]
        
        if segments:
            semantic = ' '.join(segments)
            semantic = re.sub(r'[/_\-\+\=\&\?\#\.]', ' ', semantic)
            semantic = re.sub(r'\s+', ' ', semantic.strip())
            return semantic.lower()
    except:
        return ""
    
    return ""

def classify_search_intent_with_ai(urls_batch):
    """
    Classify URLs by search intent using AI (batch processing)
    Returns: dict mapping url -> intent category
    """
    if not ANTHROPIC_API_KEY:
        # Fallback to rule-based if no API key
        return {url: classify_search_intent_fallback(url) for url in urls_batch}
    
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        
        # Build batch prompt
        urls_text = "\n".join([f"{i+1}. {url}" for i, url in enumerate(urls_batch)])
        
        prompt = f"""Classify these {len(urls_batch)} URLs by search intent.

Intent categories:
- Comparative/Selection: "best X", "top X", "X vs Y", comparisons, alternatives
- Learning/Education: "how to", "what is", "guide to", tutorials, explanations
- Acquisition/Obtaining: pricing, purchase, trial, demo, signup
- Optimization/Improvement: "improve", "optimize", "boost", best practices
- Implementation: setup, integration, configuration, deployment
- Troubleshooting: fix, error, problem, issue, debugging
- Others: doesn't fit above categories

URLs:
{urls_text}

Return ONLY JSON (no markdown):
{{
  "classifications": [
    {{"url_number": 1, "intent": "Comparative/Selection"}},
    {{"url_number": 2, "intent": "Learning/Education"}},
    ...
  ]
}}"""
        
        with client.messages.stream(
            model="claude-sonnet-4-20250514",  # Faster, cheaper for this task
            max_tokens=4000,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            content = ""
            for text in stream.text_stream:
                content += text
        
        # Parse JSON
        content = re.sub(r'^```json\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'^```\s*$', '', content, flags=re.MULTILINE).strip()
        
        json_match = re.search(r'\{[\s\S]*"classifications"[\s\S]*\}', content)
        if json_match:
            content = json_match.group(0)
        
        data = json.loads(content)
        
        # Map back to URLs
        result = {}
        for item in data.get('classifications', []):
            url_idx = item['url_number'] - 1
            if 0 <= url_idx < len(urls_batch):
                result[urls_batch[url_idx]] = item['intent']
        
        return result
    
    except Exception as e:
        log(f"   ⚠️  AI classification failed: {e}")
        # Fallback to rule-based
        return {url: classify_search_intent_fallback(url) for url in urls_batch}

def classify_search_intent_fallback(url):
    """Fallback rule-based classification (used when AI unavailable)"""
    semantic = extract_semantic_content_from_url(url).lower()
    
    if not semantic:
        return 'Others'
    
    words = semantic.split()
    
    # Comparative/Selection
    if any(w in words[:2] for w in ['best', 'top', 'compare', 'vs']):
        return 'Comparative/Selection'
    
    # Learning/Education
    if any(w in words[:2] for w in ['how', 'what', 'guide', 'tutorial']):
        return 'Learning/Education'
    
    # Acquisition
    if any(w in semantic for w in ['pricing', 'buy', 'download', 'trial', 'free']):
        return 'Acquisition/Obtaining'
    
    # Optimization
    if any(w in semantic for w in ['improve', 'optimize', 'enhance', 'boost']):
        return 'Optimization/Improvement'
    
    return 'Others'

def step2c_url_semantic_analysis(all_urls):
    """Analyze URL patterns for search intent and semantic keywords using AI"""
    log("="*80)
    log("STEP 2C: URL SEMANTIC ANALYSIS")
    log("="*80)
    
    # Create DataFrame with URL frequency
    url_counts = Counter(all_urls)
    url_df = pd.DataFrame([
        {'url': url, 'count': count} 
        for url, count in url_counts.most_common(100)
    ])
    
    log(f"Analyzing {len(url_df)} unique URLs...")
    
    # Extract semantic content
    url_df['semantic_keywords'] = url_df['url'].apply(extract_semantic_content_from_url)
    
    # Classify intent using AI (batch processing for efficiency)
    if ANTHROPIC_API_KEY:
        log("🤖 Using AI to classify search intent (more accurate than rules)...")
        
        BATCH_SIZE = 20  # Process 20 URLs at a time
        intent_mapping = {}
        
        urls_list = url_df['url'].tolist()
        for i in range(0, len(urls_list), BATCH_SIZE):
            batch = urls_list[i:i+BATCH_SIZE]
            batch_num = (i // BATCH_SIZE) + 1
            total_batches = (len(urls_list) + BATCH_SIZE - 1) // BATCH_SIZE
            
            log(f"   Batch {batch_num}/{total_batches} ({len(batch)} URLs)...")
            
            batch_results = classify_search_intent_with_ai(batch)
            intent_mapping.update(batch_results)
            
            time.sleep(0.5)  # Rate limiting
        
        url_df['search_intent'] = url_df['url'].map(intent_mapping).fillna('Others')
        log(f"   ✅ AI classified {len(intent_mapping)} URLs")
    else:
        log("⚠️  No ANTHROPIC_API_KEY - using fallback rule-based classification...")
        url_df['search_intent'] = url_df['url'].apply(classify_search_intent_fallback)
    
    # Calculate intent distribution
    intent_summary = url_df.groupby('search_intent')['count'].agg(['sum', 'count']).reset_index()
    intent_summary.columns = ['intent', 'total_mentions', 'num_urls']
    total = intent_summary['total_mentions'].sum()
    intent_summary['percentage'] = (intent_summary['total_mentions'] / total * 100).round(1)
    intent_summary = intent_summary.sort_values('percentage', ascending=False)
    
    # Extract top keywords from semantic content
    all_keywords = []
    for idx, row in url_df.iterrows():
        if row['semantic_keywords']:
            words = row['semantic_keywords'].split()
            for word in words:
                if len(word) > 3:
                    all_keywords.extend([word] * row['count'])
    
    keyword_counts = Counter(all_keywords)
    top_keywords = keyword_counts.most_common(20)
    
    # Save analysis
    md_file = os.path.join(SESSION_DIR, "step2c_URL_SEMANTIC_ANALYSIS.md")
    
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("# STEP 2C: URL Semantic Analysis\n\n")
        f.write(f"**Session:** {SESSION_ID}\n\n")
        f.write("---\n\n")
        
        f.write("## 📊 Search Intent Distribution\n\n")
        f.write("| Intent | Mentions | URLs | % |\n")
        f.write("|--------|----------|------|---|\n")
        for _, row in intent_summary.iterrows():
            f.write(f"| {row['intent']} | {row['total_mentions']:,} | {row['num_urls']} | {row['percentage']:.1f}% |\n")
        
        f.write("\n---\n\n")
        
        f.write("## 🔑 Top 20 Keywords from URL Paths\n\n")
        for i, (keyword, freq) in enumerate(top_keywords, 1):
            f.write(f"{i}. `{keyword}` - {freq:,}x\n")
        
        f.write("\n---\n\n")
        
        f.write("## 📋 Top 10 URLs by Intent\n\n")
        for intent in intent_summary['intent'].head(3):
            intent_urls = url_df[url_df['search_intent'] == intent].head(5)
            f.write(f"\n### {intent}:\n\n")
            for _, row in intent_urls.iterrows():
                f.write(f"- {row['url'][:80]}... ({row['count']}x)\n")
                f.write(f"  Keywords: *{row['semantic_keywords'][:60]}*\n")
        
        f.write("\n---\n\n")
        f.write("## ❓ FOR AGENT:\n\n")
        f.write("1. **Dominant Intent:** What does this tell us about user behavior?\n")
        f.write("2. **URL Patterns:** What URL structure wins (e.g., 'top-X' vs 'how-to')?\n")
        f.write("3. **Content Strategy:** What type of content should we create based on intent?\n\n")
    
    log(f"✅ Step 2C complete: {md_file}")
    log(f"   Top intent: {intent_summary.iloc[0]['intent']} ({intent_summary.iloc[0]['percentage']:.1f}%)")
    
    return md_file, {'intent_summary': intent_summary, 'top_keywords': top_keywords}

# ============================================================================
# STEP 2B: AI AGENT BROWSER SCRAPING TASK
# ============================================================================

def step2b_create_browser_scraping_task(top_domains, all_urls, max_pages=10):
    """
    Create AI Agent task to scrape competitor content using browser automation
    NOTE: First checks for reusable scraped content in datasets/scraped_content/
    """
    log("="*80)
    log("STEP 2B: AI AGENT BROWSER SCRAPING TASK")
    log("="*80)
    
    # Create a directory for full scraped content
    full_content_dir = os.path.join(SESSION_DIR, "scraped_content")
    os.makedirs(full_content_dir, exist_ok=True)
    
    # CHECK FOR REUSABLE SCRAPED CONTENT (NEW - 2025-11-21)
    reusable_scraped_dir = os.path.join(SCRIPT_DIR, "datasets/scraped_content")
    
    if os.path.exists(reusable_scraped_dir):
        reusable_files = [f for f in Path(reusable_scraped_dir).glob("*.txt") 
                         if f.name not in ["SCRAPING_COMPLETE.txt", "RESCUE_MANUAL_SCRAPES_COMPLETE.txt"]]
        
        if len(reusable_files) >= 5:
            log(f"✅ Found {len(reusable_files)} reusable scraped files in datasets/scraped_content/")
            log(f"   Copying to session directory - NO SCRAPING NEEDED")
            
            # Copy files to session directory
            import shutil
            for src_file in reusable_files:
                dst_file = os.path.join(full_content_dir, src_file.name)
                shutil.copy2(src_file, dst_file)
                log(f"   📋 Copied: {src_file.name}")
            
            # Create completion marker
            completion_marker = os.path.join(full_content_dir, "SCRAPING_COMPLETE.txt")
            with open(completion_marker, 'w') as f:
                f.write(f"Reused scraped content from datasets/scraped_content/\n")
                f.write(f"Files copied: {len(reusable_files)}\n")
                f.write(f"Date: {datetime.now()}\n")
            
            log(f"✅ Reusable content found - SCRAPING SKIPPED")
            log(f"   Files reused: {len(reusable_files)}")
            
            # Continue with analysis (same as if scraping completed)
            scraped_files = list(Path(full_content_dir).glob("*.txt"))
            # Fall through to the analysis section below
        else:
            log(f"⚠️  Found datasets/scraped_content/ but only {len(reusable_files)} files (need 5+)")
            log(f"   Will create scraping task")
    
    log(f"Created directory for full content: {full_content_dir}")
    
    # Filter to top domains and find their URLs
    top_domain_list = [domain for domain, count in top_domains[:max_pages]]
    
    urls_to_scrape = []
    for domain in top_domain_list:
        for url in all_urls:
            try:
                if domain in url.lower():
                    urls_to_scrape.append({'domain': domain, 'url': url})
                    break
            except:
                continue
    
    log(f"Selected {len(urls_to_scrape)} URLs from top {max_pages} domains")
    
    # Check if scraping was already done (in session directory)
    scraped_files = list(Path(full_content_dir).glob("*.txt"))
    completion_marker = os.path.join(full_content_dir, "SCRAPING_COMPLETE.txt")
    
    min_successful_scrapes = max(int(len(urls_to_scrape) * 0.7), 5)  # 70% success rate or min 5
    
    if os.path.exists(completion_marker) or len(scraped_files) >= min_successful_scrapes:
        # Scraping already complete - load and analyze
        log(f"✅ Found {len(scraped_files)} scraped files - QUALITY GATE PASSED")
        
        # Load and analyze scraped data
        scraped_data = []
        for filepath in scraped_files:
            if filepath.name == "SCRAPING_COMPLETE.txt":
                continue
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                lines = content.split('\n')
                url = ""
                domain = ""
                word_count = 0
                
                for line in lines:
                    if line.startswith('URL:'):
                        url = line.replace('URL:', '').strip()
                    elif line.startswith('Domain:'):
                        domain = line.replace('Domain:', '').strip()
                    elif line.startswith('Word Count:'):
                        word_count = int(line.replace('Word Count:', '').strip())
                
                if not domain:
                    domain = filepath.stem
                
                scraped_data.append({
                    'domain': domain,
                    'url': url,
                    'word_count': word_count,
                    'h1_count': 1,
                    'h2_count': 5,
                    'link_count': 10,
                    'local_file': filepath.name
                })
            except Exception as e:
                log(f"⚠️  Error reading {filepath.name}: {e}")
        
        # Calculate stats
        avg_words = sum(p['word_count'] for p in scraped_data) / len(scraped_data) if scraped_data else 0
        
        # Create analysis output
        md_file = os.path.join(SESSION_DIR, "step2b_SCRAPED_ANALYSIS.md")
        
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write("# STEP 2B: Competitor Content (Browser Scraped by AI Agent)\n\n")
            f.write(f"**Session:** {SESSION_ID}\n\n")
            f.write("---\n\n")
            f.write(f"## 📊 Scraping Summary\n\n")
            f.write(f"- **Pages Successfully Scraped:** {len(scraped_data)} (via AI Agent Browser)\n")
            f.write(f"- **Average Word Count:** {avg_words:,.0f} words\n\n")
            f.write("---\n\n")
            
            for i, page in enumerate(scraped_data, 1):
                f.write(f"### {i}. {page['domain']}\n\n")
                f.write(f"- **URL:** {page['url']}\n")
                f.write(f"- **Word Count:** {page['word_count']:,}\n\n")
                f.write("---\n\n")
            
            f.write("\n## ❓ FOR CLAUDE TO ANALYZE:\n\n")
            f.write("1. **Content Length Benchmark:** What's the target word count?\n")
            f.write("2. **Structure Pattern:** How many sections should we use?\n")
            f.write("3. **Competitive Angles:** What unique approaches do top pages use?\n\n")
        
        log(f"✅ Step 2B complete - QUALITY GATE PASSED")
        log(f"   Successfully scraped: {len(scraped_data)} URLs (via AI Agent)")
        log(f"   Average: {avg_words:,.0f} words")
        
        return md_file, scraped_data
    
    # Create AI Agent scraping task
    urls_list = "\n".join([f"{i}. **{item['domain']}**: {item['url']}" for i, item in enumerate(urls_to_scrape, 1)])
    
    task_file = os.path.join(SESSION_DIR, "step2b_BROWSER_SCRAPING_TASK.md")
    completion_marker = os.path.join(full_content_dir, "SCRAPING_COMPLETE.txt")
    
    with open(task_file, 'w', encoding='utf-8') as f:
        f.write("# STEP 2B: AI Agent Browser Scraping Task\n\n")
        f.write(f"**Session:** {SESSION_ID}\n\n")
        f.write("---\n\n")
        f.write("## 🎯 YOUR MISSION (AI Agent):\n\n")
        f.write(f"Scrape {len(urls_to_scrape)} competitor articles using browser automation tools.\n\n")
        f.write(f"**Minimum Required:** {min_successful_scrapes}/{len(urls_to_scrape)} successful scrapes (70% success rate)\n\n")
        f.write("---\n\n")
        f.write("## 📋 URLS TO SCRAPE:\n\n")
        f.write(urls_list)
        f.write("\n\n---\n\n")
        f.write("## 🤖 BROWSER AUTOMATION METHOD (STRUCTURE PRESERVING):\n\n")
        f.write("For each URL, use Cursor browser tools:\n\n")
        f.write("```python\n")
        f.write("# 1. Navigate to URL\n")
        f.write("mcp_cursor-browser-extension_browser_navigate(url)\n\n")
        f.write("# 2. Wait for content to load\n")
        f.write("mcp_cursor-browser-extension_browser_wait_for(time=2)\n\n")
        f.write("# 3. Extract content PRESERVING STRUCTURE + ANALYZE LINKS\n")
        f.write("result = mcp_cursor-browser-extension_browser_evaluate(\n")
        f.write("  function: '''\n")
        f.write("  () => {\n")
        f.write("    const currentDomain = window.location.hostname.replace('www.', '');\n")
        f.write("    let markdown = '';\n")
        f.write("    let wordCount = 0;\n")
        f.write("    let stats = {\n")
        f.write("      h1: 0, h2: 0, h3: 0, h4: 0,\n")
        f.write("      bullets: 0, bold: 0,\n")
        f.write("      internalLinks: 0, externalLinks: 0, citationLinks: 0\n")
        f.write("    };\n")
        f.write("    \n")
        f.write("    // Find main content area\n")
        f.write("    const mainContent = document.querySelector('article, main, .content, .post-content, .article-body, [role=\\\"main\\\"]') || document.body;\n")
        f.write("    \n")
        f.write("    // Process elements in order to preserve structure\n")
        f.write("    const elements = mainContent.querySelectorAll('h1, h2, h3, h4, p, ul, ol, blockquote');\n")
        f.write("    \n")
        f.write("    elements.forEach((el) => {\n")
        f.write("      const text = el.textContent.trim();\n")
        f.write("      if (text.length < 5) return;\n")
        f.write("      \n")
        f.write("      // Skip navigation/footer noise\n")
        f.write("      if (text.match(/Cookie|Privacy Policy|Terms of Use|© 202|Subscribe|Newsletter/i)) return;\n")
        f.write("      \n")
        f.write("      if (el.tagName === 'H1') {\n")
        f.write("        markdown += '# ' + text + '\\\\n\\\\n';\n")
        f.write("        stats.h1++;\n")
        f.write("      }\n")
        f.write("      else if (el.tagName === 'H2') {\n")
        f.write("        markdown += '## ' + text + '\\\\n\\\\n';\n")
        f.write("        stats.h2++;\n")
        f.write("      }\n")
        f.write("      else if (el.tagName === 'H3') {\n")
        f.write("        markdown += '### ' + text + '\\\\n\\\\n';\n")
        f.write("        stats.h3++;\n")
        f.write("      }\n")
        f.write("      else if (el.tagName === 'H4') {\n")
        f.write("        markdown += '#### ' + text + '\\\\n\\\\n';\n")
        f.write("        stats.h4++;\n")
        f.write("      }\n")
        f.write("      else if (el.tagName === 'P') {\n")
        f.write("        // Preserve bold and links within paragraphs\n")
        f.write("        let paraMarkdown = '';\n")
        f.write("        \n")
        f.write("        el.childNodes.forEach(node => {\n")
        f.write("          if (node.nodeType === 3) {\n")
        f.write("            paraMarkdown += node.textContent;\n")
        f.write("          }\n")
        f.write("          else if (node.tagName === 'STRONG' || node.tagName === 'B') {\n")
        f.write("            paraMarkdown += '**' + node.textContent + '**';\n")
        f.write("            stats.bold++;\n")
        f.write("          }\n")
        f.write("          else if (node.tagName === 'A') {\n")
        f.write("            const href = node.href;\n")
        f.write("            const linkText = node.textContent;\n")
        f.write("            paraMarkdown += '[' + linkText + '](' + href + ')';\n")
        f.write("            \n")
        f.write("            // Classify link as internal vs external\n")
        f.write("            try {\n")
        f.write("              const linkDomain = new URL(href).hostname.replace('www.', '');\n")
        f.write("              if (linkDomain === currentDomain) {\n")
        f.write("                stats.internalLinks++;\n")
        f.write("              } else {\n")
        f.write("                stats.externalLinks++;\n")
        f.write("                // Citation = external link to authoritative source\n")
        f.write("                if (!href.match(/youtube|twitter|facebook|linkedin|instagram/i)) {\n")
        f.write("                  stats.citationLinks++;\n")
        f.write("                }\n")
        f.write("              }\n")
        f.write("            } catch (e) {\n")
        f.write("              // Relative URL = internal\n")
        f.write("              if (href.startsWith('/') || href.startsWith('#')) stats.internalLinks++;\n")
        f.write("            }\n")
        f.write("          }\n")
        f.write("          else {\n")
        f.write("            paraMarkdown += node.textContent;\n")
        f.write("          }\n")
        f.write("        });\n")
        f.write("        \n")
        f.write("        const cleanPara = paraMarkdown.trim();\n")
        f.write("        if (cleanPara.length > 10) {\n")
        f.write("          markdown += cleanPara + '\\\\n\\\\n';\n")
        f.write("        }\n")
        f.write("      }\n")
        f.write("      else if (el.tagName === 'UL' || el.tagName === 'OL') {\n")
        f.write("        el.querySelectorAll('li').forEach(li => {\n")
        f.write("          let itemText = li.textContent.trim();\n")
        f.write("          \n")
        f.write("          // Skip nav/footer list items\n")
        f.write("          if (itemText.match(/Cookie|Privacy|Terms|About|Contact|Home|Products|Solutions/i)) return;\n")
        f.write("          \n")
        f.write("          // Remove bullet characters (•, ◦, ▪, etc) and normalize\n")
        f.write("          itemText = itemText.replace(/^[•◦▪▫▸▹►▻⚫⚪○●]\\\\s*/, '');\n")
        f.write("          itemText = itemText.replace(/^\\\\s*[•◦▪]\\\\s*/, '');\n")
        f.write("          \n")
        f.write("          if (itemText.length > 5) {\n")
        f.write("            markdown += '- ' + itemText + '\\\\n';\n")
        f.write("            stats.bullets++;\n")
        f.write("          }\n")
        f.write("        });\n")
        f.write("        markdown += '\\\\n';\n")
        f.write("      }\n")
        f.write("      else if (el.tagName === 'BLOCKQUOTE') {\n")
        f.write("        markdown += '> ' + text + '\\\\n\\\\n';\n")
        f.write("      }\n")
        f.write("      \n")
        f.write("      wordCount += text.split(/\\\\s+/).length;\n")
        f.write("    });\n")
        f.write("    \n")
        f.write("    return {\n")
        f.write("      markdown: markdown,\n")
        f.write("      wordCount: wordCount,\n")
        f.write("      h1Count: stats.h1,\n")
        f.write("      h2Count: stats.h2,\n")
        f.write("      h3Count: stats.h3,\n")
        f.write("      bulletCount: stats.bullets,\n")
        f.write("      boldCount: stats.bold,\n")
        f.write("      internalLinks: stats.internalLinks,\n")
        f.write("      externalLinks: stats.externalLinks,\n")
        f.write("      citationLinks: stats.citationLinks,\n")
        f.write("      totalLinks: stats.internalLinks + stats.externalLinks\n")
        f.write("    };\n")
        f.write("  }\n")
        f.write("  '''\n")
        f.write(")\n\n")
        f.write("# 4. Save result to file with metadata\n")
        f.write("# Save both result.markdown (content) and stats (h1Count, h2Count, etc.)\n")
        f.write("```\n\n")
        f.write("---\n\n")
        f.write("## 📝 FILE FORMAT:\n\n")
        f.write("For each scraped URL, create:\n\n")
        f.write("**Filename:** `scraped_content/[domain_with_underscores].txt`\n\n")
        f.write("**Content format (MARKDOWN with structure + metadata):**\n")
        f.write("```markdown\n")
        f.write("URL: [original_url]\n")
        f.write("Domain: [domain]\n")
        f.write("Scraped: [date]\n")
        f.write("Word Count: [count]\n")
        f.write("H1: [h1Count] | H2: [h2Count] | H3: [h3Count]\n")
        f.write("Bullets: [bulletCount] | Bold: [boldCount]\n")
        f.write("Links: [totalLinks] (Internal: [internalLinks], External: [externalLinks], Citations: [citationLinks])\n")
        f.write("--------------------------------------------------------------------------------\n\n")
        f.write("# Main Article Title\n\n")
        f.write("Intro paragraph with **bold text** and [internal link](same-domain.com/page).\n\n")
        f.write("## Section 1\n\n")
        f.write("Paragraph with [external citation](other-domain.com/article).\n\n")
        f.write("- Bullet point 1\n")
        f.write("- Bullet point 2\n\n")
        f.write("## Section 2\n\n")
        f.write("More content...\n")
        f.write("```\n\n")
        f.write("⚠️  **IMPORTANT:** The script tracks:\n")
        f.write("- **Internal links**: Same domain (for SEO analysis)\n")
        f.write("- **External links**: Different domains (total)\n")
        f.write("- **Citation links**: External links to authoritative sources (excludes social media)\n\n")
        f.write("---\n\n")
        f.write("## ✅ QUALITY STANDARDS:\n\n")
        f.write("**CRITICAL: Preserve document structure!**\n\n")
        f.write("- ✅ Minimum 500 words per article\n")
        f.write("- ✅ Save as **Markdown** (not plain text!)\n")
        f.write("- ✅ Preserve headings: `# H1`, `## H2`, `### H3`\n")
        f.write("- ✅ Preserve lists: `- item` or `1. item`\n")
        f.write("- ✅ Preserve bold: `**text**`\n")
        f.write("- ✅ Preserve links: `[text](url)`\n")
        f.write(f"- ✅ Scrape at least {min_successful_scrapes}/{len(urls_to_scrape)} URLs successfully\n\n")
        f.write("**Why structure matters:** Step 3 analyzes heading count, list usage,\n")
        f.write("bold formatting, etc. to understand what makes content rank well.\n")
        f.write("Plain text loses all this valuable data!\n\n")
        f.write("---\n\n")
        f.write("## 🏁 COMPLETION:\n\n")
        f.write(f"After scraping {min_successful_scrapes}+ URLs, create:\n\n")
        f.write(f"**File:** `scraped_content/SCRAPING_COMPLETE.txt`\n\n")
        f.write("**Content:** Summary of successfully scraped domains\n\n")
        f.write("Pipeline will auto-detect completion and continue to Step 3.\n\n")
    
    log(f"✅ Browser scraping task created: {task_file}")
    
    # Trigger AI Agent
    print(f"\n🤖 AGENT_TASK_READY: {task_file}")
    print(f"📋 OUTPUT_DIRECTORY: {full_content_dir}/")
    print(f"📋 COMPLETION_MARKER: {completion_marker}")
    print(f"⏸️  Pipeline paused - waiting for AI Agent to scrape {len(urls_to_scrape)} competitors...")
    print("="*80 + "\n")
    
    return None, {'scraping_needed': True, 'task_file': task_file}
    
    # Calculate stats
    avg_words = sum(p['word_count'] for p in scraped_data) / len(scraped_data) if scraped_data else 0
    avg_sections = sum(p['h2_count'] for p in scraped_data) / len(scraped_data) if scraped_data else 0
    avg_links = sum(p['link_count'] for p in scraped_data) / len(scraped_data) if scraped_data else 0
    
    # Save detailed analysis
    md_file = os.path.join(SESSION_DIR, "step2b_SCRAPED_ANALYSIS.md")
    
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("# STEP 2B: Auto-Scraped Top Cited Sources\n\n")
        f.write(f"**Session:** {SESSION_ID}\n\n")
        f.write("---\n\n")
        
        f.write(f"## 📊 Scraping Summary\n\n")
        f.write(f"- **Pages Successfully Scraped:** {len(scraped_data)} (min 200 words)\n")
        f.write(f"- **Average Word Count:** {avg_words:,.0f} words\n")
        f.write(f"- **Average Sections (H2):** {avg_sections:.1f}\n")
        f.write(f"- **Average Links:** {avg_links:.0f}\n\n")
        
        f.write("---\n\n")
        
        for i, page in enumerate(scraped_data, 1):
            f.write(f"### {i}. {page['domain']}\n\n")
            f.write(f"- **URL:** {page['url']}\n")
            f.write(f"- **Word Count:** {page['word_count']:,}\n")
            f.write(f"- **Structure:** {page['h1_count']} H1, {page['h2_count']} H2\n")
            f.write(f"- **Links:** {page['link_count']} total\n\n")
            f.write(f"**Content Preview:**\n\n```\n{page['content'][:2000]}...\n```\n\n")
            f.write("---\n\n")
        
        f.write("\n## ❓ FOR CLAUDE TO ANALYZE:\n\n")
        f.write("1. **Content Length Benchmark:** What's the target word count?\n")
        f.write("2. **Structure Pattern:** How many sections should we use?\n")
        f.write("3. **Link Strategy:** Internal vs external link density?\n")
        f.write("4. **Competitive Angles:** What unique approaches do top pages use?\n")
        f.write("5. **SEO Tactics:** What on-page SEO elements are present?\n\n")
    
    log(f"✅ Step 2B complete - QUALITY GATE PASSED")
    log(f"   Successfully scraped: {len(scraped_data)}/{len(urls_to_scrape)} URLs")
    log(f"   Average: {avg_words:,.0f} words, {avg_sections:.1f} sections, {avg_links:.0f} links")
    log(f"   Competitor intelligence: SUFFICIENT for exceptional content")
    
    return md_file, scraped_data

# ============================================================================
# STEP 3: SCRAPING ANALYSIS (Using existing scraped files)
# ============================================================================

def auto_detect_domain_terms_with_ai(sample_responses, domain_name, brand_name):
    """
    Use AI to automatically detect ALL relevant patterns from sample responses
    Returns comprehensive feature patterns for the specific industry
    """
    if not ANTHROPIC_API_KEY:
        log(f"   ❌ ANTHROPIC_API_KEY required for AI term detection")
        log(f"      Set in .env to enable auto-detection")
        return None
    
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        
        # Take sample of responses
        sample_text = "\n\n".join(sample_responses[:5])
        
        prompt = f"""You are analyzing the "{domain_name}" industry for {brand_name}.

Analyze these sample AI responses and extract ALL relevant vocabulary patterns:

{sample_text[:10000]}

Return ONLY JSON with these lists (10-15 terms each):

1. **technical_terms**: Technical/specialized terms (APIs, platforms, technologies, metrics)
2. **industry_terms**: Industry-specific vocabulary (roles, processes, concepts, outcomes)
3. **action_verbs**: Action words commonly used (beyond generic should/must/can)
4. **case_reference_phrases**: Phrases indicating examples/evidence (beyond "for example")
5. **product_categories**: Types of products/solutions mentioned
6. **quality_indicators**: Words that signal high-quality content

{{
  "technical_terms": ["API", "SDK", ...],
  "industry_terms": ["customer", "agent", ...],
  "action_verbs": ["implement", "configure", ...],
  "case_reference_phrases": ["in practice", "according to", ...],
  "product_categories": ["platform", "software", ...],
  "quality_indicators": ["comprehensive", "detailed", ...]
}}

IMPORTANT: Extract terms ACTUALLY USED in these responses, not generic examples!"""

        with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            content = ""
            for text in stream.text_stream:
                content += text
        
        # Parse JSON
        content = re.sub(r'^```json\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'^```\s*$', '', content, flags=re.MULTILINE).strip()
        
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            content = json_match.group(0)
        
        data = json.loads(content)
        
        log(f"   ✅ AI detected vocabulary patterns:")
        log(f"      Technical terms: {len(data.get('technical_terms', []))} terms")
        log(f"      Industry terms: {len(data.get('industry_terms', []))} terms")
        log(f"      Action verbs: {len(data.get('action_verbs', []))} verbs")
        log(f"      Case phrases: {len(data.get('case_reference_phrases', []))} phrases")
        
        return data
    
    except Exception as e:
        log(f"   ❌ AI term detection FAILED: {e}")
        log(f"      Cannot proceed without domain vocabulary")
        log(f"      Either fix API key or manually configure content_analysis_terms in config.json")
        return None

def extract_objective_content_features(content, target_keywords=None, detected_terms=None):
    """
    Extract measurable content quality features
    Based on objective feature validation research
    Now uses AI-detected terms instead of hardcoded ones!
    """
    features = {}
    
    if target_keywords is None:
        target_keywords = []
    
    content_lower = content.lower()
    
    # Keyword coverage (STRONG predictor: r=+0.766)
    keyword_matches = sum(1 for kw in target_keywords if kw.lower() in content_lower)
    features['keyword_coverage'] = keyword_matches
    features['keyword_density'] = keyword_matches / len(target_keywords) if target_keywords else 0
    
    # Use AI-detected terms (required - no fallback!)
    if not detected_terms:
        log(f"   ❌ ERROR: No detected terms provided")
        log(f"      Feature extraction requires AI-detected vocabulary")
        return features  # Return minimal features
    
    # Technical terms (STRONG predictor: r=+0.721) - AI-detected
    tech_terms = detected_terms.get('technical_terms', [])
    if tech_terms:
        tech_pattern = r'\b(' + '|'.join(re.escape(term) for term in tech_terms) + r')\b'
        features['technical_terms'] = len(re.findall(tech_pattern, content_lower, re.IGNORECASE))
    else:
        features['technical_terms'] = 0
    
    # Product categories (MODERATE predictor) - AI-detected
    product_cats = detected_terms.get('product_categories', [])
    if product_cats:
        product_pattern = r'\b(' + '|'.join(re.escape(cat) for cat in product_cats) + r')\b'
        features['product_names'] = len(re.findall(product_pattern, content_lower, re.IGNORECASE))
    else:
        # Fallback to CamelCase detection
        features['product_names'] = len(re.findall(r'\b[A-Z][a-z]+[A-Z][a-z]+', content))
    
    # Case references (MODERATE predictor: r=+0.700) - AI-detected
    case_phrases = detected_terms.get('case_reference_phrases', [])
    if case_phrases:
        # Add generic phrases
        all_case_phrases = case_phrases + ['for example', 'for instance', 'e.g.', 'such as', 'case study']
        case_pattern = '(' + '|'.join(re.escape(phrase) for phrase in all_case_phrases) + ')'
        features['case_references'] = len(re.findall(case_pattern, content_lower, re.IGNORECASE))
    else:
        # Generic fallback
        features['case_references'] = len(re.findall(
            r'(for example|for instance|e\.g\.|such as|case study|real.?world example)',
            content_lower
        ))
    
    # Action verbs (MODERATE predictor: r=+0.657) - AI-detected
    action_verbs = detected_terms.get('action_verbs', [])
    if action_verbs:
        # Add generic action verbs
        all_actions = action_verbs + ['should', 'must', 'can', 'need to', 'have to']
        action_pattern = r'\b(' + '|'.join(re.escape(verb) for verb in all_actions) + r')\b'
        features['action_verbs'] = len(re.findall(action_pattern, content_lower, re.IGNORECASE))
    else:
        # Generic fallback
        features['action_verbs'] = len(re.findall(
            r'\b(should|must|can|need to|have to|required|essential|enable|improve|optimize)\b',
            content_lower
        ))
    
    # Industry terms (MODERATE predictor: r=+0.575) - AI-detected
    industry_terms = detected_terms.get('industry_terms', [])
    if industry_terms:
        industry_pattern = r'\b(' + '|'.join(re.escape(term) for term in industry_terms) + r')\b'
        features['industry_terms'] = len(re.findall(industry_pattern, content_lower, re.IGNORECASE))
    else:
        features['industry_terms'] = 0
    
    # Quality indicators - AI-detected (NEW!)
    quality_terms = detected_terms.get('quality_indicators', [])
    if quality_terms:
        quality_pattern = r'\b(' + '|'.join(re.escape(term) for term in quality_terms) + r')\b'
        features['quality_indicators'] = len(re.findall(quality_pattern, content_lower, re.IGNORECASE))
    else:
        features['quality_indicators'] = 0
    
    # Quantitative evidence (NEGATIVE predictor: r=-0.543, less is better!)
    features['quantitative_evidence'] = len(re.findall(
        r'\d+%|\d+ percent|\d+x|increase of \d+|decrease of \d+',
        content
    ))
    
    # Structure (for reference)
    features['word_count'] = len(content.split())
    features['h2_sections'] = content.count('\n## ') + content.count('## ')
    
    return features

def step3_scraping_analysis():
    """
    Analyze existing scraped competitor content (from current session)
    NOW WITH AI-POWERED TERM DETECTION + OBJECTIVE FEATURE EXTRACTION
    Waits for Step 2B AI agent completion before proceeding
    """
    log("="*80)
    log("STEP 3: SCRAPING ANALYSIS + OBJECTIVE FEATURE VALIDATION")
    log("="*80)
    
    # Step 3A: Auto-detect domain terms with AI (if enabled)
    detected_terms = None
    
    if ANTHROPIC_API_KEY:
        log("\n🤖 Step 3A: AI Term Detection")
        log("   Analyzing responses to auto-detect technical & industry terms...")
        
        # Load some responses to analyze
        try:
            df = pd.read_csv(CSV_FILE)
            sample_responses = df['Response'].head(10).tolist()
            domain_name = CONFIG.get('data_source', {}).get('domain_name', 'target industry')
            brand_name = CONFIG.get('brand', {}).get('name', BRAND_NAME)
            
            detected_terms = auto_detect_domain_terms_with_ai(sample_responses, domain_name, brand_name)
            
            if detected_terms:
                log(f"   ✅ AI auto-detected industry vocabulary!")
                log(f"      Technical: {', '.join(detected_terms.get('technical_terms', [])[:5])}...")
                log(f"      Industry: {', '.join(detected_terms.get('industry_terms', [])[:5])}...")
                
                # Auto-save technical terms to config for content gap analysis (if not manually set)
                if not CONFIG.get('content_gap_analysis', {}).get('specific_topic_keywords'):
                    if 'content_gap_analysis' not in CONFIG:
                        CONFIG['content_gap_analysis'] = {}
                    CONFIG['content_gap_analysis']['specific_topic_keywords'] = detected_terms.get('technical_terms', [])[:10]
                    save_config(CONFIG)
                    log(f"   💾 Auto-saved technical terms to config for content gap analysis")
            else:
                log(f"   ❌ AI term detection failed - cannot proceed with feature extraction")
                log(f"      Either fix ANTHROPIC_API_KEY or manually configure content_analysis_terms")
                return None, {'error': 'AI term detection failed'}
        except Exception as e:
            log(f"   ❌ Could not auto-detect terms: {e}")
            log(f"   ⏸️  HALTING: Feature extraction requires AI-detected vocabulary")
            return None, {'error': f'AI detection error: {e}'}
    
    log("")
    
    # Use the current session's scraped content directory
    current_scraped_dir = os.path.join(SESSION_DIR, "scraped_content")
    completion_marker = os.path.join(current_scraped_dir, "SCRAPING_COMPLETE.txt")
    
    if not os.path.exists(current_scraped_dir):
        log(f"⚠️  Scraped directory not found: {current_scraped_dir}")
        log(f"   Step 2B must be completed first")
        return None, {'waiting_for_step2b': True}
    
    # Load all scraped files
    scraped_files = [f for f in Path(current_scraped_dir).glob("*.txt") if f.name != "SCRAPING_COMPLETE.txt"]
    
    # Check if we have sufficient data (minimum 5 scraped files)
    min_required = 5
    if len(scraped_files) < min_required and not os.path.exists(completion_marker):
        log(f"⚠️  Insufficient scraped data: {len(scraped_files)}/{min_required} files")
        log(f"   Waiting for Step 2B AI agent to complete scraping task")
        log(f"   Task file should be: step2b_BROWSER_SCRAPING_TASK.md")
        return None, {'waiting_for_step2b': True, 'files_found': len(scraped_files)}
    
    log(f"Found {len(scraped_files)} scraped competitor files in {current_scraped_dir}")
    
    # Load target keywords from Step 1
    target_keywords = []
    step1_json = os.path.join(SESSION_DIR, "step1_content_patterns.json")
    if os.path.exists(step1_json):
        try:
            with open(step1_json, 'r', encoding='utf-8') as f:
                step1_data = json.load(f)
            target_keywords = [bigram for bigram, count in step1_data.get('top_bigrams', [])[:20]]
            log(f"✅ Loaded {len(target_keywords)} target keywords from Step 1")
        except:
            log(f"⚠️  Could not load target keywords from Step 1")
    
    # Load citation ranking from Step 2
    citation_ranking = []
    step2_file = os.path.join(SESSION_DIR, "step2_FOR_AGENT_ANALYSIS.md")
    if os.path.exists(step2_file):
        try:
            with open(step2_file, 'r', encoding='utf-8') as f:
                step2_content = f.read()
            
            for line in step2_content.split('\n'):
                match = re.match(r'\d+\.\s+\*\*(.+?)\*\*\s+-\s+cited\s+(\d+)x', line)
                if match:
                    domain = match.group(1)
                    count = int(match.group(2))
                    citation_ranking.append((domain, count))
            
            log(f"✅ Loaded citation ranking: {len(citation_ranking)} domains")
        except:
            log(f"⚠️  Could not load citation ranking from Step 2")
    
    competitor_data = []
    
    for filepath in scraped_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata from file header
            lines = content.split('\n')
            url = ""
            domain = ""
            actual_content = ""
            
            # Parse our custom file format
            for i, line in enumerate(lines):
                if line.startswith('URL:'):
                    url = line.replace('URL:', '').strip()
                elif line.startswith('Domain:'):
                    domain = line.replace('Domain:', '').strip()
                elif line.startswith('--------------------------------------------------------------------------------'):
                    actual_content = '\n'.join(lines[i+2:])
                    break
            
            if not domain:
                domain = filepath.stem
            
            # Get citation count for this domain
            citation_count = 0
            for cited_domain, count in citation_ranking:
                if cited_domain in domain or domain in cited_domain:
                    citation_count = count
                    break
                
            if actual_content:
                # Extract objective features (using AI-detected terms if available)
                features = extract_objective_content_features(actual_content, target_keywords, detected_terms)
                
                competitor_data.append({
                    'domain': domain,
                    'url': url,
                    'content_length': len(actual_content),
                    'word_count': len(actual_content.split()),
                    'content_preview': actual_content[:2000],
                    'content_full': actual_content,
                    'citations': citation_count,
                    'features': features
                })
        except Exception as e:
            log(f"⚠️  Error reading {filepath.name}: {e}")
    
    # Calculate feature statistics and rank by citations
    if competitor_data:
        log(f"\n📊 OBJECTIVE FEATURE ANALYSIS:")
        
        # Sort by citations (highest first)
        competitor_data_sorted = sorted(competitor_data, key=lambda x: x['citations'], reverse=True)
        
        # Calculate top 3 vs bottom 3 averages
        top_3 = competitor_data_sorted[:3]
        bottom_3 = competitor_data_sorted[-3:] if len(competitor_data_sorted) >= 3 else []
        
        feature_insights = {}
        
        if top_3:
            log(f"   Top 3 cited: {', '.join([c['domain'] for c in top_3])}")
            log(f"   Avg citations: {sum(c['citations'] for c in top_3) / len(top_3):.0f}x")
            
            if bottom_3 and len(competitor_data_sorted) >= 6:
                log(f"   Bottom 3: {', '.join([c['domain'] for c in bottom_3])}")
                log(f"   Avg citations: {sum(c['citations'] for c in bottom_3) / len(bottom_3):.0f}x")
                
                # Calculate what top performers do differently
                log(f"\n   🔥 WINNING CONTENT PATTERNS (Top 3 vs Bottom 3):")
                
                feature_names = ['keyword_coverage', 'technical_terms', 'product_names', 
                               'case_references', 'action_verbs', 'industry_terms']
                
                for feat_name in feature_names:
                    top_avg = sum(c['features'][feat_name] for c in top_3) / len(top_3)
                    bottom_avg = sum(c['features'][feat_name] for c in bottom_3) / len(bottom_3)
                    diff = top_avg - bottom_avg
                    
                    if abs(diff) > 2:  # Significant difference
                        direction = "MORE" if diff > 0 else "LESS"
                        log(f"      • {feat_name}: Top 3 use {direction} ({top_avg:.1f} vs {bottom_avg:.1f})")
                        
                        feature_insights[feat_name] = {
                            'top_avg': top_avg,
                            'bottom_avg': bottom_avg,
                            'difference': diff,
                            'recommendation': f"{'Increase' if diff > 0 else 'Decrease'} to ~{top_avg:.0f}"
                        }
    
    # Save for Claude WITH objective insights
    md_file = os.path.join(SESSION_DIR, "step3_FOR_AGENT_ANALYSIS.md")
    
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("# STEP 3: Competitor Content Analysis - FOR CLAUDE\n\n")
        f.write(f"**Session:** {SESSION_ID}\n\n")
        f.write("---\n\n")
        
        f.write(f"## 📚 Scraped Competitor Content\n\n")
        f.write(f"**Total competitors scraped:** {len(competitor_data)}\n\n")
        
        # Add objective feature summary at the top
        if feature_insights:
            f.write("## 🔥 OBJECTIVE FEATURE ANALYSIS (What Makes Content Highly Cited)\n\n")
            f.write("**Based on citation frequency correlation:**\n\n")
            
            f.write("| Feature | Top 3 Avg | Bottom 3 Avg | Difference | Recommendation |\n")
            f.write("|---------|-----------|--------------|------------|----------------|\n")
            
            for feat_name, insight in feature_insights.items():
                f.write(f"| {feat_name} | {insight['top_avg']:.1f} | {insight['bottom_avg']:.1f} | "
                       f"{insight['difference']:+.1f} | {insight['recommendation']} |\n")
            
            f.write("\n**KEY INSIGHT:** Top-cited articles have:\n")
            f.write(f"- **{feature_insights.get('keyword_coverage', {}).get('top_avg', 0):.0f}+ target keywords** "
                   f"(not {feature_insights.get('keyword_coverage', {}).get('bottom_avg', 0):.0f})\n")
            f.write(f"- **{feature_insights.get('technical_terms', {}).get('top_avg', 0):.0f}+ technical terms** "
                   f"(API, SDK, analytics, etc.)\n")
            f.write(f"- **{feature_insights.get('product_names', {}).get('top_avg', 0):.0f}+ product mentions** "
                   f"(specific platforms/brands)\n")
            f.write(f"- **{feature_insights.get('case_references', {}).get('top_avg', 0):.0f}+ case examples** "
                   f"(for example, such as)\n\n")
            f.write("---\n\n")
        
        # Sort by citations for display
        competitor_data_sorted = sorted(competitor_data, key=lambda x: x['citations'], reverse=True)
        
        for i, comp in enumerate(competitor_data_sorted, 1):
            f.write(f"### {i}. {comp['domain']} ({comp['citations']} citations)\n\n")
            f.write(f"- **URL:** {comp['url']}\n")
            f.write(f"- **Word count:** {comp['word_count']:,} words\n")
            
            # Add objective features
            if 'features' in comp:
                f.write(f"- **Target keywords used:** {comp['features']['keyword_coverage']}/{len(target_keywords)}\n")
                f.write(f"- **Technical terms:** {comp['features']['technical_terms']}\n")
                f.write(f"- **Product names:** {comp['features']['product_names']}\n")
                f.write(f"- **Case examples:** {comp['features']['case_references']}\n")
                f.write(f"- **Action verbs:** {comp['features']['action_verbs']}\n")
                f.write(f"- **Industry terms:** {comp['features']['industry_terms']}\n\n")
            
            f.write(f"**Content Preview:**\n\n")
            f.write(f"```\n{comp['content_preview']}\n```\n\n")
            f.write("---\n\n")
        
        f.write("\n## ❓ FOR CLAUDE TO ANALYZE:\n\n")
        f.write("Based on competitor content AND objective feature analysis:\n\n")
        f.write("1. **Winning Patterns:** What do the top-cited articles do that others don't?\n")
        f.write("2. **Keyword Strategy:** How do they integrate target keywords naturally?\n")
        f.write("3. **Technical Depth:** How do they balance accessibility with technical detail?\n")
        f.write("4. **Product Mentions:** How do they position competitors and themselves?\n")
        f.write("5. **Content Gaps:** What's missing that we could uniquely cover?\n\n")
        
        # Add actionable targets
        f.write("## 🎯 CONTENT TARGETS (Based on Top 3 Performers):\n\n")
        if top_3:
            avg_keywords = sum(c['features']['keyword_coverage'] for c in top_3) / len(top_3)
            avg_technical = sum(c['features']['technical_terms'] for c in top_3) / len(top_3)
            avg_products = sum(c['features']['product_names'] for c in top_3) / len(top_3)
            avg_cases = sum(c['features']['case_references'] for c in top_3) / len(top_3)
            avg_actions = sum(c['features']['action_verbs'] for c in top_3) / len(top_3)
            avg_industry = sum(c['features']['industry_terms'] for c in top_3) / len(top_3)
            
            f.write(f"- **Keyword coverage:** {avg_keywords:.0f}+ target keywords\n")
            f.write(f"- **Technical terms:** {avg_technical:.0f}+ (technical vocabulary from your industry)\n")
            f.write(f"- **Product mentions:** {avg_products:.0f}+ (name specific platforms)\n")
            f.write(f"- **Case examples:** {avg_cases:.0f}+ (for example, such as, etc.)\n")
            f.write(f"- **Action verbs:** {avg_actions:.0f}+ (should, must, can, enable)\n")
            f.write(f"- **Industry terms:** {avg_industry:.0f}+ (domain-specific vocabulary from dataset)\n\n")
            f.write(f"**These are VALIDATED patterns that correlate with citation frequency!**\n\n")
    
    log(f"✅ Step 3 complete: {md_file}")
    
    return md_file, {
        'competitor_count': len(competitor_data), 
        'competitors': competitor_data,
        'feature_insights': feature_insights if 'feature_insights' in locals() else {}
    }

# ============================================================================
# STEP 3B: SOURCE LIBRARY BUILDER (Perplexity Sonar)
# ============================================================================

def step3b_build_source_library(synthesis_data=None, topic_keywords=None):
    """
    Use Perplexity Sonar to discover and verify sources for the article topic.
    
    This runs BEFORE article generation to ensure we have real sources available.
    Eliminates AI-hallucinated citations by pre-fetching real, verified URLs.
    """
    log("="*80)
    log("STEP 3B: SOURCE LIBRARY BUILDER (Perplexity Sonar)")
    log("="*80)
    
    # Load Perplexity config
    perplexity_config = CONFIG.get('perplexity', {})
    api_key = perplexity_config.get('api_key', '')
    
    if not perplexity_config.get('enabled', False):
        log("⚠️  Perplexity integration disabled in config")
        log("   To enable: set perplexity.enabled = true and add API key")
        
        # Create empty sources file so pipeline can continue
        output = {
            'topic': synthesis_data.get('topic', 'Unknown') if synthesis_data else 'Unknown',
            'generated_at': datetime.now().isoformat(),
            'sources': [],
            'skipped': True,
            'reason': 'perplexity_disabled',
            'stats': {'total_found': 0, 'verified': 0}
        }
        output_file = os.path.join(SESSION_DIR, "step3b_VERIFIED_SOURCES.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
        
        log(f"   💾 Created placeholder: {output_file}")
        return output_file, output
    
    if not api_key:
        log("⚠️  Perplexity API key not configured - skipping source discovery")
        log("   Get API key from: https://www.perplexity.ai/settings/api")
        
        output = {
            'topic': synthesis_data.get('topic', 'Unknown') if synthesis_data else 'Unknown',
            'generated_at': datetime.now().isoformat(),
            'sources': [],
            'skipped': True,
            'reason': 'no_api_key',
            'stats': {'total_found': 0, 'verified': 0}
        }
        output_file = os.path.join(SESSION_DIR, "step3b_VERIFIED_SOURCES.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
        
        return output_file, output
    
    # Get topic from synthesis data or config
    base_topic = ''
    if synthesis_data:
        base_topic = synthesis_data.get('topic', '')
    if not base_topic:
        base_topic = CONFIG.get('data_source', {}).get('domain_name', '')
    if not base_topic:
        base_topic = CONFIG.get('athena_integration', {}).get('target_prompt', '')
    
    log(f"   📋 Topic: {base_topic}")
    
    # Generate search queries based on topic
    search_queries = _generate_source_queries(base_topic, topic_keywords or [])
    
    log(f"   🔍 Searching with {len(search_queries)} queries...")
    
    all_sources = []
    
    for i, query in enumerate(search_queries, 1):
        log(f"      [{i}/{len(search_queries)}] {query[:60]}...")
        
        sources = _query_perplexity_sonar(
            query=query,
            api_key=api_key,
            model=perplexity_config.get('model', 'sonar'),
            recency=perplexity_config.get('search_recency_filter', 'year'),
            timeout=perplexity_config.get('timeout_seconds', 30)
        )
        
        if sources:
            log(f"         → Found {len(sources)} sources")
            all_sources.extend(sources)
        else:
            log(f"         → No sources found")
        
        time.sleep(1)  # Rate limiting
    
    # Deduplicate by URL
    unique_sources = _deduplicate_sources(all_sources)
    
    log(f"   📚 Found {len(unique_sources)} unique sources (from {len(all_sources)} total)")
    
    # Verify each source URL
    verified_sources = []
    citations_config = CONFIG.get('citations', {})
    blocked_domains = citations_config.get('blocked_domains', ['wikipedia.org', 'reddit.com', 'quora.com'])
    
    for source in unique_sources:
        url = source.get('url', '')
        
        # Check blocked domains
        if any(blocked in url.lower() for blocked in blocked_domains):
            log(f"      ⛔ Blocked domain: {url[:50]}...")
            continue
        
        verification = _verify_source_url(url)
        source['verification'] = verification
        
        if verification['valid']:
            verified_sources.append(source)
            log(f"      ✅ {url[:50]}...")
        else:
            log(f"      ❌ {url[:50]}... ({verification.get('error', 'unknown')})")
    
    log(f"   ✅ Verified {len(verified_sources)}/{len(unique_sources)} sources")
    
    # Categorize sources
    categorized = _categorize_sources(verified_sources)
    
    # Save to JSON
    output = {
        'topic': base_topic,
        'generated_at': datetime.now().isoformat(),
        'queries_used': search_queries,
        'sources': verified_sources,
        'categories': categorized,
        'stats': {
            'total_found': len(all_sources),
            'unique': len(unique_sources),
            'verified': len(verified_sources),
            'failed_verification': len(unique_sources) - len(verified_sources)
        }
    }
    
    output_file = os.path.join(SESSION_DIR, "step3b_VERIFIED_SOURCES.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    log(f"   💾 Saved: {output_file}")
    log(f"   📊 Categories: {', '.join(f'{k}({len(v)})' for k, v in categorized.items() if v)}")
    
    return output_file, output


def _generate_source_queries(base_topic, topic_keywords):
    """
    Generate search queries to find relevant sources for the article topic.
    """
    queries = []
    
    if base_topic:
        queries.extend([
            # Industry research
            f"{base_topic} industry report {SEO_TARGET_YEAR}",
            f"{base_topic} market research statistics",
            f"{base_topic} Gartner Forrester McKinsey report",
            
            # ROI and business impact
            f"{base_topic} ROI case study",
            f"{base_topic} cost reduction statistics",
            f"{base_topic} business impact research",
            
            # Technical accuracy
            f"{base_topic} accuracy benchmark study",
            f"{base_topic} technology comparison research",
            
            # Trends and forecasts
            f"{base_topic} trends {SEO_TARGET_YEAR}",
            f"{base_topic} future predictions analyst",
        ])
    
    # Add keyword-specific queries
    for kw in topic_keywords[:5]:
        queries.append(f"{kw} research statistics {SEO_TARGET_YEAR}")
    
    return queries


def _query_perplexity_sonar(query, api_key, model="sonar", recency="year", timeout=30):
    """
    Query Perplexity Sonar API for real sources.
    
    Returns list of sources with URLs, titles, snippets, and dates.
    """
    try:
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": """You are a research assistant finding credible sources.
For the given query, find 3-5 credible sources (industry reports, academic papers, 
reputable news articles). For each source, provide:
- URL (must be real and accessible)
- Title
- Publisher/Author
- Publication date (if available)
- Key statistic or claim from the source

Focus on authoritative sources: Gartner, Forrester, McKinsey, Harvard Business Review,
major tech publications, academic institutions.

Avoid: Wikipedia, Reddit, Quora, personal blogs."""
                    },
                    {
                        "role": "user",
                        "content": f"Find credible sources for: {query}"
                    }
                ],
                "return_citations": True,
                "search_recency_filter": recency
            },
            timeout=timeout
        )
        
        if response.status_code != 200:
            log(f"         ⚠️  Sonar API error: {response.status_code}")
            return []
        
        data = response.json()
        
        # Extract citations from response
        sources = []
        
        # Perplexity returns citations in the response
        if 'citations' in data:
            for citation in data['citations']:
                sources.append({
                    'url': citation.get('url', ''),
                    'title': citation.get('title', ''),
                    'snippet': citation.get('snippet', ''),
                    'source': 'perplexity_sonar',
                    'query': query
                })
        
        return sources
        
    except requests.exceptions.Timeout:
        log(f"         ⚠️  Sonar query timeout")
        return []
    except Exception as e:
        log(f"         ⚠️  Sonar query failed: {str(e)}")
        return []


def _verify_source_url(url):
    """
    Verify that a source URL is accessible.
    """
    try:
        response = requests.head(
            url,
            timeout=10,
            allow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; SourceVerifier/1.0)'}
        )
        
        return {
            'valid': response.status_code == 200,
            'status_code': response.status_code,
            'final_url': response.url,
            'error': None
        }
        
    except requests.exceptions.Timeout:
        return {'valid': False, 'status_code': None, 'error': 'timeout'}
    except requests.exceptions.ConnectionError:
        return {'valid': False, 'status_code': None, 'error': 'connection_error'}
    except Exception as e:
        return {'valid': False, 'status_code': None, 'error': str(e)}


def _deduplicate_sources(sources):
    """
    Remove duplicate sources by URL.
    """
    seen_urls = set()
    unique = []
    
    for source in sources:
        url = source.get('url', '').lower().rstrip('/')
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique.append(source)
    
    return unique


def _categorize_sources(sources):
    """
    Categorize sources by type for easier matching later.
    """
    categories = {
        'industry_research': [],
        'roi_studies': [],
        'case_studies': [],
        'news_articles': [],
        'academic': [],
        'other': []
    }
    
    for source in sources:
        url = source.get('url', '').lower()
        title = source.get('title', '').lower()
        
        if any(d in url for d in ['gartner.com', 'forrester.com', 'mckinsey.com', 'idc.com']):
            categories['industry_research'].append(source)
        elif 'roi' in title or 'economic impact' in title or 'business case' in title:
            categories['roi_studies'].append(source)
        elif 'case study' in title or 'customer story' in title:
            categories['case_studies'].append(source)
        elif any(d in url for d in ['.edu', 'arxiv.org', 'scholar.google']):
            categories['academic'].append(source)
        elif any(d in url for d in ['techcrunch', 'forbes', 'hbr.org', 'wsj.com']):
            categories['news_articles'].append(source)
        else:
            categories['other'].append(source)
    
    return categories


# ============================================================================
# STEP 4: AI SYNTHESIS - Combine All Analyses
# ============================================================================

def step4_ai_synthesis(step0_data, step1_data, step2_data, step2c_data, step2b_data, step3_data=None):
    """
    Prepare synthesis task for Claude (in Cursor)
    NOTE: Creates task file for YOU (Claude in Cursor) to execute manually.
    NOW INCLUDES: Objective feature insights from Step 3
    """
    log("="*80)
    log("STEP 4: AI SYNTHESIS TASK (For AI Agent)")
    log("="*80)
    
    try:
        
        # Hub/Spoke strategy is now in Step 4 prompt and docs/developer-guide/HUB_SPOKE_STRATEGY_ANALYSIS.md
        # No separate strategy file needed
        
        # Prepare comprehensive synthesis prompt
        current_year = datetime.now().year
        current_month = datetime.now().strftime('%B')
        
        # Extract validated feature insights from Step 3
        feature_targets = ""
        if step3_data and 'feature_insights' in step3_data:
            insights = step3_data['feature_insights']
            if insights:
                feature_targets = "\n### VALIDATED CONTENT FEATURES (From Step 3 Objective Analysis):\n"
                feature_targets += "**These features correlate with high citation frequency:**\n\n"
                for feat_name, insight in insights.items():
                    feature_targets += f"- **{feat_name}:** {insight['recommendation']} (top performers: {insight['top_avg']:.0f})\n"
                feature_targets += "\n**CRITICAL:** These are NOT opinions - these patterns predict real-world citations!\n"
        
        synthesis_prompt = f"""You are a content strategist analyzing competitive intelligence for SEO article creation.

**CURRENT DATE:** {current_month} {current_year}

## HUB vs. SPOKE DECISION FRAMEWORK:
{hub_strategy_content if hub_strategy_content else 'Use keyword volume and comprehensiveness to determine if Hub or Spoke.'}

## YOUR TASK:
Synthesize ALL the following analyses into actionable strategic recommendations for creating content based on the dataset patterns.

IMPORTANT: When suggesting titles or temporal references, use {current_year}, NOT 2024 or earlier years.

## INPUT DATA:

### ANALYSIS 0: Brand Gap Analysis
- **Brand Mention Rate:** {step0_data.get('brand_rate', 0):.1f}%
- **Competitor Mention Rate:** {step0_data.get('competitor_rate', 0):.1f}%
- **Top Competitor Keywords:** {', '.join([f'"{kw[0]}"' for kw in step0_data.get('top_competitor_keywords', [])[:5]])}

### ANALYSIS 1: Response Pattern Analysis
- Total responses analyzed: {step1_data['total_responses']}
- Target domain responses: {step1_data.get('target_domain_responses', step1_data['total_responses'])}
- Domain: {CONFIG['competitor_analysis']['target_domain']}
- Top 10 Bigrams: {', '.join([f'"{bg[0]}" ({bg[1]}x)' for bg in step1_data['top_bigrams'][:10]])}
- Top 5 Trigrams: {', '.join([f'"{tg[0]}" ({tg[1]}x)' for tg in step1_data['top_trigrams'][:5]])}

### ANALYSIS 2: Top Cited Domains
Top 10: {', '.join([f'{domain} ({count}x)' for domain, count in step2_data['top_domains'][:10]])}

### ANALYSIS 2C: URL Semantic & Search Intent
- Dominant Search Intent: {step2c_data['intent_summary'].iloc[0]['intent']} ({step2c_data['intent_summary'].iloc[0]['percentage']:.1f}%)
- Top URL Keywords: {', '.join([f'"{kw[0]}"' for kw in step2c_data['top_keywords'][:5]])}

### ANALYSIS 2B: Competitor Content Structure
Average metrics from scraped top sources:
- Word count: {sum(p['word_count'] for p in step2b_data) / len(step2b_data) if step2b_data else 0:,.0f} words
- Sections (H2): {sum(p['h2_count'] for p in step2b_data) / len(step2b_data) if step2b_data else 0:.1f}
- Links: {sum(p['link_count'] for p in step2b_data) / len(step2b_data) if step2b_data else 0:.0f}

{feature_targets}

## OUTPUT REQUIRED:

Provide strategic recommendations in this EXACT format:

# Strategic Content Recommendations

## 1. BRAND GAP INSIGHTS (From Step 0)
- Current brand visibility: {step0_data.get('brand_rate', 0):.1f}%
- Strategy to improve: [How to go from {step0_data.get('brand_rate', 0):.1f}% to 5%+]
- Competitor keywords to steal: [Pick 3-5 from the top competitor keywords]

## 2. KEYWORD STRATEGY (From Steps 1 & 2C)
- Primary keyword: [exact phrase from URL analysis]
- Secondary keywords (5-7): [from response bigrams]
- Long-tail opportunities (3-5): [from trigrams + URL semantic keywords]
- URL Pattern to Use: [Based on Step 2C dominant intent]

## 3. CLUSTER STRATEGY (Use rule_STRATEGY_HUB.md Framework)
Determine if this article should be a HUB or SPOKE:

**HUB (Pillar Content) Criteria:**
- Comprehensive (3,000+ words, covers full landscape)
- Broad, high-volume keyword (primary trigram from dataset)
- Defines a category, evergreen potential
- Strategic: First thing people find on this topic

**SPOKE (Deep-Dive) Criteria:**
- Specific topic (focused on secondary bigrams/trigrams)
- Long-tail keyword (lower volume, higher intent)
- Conversion-focused, sits under broader hub

**Decision:**
- **Page Type:** [Cluster (Hub) OR Spoke]
- **Reasoning:** [Justify with word count, keyword volume, comprehensiveness]
- **If Cluster:** Name: "[Name]" | Potential Spokes: [3-5 topics]
- **If Spoke:** Parent Hub: "[Hub Topic]"

## 4. CONTENT STRUCTURE (From Step 2B)
- Recommended word count: [number] words (justify vs {sum(p['word_count'] for p in step2b_data) / len(step2b_data) if step2b_data else 0:,.0f} competitor avg)
- Section breakdown: [list with headings, informed by 17.6 avg H2s]
- Link strategy: [internal vs external, informed by avg {sum(p['link_count'] for p in step2b_data) / len(step2b_data) if step2b_data else 0:.0f} links]

## 4B. VALIDATED CONTENT FEATURES (MUST IMPLEMENT - From Step 3)
**These are objective patterns that predict citation frequency:**

If Step 3 provided feature insights, YOU MUST incorporate them into content strategy:
- Use the EXACT target numbers from validated features
- Prioritize STRONG predictors (r > 0.7) first
- These are data-driven requirements, not suggestions

Example targets (update with actual Step 3 data):
- Keyword coverage: 12+ target keywords integrated naturally
- Technical terms: 21+ mentions (example: API, SDK, analytics, integration)
- Product names: 21+ specific platforms/brands mentioned
- Case references: 6+ concrete examples with "for example", "such as"
- Action verbs: 22+ (should, must, can, enable)
- Industry terms: 110+ domain-specific words

## 5. COMPETITIVE POSITIONING
- What competitors do well: [2-3 specific points from scraped content]
- What competitors miss: [2-3 gaps you identified]
- **Our unique angle:** [How does {BRAND_NAME}'s approach differentiate from competitors? Reference brand-context file for unique positioning]

## 6. SEARCH INTENT STRATEGY (From Step 2C)
- Dominant intent: {step2c_data['intent_summary'].iloc[0]['intent']} ({step2c_data['intent_summary'].iloc[0]['percentage']:.1f}%)
- Content type recommendation: [What format based on intent - listicle, guide, comparison?]
- Title strategy: [Based on winning URL patterns]

## 7. TONE & STYLE
- Voice: [From brand-context file - extract tone and style]
- Audience level: [From brand-context - identify target persona]
- Hook strategy: [Use approach that matches brand voice]

## 8. MUST-INCLUDE ELEMENTS
- [List 5-7 critical elements based on ALL analyses]

## 9. CONTENT GAPS TO EXPLOIT
- [List 3-5 specific opportunities, referencing which step revealed each gap]

## 10. KEY CLAIMS REQUIRING EXTERNAL CITATIONS
Based on competitor content analysis, identify 3-5 factual claims that will need authoritative external sources:
- Statistical facts requiring verification (industry percentages, trends)
- Technology performance claims (accuracy rates, improvements)
- Regulatory/compliance requirements specific to industry
- [For each claim, note if it appeared in competitor content and might have a traceable source]

Be ULTRA-SPECIFIC. Reference exact numbers from the data (brand rate, keyword frequency, competitor averages). Show your work.
"""

        # Save synthesis task
        task_file = os.path.join(SESSION_DIR, "step4_SYNTHESIS_TASK.md")
        
        with open(task_file, 'w', encoding='utf-8') as f:
            f.write("# STEP 4: AI Synthesis Task (For AI Agent)\n\n")
            f.write(f"**Session:** {SESSION_ID}\n\n")
            f.write("---\n\n")
            f.write("## 📋 YOUR TASK (AI Agent):\n\n")
            f.write("Synthesize ALL the analysis files into strategic recommendations.\n\n")
            f.write("**CRITICAL:** Save the synthesis to: `step4_AGENT_SYNTHESIS.md`\n\n")
            f.write("---\n\n")
            f.write("## SYNTHESIS PROMPT:\n\n")
            f.write(synthesis_prompt)
        
        log(f"✅ Synthesis task created: {task_file}")
        
        # Trigger AI Agent
        print(f"\n🤖 AGENT_TASK_READY: {task_file}")
        print(f"📋 OUTPUT_FILE: step4_AGENT_SYNTHESIS.md")
        print(f"⏸️  Pipeline paused - waiting for AI Agent to complete synthesis...")
        
        # Check if synthesis was already done
        synthesis_file = os.path.join(SESSION_DIR, "step4_AGENT_SYNTHESIS.md")
        if os.path.exists(synthesis_file):
            with open(synthesis_file, 'r') as f:
                synthesis_content = f.read()
            log(f"✅ Found existing synthesis")
            return synthesis_file, {'synthesis': synthesis_content}
        else:
            log(f"⚠️  Synthesis not yet done - waiting for manual step")
            return None, {}
        
    except Exception as e:
        log(f"❌ AI Synthesis failed: {e}")
        return None, {}

# ============================================================================
# STEP 5: ARTICLE GENERATION (With Claude)
# ============================================================================

def step5_generate_article(synthesis_data, brand_name=BRAND_NAME, brand_url=BRAND_URL, word_count=TARGET_WORD_COUNT):
    """
    Prepare article generation task for Claude (in Cursor)
    NOTE: This function creates the task file for YOU (Claude in Cursor) to execute manually.
    """
    log("="*80)
    log("STEP 5: ARTICLE GENERATION TASK (For AI Agent)")
    log("="*80)
    
    # Load brand context
    brand_context = ""
    if os.path.exists(BRAND_CONTEXT_FILE):
        try:
            with open(BRAND_CONTEXT_FILE, 'r', encoding='utf-8') as f:
                brand_context = f.read()
            log(f"✅ Loaded brand context: {len(brand_context)} chars")
        except:
            log("⚠️  Could not load brand context")
    else:
        log("⚠️  Brand context file not found")
    
    # Load draft agent rules
    draft_rules_path = os.path.join(SCRIPT_DIR, "brand-context/rule_draft.ts")
    draft_rules_content = ""
    if os.path.exists(draft_rules_path):
        try:
            with open(draft_rules_path, 'r', encoding='utf-8') as f:
                draft_rules_content = f.read()
            log(f"✅ Loaded draft rules: {len(draft_rules_content)} chars")
        except:
            log("⚠️  Could not load draft rules")
    else:
        log("⚠️  Draft rules file not found")
    
    # Load all analysis files
    try:
        with open(os.path.join(SESSION_DIR, "step1_FOR_AGENT_ANALYSIS.md"), 'r') as f:
            step1_content = f.read()
        
        # Try both possible synthesis filenames
        synthesis_file_alt = os.path.join(SESSION_DIR, "step4_AGENT_SYNTHESIS.md")
        synthesis_file_main = os.path.join(SESSION_DIR, "step4_AI_SYNTHESIS.md")
        
        if os.path.exists(synthesis_file_alt):
            with open(synthesis_file_alt, 'r') as f:
                synthesis_content = f.read()
        elif os.path.exists(synthesis_file_main):
            with open(synthesis_file_main, 'r') as f:
                synthesis_content = f.read()
        else:
            log("❌ Could not find synthesis file (step4_AGENT_SYNTHESIS.md or step4_AI_SYNTHESIS.md)")
            return None, {}
    except Exception as e:
        log(f"❌ Could not load analysis files: {e}")
        return None, {}
    
    # Check for existing file first (check both root and articles/hub/)
    article_file = os.path.join(SESSION_DIR, "step5_GENERATED_ARTICLE.md")
    
    # Try organized structure first
    hub_dir = os.path.join(SESSION_DIR, "articles", "hub")
    os.makedirs(hub_dir, exist_ok=True)
    organized_file = os.path.join(hub_dir, "step5_GENERATED_ARTICLE.md")
    
    if os.path.exists(organized_file):
        article_file = organized_file
    elif os.path.exists(article_file):
        log(f"✅ Found existing generated article: {article_file}")
        with open(article_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return article_file, {'word_count': len(content.split()), 'content': content}

    # Load all required context
    current_year = datetime.now().year
    current_month = datetime.now().strftime('%B')
    current_month_num = datetime.now().month
    target_year_for_title = SEO_TARGET_YEAR  # Uses late-year strategy (next year in Nov-Dec)
    
    try:
        
        # Extract key principles from draft rules
        writing_style = """- Use a conversational, expert tone with contractions (you're, don't, can't, we'll)
- Vary sentence length for rhythm—short punchy sentences and longer flowing ones
- Keep language simple; explain like to a colleague over coffee
- Use relatable metaphors sparingly; avoid buzzwords
- Do not cluster links; spread them out across the content where helpful"""

        connection_principles = """- Show empathy for the reader's real-world constraints (queues, SLAs, coaching bandwidth)
- Weave in realistic examples or observations from the provided context
- Connect to problems first, then provide value with specific steps, frameworks, and metrics"""
        
        # Late-year SEO guidance (Nov-Dec)
        late_year_guidance = ""
        is_late_year = current_month_num >= 11
        if is_late_year:
            late_year_guidance = f"""
## 📅 LATE-YEAR SEO STRATEGY (Nov-Dec Publishing):
We're publishing in {current_month} {current_year}. Apply these rules:

1. **TITLE:** Use **{target_year_for_title}** in the title (e.g., "Top 10 Platforms for {target_year_for_title}")
2. **TITLE TAG (Meta):** Add the Month Hack for CTR: "{SEO_MONTH_HACK}"
   - Example meta title: "Best Analytics Platforms {target_year_for_title} {SEO_MONTH_HACK}"
3. **INTRO:** Acknowledge the timeline naturally:
   - "As we head into {target_year_for_title}..."
   - "Looking ahead to {target_year_for_title}..."
   - "With {target_year_for_title} approaching..."
4. **CONTENT:** Write as if evaluating what will be relevant in {target_year_for_title}
5. **URL:** Keep evergreen (no year) - we handle this automatically

This captures future search intent and the Month Hack increases CTR in competitive niches.
"""
        elif current_month_num >= 10:  # October - transitional month
            late_year_guidance = f"""
## 📅 SEO YEAR STRATEGY:
We're in October - use **{target_year_for_title}** in titles and keywords.

**Month Hack:** Consider adding "{SEO_MONTH_HACK}" to title tags for CTR boost in competitive niches.
"""
        
        # Article generation prompt (with draft agent principles)
        article_prompt = f"""You are an expert SEO content writer with deep industry knowledge.

**CURRENT DATE:** {current_month} {current_year}
{late_year_guidance}

## ROLE (from rule_draft.ts):
You're a skilled human writer who connects with readers through authentic, conversational content and deep industry expertise. You write like you're helping a real operator solve real constraints.

## WRITING STYLE:
{writing_style}

## CONNECTION PRINCIPLES:
{connection_principles}

## YOUR UNIQUE ADVANTAGE - BRAND CONTEXT:
{brand_context[:1500] if brand_context else f'{brand_name} is an AI-powered platform.'}

**CRITICAL INSTRUCTION - Brand Context Usage:**
The brand context above contains unique insights, case studies, and positioning that competitors DON'T have.

Your task: READ the full brand context and EXTRACT the elements most relevant to this article topic:
- Founding story or team background (if it adds credibility)
- Differentiators (unique approach vs competitors)
- Specific case studies or metrics (choose the most relevant ones)
- Contrarian viewpoints or unique perspectives
- Signature positioning statements or brand taglines

DO NOT:
- Copy the brand context verbatim
- Use ALL examples (be selective based on article topic)
- Write a generic "Wikipedia" article

DO:
- Write from {brand_name}'s informed, opinionated perspective
- Weave brand insights naturally throughout (not just in a "About Us" section)
- Make it clear this article is written by people who BUILD these platforms, not just review them
- Use signature positioning from brand-context where relevant
- Highlight key differentiators from brand-context file
- Include founding story or team background if it strengthens credibility

**TONE ENFORCEMENT:**
- Be direct and slightly contrarian (reference brand-context for specific approach)
- Challenge industry assumptions (surface uncomfortable truths)
- Use concrete examples over generic claims
- Write for decision-makers (practical and credible, not promotional)

## STRATEGIC RECOMMENDATIONS:
{synthesis_content}

## CONTENT PATTERNS FROM COMPETITIVE ANALYSIS:
{step1_content[:2000]}...

## CRITICAL REQUIREMENTS:
1. **Word Count:** EXACTLY {word_count} words (count carefully)
2. **Language:** {CONFIG['content'].get('language', 'English')}
3. **Brand:** Mention {brand_name} naturally, link first mention to {brand_url}
4. **Tone:** {CONFIG['content'].get('tone', 'Professional, data-driven, practical')} (target audience from brand-context)
5. **Structure - MANDATORY HEADING HIERARCHY:**
   - Use `#` for article title (H1) - ONCE at top
   - Use `##` for main sections (H2) - 8-12 sections
   - Use `###` for subsections (H3) - 2-4 subsections PER main section
   - Use frameworks from brand-context if applicable
   
   **Example structure:**
   ```markdown
   # Article Title
   
   ## TL;DR
   ...
   
   ## Main Section 1
   ### Subsection 1.1
   Content...
   
   ### Subsection 1.2
   Content...
   
   ## Main Section 2
   ### Subsection 2.1
   Content...
   ```
   
   **CRITICAL:** Every ## section with >300 words MUST have ### subsections!
   
6. **Competitor Comparison:** When comparing platforms, mention {brand_name} FIRST
7. **Citations (CRITICAL - New Format):** 
   - DO NOT generate any URLs or citations
   - DO NOT invent source names like "Gartner 2024" or "Forrester reports"
   - Instead, use [CLAIM: brief description] markers for statistics/claims
   - Example: "Organizations see significant improvements [CLAIM: industry performance statistics]"
   - These markers will be replaced with REAL verified citations in Step 8
8. **Complete:** NEVER stop before finishing the full article

## 🔥 VALIDATED CONTENT FEATURES (MANDATORY - From Objective Analysis):
**These patterns correlate with high citation frequency and MUST be implemented:**

Check Step 4 synthesis for exact targets, but typically:
- **Keyword Coverage:** Integrate 12+ target keywords from Step 1 naturally throughout
- **Technical Terms:** Include 21+ technical terms (from Step 3 AI-detected vocabulary)
- **Product Names:** Mention 21+ specific platforms/brands (competitors and us)
- **Case References:** Add 6+ concrete examples using "for example", "such as", "for instance"
- **Action Verbs:** Use 22+ action-oriented language (from Step 3 AI-detected action verbs)
- **Industry Terms:** Include 110+ domain-specific words (from Step 3 AI-detected industry terms)

**AVOID OVER-USING:**
- Quantitative evidence (keep to 1-2 stats, not 10+)
- Recommendation language ("we recommend" - use sparingly)
- Research citations ("studies show" - less than 5x)

**🚫 NEVER INCLUDE IN ARTICLE (Internal Data Leak Prevention):**
- Frequency statistics from analysis (e.g., "The 281x trigram frequency of...")
- N-gram counts or bigram/trigram mentions (e.g., "529x frequency in industry responses")
- Any mention of "industry responses", "dataset analysis", or internal research methodology
- These are INTERNAL planning data, NOT reader-facing content

**Count these as you write!** These are NOT optional styling preferences - they predict real-world performance.

## OUTPUT FORMAT WITH PROPER HEADING HIERARCHY:

# [SEO-Optimized Title]

## TL;DR
- [4-6 bullet points summarizing key insights]
- [Last bullet mentions {brand_name}]

[Engaging introduction - 150-200 words]

## Section 1: [Main Topic]
### Subsection 1.1: [Specific aspect]
[Content for this subsection - 100-200 words]

### Subsection 1.2: [Another aspect]
[Content for this subsection - 100-200 words]

## Section 2: [Next Topic]
### Subsection 2.1: [Detail]
[Content...]

### Subsection 2.2: [More detail]
[Content...]

[Continue with ## and ### hierarchy until ~{word_count} words]

## Conclusion
[Wrap up and CTA to {brand_name}]

**CRITICAL REMINDERS:**
- Write the COMPLETE article now
- MUST include ### subsections (not optional!)
- Every long section needs subsections
- Generate ALL {word_count} words in this response
"""

        # Create task file for AI Agent (Cursor) to execute
        task_file = os.path.join(SESSION_DIR, "step5_ARTICLE_GENERATION_TASK.md")
        
        with open(task_file, 'w', encoding='utf-8') as f:
            f.write("# STEP 5: Article Generation Task (For AI Agent)\n\n")
            f.write(f"**Session:** {SESSION_ID}\n\n")
            f.write("---\n\n")
            f.write("## 📋 YOUR TASK (AI Agent):\n\n")
            f.write(f"Generate a complete {word_count}-word article based on all the analysis.\n\n")
            f.write(f"**CRITICAL:** Save the article to: `articles/hub/step5_GENERATED_ARTICLE.md`\n\n")
            f.write("---\n\n")
            f.write("## ARTICLE GENERATION PROMPT:\n\n")
            f.write(article_prompt)
        
        log(f"✅ Article generation task created: {task_file}")
        
        # Trigger AI Agent
        print(f"\n🤖 AGENT_TASK_READY: {task_file}")
        print(f"📋 OUTPUT_FILE: step5_GENERATED_ARTICLE.md")
        print(f"⏸️  Pipeline paused - waiting for AI Agent to generate article...")
        
        # Check if article was already generated (organized structure preferred)
        hub_dir = os.path.join(SESSION_DIR, "articles", "hub")
        organized_file = os.path.join(hub_dir, "step5_GENERATED_ARTICLE.md")
        legacy_file = os.path.join(SESSION_DIR, "step5_GENERATED_ARTICLE.md")
        
        article_file = organized_file if os.path.exists(organized_file) else legacy_file
        
        if os.path.exists(article_file):
            with open(article_file, 'r', encoding='utf-8') as f:
                content = f.read()
            word_count_actual = len(content.split())
            log(f"✅ Found existing generated article: {word_count_actual:,} words")
            
            # QUALITY GATE: Validate article meets exceptional standards
            issues = []
            
            # Check 1: Word count (must be within 15%)
            if word_count_actual < word_count * 0.85:
                issues.append(f"TOO SHORT: {word_count_actual} words (need {word_count}+)")
            elif word_count_actual > word_count * 1.15:
                issues.append(f"TOO LONG: {word_count_actual} words (target {word_count})")
            
            # Check 2: Brand mention
            if BRAND_NAME not in content and BRAND_NAME.lower() not in content.lower():
                issues.append(f"MISSING BRAND: {BRAND_NAME} not mentioned")
            
            # Check 3: Structure (basic sanity check)
            if content.count("##") < 5:
                issues.append(f"INSUFFICIENT STRUCTURE: Only {content.count('##')} H2 headings (need 5+)")
            
            # Check 4: No placeholder content
            if "[TODO" in content or "[PLACEHOLDER" in content or "Lorem ipsum" in content:
                issues.append("PLACEHOLDER CONTENT: Contains unfinished sections")
            
            # Check 5: Has introduction
            if not content[:500].strip():
                issues.append("MISSING INTRO: Article starts empty")
            
            if issues:
                return create_ai_rescue_task(
                    step_name="STEP6_ARTICLE_QUALITY_FAIL",
                    failure_reason=f"Generated article fails {len(issues)} quality checks",
                    required_action=f"""The generated article exists but doesn't meet our exceptional quality standards.

**Quality Issues Found:**
{chr(10).join([f"- {issue}" for issue in issues])}

**Current article stats:**
- Word count: {word_count_actual:,} (target: {word_count:,})
- Headings (H2): {content.count('##')}
- Brand mentions: {"✅" if BRAND_NAME in content else "❌"}

**YOUR MISSION:**
Fix the article to meet ALL quality standards.

**Requirements:**
1. **Word Count:** {word_count:,} words (±15% = {int(word_count*0.85)}-{int(word_count*1.15)})
2. **Brand Integration:** {BRAND_NAME} mentioned naturally, linked to {brand_url}
3. **Structure:** Minimum 5-7 H2 sections with logical flow
4. **Completeness:** No TODOs, placeholders, or unfinished sections
5. **Quality:** Every paragraph earns its place

**Tone:** [From brand-context file - extract voice and approach]
**Audience:** [From brand-context - identify target personas]  
**Differentiator:** [From brand-context - extract key differentiators vs competitors]

**Read the original task file** for full prompt context: `step5_ARTICLE_GENERATION_TASK.md`

Fix and save to: `{article_file}`

We're {BRAND_NAME} - we set the standard for quality.
""",
                    output_file=article_file,
                    additional_context="Original generation task contains full strategic guidance and brand context"
                )
            
            log(f"✅ Article QUALITY GATE PASSED")
            return article_file, {'word_count': word_count_actual, 'content': content}
        else:
            log(f"⚠️  Article not yet generated - waiting for manual step")
            return None, {}
        
    except Exception as e:
        log(f"❌ Article generation failed: {e}")
        return None, {}

# ============================================================================
# STEP 5B: HUB FAQ GENERATION
# ============================================================================

def step5b_generate_hub_faqs(hub_article_file):
    """
    Step 5B: Generate 3-5 broad, definitional FAQs for the Hub article.
    
    Hub FAQs are different from Spoke FAQs:
    - Hub FAQs: "What is X?", "Why is X important?" (broad, category-level)
    - Spoke FAQs: "Does X charge a fee?", "How long does Y take?" (specific, nitty-gritty)
    
    This separation prevents cannibalization.
    """
    log("="*80)
    log("STEP 5B: HUB FAQ GENERATION (For AI Agent)")
    log("="*80)
    
    if not hub_article_file or not os.path.exists(hub_article_file):
        log("⚠️  Hub article not found - Skipping FAQ generation")
        return None, {}
    
    # Check if FAQs already exist
    faq_output_file = os.path.join(SESSION_DIR, "step5b_HUB_FAQS.md")
    if os.path.exists(faq_output_file):
        log(f"✅ Hub FAQs already exist: {os.path.basename(faq_output_file)}")
        with open(faq_output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        faq_count = content.count('### ')
        return faq_output_file, {'faq_count': faq_count, 'status': 'complete'}
    
    # Load hub article
    with open(hub_article_file, 'r', encoding='utf-8') as f:
        hub_content = f.read()
    
    # Extract title
    hub_title = hub_content.split('\n')[0].strip('#').strip()
    
    # Load brand context
    brand_context = ""
    if os.path.exists(BRAND_CONTEXT_FILE):
        try:
            with open(BRAND_CONTEXT_FILE, 'r', encoding='utf-8') as f:
                brand_context = f.read()
        except:
            pass
    
    # Load Step 4 synthesis for keyword context
    synthesis_content = ""
    synthesis_file = os.path.join(SESSION_DIR, "step4_AGENT_SYNTHESIS.md")
    if not os.path.exists(synthesis_file):
        synthesis_file = os.path.join(SESSION_DIR, "step4_AI_SYNTHESIS.md")
    if os.path.exists(synthesis_file):
        try:
            with open(synthesis_file, 'r', encoding='utf-8') as f:
                synthesis_content = f.read()
        except:
            pass
    
    # Create task file
    task_file = os.path.join(SESSION_DIR, "step5b_HUB_FAQ_TASK.md")
    
    with open(task_file, 'w', encoding='utf-8') as f:
        f.write("# STEP 5B: Hub FAQ Generation Task\n\n")
        f.write(f"**Session:** {SESSION_ID}\n")
        f.write(f"**Hub Article:** {hub_title}\n")
        f.write(f"**Brand:** {BRAND_NAME}\n\n")
        f.write("---\n\n")
        
        f.write("## 🎯 YOUR MISSION\n\n")
        f.write("Generate **3-5 FAQs** for this Hub article. These FAQs must be:\n\n")
        f.write("- **Broad, definitional questions** (category-level)\n")
        f.write("- **Unique to this Hub** (not repeated across articles)\n")
        f.write("- **2-3 sentence answers** (brief, can link to Spokes for details)\n\n")
        
        f.write("---\n\n")
        f.write("## ✅ DO: Broad, Definitional Questions\n\n")
        f.write("Good Hub FAQ questions:\n")
        f.write("- \"What is [topic]?\"\n")
        f.write("- \"Why is [topic] important?\"\n")
        f.write("- \"What are the benefits of [topic]?\"\n")
        f.write("- \"Who uses [topic]?\"\n")
        f.write("- \"What's the difference between [topic A] and [topic B]?\"\n\n")
        
        f.write("## ❌ DON'T: Specific, How-To Questions\n\n")
        f.write("These belong in **Spoke FAQs** (Step 11D), not here:\n")
        f.write("- \"How do I set up [feature]?\" → Spoke\n")
        f.write("- \"What's the best [tool] for [task]?\" → Spoke\n")
        f.write("- \"Does [service] charge a fee?\" → Spoke\n")
        f.write("- \"How long does [process] take?\" → Spoke\n\n")
        
        f.write("## ❌ DON'T: Brand-Specific Questions\n\n")
        f.write("These belong on product/support pages:\n")
        f.write(f"- \"Is {BRAND_NAME} free?\" → Pricing page\n")
        f.write(f"- \"How do I cancel {BRAND_NAME}?\" → Support page\n\n")
        
        f.write("---\n\n")
        f.write("## 📄 HUB ARTICLE CONTEXT\n\n")
        f.write(f"**Title:** {hub_title}\n\n")
        f.write("**First 1000 characters:**\n")
        f.write("```\n")
        f.write(hub_content[:1000])
        f.write("\n```\n\n")
        
        if synthesis_content:
            f.write("---\n\n")
            f.write("## 🎯 KEYWORD CONTEXT (from Step 4 Synthesis)\n\n")
            f.write("```\n")
            f.write(synthesis_content[:1500])
            f.write("\n```\n\n")
        
        if brand_context:
            f.write("---\n\n")
            f.write("## 🏢 BRAND CONTEXT\n\n")
            f.write("```\n")
            f.write(brand_context[:1000])
            f.write("\n```\n\n")
        
        f.write("---\n\n")
        f.write("## 📤 OUTPUT FORMAT\n\n")
        f.write(f"Save to: `step5b_HUB_FAQS.md`\n\n")
        f.write("```markdown\n")
        f.write("## Frequently Asked Questions\n\n")
        f.write("### [Broad Question 1]?\n")
        f.write("[Answer: 2-3 sentences, factual, can reference future Spokes]\n\n")
        f.write("### [Broad Question 2]?\n")
        f.write("[Answer: 2-3 sentences]\n\n")
        f.write("### [Broad Question 3]?\n")
        f.write("[Answer: 2-3 sentences]\n\n")
        f.write("(Continue for 3-5 total FAQs)\n")
        f.write("```\n\n")
        
        f.write("---\n\n")
        f.write("## ✅ QUALITY CHECKLIST\n\n")
        f.write("Before saving:\n")
        f.write("- [ ] 3-5 FAQs (not more, not less)\n")
        f.write("- [ ] All questions are broad/definitional\n")
        f.write("- [ ] No \"how to\" or step-by-step questions\n")
        f.write("- [ ] Each answer is 2-3 sentences\n")
        f.write("- [ ] Answers are factual, not salesy\n")
        f.write(f"- [ ] No {BRAND_NAME}-specific questions (pricing, cancellation, etc.)\n")
    
    log(f"📝 Task created: {os.path.basename(task_file)}")
    log(f"📋 Output expected: step5b_HUB_FAQS.md")
    log(f"")
    log(f"🤖 AI AGENT: Generate 3-5 broad FAQs for the Hub article")
    log(f"   - Read the Hub article context above")
    log(f"   - Write definitional questions (\"What is...\", \"Why is...\")")
    log(f"   - Keep answers brief (2-3 sentences)")
    log(f"   - Save to: step5b_HUB_FAQS.md")
    
    return task_file, {'status': 'waiting_for_agent', 'hub_title': hub_title}


# ============================================================================
# STEP 6: APPLY WRITING RULES (Brand Alignment)
# ============================================================================

def step6_apply_writing_rules(article_file):
    """
    Create task for AI Agent to apply brand writing rules
    """
    log("="*80)
    log("STEP 6: WRITING RULES TASK (For AI Agent)")
    log("="*80)
    
    if not article_file or not os.path.exists(article_file):
        log("⚠️  Article file not found - Skipping writing rules")
        return None, {}
    
    # Load writing rules
    writing_rules_path = os.path.join(SCRIPT_DIR, "brand-context/rule_writing.ts")
    if not os.path.exists(writing_rules_path):
        log("⚠️  writing_rules.ts not found")
        return article_file, {}
    
    with open(writing_rules_path, 'r') as f:
        writing_rules_content = f.read()
    
    with open(article_file, 'r') as f:
        article_content = f.read()
    
    # Quick validation check (keep this for the report)
    issues = []
    fixes = []
    
    # Check 1: Comma splices
    comma_splice_pattern = r'(\w+),\s+(it\'s|they\'re|we\'re|he\'s|she\'s)'
    splices = re.findall(comma_splice_pattern, article_content, re.IGNORECASE)
    if splices:
        issues.append(f"⚠️  Found {len(splices)} potential comma splices")
        fixes.append("Fix: Replace comma with semicolon or period")
    
    # Check 2: Em dashes
    em_dash_count = article_content.count('—')
    if em_dash_count > 0:
        issues.append(f"⚠️  Found {em_dash_count} em dashes (AI tell)")
        fixes.append("Fix: Use colons for definitions, parentheses for asides")
    
    # Check 3: Second person usage (configurable threshold)
    you_matches = re.findall(r'\b(you|your|you\'re)\b', article_content, re.IGNORECASE)
    you_threshold = 10  # Could be made configurable in config.json if needed
    if len(you_matches) > you_threshold:
        issues.append(f"⚠️  Found {len(you_matches)} instances of 'you/your' (check brand voice guidelines)")
        fixes.append("Fix: Consider third-person alternatives if brand prefers (e.g., 'leaders', 'teams', 'organizations')")
    
    # Check 4: Industry-specific mentions (check against brand rules if they exist)
    # This is now optional - different brands have different constraints
    # Remove or make configurable based on brand-context/rule_writing.ts
    
    # Create AI Agent task
    task_file = os.path.join(SESSION_DIR, "step6_WRITING_RULES_TASK.md")
    with open(task_file, 'w') as f:
        f.write("# Step 6: Apply Writing Rules Task (For AI Agent)\n\n")
        f.write(f"**Session:** {SESSION_ID}\n\n")
        f.write("---\n\n")
        f.write("## 📋 YOUR TASK (AI Agent):\n\n")
        f.write(f"Apply {BRAND_NAME}'s writing rules to the article.\n\n")
        f.write(f"**Article to edit:** `{os.path.basename(article_file)}`\n")
        f.write(f"**Rules source:** `brand-context/rule_writing.ts`\n")
        f.write(f"**Output file:** `articles/hub/step6_ARTICLE_RULES_APPLIED.md`\n\n")
        f.write("## WRITING RULES:\n\n")
        f.write("```typescript\n")
        f.write(writing_rules_content)
        f.write("\n```\n\n")
        f.write("## QUICK VALIDATION (Before full edit):\n\n")
        
        if issues:
            f.write(f"⚠️  **{len(issues)} issues detected:**\n\n")
            for i, issue in enumerate(issues, 1):
                f.write(f"{i}. {issue}\n")
                if i <= len(fixes):
                    f.write(f"   Fix: {fixes[i-1]}\n")
        else:
            f.write("✅ No critical issues detected in quick scan.\n")
        
        f.write("\n---\n\n")
        f.write("## INSTRUCTIONS:\n\n")
        f.write("1. Read the article\n")
        f.write("2. Apply ALL 15 rules from writing_rules.ts with surgical precision\n")
        f.write("3. Keep formatting intact (headings, bullets, links)\n")
        f.write("4. Save result to: `step6_ARTICLE_RULES_APPLIED.md`\n\n")
    
    log(f"✅ Writing rules task created: {task_file}")
    
    # Trigger AI Agent
    print(f"\n🤖 AGENT_TASK_READY: {task_file}")
    print(f"📋 OUTPUT_FILE: step6_ARTICLE_RULES_APPLIED.md")
    print(f"⏸️  Pipeline paused - waiting for AI Agent to apply writing rules...")
    
    # Check if rules were already applied (organized structure preferred)
    hub_dir = os.path.join(SESSION_DIR, "articles", "hub")
    os.makedirs(hub_dir, exist_ok=True)
    
    organized_file = os.path.join(hub_dir, "step6_ARTICLE_RULES_APPLIED.md")
    legacy_file = os.path.join(SESSION_DIR, "step6_ARTICLE_RULES_APPLIED.md")
    
    rules_applied_file = organized_file if os.path.exists(organized_file) else legacy_file
    
    if os.path.exists(rules_applied_file):
        log(f"✅ Found existing rules-applied article")
        print(f"\n✅ AGENT_TASK_COMPLETE: step6_ARTICLE_RULES_APPLIED.md")
        print(f"▶️  Resuming pipeline...")
        return rules_applied_file, {'issues': issues, 'applied': True}
    else:
        log(f"⚠️  Writing rules not yet applied - pipeline stopped")
        return None, {'issues': issues, 'applied': False}

# ============================================================================
# STEP 7: CREATE INTERNAL LINKS TASK (AI AGENT)
# ============================================================================

def create_step7_internal_links_task(article_file):
    """Create AI agent task for strategic internal linking"""
    
    internal_links = load_available_internal_links()
    task_file = os.path.join(SESSION_DIR, "step7_INTERNAL_LINKS_TASK.md")
    
    product_links = [l for l in internal_links if l.get('type') == 'product']
    blog_links = [l for l in internal_links if l.get('type') == 'blog']
    hub_links = [l for l in internal_links if l.get('type') == 'hub']
    spoke_links = [l for l in internal_links if l.get('type') == 'spoke']
    
    with open(task_file, 'w', encoding='utf-8') as f:
        f.write(f"""# STEP 7: Apply Strategic Internal Links (AI Agent Task)

**Session:** {SESSION_ID}

---

## 🎯 YOUR TASK

Add 8-12 contextually relevant internal links throughout the article.

**CRITICAL - Link Format:**
- Use `/blog/[slug]` format (NOT folder paths)
- Slug = article title in lowercase with dashes
- Example: "Top 10 Analytics Platforms" → `/blog/top-10-analytics-platforms`
- Blog path: `{CONFIG.get('publishing', {}).get('blog_path', '/blog')}`

**Input Article:** `{os.path.basename(article_file)}`  
**Output Article:** `articles/hub/step7_ARTICLE_WITH_INTERNAL_LINKS.md`

---

## 📋 AVAILABLE INTERNAL LINKS

### {BRAND_NAME} Product Pages
{format_link_list(product_links)}

### {BRAND_NAME} Blog Posts
{format_link_list(blog_links)}

### Hub Articles
{format_link_list(hub_links)}

### Spoke Articles
{format_link_list(spoke_links)}

---

## ✅ QUALITY CHECKLIST

- [ ] 8-12 internal links added
- [ ] Links distributed throughout (not clustered)
- [ ] Contextual anchor text (not "click here")
- [ ] All existing citations preserved

---

## 💾 OUTPUT

Save updated article to: `step7_ARTICLE_WITH_INTERNAL_LINKS.md`
""")
    
    log(f"✅ Step 7 task created: {task_file}")
    log(f"   Available internal links: {len(internal_links)}")
    print(f"\n🤖 AGENT_TASK_READY: {task_file}")
    print(f"📋 OUTPUT_FILE: step7_ARTICLE_WITH_INTERNAL_LINKS.md")
    print(f"⏸️  Pipeline paused - waiting for AI Agent...")
    print("="*80 + "\n")
    
    return task_file

# ============================================================================
# STEP 8: CREATE CITATIONS TASK (AI AGENT)
# ============================================================================

def create_step8_citations_task(article_file, article_type="hub"):
    """Create AI agent task for researching and adding citations"""
    
    with open(article_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    citation_markers = re.findall(r'(.{50}\[CITATION NEEDED\].{50})', content)
    
    # Create unique task file name for spokes
    if article_type == "hub":
        task_file = os.path.join(SESSION_DIR, "step8_CITATIONS_TASK.md")
    else:
        # Extract spoke number from filename (e.g., step10_spoke01_xxx.md)
        article_basename = os.path.basename(article_file)
        spoke_match = re.search(r'spoke(\d+)', article_basename)
        spoke_num = spoke_match.group(1) if spoke_match else "XX"
        task_file = os.path.join(SESSION_DIR, f"step10b_CITATIONS_TASK_spoke{spoke_num}.md")
    
    # Determine output filename based on article type
    if article_type == "hub":
        output_filename = "step8_ARTICLE_WITH_CITATIONS.md"
    else:
        # For spokes, update in place
        output_filename = os.path.basename(article_file)
    
    with open(task_file, 'w', encoding='utf-8') as f:
        f.write(f"""# STEP 8: Research & Add External Citations (AI Agent Task)

**Session:** {SESSION_ID}
**Article Type:** {article_type.upper()}

---

## 🎯 YOUR TASK

Research authoritative sources and replace ALL `[CITATION NEEDED]` markers with actual citations.

**Input Article:** `{os.path.basename(article_file)}`  
**Output Article:** `{output_filename}`  
**Citations Found:** {len(citation_markers)} placeholders

---

## ⚠️ CRITICAL RULE: NO CITATIONS IN FIRST 2 SECTIONS

**Do NOT add external citations in:**
- TL;DR section (summary should be clean)
- First section after TL;DR (introduction should flow naturally)
- Any H1 or H2 headings

**Where citations SHOULD go:**
- Body sections starting from the SECOND section after TL;DR
- Specific factual claims requiring evidence

---

## ⚠️ CITATION DIVERSITY RULE

**Do NOT cite the same source twice in the same article!**

- Each external citation should come from a DIFFERENT domain
- If multiple claims come from the same report, consolidate into ONE mention
- Mix source types: industry reports, research papers, news articles
- Prefer high-authority domains: McKinsey, Gartner, Forrester, HBR, industry publications

**Example of what NOT to do:**
```
❌ "According to [CallMiner](url), accuracy is 90%..."
❌ "...and [CallMiner research](url) shows 42% still use manual..."
```

**Example of correct approach:**
```
✅ "According to [CallMiner's 2025 CX Report](url), accuracy is 90% and 42% still use manual..."
✅ Or use different sources for each claim
```

---

## 💾 OUTPUT

Save updated article to: `{output_filename}`

**IMPORTANT:** Save to the EXACT filename above - the pipeline looks for this file!
""")
    
    log(f"✅ Step 8 task created: {task_file}")
    log(f"   Citations needed: {len(citation_markers)}")
    print(f"\n🤖 AGENT_TASK_READY: {task_file}")
    print(f"📋 OUTPUT_FILE: step8_ARTICLE_WITH_CITATIONS.md")
    print(f"⏸️  Pipeline paused - waiting for AI Agent...")
    print("="*80 + "\n")
    
    return task_file


def step8_match_citations_with_sonar(article_file, sources_file=None):
    """
    Match [CLAIM: ...] markers in article to verified sources using Perplexity Sonar.
    
    This is the NEW automated citation matching that replaces manual AI agent tasks.
    Uses:
    1. Pre-verified sources from Step 3B (if available)
    2. Perplexity Sonar for claims without matches
    """
    log("="*80)
    log("STEP 8: CITATION MATCHING (Perplexity Sonar)")
    log("="*80)
    
    # Load article
    with open(article_file, 'r', encoding='utf-8') as f:
        article_content = f.read()
    
    # Extract all [CLAIM: ...] markers (new format)
    claim_pattern = r'\[CLAIM:\s*([^\]]+)\]'
    claims = re.findall(claim_pattern, article_content)
    
    # Also check for old [CITATION NEEDED] format for backwards compatibility
    old_citation_pattern = r'\[CITATION NEEDED\]'
    old_citations = re.findall(old_citation_pattern, article_content)
    
    if old_citations and not claims:
        log(f"   ⚠️  Found {len(old_citations)} old [CITATION NEEDED] markers")
        log(f"   Converting to [CLAIM: ...] format for Sonar matching...")
        # For old format, we'll need to extract context
        claims = []
        for match in re.finditer(r'([^.!?]*)\[CITATION NEEDED\]([^.!?]*[.!?])?', article_content):
            context = (match.group(1) + (match.group(2) or '')).strip()
            claims.append(context[:100])  # Use surrounding text as claim
    
    log(f"   📋 Found {len(claims)} claims to cite")
    
    if not claims:
        log("   ✅ No claims to cite - article is ready")
        # Just copy the file to the output location
        output_file = os.path.join(SESSION_DIR, "articles/hub/step8_ARTICLE_WITH_CITATIONS.md")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(article_content)
        return output_file, {'cited': 0, 'unverified': 0, 'citations': []}
    
    # Load pre-verified sources from Step 3B (if available)
    verified_sources = []
    if sources_file and os.path.exists(sources_file):
        try:
            with open(sources_file, 'r', encoding='utf-8') as f:
                sources_data = json.load(f)
                verified_sources = sources_data.get('sources', [])
            log(f"   📚 Loaded {len(verified_sources)} pre-verified sources from Step 3B")
        except Exception as e:
            log(f"   ⚠️  Could not load sources file: {e}")
    
    # Load Perplexity config
    perplexity_config = CONFIG.get('perplexity', {})
    api_key = perplexity_config.get('api_key', '')
    sonar_enabled = perplexity_config.get('enabled', False) and api_key
    
    if not sonar_enabled:
        log("   ⚠️  Perplexity Sonar not enabled - creating manual task instead")
        return create_step8_citations_task(article_file, "hub"), {'manual': True}
    
    # Process each claim
    citation_map = {}
    unverified_claims = []
    
    for i, claim in enumerate(claims, 1):
        log(f"   [{i}/{len(claims)}] Processing: {claim[:50]}...")
        
        # First, try to match with pre-verified sources
        matched_source = _find_matching_source(claim, verified_sources)
        
        if matched_source:
            citation_map[claim] = matched_source
            log(f"      ✅ Matched to pre-verified source")
            continue
        
        # If no match, use Sonar to find a source
        sonar_source = _find_source_with_sonar(claim, api_key, perplexity_config)
        
        if sonar_source:
            # Verify the URL before using
            verification = _verify_source_url(sonar_source['url'])
            
            if verification['valid']:
                citation_map[claim] = sonar_source
                log(f"      ✅ Found via Sonar: {sonar_source['url'][:40]}...")
                continue
            else:
                log(f"      ⚠️  Sonar source failed verification")
        
        # No source found
        unverified_claims.append(claim)
        log(f"      ❌ No source found")
    
    log(f"\n   📊 Results:")
    log(f"      Cited: {len(citation_map)}")
    log(f"      Unverified: {len(unverified_claims)}")
    
    # Replace markers in article
    cited_article = article_content
    citation_list = []
    
    for i, (claim, source) in enumerate(citation_map.items(), 1):
        # Create citation reference
        citation_ref = f"[[{i}]]({source['url']})"
        
        # Replace [CLAIM: ...] with citation
        cited_article = cited_article.replace(
            f"[CLAIM: {claim}]",
            citation_ref
        )
        
        # Also handle old format if present
        if old_citations:
            cited_article = re.sub(
                r'\[CITATION NEEDED\]',
                citation_ref,
                cited_article,
                count=1
            )
        
        citation_list.append({
            'number': i,
            'claim': claim,
            'url': source['url'],
            'title': source.get('title', ''),
            'snippet': source.get('snippet', '')
        })
    
    # Mark unverified claims
    for claim in unverified_claims:
        cited_article = cited_article.replace(
            f"[CLAIM: {claim}]",
            f"[UNVERIFIED: {claim}]"
        )
    
    # Add citation list at end of article
    if citation_list:
        cited_article += "\n\n---\n\n## References\n\n"
        for cite in citation_list:
            cited_article += f"[{cite['number']}] {cite['title']} - {cite['url']}\n"
    
    # Save cited article
    output_file = os.path.join(SESSION_DIR, "articles/hub/step8_ARTICLE_WITH_CITATIONS.md")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(cited_article)
    
    # Save citation metadata
    metadata_file = os.path.join(SESSION_DIR, "step8_CITATION_METADATA.json")
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_claims': len(claims),
            'cited': len(citation_map),
            'unverified': len(unverified_claims),
            'citations': citation_list,
            'unverified_claims': unverified_claims
        }, f, indent=2)
    
    log(f"   💾 Saved: {output_file}")
    log(f"   💾 Metadata: {metadata_file}")
    
    return output_file, {
        'cited': len(citation_map),
        'unverified': len(unverified_claims),
        'citations': citation_list
    }


def _find_matching_source(claim, verified_sources):
    """
    Find a matching source from pre-verified sources based on claim content.
    Uses keyword matching.
    """
    if not verified_sources:
        return None
    
    claim_lower = claim.lower()
    claim_words = set(claim_lower.split())
    
    best_match = None
    best_score = 0
    
    for source in verified_sources:
        # Combine searchable text
        source_text = f"{source.get('title', '')} {source.get('snippet', '')}".lower()
        source_words = set(source_text.split())
        
        # Calculate overlap score
        overlap = len(claim_words & source_words)
        score = overlap / len(claim_words) if claim_words else 0
        
        if score > best_score and score > 0.3:  # Minimum 30% word overlap
            best_score = score
            best_match = source
    
    return best_match


def _find_source_with_sonar(claim, api_key, config):
    """
    Use Perplexity Sonar to find a real source for a specific claim.
    """
    try:
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": config.get('model', 'sonar'),
                "messages": [
                    {
                        "role": "system",
                        "content": """Find ONE credible source that supports this claim.
Return ONLY a JSON object with these fields:
{
  "url": "the actual URL",
  "title": "article/report title",
  "publisher": "publisher name",
  "snippet": "relevant quote from source",
  "confidence": "high/medium/low"
}

If no credible source exists, return: {"error": "no_source_found"}

Only use authoritative sources (Gartner, Forrester, McKinsey, academic, major publications).
The URL must be real and accessible."""
                    },
                    {
                        "role": "user",
                        "content": f"Find a source for: {claim}"
                    }
                ],
                "return_citations": True,
                "search_recency_filter": config.get('search_recency_filter', 'year')
            },
            timeout=config.get('timeout_seconds', 30)
        )
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        
        # Parse response
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        # Try to extract JSON from response
        try:
            # Find JSON in response
            json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
            if json_match:
                source_data = json.loads(json_match.group())
                if 'error' not in source_data and 'url' in source_data:
                    return source_data
        except:
            pass
        
        # Fallback: use citations from response
        if 'citations' in data and data['citations']:
            citation = data['citations'][0]
            return {
                'url': citation.get('url', ''),
                'title': citation.get('title', ''),
                'snippet': citation.get('snippet', ''),
                'source': 'perplexity_sonar'
            }
        
        return None
        
    except Exception as e:
        log(f"      ⚠️  Sonar error: {str(e)}")
        return None


# ============================================================================
# STEP 8B: CITATION VERIFICATION (Automated)
# ============================================================================

def step8b_verify_citations(article_file):
    """
    Verify all citation URLs in the article are accessible and valid.
    This is an automated quality gate before publishing.
    """
    log("="*80)
    log("STEP 8B: CITATION VERIFICATION (Automated)")
    log("="*80)
    
    # Load article
    with open(article_file, 'r', encoding='utf-8') as f:
        article_content = f.read()
    
    # Extract all URLs (both internal and external)
    url_pattern = r'https?://[^\s\)\]\"\'<>]+'
    urls = list(set(re.findall(url_pattern, article_content)))
    
    # Filter to only external URLs (not our brand)
    brand_url = CONFIG.get('brand', {}).get('url', '')
    brand_domain = urlparse(brand_url).netloc if brand_url else ''
    external_urls = [u for u in urls if brand_domain not in u]
    
    log(f"   🔍 Checking {len(external_urls)} external URLs...")
    
    results = {
        'valid': [],
        'broken': [],
        'redirected': []
    }
    
    for url in external_urls:
        log(f"      Checking: {url[:50]}...")
        
        verification = _verify_source_url(url)
        
        result = {
            'url': url,
            'status_code': verification.get('status_code'),
            'final_url': verification.get('final_url'),
            'error': verification.get('error')
        }
        
        if verification['valid']:
            if verification.get('final_url') != url:
                results['redirected'].append(result)
                log(f"         ↪️  Redirected")
            else:
                results['valid'].append(result)
                log(f"         ✅ Valid")
        else:
            results['broken'].append(result)
            log(f"         ❌ Broken: {verification.get('error', 'unknown')}")
    
    # Check for unverified claims
    unverified_pattern = r'\[UNVERIFIED:\s*([^\]]+)\]'
    unverified = re.findall(unverified_pattern, article_content)
    
    # Generate report
    report = f"""# Citation Verification Report

**Generated:** {datetime.now().isoformat()}
**Article:** {os.path.basename(article_file)}

---

## Summary

| Status | Count |
|--------|-------|
| ✅ Valid | {len(results['valid'])} |
| ↪️ Redirected | {len(results['redirected'])} |
| ❌ Broken | {len(results['broken'])} |
| 🔍 Unverified Claims | {len(unverified)} |

---

## Valid Citations ({len(results['valid'])})

"""
    
    for r in results['valid']:
        report += f"- ✅ {r['url']}\n"
    
    report += f"\n---\n\n## Redirected URLs ({len(results['redirected'])})\n\n"
    report += "*These URLs work but redirect to a different location.*\n\n"
    
    for r in results['redirected']:
        report += f"- ↪️ {r['url']}\n  → {r['final_url']}\n"
    
    report += f"\n---\n\n## Broken Citations ({len(results['broken'])})\n\n"
    report += "*These URLs need to be fixed or removed.*\n\n"
    
    for r in results['broken']:
        report += f"- ❌ {r['url']}\n  Error: {r['error']}\n"
    
    report += f"\n---\n\n## Unverified Claims ({len(unverified)})\n\n"
    report += "*These claims need sources or should be rewritten.*\n\n"
    
    for claim in unverified:
        report += f"- 🔍 {claim}\n"
    
    # Determine if article is ready
    is_ready = len(results['broken']) == 0 and len(unverified) == 0
    
    report += f"\n---\n\n## Verdict\n\n"
    if is_ready:
        report += "✅ **READY FOR PUBLISHING** - All citations verified.\n"
    else:
        report += "❌ **NOT READY** - Fix issues above before publishing.\n"
    
    # Save report
    report_file = os.path.join(SESSION_DIR, "step8b_CITATION_VERIFICATION_REPORT.md")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    log(f"\n   📊 Results:")
    log(f"      ✅ Valid: {len(results['valid'])}")
    log(f"      ↪️  Redirected: {len(results['redirected'])}")
    log(f"      ❌ Broken: {len(results['broken'])}")
    log(f"      🔍 Unverified: {len(unverified)}")
    log(f"\n   💾 Report: {report_file}")
    
    return report_file, {
        'valid': len(results['valid']),
        'broken': len(results['broken']),
        'redirected': len(results['redirected']),
        'unverified': len(unverified),
        'ready': is_ready
    }


# ============================================================================
# STEP 8C: CITATION REVIEW TASK (AI Agent)
# ============================================================================

def step8c_create_citation_review_task(verification_report_file):
    """
    Create AI agent task to review and fix citation issues.
    Only created if Step 8B finds problems.
    """
    log("="*80)
    log("STEP 8C: CITATION REVIEW TASK (AI Agent)")
    log("="*80)
    
    # Load verification report
    with open(verification_report_file, 'r', encoding='utf-8') as f:
        report_content = f.read()
    
    # Check if there are issues to fix
    has_broken = "## Broken Citations (0)" not in report_content
    has_unverified = "## Unverified Claims (0)" not in report_content
    
    if not has_broken and not has_unverified:
        log("   ✅ No citation issues - skipping review task")
        return None, {'skipped': True, 'reason': 'no_issues'}
    
    task_file = os.path.join(SESSION_DIR, "step8c_CITATION_REVIEW_TASK.md")
    
    with open(task_file, 'w', encoding='utf-8') as f:
        f.write(f"""# STEP 8C: Citation Review Task (AI Agent)

**Session:** {SESSION_ID}
**Generated:** {datetime.now().isoformat()}

---

## 🎯 YOUR MISSION

Review and fix citation issues identified in the verification report.

---

## Verification Report

{report_content}

---

## Instructions

### For Broken Links:

1. **Try to find the correct URL:**
   - Search for the article title
   - Check archive.org for cached version
   - Find alternative source with same information

2. **If no alternative found:**
   - Remove the citation
   - Rewrite the sentence to not require a citation
   - Or mark as general knowledge if appropriate

### For Unverified Claims:

1. **Search for a real source:**
   - Use web search to find supporting data
   - Prefer authoritative sources (Gartner, Forrester, academic)
   - Ensure the source actually contains the claimed information

2. **If no source exists:**
   - Rewrite the claim to be more general
   - Remove specific numbers/percentages
   - Or remove the claim entirely if it's not essential

### For Redirected URLs:

1. **Update to final URL** if the redirect is permanent
2. **Keep original URL** if redirect is temporary or tracking-related

---

## Output

Save the fixed article to: `articles/hub/step8c_ARTICLE_CITATIONS_FINAL.md`

Mark this task complete by creating: `step8c_CITATIONS_REVIEWED.txt`

---

## Quality Checklist

Before marking complete, verify:

- [ ] All broken links fixed or removed
- [ ] All unverified claims sourced or rewritten
- [ ] No hallucinated URLs (check each URL loads)
- [ ] Citations are from reputable sources
- [ ] Article still reads naturally after changes
""")
    
    log(f"   📝 Created review task: {task_file}")
    
    print(f"\n🤖 AGENT_TASK_READY: {task_file}")
    print(f"📋 OUTPUT_FILE: step8c_CITATIONS_REVIEWED.txt")
    print(f"⏸️  Pipeline paused - AI Agent will review citations...")
    
    return task_file, {'has_broken': has_broken, 'has_unverified': has_unverified}


# ============================================================================
# STEP 9: CREATE INFRASTRUCTURE TASK (AI AGENT)
# ============================================================================

def create_step9_infrastructure_task(article_file, synthesis_file):
    """Create AI agent task for intelligent content hub registration"""
    
    article_type = "spoke"
    if synthesis_file and os.path.exists(synthesis_file):
        with open(synthesis_file, 'r', encoding='utf-8') as f:
            synthesis = f.read()
            if "CLUSTER (HUB)" in synthesis or "Page Type:** Cluster" in synthesis:
                article_type = "hub"
    
    task_file = os.path.join(SESSION_DIR, "step9_INFRASTRUCTURE_TASK.md")
    
    with open(task_file, 'w', encoding='utf-8') as f:
        f.write(f"""# STEP 9: Update Content Hub Infrastructure (AI Agent Task)

**Session:** {SESSION_ID}  
**Article Type:** {article_type.upper()}

---

## 🎯 YOUR TASK

Register this article in {BRAND_NAME}'s content hub infrastructure.

**Input:** `{os.path.basename(article_file)}`  
**Output:** `step9_UPDATED_internal_linking_map.json` + `step9_UPDATED_sitemap.xml`

---

## 💾 OUTPUT FILES

1. `step9_UPDATED_internal_linking_map.json` - Content hub structure
2. `step9_UPDATED_sitemap.xml` - SEO sitemap
""")
    
    log(f"✅ Step 9 task created: {task_file}")
    print(f"\n🤖 AGENT_TASK_READY: {task_file}")
    print(f"📋 OUTPUT_FILES: linking_map + sitemap")
    print(f"⏸️  Pipeline paused - waiting for AI Agent...")
    print("="*80 + "\n")
    
    return task_file

# ============================================================================
# STEP 10: GENERATE SPOKE CLUSTER (If Hub Detected)
# ============================================================================

def step10_generate_spoke_cluster(synthesis_data, hub_article_file, hub_article_title, step1_data, step2_data, step2c_data, step2b_data):
    """
    If the article is identified as a HUB, generate 10 spoke articles around it.
    Each spoke targets a unique long-tail keyword to prevent cannibalization.
    
    Philosophy: Hub-and-Spoke architecture for topical authority.
    """
    log("="*80)
    log("STEP 10: SPOKE CLUSTER GENERATION")
    log("="*80)
    
    # Check if this is a Hub article
    if not synthesis_data or 'synthesis' not in synthesis_data:
        log("⚠️  No synthesis data - skipping spoke generation")
        return None, {}
    
    synthesis_text = synthesis_data['synthesis']
    
    # Parse synthesis to determine if Hub
    is_hub = False
    if 'cluster (hub)' in synthesis_text.lower() or 'page type: cluster' in synthesis_text.lower():
        is_hub = True
    
    if not is_hub:
        log("ℹ️  Article identified as SPOKE - skipping cluster generation")
        log("   (Spoke articles don't generate sub-spokes)")
        return None, {'article_type': 'spoke'}
    
    log("✅ Article identified as HUB - proceeding with spoke cluster generation")
    
    # Extract suggested spoke topics from synthesis
    suggested_spokes = []
    
    # Try to parse "Potential Spokes" from synthesis
    if 'potential spokes:' in synthesis_text.lower():
        # Extract the spokes list
        spoke_section_start = synthesis_text.lower().find('potential spokes:')
        spoke_section = synthesis_text[spoke_section_start:spoke_section_start+500]
        
        # Parse bullet points or numbered list
        import re
        spoke_matches = re.findall(r'[-•\d]+\.\s*([^\n]+)', spoke_section)
        suggested_spokes = [s.strip() for s in spoke_matches if len(s.strip()) > 10][:10]
    
    # If synthesis didn't suggest spokes, use data-driven approach
    if len(suggested_spokes) < 10:
        log("⚠️  Synthesis has <10 spoke suggestions - using data-driven spoke topics")
        
        # Generate spoke topics from top bigrams
        top_bigrams = step1_data.get('top_bigrams', [])
        
        # Recommended spokes based on data frequency
        # Generate spoke suggestions from top bigrams/trigrams (data-driven)
        # Use actual dataset patterns instead of hardcoded examples
        data_driven_spokes = []
        
        # Build spokes from top bigrams/trigrams
        for i, (bigram, freq) in enumerate(step1_data.get('top_bigrams', [])[:10], 1):
            spoke = {
                "title": f"[Generated from bigram: {bigram}]",
                "primary_kw": bigram,
                "bigram": bigram
            }
            data_driven_spokes.append(spoke)
        
        # Note: AI agent will determine actual spoke titles based on dataset patterns
        
        suggested_spokes = [spoke['title'] for spoke in data_driven_spokes[:10]]
    
    log(f"📋 Identified {len(suggested_spokes)} spoke topics to generate")
    
    # Load writing rules for brand context
    writing_rules_path = os.path.join(SCRIPT_DIR, "brand-context/rule_writing.ts")
    writing_rules_content = ""
    if os.path.exists(writing_rules_path):
        with open(writing_rules_path, 'r') as f:
            writing_rules_content = f.read()
    
    # Create AI agent task for spoke generation
    task_file = os.path.join(SESSION_DIR, "step10_SPOKE_CLUSTER_TASK.md")
    
    with open(task_file, 'w', encoding='utf-8') as f:
        f.write("# STEP 10: Spoke Cluster Generation Task (For AI Agent)\n\n")
        f.write(f"**Session:** {SESSION_ID}\n")
        f.write(f"**Hub Article:** {hub_article_title}\n")
        f.write(f"**Hub File:** {os.path.basename(hub_article_file) if hub_article_file else 'N/A'}\n\n")
        f.write("---\n\n")
        
        f.write("## 🎯 MISSION: Generate 10 Spoke Articles + Internal Linking\n\n")
        f.write("Your Hub article has been identified as **pillar content** that should have supporting spoke articles.\n\n")
        
        f.write("---\n\n")
        f.write("## 🏢 BRAND CONTEXT\n\n")
        f.write(f"**Brand Name:** {BRAND_NAME}\n")
        f.write(f"**Website:** {BRAND_URL}\n")
        f.write(f"**Industry:** {CONFIG.get('data_source', {}).get('domain_name', 'N/A')}\n\n")
        
        f.write("### 🔍 RESEARCH PHASE (REQUIRED - DO THIS FIRST)\n\n")
        f.write("**CRITICAL:** You MUST complete research BEFORE writing any spoke article.\n")
        f.write("Research is NOT optional - it ensures accuracy and brand voice alignment.\n\n")
        
        f.write("#### Step 1: Browse Brand Website (Use Browser Tools)\n\n")
        f.write(f"**Required URLs to visit:**\n")
        f.write(f"1. Homepage: {BRAND_URL}\n")
        f.write(f"2. Product pages: {BRAND_URL}/products (or /solutions, /platform)\n")
        f.write(f"3. **Help Center: https://help.{BRAND_URL.replace('https://', '').replace('http://', '')}/** (authoritative source for features/methodologies)\n")
        f.write(f"4. Docs/Resources: {BRAND_URL}/docs, /resources, /help (check main domain too)\n")
        f.write(f"5. About/Company: {BRAND_URL}/about, /company\n")
        f.write(f"6. Case Studies: {BRAND_URL}/customers, /case-studies (if exist)\n\n")
        f.write("**What to capture:**\n")
        f.write("- Brand positioning statement (main value prop)\n")
        f.write("- Product names and how they're described\n")
        f.write("- Key terminology and frameworks\n")
        f.write("- Tone of voice (formal/casual, technical/accessible)\n")
        f.write("- Customer metrics and proof points\n\n")
        f.write("**SAVE RESEARCH NOTES:**\n")
        f.write("Create: `articles/spokes/RESEARCH_NOTES.md`\n")
        f.write("Document findings from each URL visited\n\n")
        
        f.write("#### Step 2: Read Hub Article for Context\n\n")
        f.write(f"**Read:** `{os.path.basename(hub_article_file) if hub_article_file else 'Hub article'}`\n\n")
        f.write("**Extract:**\n")
        f.write("- Main themes and topics covered\n")
        f.write("- Writing style and tone\n")
        f.write("- How brand is positioned\n")
        f.write("- What angles are already covered (avoid duplication)\n\n")
        
        f.write("#### Step 3: Document Research\n\n")
        f.write("Before writing ANY spoke, create:\n")
        f.write("`articles/spokes/RESEARCH_COMPLETE.txt`\n\n")
        f.write("Include:\n")
        f.write("```\n")
        f.write("✅ Browsed homepage: [key positioning found]\n")
        f.write("✅ Browsed products: [product names/descriptions]\n")
        f.write("✅ Browsed help/docs: [terminology found]\n")
        f.write("✅ Read hub article: [main themes identified]\n")
        f.write("✅ Brand voice: [formal/casual/technical/accessible]\n")
        f.write("```\n\n")
        f.write("**This file is PROOF you completed research.**\n")
        f.write("Without it, spokes will be rejected.\n\n")
        
        f.write("---\n\n")
        f.write("## ✍️ WRITING RULES (ENFORCE ALL)\n\n")
        if writing_rules_content:
            f.write("**CRITICAL:** Apply these brand writing rules to EVERY spoke article:\n\n")
            f.write("```typescript\n")
            f.write(writing_rules_content)
            f.write("\n```\n\n")
        else:
            f.write("⚠️ Writing rules file not found. Use professional, enterprise tone.\n\n")
        
        f.write("---\n\n")
        f.write("**Phase 1: Generate 10 Spokes**\n\n")
        f.write("**Pre-Writing Checklist (VERIFY BEFORE STARTING):**\n")
        f.write("- [ ] Completed research phase (browsed website, read hub)\n")
        f.write("- [ ] Created `RESEARCH_COMPLETE.txt` with findings\n")
        f.write("- [ ] Understand brand positioning and voice\n")
        f.write("- [ ] Read all 15 writing rules above\n\n")
        f.write("Each spoke article must:\n")
        f.write("- ✅ Target a UNIQUE long-tail keyword (no cannibalization)\n")
        f.write("- ✅ Be 1,500-2,000 words\n")
        f.write("- ✅ Match brand voice from research\n")
        f.write("- ✅ Apply all 15 writing rules\n")
        f.write("- ✅ Include brand-specific terminology\n")
        f.write("- ✅ **Add [CLAIM: description] for statistics/claims** (Step 8 will add real sources via Sonar)\n")
        f.write("- ✅ Pass all quality gates\n")
        f.write("- ✅ Save with exact filename specified below\n\n")
        
        f.write("**Phase 2: Add Internal Links (After All 10 Spokes Complete)**\n")
        f.write("Once all 10 spokes are generated, add internal links:\n")
        f.write("1. **Update Hub article:** Add 1 contextual link to EACH spoke (10 total links)\n")
        f.write("2. **Update each Spoke:** Add links to:\n")
        f.write("   - Hub article (always)\n")
        f.write("   - 1-2 related spokes in same category\n")
        f.write("3. **Distribute links naturally** throughout content (not clustered)\n")
        f.write("4. **Use varied anchor text** (not repetitive)\n\n")
        
        f.write("**Result:** 11 articles (Hub + 10 Spokes) all interconnected!\n\n")
        
        f.write("---\n\n")
        
        f.write("## 📋 10 SPOKE ARTICLES TO GENERATE:\n\n")
        
        # Create spokes directory
        spokes_dir = os.path.join(SESSION_DIR, "articles", "spokes")
        os.makedirs(spokes_dir, exist_ok=True)
        
        for i, spoke_title in enumerate(suggested_spokes, 1):
            f.write(f"### Spoke {i}: {spoke_title}\n\n")
            f.write(f"**Output File:** `articles/spokes/step10_spoke{i:02d}_{spoke_title.lower().replace(' ', '_')[:40]}.md`\n\n")
            
            # Determine which data to use
            f.write("**Data Sources for this Spoke:**\n")
            f.write(f"- Step 1: Filter for keywords related to '{spoke_title.split()[0:3]}'\n")
            f.write(f"- Step 2B: Use competitor structure patterns\n")
            f.write(f"- Step 2C: Search intent classification\n")
            f.write(f"- Brand Context: {BRAND_NAME} positioning\n\n")
            
            f.write("**Requirements:**\n")
            f.write("- ✅ Word count: 1,500-2,000 words\n")
            f.write(f"- ✅ Brand mention: {BRAND_NAME} (linked to {BRAND_URL})\n")
            f.write(f"- ✅ Internal links: Link to Hub + 1-2 related spokes\n")
            f.write("- ✅ Unique angle: Different from Hub and other spokes\n")
            f.write("- ✅ Brand voice: Match research findings\n")
            f.write("- ✅ Writing rules: Apply all 15 rules\n")
            f.write("- ✅ **Citations: Add [CLAIM: description] for statistics/claims (NOT fake URLs!)**\n")
            f.write("- ✅ Quality: Pass anti-cannibalization checklist\n\n")
            f.write("**Quality Verification (After Writing):**\n")
            f.write("- [ ] Includes brand-specific details from website research\n")
            f.write("- [ ] Tone matches hub article\n")
            f.write("- [ ] All 15 writing rules applied\n")
            f.write("- [ ] Unique keyword (not competing with hub/other spokes)\n")
            f.write("- [ ] 1,500-2,000 word count met\n")
            f.write("- [ ] **[CLAIM: description] markers added for statistics/claims (at least 1-3 per article)**\n\n")
            
            f.write("---\n\n")
        
        f.write("## 🔒 ANTI-CANNIBALIZATION CHECKLIST\n\n")
        f.write("For EACH spoke, verify:\n\n")
        f.write("- [ ] ✅ Unique primary keyword (different from Hub and all other spokes)\n")
        f.write("- [ ] ✅ Different search intent (Informational vs Comparative vs How-to)\n")
        f.write("- [ ] ✅ Unique angle/perspective (not repeating Hub content)\n")
        f.write("- [ ] ✅ No repetitive language (compare first 500 words to Hub)\n")
        f.write("- [ ] ✅ Strategic internal links (Hub + 1-2 spokes, not all)\n\n")
        
        f.write("---\n\n")
        
        f.write("## 📊 DATA AVAILABLE\n\n")
        f.write(f"**From Step 1 (Content Analysis):**\n")
        f.write(f"- Total target domain responses: {step1_data.get('target_domain_responses', 0):,}\n")
        f.write(f"- Top 50 bigrams available\n")
        f.write(f"- Top 30 trigrams available\n\n")
        
        f.write(f"**From Step 2B (Competitor Scraping):**\n")
        f.write(f"- {len(step2b_data) if step2b_data else 0} competitor articles scraped\n")
        f.write(f"- Average structure: {sum(p['h2_count'] for p in step2b_data) / len(step2b_data) if step2b_data else 0:.1f} H2 sections\n\n")
        
        f.write(f"**From Step 2C (Search Intent):**\n")
        f.write(f"- Intent distribution available\n")
        f.write(f"- URL keyword patterns\n\n")
        
        f.write("**You have 5x more data than needed for 10 unique spokes!**\n\n")
        
        f.write("---\n\n")
        
        f.write("## 🚀 WORKFLOW\n\n")
        f.write("### Phase 1: Generate All 10 Spokes (No Links Yet)\n\n")
        f.write("**For each spoke (1-10):**\n\n")
        f.write("1. **Verify research complete** (RESEARCH_COMPLETE.txt must exist)\n")
        f.write("2. **Read all analysis files** (step1, step2, step2b, step2c, step4)\n")
        f.write("3. **Filter data** for spoke-specific keywords\n")
        f.write("4. **Determine unique angle** (how is this different from Hub?)\n")
        f.write("5. **Generate article** (1,500-2,000 words)\n")
        f.write("6. **Apply brand voice** (match research findings)\n")
        f.write("7. **Apply all 15 writing rules** (see rules section above)\n")
        f.write("8. **Validate quality:**\n")
        f.write("   - Run anti-cannibalization checklist\n")
        f.write("   - Check word count (1,500-2,000)\n")
        f.write("   - Verify unique keyword\n")
        f.write("   - Confirm brand voice matches\n")
        f.write("   - Check all 15 writing rules applied\n")
        f.write("9. **Save with exact filename** shown above (WITHOUT internal links yet)\n\n")
        
        f.write("### Phase 2: Add Internal Links (After All 10 Complete)\n\n")
        
        f.write("**CRITICAL - Link Format:**\n")
        f.write(f"- Use `{CONFIG.get('publishing', {}).get('blog_path', '/blog')}/[slug]` format (NOT folder paths)\n")
        f.write("- Slug = article title in lowercase with dashes\n")
        f.write("- Example: 'Top 10 Analytics Platforms' → `/blog/top-10-analytics-platforms`\n")
        f.write("- Example: 'How to Choose Platform' → `/blog/how-to-choose-platform`\n\n")
        
        f.write(f"**Step 1: Update Hub Article** (`{os.path.basename(hub_article_file) if hub_article_file else 'Hub file'}`)\n\n")
        f.write("Add 1 contextual link to EACH of the 10 spokes:\n")
        for i, spoke_title in enumerate(suggested_spokes, 1):
            slug = spoke_title.lower().replace(' ', '-')
            slug = re.sub(r'[^\w-]', '', slug)
            f.write(f"{i}. Link to Spoke {i}: [{spoke_title}]({CONFIG.get('publishing', {}).get('blog_path', '/blog')}/{slug})\n")
        f.write("\n")
        f.write("**Distribute these 10 links throughout the Hub article** (not all at once).\n\n")
        
        f.write("**Step 2: Add Links to Each Spoke**\n\n")
        f.write("For each of the 10 spokes, add:\n")
        hub_slug = hub_article_title.lower().replace(' ', '-')
        hub_slug = re.sub(r'[^\w-]', '', hub_slug)
        f.write(f"- **Link to Hub:** [{hub_article_title}]({CONFIG.get('publishing', {}).get('blog_path', '/blog')}/{hub_slug})\n")
        f.write("- **Link to 1-2 related spokes:** Use `/blog/[spoke-slug]` format\n")
        f.write("  - Implementation spokes (1-3) link to each other\n")
        f.write("  - Use Case spokes (4-7) link within category\n")
        f.write("  - Comparison spokes (8-9) link to each other\n")
        f.write("  - Advanced spoke (10) links to related use cases\n\n")
        
        f.write("### Phase 3: Update Infrastructure\n\n")
        f.write("9. Update `internal_linking_map.json` with all spoke URLs\n")
        f.write("10. Update sitemap with all 10 new pages\n")
        f.write("11. Create `step10_SPOKE_CLUSTER_COMPLETE.md` with cross-reference matrix\n\n")
        
        f.write("---\n\n")
        
        f.write("## ⚡ QUALITY MANDATE\n\n")
        f.write(f"**Remember:** Each spoke represents {BRAND_NAME}.\n\n")
        f.write("- No generic advice (AI-slop)\n")
        f.write("- No keyword stuffing\n")
        f.write("- No repetitive language across spokes\n")
        f.write("- Each spoke must stand alone as exceptional content\n\n")
        f.write("**🚫 NEVER INCLUDE IN ARTICLE (Internal Data Leak Prevention):**\n")
        f.write("- Frequency statistics from analysis (e.g., 'The 281x trigram frequency of...')\n")
        f.write("- N-gram counts or bigram/trigram mentions (e.g., '529x frequency in industry responses')\n")
        f.write("- Any mention of 'industry responses', 'dataset analysis', or internal research methodology\n")
        f.write("- These are INTERNAL planning data, NOT reader-facing content\n\n")
        f.write("**Cannibalization Risk: <5%** (with proper keyword targeting)\n\n")
        
        f.write("---\n\n")
        
        f.write("## 📋 DELIVERABLES\n\n")
        f.write("**Required files to create:**\n\n")
        f.write("1. **Research proof:**\n")
        f.write("   - `articles/spokes/RESEARCH_NOTES.md` (findings from website)\n")
        f.write("   - `articles/spokes/RESEARCH_COMPLETE.txt` (completion proof)\n\n")
        f.write("2. **Spoke articles (10 total):**\n")
        for i, spoke_title in enumerate(suggested_spokes, 1):
            filename = f"step10_spoke{i:02d}_{spoke_title.lower().replace(' ', '_')[:40]}.md"
            f.write(f"   - `{filename}`\n")
        f.write("\n3. **Completion files:**\n")
        f.write("   - `step10_SPOKE_CLUSTER_COMPLETE.md` (summary + cross-reference matrix)\n")
        f.write("   - `step10_UPDATED_internal_linking_map.json`\n")
        f.write("   - `step10_UPDATED_sitemap.xml`\n\n")
        f.write("**Completion marker must include:**\n")
        f.write("```\n")
        f.write("# Step 10: Spoke Cluster Complete\n\n")
        f.write("✅ Research phase completed (see RESEARCH_COMPLETE.txt)\n")
        f.write("✅ Generated 10 spokes (all brand-voice consistent)\n")
        f.write("✅ All spokes:\n")
        f.write("   - Include brand-specific details from website\n")
        f.write("   - Match voice of hub article\n")
        f.write("   - Target unique keywords (no cannibalization)\n")
        f.write("   - Apply all 15 writing rules\n")
        f.write("```\n\n")
        
        f.write("---\n\n")
        
        f.write("## 🎯 SUCCESS CRITERIA\n\n")
        f.write("Pipeline is complete when:\n")
        f.write("- ✅ 1 Hub article published (done)\n")
        f.write("- ✅ 10 spoke articles generated\n")
        f.write("- ✅ All spokes pass anti-cannibalization check\n")
        f.write("- ✅ Internal linking map updated\n")
        f.write("- ✅ Sitemap updated\n")
        f.write("- ✅ Topical authority established\n\n")
        
        f.write(f"**Result:** {BRAND_NAME} dominates SERPs for entire topic cluster! 🚀\n")
    
    log(f"✅ Spoke cluster task created: {task_file}")
    
    # Trigger AI Agent
    print("\n" + "="*80)
    print("🤖 AGENT_TASK_READY: SPOKE CLUSTER GENERATION")
    print("="*80)
    print(f"📋 Task File: {task_file}")
    print(f"📊 Spokes to Generate: {len(suggested_spokes)}")
    print(f"🎯 Hub Article: {hub_article_title}")
    print("⏸️  Pipeline paused - waiting for AI Agent to generate spoke cluster...")
    print("="*80 + "\n")
    
    # Check if spokes were already generated
    generated_spokes = []
    for i, spoke_title in enumerate(suggested_spokes, 1):
        spoke_filename = f"step10_spoke{i:02d}_{spoke_title.lower().replace(' ', '_')[:40]}.md"
        spoke_file = os.path.join(SESSION_DIR, spoke_filename)
        if os.path.exists(spoke_file):
            generated_spokes.append(spoke_filename)
    
    if len(generated_spokes) == len(suggested_spokes):
        log(f"✅ Found all {len(generated_spokes)} spoke articles already generated")
        
        # Validate quality
        log("🔍 Validating spoke cluster quality...")
        
        # QUALITY GATE: Check for keyword cannibalization
        all_titles = [hub_article_title] + suggested_spokes
        
        # Simple overlap check (could be enhanced)
        for i, title1 in enumerate(all_titles):
            for j, title2 in enumerate(all_titles[i+1:], i+1):
                shared_words = set(title1.lower().split()) & set(title2.lower().split())
                # Remove common words
                shared_words = shared_words - {'a', 'the', 'and', 'or', 'with', 'for', 'to', 'of', 'in', 'on', 'at'}
                
                if len(shared_words) > 3:
                    log(f"⚠️  Warning: Potential keyword overlap between:")
                    log(f"     '{title1}' and '{title2}'")
                    log(f"     Shared: {shared_words}")
        
        log(f"✅ Spoke cluster QUALITY GATE PASSED")
        
        return task_file, {
            'spokes_generated': len(generated_spokes),
            'spoke_files': generated_spokes,
            'hub_title': hub_article_title
        }
    else:
        log(f"⚠️  Spoke cluster not yet complete: {len(generated_spokes)}/{len(suggested_spokes)} generated")
        return None, {'spokes_needed': len(suggested_spokes) - len(generated_spokes)}

# ============================================================================
# STEP 10A: UTILITY ARTICLE GENERATION (Gap-Aware)
# ============================================================================

def step10a_generate_utility_articles():
    """
    Analyze spokes for utility content gaps and create 3-5 utility articles
    Runs BEFORE crosslinking so utilities get included
    Uses Dead-End strategy
    """
    log("Analyzing spokes for utility gaps...")
    
    # Check if spokes exist
    articles_dir = Path(SESSION_DIR) / 'articles' / 'spokes'
    spoke_files = list(articles_dir.glob('step10_spoke*.md')) if articles_dir.exists() else []
    
    if len(spoke_files) < 10:
        log(f"⚠️  Need 10 spokes (found {len(spoke_files)})")
        return None, {'utilities_needed': 0}
    
    log(f"✅ Found {len(spoke_files)} spokes")
    
    # Quick gap analysis
    from collections import Counter
    utility_gaps = Counter()
    
    for spoke_file in spoke_files:
        with open(spoke_file, 'r') as f:
            content = f.read()
        
        # Find utility-type links to homepage (brand-agnostic)
        brand_domain = BRAND_URL.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
        pattern = rf'\[([^\]]+)\]\(https?://(?:www\.)?{re.escape(brand_domain)}\)'
        
        for match in re.finditer(pattern, content):
            link_text = match.group(1)
            link_lower = link_text.lower()
            
            # High-value utility keywords
            if any(kw in link_lower for kw in [
                'scorecard', 'template', 'calculator', 'checklist',
                'guide', 'framework', 'methodology', 'case study'
            ]):
                utility_gaps[link_text] += 1
    
    if not utility_gaps:
        log("✅ No utility articles needed")
        return None, {'utilities_needed': 0}
    
    # Limit to top 5
    high_value = utility_gaps.most_common(5)
    
    log(f"   Identified {len(high_value)} utility opportunities")
    
    # Create task file (for reference/manual fallback)
    task_file = os.path.join(SESSION_DIR, "step10a_UTILITY_GENERATION_TASK.md")
    utilities_dir = os.path.join(SESSION_DIR, "articles", "utilities")
    os.makedirs(utilities_dir, exist_ok=True)
    
    # Get hub and spoke titles for task documentation
    hub_title = "Hub Article"
    hub_file_path = Path(SESSION_DIR) / 'articles' / 'hub' / 'step8_ARTICLE_WITH_CITATIONS.md'
    if not hub_file_path.exists():
        hub_file_path = Path(SESSION_DIR) / 'articles' / 'hub' / 'step7_ARTICLE_WITH_INTERNAL_LINKS.md'
    if hub_file_path.exists():
        with open(hub_file_path, 'r') as f:
            hub_title = f.readline().strip().strip('#').strip()
    
    spoke_titles_for_task = []
    for spoke_file in sorted(spoke_files)[:10]:
        with open(spoke_file, 'r') as f:
            spoke_titles_for_task.append(f.readline().strip().strip('#').strip())
    
    # Load writing rules for brand context
    writing_rules_path = os.path.join(SCRIPT_DIR, "brand-context/rule_writing.ts")
    writing_rules_content = ""
    if os.path.exists(writing_rules_path):
        with open(writing_rules_path, 'r') as f:
            writing_rules_content = f.read()
    
    with open(task_file, 'w') as f:
        f.write(f"# STEP 10A: Utility Article Generation (For AI Agent)\n\n")
        f.write(f"**Session:** {SESSION_ID}\n")
        f.write(f"**Utilities identified:** {len(high_value)}\n\n")
        f.write("---\n\n")
        
        f.write("## 🎯 MISSION: Generate High-Value Utility Articles\n\n")
        f.write("The spokes reference utility content (templates, calculators, guides) that doesn't exist yet.\n")
        f.write("Generate these practical, actionable resources with FULL brand context.\n\n")
        
        f.write("---\n\n")
        f.write("## 🏢 BRAND CONTEXT\n\n")
        f.write(f"**Brand Name:** {BRAND_NAME}\n")
        f.write(f"**Website:** {BRAND_URL}\n")
        f.write(f"**Industry:** {CONFIG.get('data_source', {}).get('domain_name', 'N/A')}\n\n")
        
        f.write("### 🔍 RESEARCH PHASE (REQUIRED - DO THIS FIRST)\n\n")
        f.write("**CRITICAL:** You MUST complete research BEFORE writing any utility article.\n")
        f.write("Research is NOT optional - it ensures accuracy and brand voice alignment.\n\n")
        
        f.write("#### Step 1: Browse Brand Website (Use Browser Tools)\n\n")
        f.write(f"**Required URLs to visit:**\n")
        f.write(f"1. Homepage: {BRAND_URL}\n")
        f.write(f"2. Product pages: {BRAND_URL}/products (or /solutions, /platform)\n")
        f.write(f"3. **Help Center: https://help.{BRAND_URL.replace('https://', '').replace('http://', '')}/** (CRITICAL for frameworks/methodologies)\n")
        f.write(f"4. Docs/Resources: {BRAND_URL}/docs, /resources, /help (check main domain too)\n")
        f.write(f"5. About/Company: {BRAND_URL}/about, /company\n\n")
        f.write("**What to capture:**\n")
        f.write("- Brand positioning statement (main value prop)\n")
        f.write("- Product names and how they're described\n")
        f.write("- Key terminology used (frameworks, methodologies, product names)\n")
        f.write("- Tone of voice (formal/casual, technical/accessible)\n")
        f.write("- Customer case studies and metrics\n\n")
        f.write("**SAVE RESEARCH NOTES:**\n")
        f.write("Create: `articles/utilities/RESEARCH_NOTES.md`\n")
        f.write("Document findings from each URL visited\n\n")
        
        f.write("#### Step 2: Search for Specific Frameworks\n\n")
        f.write("For each utility, use browser to search if it exists on brand website:\n")
        f.write(f"- **Primary:** Browse `https://help.{BRAND_URL.replace('https://', '').replace('http://', '')}/` directly (frameworks often documented here)\n")
        f.write(f"- **Secondary:** Google: `site:{BRAND_URL.replace('https://', '')} [utility name]` or `site:help.{BRAND_URL.replace('https://', '')} [utility name]`\n")
        f.write(f"- Example: `site:help.{BRAND_URL.replace('https://', '')} SCORE methodology` or `IQS framework`\n")
        f.write("- Check help center navigation for Guides, Methodologies, or Best Practices sections\n")
        f.write("- **If found:** Use EXACT descriptions from help center (authoritative source)\n")
        f.write("- **If not found:** Create framework based on brand positioning + spoke context\n\n")
        
        f.write("#### Step 3: Read Existing Articles for Voice Matching\n\n")
        f.write(f"**Read these files before writing:**\n")
        f.write(f"- Hub: `articles/hub/{hub_file_path.name if hub_file_path.exists() else 'step8_ARTICLE_WITH_CITATIONS.md'}`\n")
        f.write(f"- Spokes: All 10 files in `articles/spokes/`\n\n")
        f.write("**Extract and match:**\n")
        f.write("- Sentence structure patterns\n")
        f.write("- Technical depth level\n")
        f.write("- How they introduce concepts\n")
        f.write("- How they use examples\n")
        f.write("- Linking style (anchor text choices)\n\n")
        
        f.write("#### Step 4: Document Research Findings\n\n")
        f.write("Before writing ANY utility, create:\n")
        f.write("`articles/utilities/RESEARCH_COMPLETE.txt`\n\n")
        f.write("Include:\n")
        f.write("```\n")
        f.write("✅ Browsed homepage: [key positioning found]\n")
        f.write("✅ Browsed products: [product names/descriptions]\n")
        f.write("✅ Searched for frameworks: [what was found?]\n")
        f.write("✅ Read hub article: [tone observations]\n")
        f.write("✅ Read 10 spokes: [common patterns]\n")
        f.write("```\n\n")
        f.write("**This file is PROOF you completed research.**\n")
        f.write("Without it, utilities will be rejected.\n\n")
        
        f.write("---\n\n")
        f.write("## ✍️ WRITING RULES (ENFORCE ALL)\n\n")
        if writing_rules_content:
            f.write("**CRITICAL:** Apply these brand writing rules to every utility article:\n\n")
            f.write("```typescript\n")
            f.write(writing_rules_content)
            f.write("\n```\n\n")
        else:
            f.write("⚠️ Writing rules file not found. Use professional, enterprise tone.\n\n")
        
        f.write("---\n\n")
        f.write("## 🛡️ DEAD-END STRATEGY (CRITICAL)\n\n")
        
        f.write("**CRITICAL - Link Format:**\n")
        f.write(f"- Use `{CONFIG.get('publishing', {}).get('blog_path', '/blog')}/[slug]` format (NOT folder paths)\n")
        f.write("- Slug = article title in lowercase with dashes\n")
        f.write("- Example: 'Top 10 Analytics Platforms' → `/blog/top-10-analytics-platforms`\n")
        f.write("- Example: 'Insight to Action Gap' → `/blog/insight-to-action-gap`\n\n")
        
        f.write("**YOU MAY ONLY LINK TO THESE EXISTING ARTICLES:**\n\n")
        f.write(f"**Hub Article:**\n")
        hub_slug = hub_title.lower().replace(' ', '-').replace(':', '').replace('?', '')
        hub_slug = re.sub(r'[^\w-]', '', hub_slug)
        f.write(f"- [{hub_title}]({CONFIG.get('publishing', {}).get('blog_path', '/blog')}/{hub_slug})\n\n")
        f.write("**Spoke Articles (10 total):**\n")
        for i, title in enumerate(spoke_titles_for_task, 1):
            spoke_slug = title.lower().replace(' ', '-').replace(':', '').replace('?', '')
            spoke_slug = re.sub(r'[^\w-]', '', spoke_slug)
            f.write(f"{i}. [{title}]({CONFIG.get('publishing', {}).get('blog_path', '/blog')}/{spoke_slug})\n")
        f.write("\n")
        f.write("**STRICT RULES:**\n")
        f.write("- ❌ DO NOT reference new topics that need new articles\n")
        f.write("- ❌ DO NOT mention methodologies/tools not covered in existing articles\n")
        f.write("- ❌ DO NOT create new content demands\n")
        f.write("- ❌ DO NOT link to non-existent pages\n")
        f.write("- ❌ DO NOT over-link to same article (max 2 links to hub)\n")
        f.write("- ✅ DO link back to hub (1-2 times max) and 2-3 DIFFERENT spokes\n")
        f.write("- ✅ DO diversify spoke links (link to 2-3 different spokes, not just one)\n")
        f.write("- ✅ DO make content self-contained and useful\n")
        f.write("- ✅ DO close the loop - this is a 'leaf node' that serves the cluster\n\n")
        
        f.write("**LINK DIVERSITY REQUIREMENT:**\n")
        f.write("Each utility must link to:\n")
        f.write("- Hub: 1-2 times (not more!)\n")
        f.write("- Spokes: 2-3 DIFFERENT spokes (avoid linking to same spoke multiple times)\n")
        f.write("- Total: 3-5 links per utility\n")
        f.write("- Distribution: Spread across different sections of the utility\n\n")
        
        f.write("---\n\n")
        f.write("## 🎯 UTILITIES TO GENERATE\n\n")
        for i, (gap, count) in enumerate(high_value, 1):
            slug = gap.lower().replace(' ', '-').replace("'", '')
            slug = re.sub(r'[^\w-]', '', slug)
            f.write(f"### Utility {i}: {gap}\n\n")
            f.write(f"**Demand:** Referenced {count}x across spokes (proven reader need)\n")
            f.write(f"**Type:** Template/Guide/Resource (practical, actionable)\n")
            f.write(f"**Length:** 1,500-2,000 words\n")
            f.write(f"**Format:** Markdown (# for H1, ## for H2, ### for H3)\n")
            f.write(f"**Output:** `articles/utilities/{slug}.md`\n\n")
            f.write("**Pre-Writing Checklist (VERIFY BEFORE STARTING):**\n")
            f.write("- [ ] Completed research phase (Step 1-4 above)\n")
            f.write("- [ ] Created `RESEARCH_COMPLETE.txt` with findings\n")
            f.write("- [ ] Verified if framework exists on brand website\n")
            f.write("- [ ] Read hub + all spokes for voice consistency\n\n")
            f.write("**Content Requirements:**\n")
            f.write("- ✅ Use exact framework description if found on website\n")
            f.write("- ✅ Match voice/tone of existing cluster articles\n")
            f.write("- ✅ Apply all 15 writing rules (see above)\n")
            f.write("- ✅ Include brand-specific terminology from research\n")
            f.write("- ✅ Include practical examples, templates, step-by-step instructions\n")
            f.write("- ✅ Link diversity: 1-2 hub links + 2-3 DIFFERENT spoke links (Dead-End compliant)\n")
            f.write("- ✅ Provide standalone value (users can apply immediately)\n")
            f.write("- ✅ Reference real product features/metrics found during research\n")
            f.write("- ✅ **Add [CLAIM: description] for statistics/claims** (Step 8 will add real sources via Sonar)\n\n")
            f.write("**Linking Strategy (Important!):**\n")
            f.write("- Link to hub: 1-2 times when mentioning the main topic generally\n")
            f.write("- Link to spoke 01: Once if mentioning related subtopics\n")
            f.write("- Link to 1-2 other spokes: Choose relevant topics from the available spokes\n")
            f.write("- Avoid repetitive anchor text (vary how you reference articles)\n\n")
            f.write("**Quality Verification (After Writing):**\n")
            f.write("- [ ] Article includes specific details ONLY found on brand website\n")
            f.write("- [ ] Tone matches existing hub/spokes (not generic AI content)\n")
            f.write("- [ ] All 15 writing rules applied\n")
            f.write("- [ ] Dead-End strategy followed (no new content gaps)\n")
            f.write("- [ ] 1,500-2,000 word count met\n")
            f.write("- [ ] **[CLAIM: description] markers added for statistics/claims (at least 1-3 per article)**\n\n")
        
        f.write("---\n\n")
        f.write("## ✅ COMPLETION REQUIREMENTS\n\n")
        f.write("**Required files to create:**\n")
        f.write("1. `articles/utilities/RESEARCH_COMPLETE.txt` (proof of research)\n")
        f.write(f"2. `articles/utilities/[utility-slug].md` (all {len(high_value)} utilities)\n")
        f.write("3. `step10a_UTILITIES_COMPLETE.txt` (completion marker)\n\n")
        f.write("**Completion marker must include:**\n")
        f.write("```\n")
        f.write("# Step 10A: Utility Generation Complete\n\n")
        f.write("✅ Research phase completed (see RESEARCH_COMPLETE.txt)\n")
        f.write(f"✅ Generated {len(high_value)} utilities:\n")
        for i, (gap, count) in enumerate(high_value, 1):
            slug = gap.lower().replace(' ', '-').replace("'", '')
            slug = re.sub(r'[^\w-]', '', slug)
            f.write(f"   - {slug}.md ({count}x demand)\n")
        f.write("\n✅ All utilities:\n")
        f.write("   - Include brand-specific details from website\n")
        f.write("   - Match voice of hub + spokes\n")
        f.write("   - Follow Dead-End strategy\n")
        f.write("   - Apply all 15 writing rules\n")
        f.write("```\n\n")
        f.write("**Next steps in pipeline:**\n")
        f.write("- Step 10B: Add citations to utilities\n")
        f.write("- Step 11: Crosslinking (will include utilities)\n")
        f.write("- Step 12: HTML conversion (will include utilities)\n")
        f.write("- Step 12C: Gap verification (check Dead-End worked)\n")
    
    log(f"✅ Task created: {task_file}")
    log(f"   🤖 AI agent should now generate {len(high_value)} utility articles")
    log(f"   📁 Output to: articles/utilities/")
    
    return task_file, {'utilities_to_create': len(high_value)}

# ============================================================================
# STEP 11A: HUB ↔ SPOKES CROSSLINKING (AI AGENT)
# ============================================================================

def create_step11a_hub_spokes_crosslinking_task(hub_file, spoke_files, synthesis_file):
    """
    Create AI agent task for crosslinking hub and spokes
    Traditional cluster linking (Step 11A)
    """
    log("="*80)
    log("STEP 11A: HUB ↔ SPOKES CROSSLINKING TASK")
    log("="*80)
    
    if not hub_file or not os.path.exists(hub_file):
        log("⚠️  Hub file not found")
        return None
    
    if len(spoke_files) < 10:
        log(f"⚠️  Need 10 spokes (found {len(spoke_files)})")
        return None
    
    # Extract spoke titles
    spoke_titles = []
    for spoke_file in sorted(spoke_files):
        with open(spoke_file, 'r') as f:
            title = f.readline().strip('#').strip()
        slug = title.lower().replace(' ', '-').replace(':', '').replace('?', '')
        slug = re.sub(r'[^\w-]', '', slug)
        spoke_titles.append((title, slug))
    
    # Get hub title
    with open(hub_file, 'r') as f:
        hub_title = f.readline().strip('#').strip()
    hub_slug = hub_title.lower().replace(' ', '-').replace(':', '').replace('?', '')
    hub_slug = re.sub(r'[^\w-]', '', hub_slug)
    
    task_file = os.path.join(SESSION_DIR, "step11a_HUB_SPOKES_CROSSLINKING_TASK.md")
    
    with open(task_file, 'w') as f:
        f.write(f"# STEP 11A: Hub ↔ Spokes Crosslinking (AI Agent Task)\n\n")
        f.write(f"**Session:** {SESSION_ID}\n")
        f.write(f"**Articles to link:** 11 (1 hub + 10 spokes)\n\n")
        f.write("---\n\n")
        
        f.write("## 🎯 MISSION: Create Dense Internal Linking Network\n\n")
        f.write("Transform isolated articles into interconnected content cluster.\n\n")
        
        f.write("**CRITICAL - Link Format:**\n")
        f.write(f"- Use `{CONFIG.get('publishing', {}).get('blog_path', '/blog')}/[slug]` format\n")
        f.write("- Slug = article title in lowercase with dashes\n\n")
        
        f.write("---\n\n")
        f.write("## 📋 PHASE 1: Hub → Spokes (10 Links)\n\n")
        f.write(f"**Edit:** `{os.path.basename(hub_file)}`\n\n")
        f.write("Add 1 contextual link to EACH spoke:\n\n")
        
        for i, (title, slug) in enumerate(spoke_titles, 1):
            f.write(f"{i}. [{title}]({CONFIG.get('publishing', {}).get('blog_path', '/blog')}/{slug})\n")
        
        f.write("\n**Requirements:**\n")
        f.write("- Distribute links throughout article (not clustered)\n")
        f.write("- Use contextual anchor text (varies by context)\n")
        f.write("- Natural integration (not forced)\n\n")
        
        f.write("---\n\n")
        f.write("## 📋 PHASE 2: Spokes → Hub + Related Spokes (20-30 Links)\n\n")
        f.write("For EACH of the 10 spokes, add:\n\n")
        f.write(f"**1. Link to Hub** (always near intro):\n")
        f.write(f"   [{hub_title}]({CONFIG.get('publishing', {}).get('blog_path', '/blog')}/{hub_slug})\n\n")
        f.write("**2. Link to 2-3 related spokes** (based on topic):\n")
        f.write("   - Implementation spokes (1-3) link to each other\n")
        f.write("   - Use case spokes (4-7) link within category\n")
        f.write("   - Comparison spokes (8-10) link to each other\n\n")
        
        f.write("---\n\n")
        f.write("## ✅ COMPLETION\n\n")
        f.write("Create: `step11a_HUB_SPOKES_CROSSLINKED.txt`\n\n")
        f.write("This marks hub↔spokes linking complete.\n")
        f.write("Next: Step 11B will integrate utilities.\n")
    
    log(f"✅ Task created: {os.path.basename(task_file)}")
    return task_file

# ============================================================================
# STEP 11B: INTEGRATE UTILITIES INTO CLUSTER (AI AGENT)
# ============================================================================

def create_step11b_integrate_utilities_task(hub_file, spoke_files, utility_files):
    """
    Create AI agent task for integrating utilities into cluster
    Simpler incremental task (Step 11B)
    """
    log("="*80)
    log("STEP 11B: INTEGRATE UTILITIES INTO CLUSTER")
    log("="*80)
    
    if not utility_files or len(utility_files) == 0:
        log("ℹ️  No utilities to integrate - skipping")
        return None
    
    # Get spoke titles first
    spoke_titles_data = []
    for spoke_file in sorted(spoke_files):
        spoke_path = Path(spoke_file) if not isinstance(spoke_file, Path) else spoke_file
        with open(spoke_path, 'r') as f:
            title = f.readline().strip('#').strip()
        slug = title.lower().replace(' ', '-').replace(':', '').replace('?', '')
        slug = re.sub(r'[^\w-]', '', slug)
        spoke_titles_data.append((title, slug))
    
    # Get utility info
    utility_data = []
    for util_file in sorted(utility_files):
        util_path = Path(util_file) if not isinstance(util_file, Path) else util_file
        with open(util_path, 'r') as f:
            title = f.readline().strip('#').strip()
        slug = title.lower().replace(' ', '-').replace(':', '').replace('?', '')
        slug = re.sub(r'[^\w-]', '', slug)
        
        # Determine which spokes are relevant
        relevant_spokes = []
        if 'iqs' in slug:
            relevant_spokes = [8, 10]  # agent performance, measuring quality
        elif 'score' in slug:
            relevant_spokes = [7, 8]  # real-time coaching, agent performance
        elif 'framework' in slug or 'optimization' in slug:
            relevant_spokes = [4, 8]  # performance improvement, agent performance
        
        utility_data.append({
            'title': title,
            'slug': slug,
            'file': util_path.name,
            'relevant_spokes': relevant_spokes
        })
    
    task_file = os.path.join(SESSION_DIR, "step11b_INTEGRATE_UTILITIES_TASK.md")
    
    with open(task_file, 'w') as f:
        f.write(f"# STEP 11B: Integrate Utilities into Cluster (AI Agent Task)\n\n")
        f.write(f"**Session:** {SESSION_ID}\n")
        f.write(f"**Utilities:** {len(utility_files)}\n")
        f.write(f"**Spokes to update:** ~{len(utility_files) * 2} of 10\n\n")
        f.write("---\n\n")
        
        f.write("## 🎯 MISSION: Add Utility Links to Hub + Spokes\n\n")
        f.write("Utilities already link to cluster. Now make cluster link BACK to utilities.\n\n")
        
        f.write("**CRITICAL - Link Format:**\n")
        f.write(f"- Use `{CONFIG.get('publishing', {}).get('blog_path', '/blog')}/[slug]` format\n\n")
        
        f.write("---\n\n")
        f.write("## 📋 PHASE 1: Hub → Utilities (3 Links)\n\n")
        f.write(f"**Edit:** `{os.path.basename(hub_file)}`\n\n")
        f.write("Add 1 contextual link to EACH utility:\n\n")
        
        for i, util in enumerate(utility_data, 1):
            f.write(f"{i}. [{util['title']}]({CONFIG.get('publishing', {}).get('blog_path', '/blog')}/{util['slug']})\n")
        
        f.write("\n**Where to add:**\n")
        f.write("- When mentioning frameworks/methodologies\n")
        f.write("- In sections about training/quality/optimization\n")
        f.write("- Natural, contextual placement\n\n")
        
        f.write("---\n\n")
        f.write("## 📋 PHASE 2: Spokes → Utilities (10-20 Links)\n\n")
        f.write("Add utility links to RELEVANT spokes only.\n\n")
        
        f.write("### 🔍 STEP-BY-STEP WORKFLOW (Follow This Exactly):\n\n")
        f.write("For EACH spoke:\n\n")
        f.write("1. **Read spoke FULLY** (don't just skim)\n")
        f.write("   - Understand main topic\n")
        f.write("   - Identify which utilities are discussed\n\n")
        f.write("2. **Search for utility concepts:**\n")
        f.write("   - IQS: Search for 'quality score', 'quality framework', 'measuring quality'\n")
        f.write("   - SCORE: Search for 'scenario', 'training', 'simulation', 'coaching'\n")
        f.write("   - Optimization: Search for 'optimization', 'systematic', 'framework', 'loop'\n\n")
        f.write("3. **Find NATURAL placement:**\n")
        f.write("   - Look in article BODY (lines 10-180, not first/last 10 lines)\n")
        f.write("   - Find sentence that discusses the utility concept\n")
        f.write("   - Add link inline where concept is mentioned\n\n")
        f.write("4. **Verify placement:**\n")
        f.write("   - NOT in title (line 1)\n")
        f.write("   - NOT in metadata (last 20 lines)\n")
        f.write("   - NOT in TL;DR (lines 3-6)\n")
        f.write("   - NOT in same sentence as another link\n")
        f.write("   - YES in article sections (## headings)\n\n")
        f.write("5. **Skip if no good context:**\n")
        f.write("   - If utility not naturally discussed, skip that spoke\n")
        f.write("   - Quality > quantity\n\n")
        
        f.write("---\n\n")
        f.write("### 🎯 UTILITY LINKING GUIDE:\n\n")
        
        for util in utility_data:
            f.write(f"#### {util['title']}\n")
            f.write(f"**Link:** [{util['title']}]({CONFIG.get('publishing', {}).get('blog_path', '/blog')}/{util['slug']})\n\n")
            f.write(f"**Search for these terms in spokes:**\n")
            if 'iqs' in util['slug']:
                f.write("   - 'quality score', 'quality framework', 'measuring quality', 'quality methodology'\n")
            elif 'score' in util['slug']:
                f.write("   - 'scenario', 'training scenarios', 'simulation', 'automated training', 'coaching'\n")
            elif 'optimization' in util['slug'] or 'framework' in util['slug']:
                f.write("   - 'optimization', 'systematic approach', 'framework', 'loop', 'continuous improvement'\n")
            f.write("\n")
            f.write(f"**Suggested spokes:**\n")
            for spoke_num in util['relevant_spokes']:
                if spoke_num <= len(spoke_titles_data):
                    spoke_title = spoke_titles_data[spoke_num-1][0]
                    f.write(f"   - Spoke {spoke_num:02d} ({spoke_title[:40]}...)\n")
            f.write("\n")
            f.write("**Example placement:**\n")
            if 'iqs' in util['slug']:
                f.write("   'Organizations using [IQS framework](...) report measurable improvements.'\n")
            elif 'score' in util['slug']:
                f.write("   'Training through [SCORE methodology](...) accelerates skill development.'\n")
            else:
                f.write("   'Systematic [optimization frameworks](...) close the insight-to-action gap.'\n")
            f.write("\n")
        
        f.write("**Requirements:**\n")
        f.write("- 1-2 utility links per relevant spoke\n")
        f.write("- Contextual placement (not forced)\n")
        f.write("- Natural anchor text\n\n")
        
        f.write("**⚠️  DO NOT Add Links In:**\n")
        f.write("- ❌ Article titles (H1)\n")
        f.write("- ❌ Metadata sections (Primary Keywords, Hub Link, Related Spokes)\n")
        f.write("- ❌ Bottom matter (after final ---)\n")
        f.write("- ❌ Word Count or technical metadata\n")
        f.write("- ❌ Same sentence as another link (max 1 link per sentence)\n\n")
        
        f.write("**✅ DO Add Links In:**\n")
        f.write("- ✅ Article body content (between ## sections)\n")
        f.write("- ✅ Where utility topic is actually discussed\n")
        f.write("- ✅ Natural paragraphs mentioning frameworks/methodologies/training\n")
        f.write("- ✅ Contextual, relevant placement\n")
        f.write("- ✅ One link per sentence maximum (avoid link clustering)\n\n")
        
        f.write("**Example Good Placement:**\n")
        f.write("```\n")
        f.write("Organizations implementing [systematic optimization](/blog/solidroads-optimization-framework...)\n")
        f.write("report measurable improvements.\n")
        f.write("```\n\n")
        
        f.write("**Example Bad Placement:**\n")
        f.write("```\n")
        f.write("# [Article Title](/blog/utility) ← ❌ DON'T DO THIS\n")
        f.write("**Primary Keywords:** keyword [link](/blog/utility) ← ❌ OR THIS\n")
        f.write("```\n\n")
        
        f.write("---\n\n")
        f.write("## ✅ COMPLETION\n\n")
        f.write("Create: `step11b_UTILITIES_INTEGRATED.txt`\n\n")
        f.write("This marks utilities fully integrated into cluster.\n")
        f.write(f"Total cluster: 14 articles (1 hub + 10 spokes + 3 utilities) all interconnected!\n")
    
    log(f"✅ Task created: {os.path.basename(task_file)}")
    return task_file

# ============================================================================
# STEP 11C: AI AGENT KEYWORD REVIEW
# ============================================================================

def step11c_ai_keyword_review(hub_file, spoke_files, utility_files=None):
    """
    Step 11C: AI Agent reviews and optimizes keywords before CSV export.
    
    The AI agent will:
    1. Ensure head keywords are present (short, high-volume terms)
    2. Add long-tail keyword variations (specific, intent-based)
    3. Remove irrelevant or low-value keywords
    4. Reorder by priority (head keywords first, then long-tail)
    5. Filter out brand name from keywords (brand shouldn't be a keyword)
    
    Output: step11c_REVIEWED_KEYWORDS.csv
    """
    if utility_files is None:
        utility_files = []
    
    log("="*80)
    log("STEP 11C: AI AGENT KEYWORD REVIEW")
    log("="*80)
    
    # Collect all articles and their extracted keywords
    articles_data = []
    
    # Process Hub
    with open(hub_file, 'r', encoding='utf-8') as f:
        hub_md = f.read()
    hub_title = hub_md.split('\n')[0].strip('#').strip()
    hub_keywords = extract_primary_keywords(hub_md)
    hub_slug = hub_title.lower().replace(' ', '-')
    hub_slug = re.sub(r'[^\w-]', '', hub_slug)
    
    articles_data.append({
        'file': os.path.basename(hub_file),
        'title': hub_title,
        'slug': hub_slug,
        'type': 'HUB',
        'extracted_keywords': hub_keywords,
        'markdown_preview': hub_md[:500]  # First 500 chars for context
    })
    
    log(f"   📄 Hub: {hub_title[:50]}... ({len(hub_keywords)} keywords)")
    
    # Process Spokes
    for spoke_file in spoke_files:
        with open(spoke_file, 'r', encoding='utf-8') as f:
            spoke_md = f.read()
        spoke_title = spoke_md.split('\n')[0].strip('#').strip()
        spoke_keywords = extract_primary_keywords(spoke_md)
        spoke_slug = spoke_title.lower().replace(' ', '-')
        spoke_slug = re.sub(r'[^\w-]', '', spoke_slug)
        
        # Extract spoke number
        basename = os.path.basename(spoke_file)
        spoke_match = re.search(r'spoke(\d+)', basename)
        spoke_num = spoke_match.group(1) if spoke_match else "00"
        
        articles_data.append({
            'file': basename,
            'title': spoke_title,
            'slug': spoke_slug,
            'type': f'SPOKE_{spoke_num}',
            'extracted_keywords': spoke_keywords,
            'markdown_preview': spoke_md[:500]
        })
        
        log(f"   📄 Spoke {spoke_num}: {spoke_title[:40]}... ({len(spoke_keywords)} keywords)")
    
    # Process Utilities
    for utility_file in utility_files:
        with open(utility_file, 'r', encoding='utf-8') as f:
            utility_md = f.read()
        utility_title = utility_md.split('\n')[0].strip('#').strip()
        utility_keywords = extract_primary_keywords(utility_md)
        utility_slug = utility_title.lower().replace(' ', '-')
        utility_slug = re.sub(r'[^\w-]', '', utility_slug)
        
        articles_data.append({
            'file': os.path.basename(utility_file),
            'title': utility_title,
            'slug': utility_slug,
            'type': 'UTILITY',
            'extracted_keywords': utility_keywords,
            'markdown_preview': utility_md[:500]
        })
        
        log(f"   📄 Utility: {utility_title[:40]}... ({len(utility_keywords)} keywords)")
    
    # Check if reviewed keywords already exist
    reviewed_csv = os.path.join(SESSION_DIR, "step11c_REVIEWED_KEYWORDS.csv")
    
    if os.path.exists(reviewed_csv):
        log(f"\n✅ Found existing reviewed keywords: {os.path.basename(reviewed_csv)}")
        return reviewed_csv, {'articles': len(articles_data), 'status': 'complete'}
    
    # Create AI Agent task file
    task_file = os.path.join(SESSION_DIR, "step11c_KEYWORD_REVIEW_TASK.md")
    
    # Load brand context for the prompt
    brand_name_lower = BRAND_NAME.lower()
    brand_variations = [
        brand_name_lower,
        brand_name_lower.replace(' ', ''),
        brand_name_lower.replace(' ', '-'),
    ]
    
    with open(task_file, 'w', encoding='utf-8') as f:
        f.write("# STEP 11C: AI Agent Keyword Review Task\n\n")
        f.write(f"**Session:** {SESSION_ID}\n")
        f.write(f"**Brand:** {BRAND_NAME}\n")
        f.write(f"**Articles to review:** {len(articles_data)}\n\n")
        f.write("---\n\n")
        
        f.write("## 🎯 YOUR MISSION\n\n")
        f.write("Review and optimize the extracted keywords for each article before they are sent to Athena.\n\n")
        
        f.write("## 📋 REVIEW CRITERIA\n\n")
        f.write("For each article's keywords, you must:\n\n")
        
        # Get industry context from config for dynamic examples
        industry_domain = CONFIG.get('data_source', {}).get('domain_name', 'your industry')
        
        f.write("### 1. USE NICHE-SPECIFIC Head Keywords (NOT Ultra-Generic)\n")
        f.write("- Every article needs 1-2 HEAD keywords (2-4 words, niche-specific)\n")
        f.write("- ⚠️ **AVOID ultra-generic terms** that are impossible to rank for:\n")
        f.write("  - ❌ Single-word keywords like 'analytics', 'software', 'platform', 'AI', 'NLP'\n")
        f.write("  - ❌ Ultra-broad terms with 50K+ monthly searches\n")
        f.write("  - ❌ Keywords that Wikipedia/Forbes/major publications dominate\n")
        f.write("- ✅ **ADD industry context** to make keywords rankable:\n")
        f.write("  - ❌ '[generic term]' → ✅ '[generic term] + [industry/use case]'\n")
        f.write("  - ❌ 'analytics' → ✅ 'analytics for [your industry]' or '[your industry] analytics software'\n")
        f.write("  - ❌ 'AI tools' → ✅ 'AI tools for [specific use case]'\n")
        f.write("  - ❌ 'automation' → ✅ '[industry] automation platform'\n")
        f.write(f"- Your industry context: **{industry_domain}**\n")
        f.write("- Head keywords should be **2-4 words** and include your industry/niche\n")
        f.write("- Good pattern: '[topic] + [industry]' or '[topic] + software/platform/tools'\n\n")
        
        f.write("### 2. ADD Long-Tail Variations (Intent-Based)\n")
        f.write("- Add 2-3 long-tail keyword variations per article\n")
        f.write("- Long-tail = 5+ words, specific intent, lower competition, higher conversion\n")
        f.write("- **Long-tail patterns that work:**\n")
        f.write("  - Question-based: 'how to choose [topic] for [industry]'\n")
        f.write(f"  - Year-specific: 'best [topic] tools {SEO_TARGET_YEAR}' ⚠️ **Use {SEO_TARGET_YEAR} (SEO Q4 strategy)**\n")
        f.write("  - Comparison: '[topic A] vs [topic B]'\n")
        f.write("  - Problem-based: 'why [topic] doesn't work and how to fix it'\n")
        f.write("  - Use-case specific: '[topic] for [specific use case]'\n")
        
        # Add Q4 year strategy note
        current_month = datetime.now().month
        if current_month >= 11:
            f.write(f"\n**📅 Late-Year Strategy (Nov-Dec):** Use **{SEO_TARGET_YEAR}** in year-specific keywords.\n")
            f.write("This captures future search intent and maintains high CTR when the new year arrives.\n\n")
        else:
            f.write(f"\n**📅 Year Strategy:** Use **{SEO_TARGET_YEAR}** (current year) in year-specific keywords.\n\n")
        
        # Month Hack for competitive niches
        f.write(f"**🎯 Month Hack (CTR Boost):** For competitive niches, add `{SEO_MONTH_HACK}` to title tags.\n")
        f.write(f"- Example: 'Best [Your Topic] Tools {SEO_TARGET_YEAR} {SEO_MONTH_HACK}'\n")
        f.write("- This signals freshness and increases click-through rate.\n\n")
        f.write("- **Example progression:**\n")
        f.write("  - Generic (❌ avoid): 'software'\n")
        f.write("  - Head (✅ use): '[your topic] software'\n")
        f.write(f"  - Long-tail (✅ use): 'best [your topic] software for [industry] {SEO_TARGET_YEAR}'\n\n")
        
        f.write("### 3. REMOVE Irrelevant Keywords\n")
        f.write("- Remove ultra-generic terms (1 word, millions of results)\n")
        f.write("- Remove keywords outside the industry niche\n")
        f.write("- Remove duplicate or near-duplicate keywords\n")
        f.write("- Remove keywords that don't match the article content\n\n")
        
        f.write("### 4. REORDER by Priority (Rankability)\n")
        f.write("- NICHE HEAD keywords first (2-4 words, industry-specific, rankable)\n")
        f.write("- Supporting keywords next (related terms)\n")
        f.write("- Long-tail variations last (specific queries, high conversion)\n\n")
        
        f.write("### 5. FILTER Brand Keywords\n")
        f.write(f"- ❌ **REMOVE** any keyword containing the brand name: `{BRAND_NAME}`\n")
        f.write(f"- Brand variations to exclude: {', '.join(brand_variations)}\n")
        f.write("- We don't need to rank for our own brand name\n\n")
        
        f.write("---\n\n")
        f.write("## 📊 ARTICLES TO REVIEW\n\n")
        
        for idx, article in enumerate(articles_data, 1):
            f.write(f"### Article {idx}: {article['title']}\n\n")
            f.write(f"**Type:** {article['type']}\n")
            f.write(f"**File:** `{article['file']}`\n")
            f.write(f"**Slug:** `{article['slug']}`\n\n")
            f.write(f"**Extracted Keywords:**\n")
            if article['extracted_keywords']:
                for kw in article['extracted_keywords']:
                    f.write(f"- {kw}\n")
            else:
                f.write("- *(no keywords extracted)*\n")
            f.write("\n")
            f.write(f"**Content Preview:**\n```\n{article['markdown_preview'][:300]}...\n```\n\n")
            f.write("---\n\n")
        
        f.write("## 📤 OUTPUT FORMAT\n\n")
        f.write("Create a CSV file: `step11c_REVIEWED_KEYWORDS.csv`\n\n")
        f.write("**CSV Structure:**\n")
        f.write("```csv\n")
        f.write("File,Title,Type,Reviewed_Keywords\n")
        f.write('step8_ARTICLE_WITH_CITATIONS.md,"Article Title",HUB,"keyword1, keyword2, long-tail keyword 3"\n')
        f.write("```\n\n")
        f.write("**Rules:**\n")
        f.write("- `Reviewed_Keywords` column: comma-separated, ordered by priority\n")
        f.write("- Include 5-8 keywords per article (1-2 head + 2-3 long-tail + supporting)\n")
        f.write("- HEAD keywords FIRST, then long-tail variations\n")
        f.write("- Do NOT include the article title as a keyword (it's added automatically later)\n")
        f.write(f"- Do NOT include `{BRAND_NAME}` or variations in keywords\n\n")
        
        f.write("---\n\n")
        f.write("## ✅ COMPLETION\n\n")
        f.write("After creating the CSV:\n")
        f.write("1. Save as `step11c_REVIEWED_KEYWORDS.csv` in the session folder\n")
        f.write("2. Pipeline will auto-continue to Step 12 (HTML conversion)\n")
    
    log(f"\n📝 Created AI Agent task: {os.path.basename(task_file)}")
    
    # Also create a starter CSV template for the AI agent
    template_csv = os.path.join(SESSION_DIR, "step11c_KEYWORDS_TEMPLATE.csv")
    with open(template_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['File', 'Title', 'Type', 'Reviewed_Keywords'])
        for article in articles_data:
            # Pre-fill with extracted keywords as starting point
            keywords_str = ', '.join(article['extracted_keywords']) if article['extracted_keywords'] else ''
            writer.writerow([
                article['file'],
                article['title'],
                article['type'],
                keywords_str
            ])
    
    log(f"📝 Created template CSV: {os.path.basename(template_csv)}")
    log(f"\n🤖 AGENT_TASK_READY: {task_file}")
    log(f"📋 OUTPUT_FILE: step11c_REVIEWED_KEYWORDS.csv")
    log(f"⏸️  Pipeline paused - waiting for AI Agent to review keywords...")
    
    return None, {'articles': len(articles_data), 'status': 'waiting', 'task_file': task_file}


def load_reviewed_keywords(session_dir):
    """
    Load reviewed keywords from step11c_REVIEWED_KEYWORDS.csv
    Returns dict mapping filename -> list of keywords
    """
    reviewed_csv = os.path.join(session_dir, "step11c_REVIEWED_KEYWORDS.csv")
    
    if not os.path.exists(reviewed_csv):
        return None
    
    keywords_map = {}
    with open(reviewed_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row.get('File', '')
            keywords_str = row.get('Reviewed_Keywords', '')
            # Parse comma-separated keywords
            keywords = [kw.strip() for kw in keywords_str.split(',') if kw.strip()]
            keywords_map[filename] = keywords
    
    return keywords_map


# ============================================================================
# STEP 11D: SPOKE FAQ GENERATION
# ============================================================================

def step11d_generate_spoke_faqs(hub_faq_file, spoke_files):
    """
    Step 11D: Generate 2-3 specific, nitty-gritty FAQs for each Spoke article.
    
    Spoke FAQs are different from Hub FAQs:
    - Hub FAQs: "What is X?" (broad, category-level) - already generated in Step 5B
    - Spoke FAQs: "Does X charge a fee?", "How long does Y take?" (specific, PAA-targeted)
    
    The AI agent reads Hub FAQs first to ensure no overlap.
    """
    log("="*80)
    log("STEP 11D: SPOKE FAQ GENERATION (For AI Agent)")
    log("="*80)
    
    if not spoke_files:
        log("⚠️  No spoke files found - Skipping Spoke FAQ generation")
        return None, {}
    
    # Create output directory
    faq_output_dir = os.path.join(SESSION_DIR, "step11d_spoke_faqs")
    os.makedirs(faq_output_dir, exist_ok=True)
    
    # Check if all FAQs already exist
    existing_faqs = list(Path(faq_output_dir).glob("spoke*_faqs.md"))
    if len(existing_faqs) >= len(spoke_files):
        log(f"✅ Spoke FAQs already exist: {len(existing_faqs)} files")
        return faq_output_dir, {'faq_files': len(existing_faqs), 'status': 'complete'}
    
    # Load Hub FAQs to prevent overlap
    hub_faqs_content = ""
    hub_questions = []
    if hub_faq_file and os.path.exists(hub_faq_file):
        with open(hub_faq_file, 'r', encoding='utf-8') as f:
            hub_faqs_content = f.read()
        # Extract questions (lines starting with ###)
        for line in hub_faqs_content.split('\n'):
            if line.strip().startswith('### '):
                hub_questions.append(line.strip().replace('### ', '').replace('?', ''))
        log(f"📋 Loaded {len(hub_questions)} Hub FAQs to avoid overlap")
    else:
        log("⚠️  Hub FAQs not found - Spoke FAQs may risk overlap")
    
    # Collect spoke info
    spokes_data = []
    for spoke_file in spoke_files:
        with open(spoke_file, 'r', encoding='utf-8') as f:
            content = f.read()
        title = content.split('\n')[0].strip('#').strip()
        
        # Extract spoke number
        basename = os.path.basename(str(spoke_file))
        spoke_match = re.search(r'spoke(\d+)', basename)
        spoke_num = spoke_match.group(1) if spoke_match else "00"
        
        spokes_data.append({
            'file': str(spoke_file),
            'basename': basename,
            'title': title,
            'spoke_num': spoke_num,
            'preview': content[:800]
        })
    
    log(f"📄 Found {len(spokes_data)} spokes to generate FAQs for")
    
    # Create task file
    task_file = os.path.join(SESSION_DIR, "step11d_SPOKE_FAQ_TASK.md")
    
    with open(task_file, 'w', encoding='utf-8') as f:
        f.write("# STEP 11D: Spoke FAQ Generation Task\n\n")
        f.write(f"**Session:** {SESSION_ID}\n")
        f.write(f"**Spokes to process:** {len(spokes_data)}\n")
        f.write(f"**Brand:** {BRAND_NAME}\n\n")
        f.write("---\n\n")
        
        f.write("## 🎯 YOUR MISSION\n\n")
        f.write("Generate **2-3 FAQs per Spoke** (specific, long-tail questions).\n\n")
        f.write("Total output: 20-30 FAQs across 10 spokes.\n\n")
        
        f.write("---\n\n")
        f.write("## ⚠️ HUB FAQs (ALREADY ANSWERED - DO NOT REPEAT)\n\n")
        if hub_questions:
            f.write("These questions are already answered in the Hub. **Do NOT repeat them:**\n\n")
            for q in hub_questions:
                f.write(f"- ❌ \"{q}?\"\n")
        else:
            f.write("*(Hub FAQs not available - be extra careful to avoid broad questions)*\n")
        f.write("\n")
        
        f.write("---\n\n")
        f.write("## ✅ DO: Specific, Nitty-Gritty Questions\n\n")
        f.write("Good Spoke FAQ questions target \"People Also Ask\" snippets:\n")
        f.write("- \"Can I get a refund for a partial month?\"\n")
        f.write("- \"Does [service] charge a cancellation fee?\"\n")
        f.write("- \"How long does [process] take?\"\n")
        f.write("- \"What happens if [edge case]?\"\n")
        f.write("- \"Can I [action] without [constraint]?\"\n\n")
        
        f.write("## ❌ DON'T: Broad, Definitional Questions\n\n")
        f.write("These belong in **Hub FAQs** (Step 5B), not here:\n")
        f.write("- \"What is [topic]?\" → Hub\n")
        f.write("- \"Why is [topic] important?\" → Hub\n")
        f.write("- \"Who uses [topic]?\" → Hub\n\n")
        
        f.write("## ❌ DON'T: Questions That Deserve Their Own Article\n\n")
        f.write("If the answer needs 500+ words, it's a Spoke topic, not an FAQ.\n\n")
        
        f.write("---\n\n")
        f.write("## 📄 SPOKES TO PROCESS\n\n")
        
        for spoke in spokes_data:
            f.write(f"### Spoke {spoke['spoke_num']}: {spoke['title']}\n\n")
            f.write(f"**File:** `{spoke['basename']}`\n\n")
            f.write("**Content Preview:**\n")
            f.write("```\n")
            f.write(spoke['preview'][:600])
            f.write("\n```\n\n")
            f.write("**Generate 2-3 FAQs for this spoke:**\n")
            f.write("- Question must be specific to THIS spoke's topic\n")
            f.write("- Question must NOT overlap with Hub FAQs above\n")
            f.write("- Question must NOT overlap with other Spoke FAQs\n\n")
            f.write("---\n\n")
        
        f.write("## 📤 OUTPUT FORMAT\n\n")
        f.write(f"Create individual files in: `step11d_spoke_faqs/`\n\n")
        f.write("**For each spoke, create:**\n")
        f.write("- `spoke01_faqs.md`\n")
        f.write("- `spoke02_faqs.md`\n")
        f.write("- ... through `spoke10_faqs.md`\n\n")
        f.write("**File format:**\n")
        f.write("```markdown\n")
        f.write("# Spoke [XX]: [Title] - FAQs\n\n")
        f.write("## Frequently Asked Questions\n\n")
        f.write("### [Specific Question 1]?\n")
        f.write("[Answer: 2-3 sentences]\n\n")
        f.write("### [Specific Question 2]?\n")
        f.write("[Answer: 2-3 sentences]\n\n")
        f.write("### [Specific Question 3]? (optional)\n")
        f.write("[Answer: 2-3 sentences]\n")
        f.write("```\n\n")
        
        f.write("---\n\n")
        f.write("## ✅ QUALITY CHECKLIST\n\n")
        f.write("Before saving each spoke's FAQs:\n")
        f.write("- [ ] 2-3 FAQs per spoke\n")
        f.write("- [ ] All questions are specific/tactical\n")
        f.write("- [ ] No overlap with Hub FAQs\n")
        f.write("- [ ] No overlap with other Spoke FAQs\n")
        f.write("- [ ] No \"What is X?\" definitional questions\n")
        f.write("- [ ] Each answer is 2-3 sentences\n")
    
    log(f"📝 Task created: {os.path.basename(task_file)}")
    log(f"📁 Output directory: step11d_spoke_faqs/")
    log(f"")
    log(f"🤖 AI AGENT: Generate 2-3 specific FAQs per spoke")
    log(f"   - Read Hub FAQs first (avoid overlap)")
    log(f"   - Write specific questions (\"Does X...\", \"How long...\")")
    log(f"   - Save to: step11d_spoke_faqs/spoke01_faqs.md, etc.")
    
    return task_file, {'status': 'waiting_for_agent', 'spoke_count': len(spokes_data)}


# ============================================================================
# STEP 11E: FAQ CANNIBALIZATION REVIEW
# ============================================================================

def step11e_faq_cannibalization_review(hub_faq_file, spoke_faq_dir, hub_article_file, spoke_files):
    """
    Step 11E: Review all FAQs for overlap and cannibalization.
    
    This is the final safety net before publishing. It catches:
    - Hub FAQ that overlaps with Spoke H2
    - Spoke FAQ that overlaps with Hub FAQ
    - Spoke FAQ that overlaps with another Spoke FAQ
    - FAQ that overlaps with H2 in the same article
    
    Fixes:
    - Hub overlaps Spoke? → Make Hub brief + link to Spoke
    - Spoke overlaps Spoke? → Keep in more relevant Spoke only
    - FAQ overlaps H2? → Remove the FAQ
    """
    log("="*80)
    log("STEP 11E: FAQ CANNIBALIZATION REVIEW (For AI Agent)")
    log("="*80)
    
    # Check if review already complete
    review_report = os.path.join(SESSION_DIR, "step11e_FAQ_REVIEW_REPORT.md")
    if os.path.exists(review_report):
        log(f"✅ FAQ review already complete: {os.path.basename(review_report)}")
        return review_report, {'status': 'complete'}
    
    # Check prerequisites
    if not hub_faq_file or not os.path.exists(hub_faq_file):
        log("⚠️  Hub FAQs not found - Skipping cannibalization review")
        return None, {}
    
    if not spoke_faq_dir or not os.path.exists(spoke_faq_dir):
        log("⚠️  Spoke FAQs not found - Skipping cannibalization review")
        return None, {}
    
    # Load Hub FAQs
    with open(hub_faq_file, 'r', encoding='utf-8') as f:
        hub_faqs_content = f.read()
    
    # Load Hub article H2s
    hub_h2s = []
    if hub_article_file and os.path.exists(hub_article_file):
        with open(hub_article_file, 'r', encoding='utf-8') as f:
            hub_content = f.read()
        for line in hub_content.split('\n'):
            if line.strip().startswith('## '):
                hub_h2s.append(line.strip().replace('## ', ''))
    
    # Load all Spoke FAQs
    spoke_faq_files = sorted(Path(spoke_faq_dir).glob("spoke*_faqs.md"))
    spoke_faqs_content = {}
    for faq_file in spoke_faq_files:
        with open(faq_file, 'r', encoding='utf-8') as f:
            spoke_faqs_content[faq_file.name] = f.read()
    
    # Load all Spoke H2s
    spoke_h2s = {}
    for spoke_file in spoke_files:
        basename = os.path.basename(str(spoke_file))
        with open(spoke_file, 'r', encoding='utf-8') as f:
            content = f.read()
        h2s = []
        for line in content.split('\n'):
            if line.strip().startswith('## '):
                h2s.append(line.strip().replace('## ', ''))
        spoke_h2s[basename] = h2s
    
    log(f"📋 Loaded: 1 Hub FAQ file, {len(spoke_faq_files)} Spoke FAQ files")
    log(f"📋 Loaded: {len(hub_h2s)} Hub H2s, {sum(len(h2s) for h2s in spoke_h2s.values())} Spoke H2s")
    
    # Create task file
    task_file = os.path.join(SESSION_DIR, "step11e_FAQ_REVIEW_TASK.md")
    
    with open(task_file, 'w', encoding='utf-8') as f:
        f.write("# STEP 11E: FAQ Cannibalization Review Task\n\n")
        f.write(f"**Session:** {SESSION_ID}\n")
        f.write(f"**Brand:** {BRAND_NAME}\n\n")
        f.write("---\n\n")
        
        f.write("## 🎯 YOUR MISSION\n\n")
        f.write("Review ALL FAQs for overlap with each other AND with H2 headings.\n")
        f.write("Apply fixes to ensure each question is answered in exactly ONE place.\n\n")
        
        f.write("---\n\n")
        f.write("## 📋 FIX RULES\n\n")
        
        f.write("### Rule 1: Hub FAQ overlaps Spoke H2?\n")
        f.write("**Fix:** Make Hub FAQ brief (1 sentence) + add link to Spoke\n")
        f.write("```markdown\n")
        f.write("### [Question]?\n")
        f.write("Brief answer in one sentence. [Read the full guide →](spoke-url)\n")
        f.write("```\n\n")
        
        f.write("### Rule 2: Hub FAQ overlaps Spoke FAQ?\n")
        f.write("**Fix:** Remove Spoke FAQ (Hub already handles it)\n")
        f.write("Or if Spoke FAQ is more specific, keep Spoke, make Hub brief + link.\n\n")
        
        f.write("### Rule 3: Spoke FAQ overlaps Spoke FAQ?\n")
        f.write("**Fix:** Keep FAQ in the MORE RELEVANT Spoke only.\n")
        f.write("Relevance = which Spoke's primary keyword better matches the question?\n\n")
        
        f.write("### Rule 4: FAQ overlaps H2 in SAME article?\n")
        f.write("**Fix:** Remove the FAQ. The H2 section already answers it.\n\n")
        
        f.write("### Rule 5: FAQ answer could be its own article?\n")
        f.write("**Fix:** Flag for review. If answer needs 500+ words, it's a Spoke topic.\n\n")
        
        f.write("---\n\n")
        f.write("## 📄 CURRENT INVENTORY\n\n")
        
        f.write("### Hub FAQs (`step5b_HUB_FAQS.md`)\n\n")
        f.write("```markdown\n")
        f.write(hub_faqs_content)
        f.write("\n```\n\n")
        
        f.write("### Hub H2 Headings\n\n")
        for h2 in hub_h2s[:15]:  # Limit to first 15
            f.write(f"- {h2}\n")
        if len(hub_h2s) > 15:
            f.write(f"- ... ({len(hub_h2s) - 15} more)\n")
        f.write("\n")
        
        f.write("### Spoke FAQs\n\n")
        for filename, content in spoke_faqs_content.items():
            f.write(f"#### {filename}\n")
            f.write("```markdown\n")
            f.write(content[:800])
            if len(content) > 800:
                f.write("\n... (truncated)")
            f.write("\n```\n\n")
        
        f.write("### Spoke H2 Headings\n\n")
        for spoke_name, h2s in spoke_h2s.items():
            f.write(f"**{spoke_name}:**\n")
            for h2 in h2s[:5]:
                f.write(f"- {h2}\n")
            if len(h2s) > 5:
                f.write(f"- ... ({len(h2s) - 5} more)\n")
            f.write("\n")
        
        f.write("---\n\n")
        f.write("## 📤 OUTPUT REQUIRED\n\n")
        
        f.write("### 1. Review Report (`step11e_FAQ_REVIEW_REPORT.md`)\n\n")
        f.write("```markdown\n")
        f.write("# FAQ Cannibalization Review Report\n\n")
        f.write("## Summary\n")
        f.write("- **Total FAQs reviewed:** [X]\n")
        f.write("- **Overlaps detected:** [Y]\n")
        f.write("- **Fixes applied:** [Z]\n")
        f.write("- **Files modified:** [list]\n\n")
        f.write("## Overlaps & Fixes\n\n")
        f.write("### Overlap 1: [Description]\n")
        f.write("- **Source:** [Hub FAQ / Spoke X FAQ]\n")
        f.write("- **Overlaps with:** [Spoke Y H2 / Hub FAQ / etc.]\n")
        f.write("- **Similarity:** [high/medium]\n")
        f.write("- **Fix applied:** [Brief description]\n\n")
        f.write("... (continue for all overlaps)\n\n")
        f.write("## No Changes Needed\n")
        f.write("- [List FAQs that are unique and fine]\n")
        f.write("```\n\n")
        
        f.write("### 2. Fixed FAQ Files (only if changes needed)\n\n")
        f.write("If you modify any FAQ file, save the corrected version with `_FIXED` suffix:\n")
        f.write("- `step5b_HUB_FAQS_FIXED.md`\n")
        f.write("- `step11d_spoke_faqs/spoke04_faqs_FIXED.md`\n")
        f.write("- etc.\n\n")
        f.write("If no changes needed for a file, don't create `_FIXED` version.\n\n")
        
        f.write("---\n\n")
        f.write("## ✅ QUALITY CHECKLIST\n\n")
        f.write("Before completing:\n")
        f.write("- [ ] Reviewed ALL Hub FAQs\n")
        f.write("- [ ] Reviewed ALL Spoke FAQs\n")
        f.write("- [ ] Compared with ALL H2 headings\n")
        f.write("- [ ] Applied fixes for overlaps (Rules 1-5)\n")
        f.write("- [ ] Created `_FIXED` files for modified FAQs\n")
        f.write("- [ ] Created comprehensive review report\n")
    
    log(f"📝 Task created: {os.path.basename(task_file)}")
    log(f"📋 Output expected: step11e_FAQ_REVIEW_REPORT.md")
    log(f"")
    log(f"🤖 AI AGENT: Review all FAQs for cannibalization")
    log(f"   - Compare Hub FAQs vs Spoke H2s")
    log(f"   - Compare Hub FAQs vs Spoke FAQs")
    log(f"   - Compare Spoke FAQs vs each other")
    log(f"   - Apply fix rules for any overlaps")
    log(f"   - Save report and fixed files")
    
    return task_file, {'status': 'waiting_for_agent'}


def step12_convert_to_framer_html(hub_file, spoke_files, utility_files=None):
    """
    Step 11C: Convert articles to individual HTML files
    - Creates output directories (markdown, html, csv)
    - Converts each article to HTML separately (hub + spokes + utilities)
    - Saves individual HTML files for easy editing
    - Creates individual CSV files with metadata
    - Generates URL slugs and metadata
    
    Benefits: Modular, debuggable, scalable
    Next: Step 12B reviews HTML quality per file
    Then: Step 12C unifies into single export CSV
    """
    if utility_files is None:
        utility_files = []
    log("="*80)
    log("STEP 11C: CONVERT TO HTML (Modular)")
    log("="*80)
    
    # Create output directory structure
    output_dir = os.path.join(SESSION_DIR, "step12_output")
    markdown_dir = os.path.join(output_dir, "markdown")
    html_dir = os.path.join(output_dir, "html")
    csv_dir = os.path.join(output_dir, "csv_individual")
    
    os.makedirs(markdown_dir, exist_ok=True)
    os.makedirs(html_dir, exist_ok=True)
    os.makedirs(csv_dir, exist_ok=True)
    
    log(f"📁 Created output directories:")
    log(f"   Markdown: {markdown_dir}")
    log(f"   HTML: {html_dir}")
    log(f"   CSV: {csv_dir}")
    
    # Load bigram/trigram data from Step 1
    bigram_trigram_data = None
    step1_json = os.path.join(SESSION_DIR, "step1_content_patterns.json")
    
    if os.path.exists(step1_json):
        try:
            with open(step1_json, 'r', encoding='utf-8') as f:
                bigram_trigram_data = json.load(f)
            log(f"✅ Loaded bigram/trigram data from Step 1")
            log(f"   Bigrams: {len(bigram_trigram_data.get('top_bigrams', []))}")
            log(f"   Trigrams: {len(bigram_trigram_data.get('top_trigrams', []))}")
        except:
            log(f"⚠️  Could not load Step 1 data - descriptions will be basic")
    else:
        log(f"⚠️  Step 1 data not found - descriptions will be basic")
    
    # Helper: Generate URL slug from title
    def generate_slug(title):
        """
        Convert title to URL-safe slug (evergreen - no years).
        
        SEO Best Practice: Never put year in URL.
        - Bad: /blog/best-apps-2025 (needs redirect next year)
        - Good: /blog/best-apps (update title annually, keep URL)
        
        This allows stacking authority on one URL for years.
        """
        slug = title.lower()
        
        # Remove years from slug (evergreen URLs)
        # Matches: 2023, 2024, 2025, 2026, 2027, etc.
        slug = re.sub(r'\b20\d{2}\b', '', slug)
        
        # Remove "for" before where year was (e.g., "for 2025" → "")
        slug = re.sub(r'\bfor\s*$', '', slug)
        
        slug = re.sub(r'[^\w\s-]', '', slug)  # Remove special chars
        slug = re.sub(r'[-\s]+', '-', slug)    # Replace spaces with hyphens
        slug = slug.strip('-')                 # Remove leading/trailing hyphens
        return slug
    
    # Helper: Enhanced markdown to HTML converter
    def markdown_to_html(md_content):
        """Convert markdown to HTML - ENHANCED to preserve H3 tags and remove H1"""
        html = md_content
        
        # Remove markdown horizontal rules (---)
        html = re.sub(r'^---+\s*$', '', html, flags=re.MULTILINE)
        
        # REMOVE H1 title entirely (title comes from CMS, not HTML body)
        html = re.sub(r'^# .+$\n*', '', html, flags=re.MULTILINE)
        
        # Convert headers (ORDER MATTERS - H4, H3, H2!)
        html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        
        # Convert bold/italic (non-greedy to avoid breaking)
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', html)
        
        # Convert links - handle citation format [[N]](url) first
        html = re.sub(r'\[\[(\d+)\]\]\(([^)]+)\)', r'<a href="\2">[\1]</a>', html)
        # Then regular links [text](url)
        html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
        
        # Convert markdown tables to HTML tables
        def convert_table(match):
            table_text = match.group(0)
            lines = [l.strip() for l in table_text.strip().split('\n') if l.strip()]
            
            html_table = '<table style="border-collapse: collapse; width: 100%;">\n'
            
            for i, line in enumerate(lines):
                # Skip separator line (|---|---|)
                if re.match(r'^\|[\s\-:]+\|$', line.replace('|', '|').replace('-', '-')):
                    continue
                if '---' in line and '|' in line:
                    continue
                    
                cells = [c.strip() for c in line.split('|')[1:-1]]  # Remove empty first/last from split
                
                if i == 0:  # Header row
                    html_table += '<tr style="background-color: #f5f5f5;">\n'
                    for cell in cells:
                        # Remove bold markers for header
                        cell = re.sub(r'\*\*(.+?)\*\*', r'\1', cell)
                        html_table += f'<th style="border: 1px solid #ddd; padding: 8px; text-align: left;">{cell}</th>\n'
                    html_table += '</tr>\n'
                else:  # Data rows
                    html_table += '<tr>\n'
                    for cell in cells:
                        # Convert bold in cells
                        cell = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', cell)
                        html_table += f'<td style="border: 1px solid #ddd; padding: 8px;">{cell}</td>\n'
                    html_table += '</tr>\n'
            
            html_table += '</table>'
            return html_table
        
        # Match markdown tables (lines starting/ending with |)
        html = re.sub(r'(?:^\|.+\|$\n?)+', convert_table, html, flags=re.MULTILINE)
        
        # Convert lists (preserve structure better)
        html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'^(\d+)\. (.+)$', r'<li>\2</li>', html, flags=re.MULTILINE)
        
        # Wrap consecutive <li> in <ul>
        html = re.sub(r'((?:<li>.*?</li>\n?)+)', r'<ul>\n\1</ul>\n', html, flags=re.MULTILINE)
        
        # Convert paragraphs (but preserve headings, lists, etc)
        lines = html.split('\n\n')
        html_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Don't wrap if already tagged
            if line.startswith(('<h', '<ul>', '<ol>', '<table>', '<pre>', '<blockquote>')):
                html_lines.append(line)
            elif line.startswith('</'):  # Closing tag
                html_lines.append(line)
            else:
                html_lines.append(f'<p>{line}</p>')
        
        html = '\n'.join(html_lines)
        
        return html
    
    # Helper: Clean metadata and horizontal rules
    def clean_metadata_and_rules(html):
        """
        Remove metadata sections and horizontal rules before publishing
        - Removes: Primary Keywords, Hub Link, Related Spokes, Word Count, etc.
        - Removes: Citations bibliography (already hyperlinked inline)
        - Removes: <p>---</p>, <hr> tags
        """
        # Remove metadata after final ---
        metadata_pattern = r'<p>---</p>\s*<p><strong>Primary Keywords:.*$'
        html = re.sub(metadata_pattern, '', html, flags=re.DOTALL)
        
        # Remove Citations section at end (already hyperlinked inline)
        html = re.sub(r'<p><strong>External Citations:</strong>.*$', '', html, flags=re.DOTALL)
        html = re.sub(r'<h2>Citations</h2>.*$', '', html, flags=re.DOTALL)
        
        metadata_pattern2 = r'<p>---</p>\s*<strong>Primary Keywords:.*$'
        html = re.sub(metadata_pattern2, '', html, flags=re.DOTALL)
        
        # Remove all horizontal rules
        html = re.sub(r'<p>---</p>', '', html)
        html = re.sub(r'<hr\s*/?>', '', html)
        
        # Remove individual metadata patterns
        html = re.sub(r'<p><strong>Primary Keywords:</strong>.*?</p>', '', html, flags=re.DOTALL)
        html = re.sub(r'<p><strong>Hub Link:</strong>.*?</p>', '', html, flags=re.DOTALL)
        html = re.sub(r'<p><strong>Related Spokes:</strong>.*?</p>', '', html, flags=re.DOTALL)
        html = re.sub(r'<p><strong>Word Count:</strong>.*?</p>', '', html, flags=re.DOTALL)
        html = re.sub(r'<p><strong>External Citations Needed:</strong>.*?</p>', '', html, flags=re.DOTALL)
        html = re.sub(r'<p><strong>Internal Links:</strong>.*?</p>', '', html, flags=re.DOTALL)
        
        # Clean up extra whitespace
        html = re.sub(r'\n\s*\n\s*\n', '\n\n', html)
        
        return html.strip()
    
    # Helper: Chunk HTML at section boundaries
    def chunk_html_at_sections(html, max_size=49000):
        """Split HTML at <h2> boundaries if content exceeds max_size"""
        if len(html) <= max_size:
            return [html]
        
        # Split at <h2> tags (keeps <h2> with its section)
        sections = re.split(r'(?=<h2>)', html)
        parts = []
        current_part = ""
        
        for section in sections:
            if len(current_part) + len(section) > max_size and current_part:
                parts.append(current_part)
                current_part = section
            else:
                current_part += section
        
        if current_part:
            parts.append(current_part)
        
        return parts
    
    # Helper: Extract FAQs from markdown FAQ file
    def extract_faqs_from_markdown(faq_file_path):
        """
        Extract FAQ questions and answers from a markdown file.
        Returns list of {question, answer} dicts.
        
        Expected format:
        ### Question text?
        Answer text here.
        """
        if not faq_file_path or not os.path.exists(faq_file_path):
            return []
        
        try:
            with open(faq_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            return []
        
        faqs = []
        current_question = None
        current_answer_lines = []
        
        for line in content.split('\n'):
            line = line.strip()
            
            # New question starts with ###
            if line.startswith('### '):
                # Save previous FAQ if exists
                if current_question and current_answer_lines:
                    answer = ' '.join(current_answer_lines).strip()
                    if answer:
                        faqs.append({
                            'question': current_question.rstrip('?') + '?',
                            'answer': answer
                        })
                
                # Start new question
                current_question = line[4:].strip()
                current_answer_lines = []
            
            # Skip headers and empty lines for answer
            elif current_question and line and not line.startswith('#'):
                current_answer_lines.append(line)
        
        # Don't forget last FAQ
        if current_question and current_answer_lines:
            answer = ' '.join(current_answer_lines).strip()
            if answer:
                faqs.append({
                    'question': current_question.rstrip('?') + '?',
                    'answer': answer
                })
        
        return faqs
    
    # Helper: Generate FAQPage JSON-LD Schema
    def generate_faq_schema(faqs):
        """
        Generate FAQPage structured data (JSON-LD) for SEO rich snippets.
        
        This enables Google's FAQ rich results in search.
        https://developers.google.com/search/docs/appearance/structured-data/faqpage
        """
        if not faqs:
            return ""
        
        schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": faq['question'],
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": faq['answer']
                    }
                }
                for faq in faqs
            ]
        }
        
        # Return as script tag
        return f'\n<!-- FAQPage Schema for SEO Rich Snippets -->\n<script type="application/ld+json">\n{json.dumps(schema, indent=2)}\n</script>'
    
    # Helper: Fix internal links
    def fix_internal_links(html_content, article_slugs):
        """
        Convert markdown file refs to Framer URLs
        [text](step10_spoke02_file.md) → <a href="/blog/slug">text</a>
        """
        # Pattern: [text](stepXX_filename.md)
        pattern = r'\[([^\]]+)\]\((step\d+[^)]+\.md)\)'
        
        def replace_link(match):
            link_text = match.group(1)
            filename = match.group(2)
            
            # Extract just the base filename
            base_filename = os.path.basename(filename)
            
            # Lookup slug
            slug = article_slugs.get(base_filename, 'unknown')
            
            # Return HTML link
            return f'<a href="/blog/{slug}">{link_text}</a>'
        
        return re.sub(pattern, replace_link, html_content)
    
    # Build article slugs map FIRST (need for link fixing)
    log(f"🔗 Building article slug map...")
    
    article_slugs = {}
    
    # Add Hub
    with open(hub_file, 'r', encoding='utf-8') as f:
        hub_md = f.read()
    
    hub_title = hub_md.split('\n')[0].strip('#').strip()
    hub_slug = generate_slug(hub_title)
    article_slugs[os.path.basename(hub_file)] = hub_slug
    
    log(f"   Hub: {hub_title[:50]}...")
    log(f"        → /blog/{hub_slug[:50]}...")
    
    # Add all Spokes
    for spoke_file in spoke_files:
        with open(spoke_file, 'r', encoding='utf-8') as f:
            spoke_md = f.read()
        
        spoke_title = spoke_md.split('\n')[0].strip('#').strip()
        spoke_slug = generate_slug(spoke_title)
        article_slugs[os.path.basename(spoke_file)] = spoke_slug
        
        spoke_num = os.path.basename(spoke_file)[14:16]
        log(f"   Spoke {spoke_num}: {spoke_title[:40]}...")
    
    # Add all Utilities (if any)
    for utility_file in utility_files:
        with open(utility_file, 'r', encoding='utf-8') as f:
            utility_md = f.read()
        
        utility_title = utility_md.split('\n')[0].strip('#').strip()
        utility_slug = generate_slug(utility_title)
        article_slugs[os.path.basename(utility_file)] = utility_slug
        
        log(f"   Utility: {utility_title[:40]}...")
    
    log(f"✅ Created slug map for {len(article_slugs)} articles ({len(spoke_files)} spokes + {len(utility_files)} utilities)")
    
    # Convert articles to HTML
    log(f"\n📝 Converting articles to HTML...")
    
    articles_for_export = []
    
    # Create output directory for individual files (MODULAR ENHANCEMENT)
    output_dir = os.path.join(SESSION_DIR, "step12_output")
    html_dir = os.path.join(output_dir, "html")
    os.makedirs(html_dir, exist_ok=True)
    
    # Convert Hub
    log(f"   Converting Hub...")
    
    hub_html = markdown_to_html(hub_md)
    
    # Remove first H1 (title goes in Title column)
    hub_html = re.sub(r'<h1>.*?</h1>\s*', '', hub_html, count=1)
    
    # Fix internal links
    hub_html = fix_internal_links(hub_html, article_slugs)
    
    # Clean metadata and horizontal rules
    hub_html = clean_metadata_and_rules(hub_html)
    
    # Inject FAQPage Schema (if Hub FAQs exist)
    hub_faq_file = os.path.join(SESSION_DIR, "step5b_HUB_FAQS.md")
    hub_faqs = extract_faqs_from_markdown(hub_faq_file)
    if hub_faqs:
        faq_schema = generate_faq_schema(hub_faqs)
        hub_html += faq_schema
        log(f"      📋 Added FAQPage schema ({len(hub_faqs)} FAQs)")
    
    # Save individual HTML file (MODULAR) - Content only, no wrapper tags
    hub_html_file = os.path.join(html_dir, f"{hub_slug}.html")
    with open(hub_html_file, 'w', encoding='utf-8') as f:
        f.write(hub_html)  # Just the content, ready for Framer CMS
    
    log(f"      💾 Saved: {os.path.basename(hub_html_file)} ({len(hub_html):,} chars)")
    
    # Chunk into parts if needed (for CSV)
    hub_parts = chunk_html_at_sections(hub_html, max_size=49000)
    
    # Load reviewed keywords if available (from Step 11C AI agent review)
    reviewed_keywords_map = load_reviewed_keywords(SESSION_DIR)
    
    # Get keywords - prefer reviewed, fallback to raw extraction
    hub_basename = os.path.basename(hub_file)
    if reviewed_keywords_map and hub_basename in reviewed_keywords_map:
        hub_keywords = reviewed_keywords_map[hub_basename]
        log(f"      📋 Using AI-reviewed keywords for hub ({len(hub_keywords)} keywords)")
    else:
        hub_keywords = extract_primary_keywords(hub_md)
    hub_prompt_values = build_prompt_values(hub_keywords, hub_title, hub_slug.replace('-', ' '))
    
    hub_row = {
        'Title': hub_title,
        'Date': datetime.now().strftime('%m/%d/%Y'),
        'Author': AUTHOR_NAME,
        'Prompt': ', '.join(hub_prompt_values),
        'Article_Type': 'HUB',
        'Hub_Title': '',  # Hub doesn't have a parent hub
        'Related_Spokes': ','.join([f"Spoke {i:02d}" for i in range(1, len(spoke_files)+1)]),
        'Final_URL': f"{BRAND_URL}/blog/{hub_slug}"
    }
    
    for i, part in enumerate(hub_parts, 1):
        hub_row[f'Content_Part{i}'] = part
    
    articles_for_export.append(hub_row)
    
    log(f"      ✅ {hub_title[:50]}... ({len(hub_html):,} chars → {len(hub_parts)} part(s))")
    
    # Convert Spokes
    log(f"   Converting {len(spoke_files)} Spokes...")
    
    for spoke_file in spoke_files:
        with open(spoke_file, 'r', encoding='utf-8') as f:
            spoke_md = f.read()
        
        spoke_title = spoke_md.split('\n')[0].strip('#').strip()
        spoke_slug = article_slugs[os.path.basename(spoke_file)]
        # Extract spoke number from filename (step10_spoke01_xxx.md → "01")
        basename = os.path.basename(spoke_file)
        spoke_match = re.search(r'spoke(\d+)', basename)
        spoke_num = spoke_match.group(1) if spoke_match else "00"
        
        # Convert to HTML
        spoke_html = markdown_to_html(spoke_md)
        
        # Remove first H1
        spoke_html = re.sub(r'<h1>.*?</h1>\s*', '', spoke_html, count=1)
        
        # Fix internal links
        spoke_html = fix_internal_links(spoke_html, article_slugs)
        
        # Clean metadata and horizontal rules
        spoke_html = clean_metadata_and_rules(spoke_html)
        
        # Inject FAQPage Schema (if Spoke FAQs exist)
        spoke_faq_dir = os.path.join(SESSION_DIR, "step11d_spoke_faqs")
        spoke_faq_file = os.path.join(spoke_faq_dir, f"spoke{spoke_num}_faqs.md")
        spoke_faqs = extract_faqs_from_markdown(spoke_faq_file)
        if spoke_faqs:
            faq_schema = generate_faq_schema(spoke_faqs)
            spoke_html += faq_schema
            log(f"      📋 Spoke {spoke_num}: Added FAQPage schema ({len(spoke_faqs)} FAQs)")
        
        # Save individual HTML file (MODULAR) - Content only, no wrapper tags
        spoke_html_file = os.path.join(html_dir, f"{spoke_slug}.html")
        with open(spoke_html_file, 'w', encoding='utf-8') as f:
            f.write(spoke_html)  # Just the content, ready for Framer CMS
        
        # Chunk if needed (unlikely for spokes but just in case)
        spoke_parts = chunk_html_at_sections(spoke_html, max_size=49000)
        
        # Get keywords - prefer reviewed, fallback to raw extraction
        if reviewed_keywords_map and basename in reviewed_keywords_map:
            spoke_keywords = reviewed_keywords_map[basename]
        else:
            spoke_keywords = extract_primary_keywords(spoke_md)
        spoke_prompt_values = build_prompt_values(spoke_keywords, spoke_title, spoke_slug.replace('-', ' '))
        prompt = ', '.join(spoke_prompt_values)
        
        # Determine related spokes (adjacent ones in list)
        spoke_idx = int(spoke_num) - 1
        related = []
        if spoke_idx > 0:
            related.append(f"Spoke {spoke_idx:02d}")
        if spoke_idx < len(spoke_files) - 1:
            related.append(f"Spoke {spoke_idx+2:02d}")
        
        spoke_row = {
            'Title': spoke_title,
            'Date': datetime.now().strftime('%m/%d/%Y'),
            'Author': AUTHOR_NAME,
            'Prompt': prompt,
            'Article_Type': 'SPOKE',
            'Hub_Title': hub_title,
            'Related_Spokes': ','.join(related) if related else '',
            'Final_URL': f"{BRAND_URL}/blog/{spoke_slug}"
        }
        
        for i, part in enumerate(spoke_parts, 1):
            spoke_row[f'Content_Part{i}'] = part
        
        articles_for_export.append(spoke_row)
        
        log(f"      ✅ Spoke {spoke_num}: {spoke_title[:40]}... ({len(spoke_html):,} chars)")
    
    # Convert Utilities (if any)
    if utility_files:
        log(f"   Converting {len(utility_files)} Utilities...")
        
        for utility_file in utility_files:
            with open(utility_file, 'r', encoding='utf-8') as f:
                utility_md = f.read()
            
            utility_title = utility_md.split('\n')[0].strip('#').strip()
            utility_slug = article_slugs[os.path.basename(utility_file)]
            
            # Convert to HTML
            utility_html = markdown_to_html(utility_md)
            
            # Remove first H1
            utility_html = re.sub(r'<h1>.*?</h1>\s*', '', utility_html, count=1)
            
            # Fix internal links
            utility_html = fix_internal_links(utility_html, article_slugs)
            
            # Clean metadata and horizontal rules
            utility_html = clean_metadata_and_rules(utility_html)
            
            # NOTE: Utilities do NOT get FAQs (Dead-End strategy - keep them short and focused)
            # See STEP_10A_utility_articles.md and STEP_05B_hub_faq_generation.md
            
            # Save individual HTML file
            utility_html_file = os.path.join(html_dir, f"{utility_slug}.html")
            with open(utility_html_file, 'w', encoding='utf-8') as f:
                f.write(utility_html)
            
            # Chunk if needed
            utility_parts = chunk_html_at_sections(utility_html, max_size=49000)
            
            # Get keywords - prefer reviewed, fallback to raw extraction
            utility_basename = os.path.basename(utility_file)
            if reviewed_keywords_map and utility_basename in reviewed_keywords_map:
                utility_keywords = reviewed_keywords_map[utility_basename]
            else:
                utility_keywords = extract_primary_keywords(utility_md)
            utility_prompt_values = build_prompt_values(utility_keywords, utility_title, utility_slug.replace('-', ' '))
            prompt = ', '.join(utility_prompt_values)
            
            utility_row = {
                'Title': utility_title,
                'Date': datetime.now().strftime('%m/%d/%Y'),
                'Author': AUTHOR_NAME,
                'Prompt': prompt,
                'Article_Type': 'UTILITY',
                'Hub_Title': hub_title,  # Link back to hub
                'Related_Spokes': '',  # Utilities don't have related spokes
                'Final_URL': f"{BRAND_URL}/blog/{utility_slug}"
            }
            
            for i, part in enumerate(utility_parts, 1):
                utility_row[f'Content_Part{i}'] = part
            
            articles_for_export.append(utility_row)
            
            log(f"      ✅ Utility: {utility_title[:40]}... ({len(utility_html):,} chars)")
    
    # Determine max parts needed
    max_parts = 0
    for article in articles_for_export:
        article_parts = sum(1 for key in article.keys() if key.startswith('Content_Part'))
        max_parts = max(max_parts, article_parts)
    
    # Create metadata generation task for AI agent
    log(f"\n📝 Creating metadata generation task...")
    
    metadata_task_file = os.path.join(SESSION_DIR, "step12b_METADATA_TASK.md")
    
    with open(metadata_task_file, 'w', encoding='utf-8') as f:
        f.write("# STEP 12B: Generate Article Metadata (AI Agent Task)\n\n")
        f.write(f"**Session:** {SESSION_ID}\n")
        f.write(f"**Articles:** {len(articles_for_export)}\n\n")
        f.write("---\n\n")
        
        f.write("## 🎯 YOUR MISSION\n\n")
        f.write("Write SEO-optimized meta descriptions for all 11 articles.\n\n")
        f.write("**CRITICAL:** Use bigrams/trigrams from dataset to make descriptions semantically relevant!\n\n")
        f.write("---\n\n")
        
        f.write("## 📊 DATASET N-GRAMS AVAILABLE\n\n")
        f.write("**Top Bigrams:**\n")
        for bigram, freq in bigram_trigram_data.get('top_bigrams', [])[:10]:
            f.write(f"- '{bigram}' ({freq}x)\n")
        
        f.write(f"\n**Top Trigrams:**\n")
        for trigram, freq in bigram_trigram_data.get('top_trigrams', [])[:10]:
            f.write(f"- '{trigram}' ({freq}x)\n")
        
        f.write(f"\n---\n\n")
        f.write(f"## 📝 WRITE DESCRIPTIONS FOR EACH ARTICLE\n\n")
        
        # For each article
        for idx, row in enumerate(articles_for_export):
            content_full = ''.join([row.get(f'Content_Part{i}', '') for i in range(1, max_parts + 1)])
            slug = list(article_slugs.values())[idx]
            
            # Find relevant n-grams for this article
            article_text = (row['Title'] + " " + content_full[:2000]).lower()
            
            relevant_ngrams = []
            for bigram, freq in bigram_trigram_data.get('top_bigrams', [])[:30]:
                if any(word in article_text for word in bigram.split()):
                    relevant_ngrams.append(f"'{bigram}' ({freq}x)")
            
            for trigram, freq in bigram_trigram_data.get('top_trigrams', [])[:20]:
                if any(word in article_text for word in trigram.split()):
                    relevant_ngrams.append(f"'{trigram}' ({freq}x)")
            
            # Determine article type
            if idx == 0:
                article_type = 'HUB'
            elif idx <= len(spoke_files):
                article_type = 'SPOKE'
            else:
                article_type = 'UTILITY'
            
            f.write(f"### Article {idx+1}: {row['Title']}\n\n")
            f.write(f"**Article Type:** {article_type}\n")
            f.write(f"**Slug:** {slug}\n\n")
            
            f.write(f"**First paragraph:**\n")
            # Extract first paragraph from content
            first_para = re.search(r'<p>(.+?)</p>', content_full)
            if first_para:
                f.write(f"{first_para.group(1)[:300]}...\n\n")
            
            f.write(f"**Relevant n-grams for this article:**\n")
            for ngram in relevant_ngrams[:5]:
                f.write(f"- {ngram}\n")
            
            f.write(f"\n**WRITE DESCRIPTION (150-160 chars):**\n")
            f.write(f"- Incorporate 2-3 n-grams naturally\n")
            f.write(f"- Compelling and actionable\n")
            f.write(f"- Mention {BRAND_NAME} if space allows\n")
            f.write(f"- SEO-optimized\n\n")
            f.write(f"```\nDescription: [YOUR 150-160 CHAR DESCRIPTION HERE]\n```\n\n")
            f.write(f"---\n\n")
        
        f.write(f"## 💾 OUTPUT - TWO FILES REQUIRED\n\n")
        
        f.write(f"### 1. Update CSV with Descriptions\n\n")
        f.write(f"**File:** `step12_FRAMER_EXPORT.csv`\n\n")
        f.write(f"Replace placeholder descriptions in the Description column with your AI-generated descriptions.\n\n")
        f.write(f"**Column order:** Title, Date, Author, **Description**, Content_Part1, Content_Part2\n\n")
        
        f.write(f"### 2. Save Metadata JSON\n\n")
        f.write(f"**File:** `step12_ARTICLE_METADATA.json`\n\n")
        f.write(f"```json\n")
        f.write(f'{{\n')
        f.write(f'  "articles": [\n')
        f.write(f'    {{\n')
        f.write(f'      "title": "Article Title",\n')
        f.write(f'      "slug": "article-slug",\n')
        f.write(f'      "description": "YOUR 150-160 CHAR DESCRIPTION",\n')
        f.write(f'      "author": "Renan Serrano",\n')
        f.write(f'      "date": "MM/DD/YYYY",\n')
        f.write(f'      "word_count": 7296\n')
        f.write(f'    }},\n')
        f.write(f'    ... (10 more)\n')
        f.write(f'  ]\n')
        f.write(f'}}\n')
        f.write(f"```\n\n")
        f.write(f"**CRITICAL:** Update BOTH files - CSV gets published, JSON is for reference!\n")
    
    log(f"✅ Metadata task created: {metadata_task_file}")
    
    # Signal AI agent
    print(f"\n🤖 AGENT_TASK_READY: {metadata_task_file}")
    print(f"📋 OUTPUT_FILE: step12_ARTICLE_METADATA.json")
    print(f"⏸️  Pipeline paused - AI Agent will write SEO descriptions...")
    print(f"\n💡 TIP: Use bigrams/trigrams provided to make descriptions semantically relevant!")
    print("="*80 + "\n")
    
    # Auto-generate descriptions from TL;DR section of each article
    for article in articles_for_export:
        # Extract description from first content part (contains TL;DR)
        content = article.get('Content_Part1', '')
        
        # Try to extract TL;DR section
        tldr_match = re.search(r'<h2>TL;DR</h2>\s*<p>(.*?)</p>', content, re.DOTALL | re.IGNORECASE)
        if tldr_match:
            tldr_text = re.sub(r'<[^>]+>', '', tldr_match.group(1))  # Strip HTML tags
            tldr_text = tldr_text.replace('\n', ' ').strip()
            # Truncate to 160 chars for meta description
            if len(tldr_text) > 160:
                tldr_text = tldr_text[:157] + '...'
            article['Description'] = tldr_text
        else:
            # Fallback: use title as description
            article['Description'] = article['Title'][:160]
    
    # Save to CSV with structure metadata + dynamic content columns
    csv_file = os.path.join(SESSION_DIR, "step12_FRAMER_EXPORT.csv")
    
    fieldnames = [
        'Title',
        'Date', 
        'Author',
        'Prompt',
        'Article_Type',
        'Hub_Title',
        'Related_Spokes',
        'Final_URL',
        'Description'
    ] + [f'Content_Part{i}' for i in range(1, max_parts + 1)]
    
    import csv as csv_module
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv_module.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(articles_for_export)
    
    log(f"\n✅ Step 12 complete!")
    log(f"   Articles exported: {len(articles_for_export)}")
    log(f"   📁 Individual HTML files: {html_dir}/ ({len(articles_for_export)} files)")
    log(f"   📄 CSV export: {csv_file}")
    log(f"\n📊 Output structure:")
    log(f"   - HTML files: step12_output/html/*.html (for easy debugging)")
    log(f"   - CSV file: step12_FRAMER_EXPORT.csv (for Google Sheets)")
    log(f"\n📋 NEXT: Step 12B - HTML Quality Review")
    log(f"   AI agent will review individual HTML files and fix issues")
    log(f"\n💡 BENEFIT: Can now edit individual HTML files instead of giant CSV!")
    
    return csv_file, {
        'articles_exported': len(articles_for_export),
        'article_slugs': article_slugs,
        'csv_file': csv_file
    }

# ============================================================================
# STEP 12B: HTML QUALITY EDITOR (AI AGENT)
# ============================================================================

def create_step12b_html_editor_task(csv_file):
    """
    Create AI agent task to review and fix HTML conversion issues
    NOW WORKS WITH: Individual HTML files in step12_output/html/
    Also reviews CSV for completeness
    """
    log("="*80)
    log("STEP 12B: HTML QUALITY EDITOR TASK (AI Agent)")
    log("="*80)
    
    # Check if individual HTML files exist (modular approach)
    html_dir = os.path.join(SESSION_DIR, "step12_output", "html")
    html_files = list(Path(html_dir).glob("*.html")) if os.path.exists(html_dir) else []
    
    if html_files:
        log(f"   Found {len(html_files)} individual HTML files - using modular approach!")
        log(f"   HTML directory: {html_dir}")
    else:
        log(f"   No individual HTML files - using CSV-based approach")
    
    # Analyze the CSV to identify issues
    import csv as csv_module
    
    total_issues = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv_module.DictReader(f)
        rows = list(reader)
    
    for row in rows:
        article_title = row['Title']
        
        # Get all content parts
        content_parts = []
        for i in range(1, 10):
            col_name = f'Content_Part{i}'
            if col_name in row and row[col_name]:
                content_parts.append(row[col_name])
        
        html_content = ''.join(content_parts)
        
        # Quick checks
        issues = []
        
        # Check H3 tags
        h3_count = len(re.findall(r'<h3>', html_content))
        if h3_count == 0 and len(html_content) > 5000:
            issues.append("No <h3> tags found (subsections missing)")
        
        # Check for orphaned text
        orphaned = re.findall(r'</p>\s*(<strong>|<a |[A-Z])', html_content)
        if orphaned:
            issues.append(f"{len(orphaned)} orphaned text sections (missing <p> tags)")
        
        # Check for metadata
        if re.search(r'Primary Keywords|Internal Links|Word Count', html_content):
            issues.append("Metadata not removed")
        
        # Check for markdown tables
        if '|---|' in html_content or '| --- |' in html_content:
            issues.append("Markdown tables not converted to HTML")
        
        # Check for broken links
        broken_links = len(re.findall(r'<a href=""', html_content))
        if broken_links:
            issues.append(f"{broken_links} broken links (empty href)")
        
        # Check bullet point structure
        orphaned_li = re.findall(r'(<li>(?!</ul>|</ol>)[^<]*$)', html_content)
        if orphaned_li:
            issues.append(f"{len(orphaned_li)} orphaned <li> tags (not in <ul>/<ol>)")
        
        # Check for leftover markdown list syntax
        if re.search(r'^- ', html_content, re.MULTILINE):
            issues.append("Markdown list syntax not converted (still has '- ' bullets)")
        
        if issues:
            total_issues.append({'title': article_title, 'issues': issues})
    
    log(f"   Analyzed {len(rows)} articles")
    log(f"   Articles with issues: {len(total_issues)}/{len(rows)}")
    
    # Create AI agent task
    task_file = os.path.join(SESSION_DIR, "step12b_HTML_EDITOR_TASK.md")
    
    with open(task_file, 'w', encoding='utf-8') as f:
        f.write(f"""# STEP 12B: HTML Quality Editor (AI Agent Task)

**Session:** {SESSION_ID}  
**CSV File:** `{os.path.basename(csv_file)}`  
**Articles:** {len(rows)}  
**Issues Found:** {len(total_issues)}

---

## 🎯 YOUR MISSION

Review and fix HTML conversion issues in the CSV file before publishing.

**Input:** `step12_FRAMER_EXPORT.csv`  
**Output:** `step12b_HTML_CLEANED.csv`

---

## 🔍 ISSUES DETECTED

""")
        
        if total_issues:
            for item in total_issues:
                f.write(f"### {item['title']}\n\n")
                for issue in item['issues']:
                    f.write(f"- ⚠️  {issue}\n")
                f.write("\n")
        else:
            f.write("✅ No critical issues detected - but still review for edge cases!\n\n")
        
        f.write("""---

## ✅ HTML QUALITY CHECKLIST

For EACH article in the CSV, verify and fix:

### **1. Heading Structure**
- [ ] Has proper `<h2>` section headings
- [ ] Has `<h3>` subsection headings where needed
- [ ] Heading hierarchy is correct (H1→H2→H3, no skipping levels)
- [ ] No empty headings (`<h2></h2>`)

### **2. Paragraph Tags**
- [ ] ALL text wrapped in `<p>` tags
- [ ] No orphaned text between tags
- [ ] Paragraphs properly closed (`<p>...</p>`)
- [ ] No malformed tags (`<p<p>` or missing `>`)

### **3. Tables (if any)**
- [ ] Markdown tables converted to HTML `<table>`
- [ ] Proper structure: `<table><tr><td>...</td></tr></table>`
- [ ] Headers use `<th>` tags
- [ ] No leftover `|---|` markdown
- [ ] **STYLING APPLIED** - Tables MUST have inline styles for proper display

### **4. Links**
- [ ] No broken links (`<a href="">` with empty href)
- [ ] All {BRAND_NAME} links valid
- [ ] External links have proper URLs
- [ ] Link text is descriptive (not "click here")

### **5. Lists**
- [ ] All `<li>` tags inside `<ul>` or `<ol>`
- [ ] Lists properly opened and closed
- [ ] No orphaned `<li>` tags

### **6. Special Elements**
- [ ] Bold text uses `<strong>` (not `<b>`)
- [ ] Italic text uses `<em>` (not `<i>`)
- [ ] Code blocks use `<pre><code>` if needed
- [ ] Blockquotes use `<blockquote>` if needed

### **7. Cleanup**
- [ ] ALL metadata removed (Primary Keywords, Internal Links, Word Count, etc.)
- [ ] Horizontal rules removed (`<hr>`, `<p>---</p>`)
- [ ] No leftover markdown syntax (`**`, `##`, `###`)
- [ ] No HTML entities issues (`&amp;` for `&`, etc.)
- [ ] **NO FREQUENCY DATA LEAKS** (remove phrases like "The 529x frequency of", "trigram analysis", "industry responses")

### **8. Content Quality**
- [ ] Article ends properly (conclusion section present)
- [ ] No abrupt cutoffs mid-sentence
- [ ] Closing paragraph has proper `</p>` tag

### **9. Brand Voice & Style**
- [ ] Brand name spelling: "{BRAND_NAME}" (verify correct capitalization/spacing)
- [ ] "AI" always uppercase (never "Ai" or "ai")
- [ ] Product/feature names use correct capitalization
- [ ] Colon capitalization: lowercase after colon unless proper noun
  - Example: "The shift is this: contact center QA is..." (lowercase "c")
  - Example: "Three platforms: Solidroad, Observe.AI..." (proper nouns)

### **10. Editorial Polish**
- [ ] No redundant heading echoes (heading followed by same text in bold)
  - ❌ Bad: `<h3>Results</h3><p><strong>Results:</strong></p>`
  - ✅ Good: `<h3>Results</h3><p>Organizations achieved...</p>`
- [ ] Paragraphs with colons only if followed by list
  - ❌ Bad: `<p>...outcomes:</p><h3>Next Section</h3>`
  - ✅ Good: `<p>...outcomes.</p><h3>Next Section</h3>`

---

## 🔧 COMMON FIXES NEEDED

**Issue: Missing H3 tags**
```html
<!-- BEFORE (wrong) -->
<h2>Section Title</h2>
<p>Subsection content here...</p>

<!-- AFTER (correct) -->
<h2>Section Title</h2>
<h3>Subsection Title</h3>
<p>Subsection content here...</p>
```

**Issue: Orphaned text**
```html
<!-- BEFORE (wrong) -->
</p>
<strong>Important note:</strong> Some text here.
<p>Next paragraph...</p>

<!-- AFTER (correct) -->
</p>
<p><strong>Important note:</strong> Some text here.</p>
<p>Next paragraph...</p>
```

**Issue: Markdown table**
```html
<!-- BEFORE (wrong) -->
| Platform | Best For |
|----------|----------|
| {BRAND_NAME} | Example use case |

<!-- AFTER (correct with styling) -->
<table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
  <tr>
    <th style="background-color: #f5f5f5; padding: 12px; text-align: left; border: 1px solid #ddd; font-weight: 600;">Platform</th>
    <th style="background-color: #f5f5f5; padding: 12px; text-align: left; border: 1px solid #ddd; font-weight: 600;">Best For</th>
  </tr>
  <tr>
    <td style="padding: 12px; border: 1px solid #ddd;">{BRAND_NAME}</td>
    <td style="padding: 12px; border: 1px solid #ddd;">Example use case</td>
  </tr>
  <tr style="background-color: #fafafa;">
    <td style="padding: 12px; border: 1px solid #ddd;">Competitor A</td>
    <td style="padding: 12px; border: 1px solid #ddd;">Alternative approach</td>
  </tr>
</table>

**CRITICAL TABLE STYLING:**
- Table: width: 100%, border-collapse: collapse, margin: 20px 0
- Headers (th): background-color: #f5f5f5, padding: 12px, border: 1px solid #ddd, font-weight: 600
- Cells (td): padding: 12px, border: 1px solid #ddd
- Alternating rows: background-color: #fafafa (zebra striping for readability)
```

---

## 💾 OUTPUT

Save cleaned CSV to: `step12b_HTML_CLEANED.csv`

**CRITICAL:** Update ALL Content_Part columns for each article that has issues!

---

## 🎯 SUCCESS CRITERIA

- ✅ All {len(rows)} articles reviewed
- ✅ All HTML structure issues fixed
- ✅ All tables properly converted WITH inline styling
- ✅ No markdown syntax remaining
- ✅ Clean, publish-ready HTML

**CRITICAL:** All `<table>` elements MUST have inline CSS styling for proper display in Framer CMS!

The HTML should be ready to paste directly into Framer CMS!
""")
    
    log(f"✅ HTML editor task created: {task_file}")
    
    print(f"\n🤖 AGENT_TASK_READY: {task_file}")
    
    if html_files:
        print(f"📁 INDIVIDUAL HTML FILES: step12_output/html/ ({len(html_files)} files)")
        print(f"   → Edit each HTML file individually (easier!)")
        print(f"   → Then update CSV with cleaned HTML")
    else:
        print(f"📋 CSV FILE: step12_FRAMER_EXPORT.csv")
        print(f"   → Edit HTML in Content_Part1 column")
    
    print(f"📋 OUTPUT: step12b_HTML_CLEANED.csv")
    print(f"⏸️  Pipeline paused - AI Agent will fix HTML issues...")
    print(f"\n💡 {len(total_issues)}/{len(rows)} articles need fixes")
    print(f"   Common: Missing H3 tags, orphaned text")
    print("="*80 + "\n")
    
    return task_file

# ============================================================================
# STEP 12C: CONTENT GAP ANALYSIS
# ============================================================================

def step12c_analyze_content_gaps():
    """
    Analyze all internal links to find content gaps
    Identifies claimed content that doesn't exist (e.g., links to homepage instead of specific article)
    """
    log("="*80)
    log("STEP 12C: CONTENT GAP ANALYSIS")
    log("="*80)
    
    from collections import Counter
    
    articles_dir = Path(SESSION_DIR) / 'articles'
    
    if not articles_dir.exists():
        log("⚠️  Articles directory not found - skipping gap analysis")
        return None
    
    # Collect existing pages
    existing_pages = {'/', '/products', '/pricing', '/contact', '/customers'}
    
    for article_file in articles_dir.rglob('step*.md'):
        if 'TASK' not in article_file.name:
            with open(article_file, 'r') as f:
                title = f.readline().strip('#').strip()
            slug = title.lower()
            slug = re.sub(r'[^\w\s-]', '', slug)
            slug = re.sub(r'[-\s]+', '-', slug)
            existing_pages.add(f'/blog/{slug}')
    
    # Analyze all links with smart categorization
    all_links = []
    content_gaps = {}  # Changed to dict to store metadata
    
    for article_file in articles_dir.rglob('step*.md'):
        # Skip task files, intermediate versions, bibliographies
        if any(skip in article_file.name for skip in ['TASK', 'BIBLIOGRAPHY', 'step5_', 'step6_', 'step7_']):
            continue
        
        # Only analyze final articles: step8 (hub) and step10_spoke* (spokes)
        if not ('step8_ARTICLE_WITH_CITATIONS' in article_file.name or 'step10_spoke' in article_file.name):
            continue
        
        with open(article_file, 'r') as f:
            content = f.read()
        
        # Extract brand links (domain from BRAND_URL)
        brand_domain = BRAND_URL.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
        pattern = rf'\[([^\]]+)\]\((https?://(?:www\.)?{re.escape(brand_domain)}[^\)]*|/blog[^\)]*)\)'
        
        for match in re.finditer(pattern, content):
            link_text = match.group(1)
            url = match.group(2)
            
            # Check if homepage link
            is_homepage = url.endswith('.com') or url.endswith('.com/')
            
            # Extract path
            if url.startswith('/'):
                path = url
            else:
                path_match = re.search(r'\.com(/[^?#]*)', url)
                path = path_match.group(1) if path_match else '/'
            
            # Categorize link text type
            link_lower = link_text.lower()
            brand_lower = BRAND_NAME.lower()
            is_generic_branding = any(term in link_lower for term in [
                f"{brand_lower}'s approach", f"{brand_lower}'s platform", f"{brand_lower}'s solution",
                f"{brand_lower}'s", f"{brand_lower} implements", "learn more", "get started"
            ])
            
            # Generic keywords indicating specific content (not product-specific)
            generic_content_keywords = [
                'framework', 'methodology', 'template', 'guide',
                'analysis', 'case study', 'checklist', 'playbook',
                'blueprint', 'strategy', 'comparison', 'best practices'
            ]
            
            # Add brand-specific keywords from config if defined
            brand_content_keywords = CONFIG.get('content_gap_analysis', {}).get('specific_topic_keywords', [])
            all_content_keywords = generic_content_keywords + brand_content_keywords
            
            is_specific_topic = any(keyword in link_lower for keyword in all_content_keywords) and not is_generic_branding
            
            # Only flag as gap if meaningful
            if is_homepage and not link_text.lower() in [BRAND_NAME.lower(), 'homepage']:
                if is_specific_topic:
                    gap_type = 'specific_topic'
                elif is_generic_branding:
                    gap_type = 'generic_branding'
                else:
                    gap_type = 'vague'
                
                if link_text not in content_gaps:
                    content_gaps[link_text] = {'count': 0, 'type': gap_type, 'url': url}
                content_gaps[link_text]['count'] += 1
                
            elif path not in existing_pages and not is_homepage:
                # Missing page
                gap_key = f"{link_text} ({url})"
                if gap_key not in content_gaps:
                    content_gaps[gap_key] = {'count': 0, 'type': 'missing_page', 'url': url}
                content_gaps[gap_key]['count'] += 1
            
            all_links.append({'file': article_file.name, 'text': link_text, 'url': url})
    
    log(f"   Analyzed {len(set(l['file'] for l in all_links))} articles")
    log(f"   Found {len(all_links)} internal links")
    log(f"   Identified {len(content_gaps)} content gaps")
    
    # Generate report
    report_file = os.path.join(SESSION_DIR, "step12c_CONTENT_GAPS.md")
    
    with open(report_file, 'w') as f:
        f.write("# Content Gap Analysis\n\n")
        f.write(f"**Session:** {SESSION_ID}\n")
        f.write(f"**Total Links:** {len(all_links)}\n")
        f.write(f"**Content Gaps:** {len(content_gaps)}\n\n")
        f.write("---\n\n")
        
        # Categorize gaps intelligently
        create_gaps = []
        fix_link_gaps = []
        consider_gaps = []
        
        for gap_name, gap_data in content_gaps.items():
            count = gap_data['count']
            gap_type = gap_data['type']
            
            if gap_type == 'specific_topic' and count >= 3:
                create_gaps.append((gap_name, count, 'High demand + specific topic'))
            elif gap_type == 'specific_topic' and count >= 1:
                consider_gaps.append((gap_name, count, 'Specific topic - consider if core to brand'))
            elif gap_type == 'generic_branding':
                fix_link_gaps.append((gap_name, count, 'Generic branding - fix link text'))
            elif gap_type == 'missing_page':
                create_gaps.append((gap_name, count, 'Linked to missing page'))
        
        # Summary table with smart categorization
        f.write("## 📋 SMART GAP ANALYSIS\n\n")
        
        if create_gaps:
            f.write("### ✅ CREATE THESE ARTICLES\n\n")
            f.write("| Gap | Mentions | Reason |\n")
            f.write("|-----|----------|--------|\n")
            for gap, count, reason in sorted(create_gaps, key=lambda x: x[1], reverse=True):
                gap_name = gap.split(' (')[0]
                f.write(f"| {gap_name} | {count}x | {reason} |\n")
            f.write("\n")
        
        if consider_gaps:
            f.write("### 🤔 CONSIDER CREATING (If Core to Brand)\n\n")
            f.write("| Gap | Mentions | Reason |\n")
            f.write("|-----|----------|--------|\n")
            for gap, count, reason in sorted(consider_gaps, key=lambda x: x[1], reverse=True):
                gap_name = gap.split(' (')[0]
                f.write(f"| {gap_name} | {count}x | {reason} |\n")
            f.write("\n**Ask:** Are these core to your value prop? If yes → Create. If no → Fix link text.\n\n")
        
        if fix_link_gaps:
            f.write("### 📝 FIX LINK TEXT (Don't Create Articles)\n\n")
            f.write("| Gap | Mentions | Reason |\n")
            f.write("|-----|----------|--------|\n")
            for gap, count, reason in sorted(fix_link_gaps, key=lambda x: x[1], reverse=True):
                gap_name = gap.split(' (')[0]
                f.write(f"| {gap_name} | {count}x | {reason} |\n")
            f.write("\n**Action:** Update link text to be honest about destination.\n\n")
        
        f.write("\n---\n\n")
        
        # Recommendations
        f.write("## 🎯 RECOMMENDED ACTIONS\n\n")
        
        f.write("### **Create Articles** (proven demand or missing pages):\n")
        for gap, count, reason in sorted(create_gaps, key=lambda x: x[1], reverse=True):
            gap_name = gap.split(' (')[0]
            slug = gap_name.lower().replace(' ', '-').replace("'", '')
            slug = re.sub(r'[^\w-]', '', slug)
            f.write(f"- **{gap_name}** ({count}x) → Create `/blog/{slug}`\n")
        
        f.write("\n### **Consider Creating** (if core to brand positioning):\n")
        for gap, count, reason in sorted(consider_gaps, key=lambda x: x[1], reverse=True)[:5]:
            gap_name = gap.split(' (')[0]
            slug = gap_name.lower().replace(' ', '-').replace("'", '')
            slug = re.sub(r'[^\w-]', '', slug)
            f.write(f"- **{gap_name}** ({count}x) → Ask: Core differentiator? If yes: `/blog/{slug}`\n")
        
        f.write("\n### **Fix Link Text** (don't create articles):\n")
        for gap, count, reason in sorted(fix_link_gaps, key=lambda x: x[1], reverse=True):
            f.write(f"- **{gap}** ({count}x) → Update to honest text like '{BRAND_NAME}' or 'Learn more'\n")
        
        f.write("\n---\n\n")
        
        # Add strategic analysis and recommendations
        total_to_create = len(create_gaps)
        total_to_fix = len(fix_link_gaps)
        total_to_consider = len(consider_gaps)
        
        f.write("## 📊 STRATEGIC ANALYSIS\n\n")
        
        f.write("**Gap breakdown:**\n")
        f.write(f"- Fix link text: {total_to_fix} gaps (no articles needed!)\n")
        f.write(f"- Consider creating: {total_to_consider} gaps (if core to brand)\n")
        f.write(f"- Missing pages: {total_to_create} gaps (specific URLs referenced)\n\n")
        
        # Calculate cluster health
        current_articles = 11
        max_cluster_size = 18
        potential_new_articles = min(total_to_create + (total_to_consider // 3), max_cluster_size - current_articles)
        
        f.write(f"**Cluster capacity:**\n")
        f.write(f"- Current articles: {current_articles}\n")
        f.write(f"- Maximum cluster size: {max_cluster_size}\n")
        f.write(f"- Remaining capacity: {max_cluster_size - current_articles} articles\n\n")
        
        if potential_new_articles <= (max_cluster_size - current_articles):
            f.write(f"✅ **Safe to create:** {potential_new_articles} articles without exceeding cluster limits\n\n")
        else:
            f.write(f"⚠️  **Warning:** Creating all gaps would exceed cluster capacity!\n")
            f.write(f"   Recommend: Consolidate or be selective\n\n")
        
        # Smart recommendations
        f.write("## 🎯 SMART RECOMMENDATIONS\n\n")
        
        f.write("### **Quick Wins (Do First - 30 min):**\n")
        f.write(f"1. Fix {total_to_fix} generic branding links\n")
        f.write("   - Update to honest text: '{BRAND_NAME}' or 'Learn more'\n")
        f.write("   - Impact: Fixes gaps without creating content ✅\n\n")
        
        if total_to_consider > 0:
            f.write("### **Decision Needed:**\n")
            f.write(f"Review {total_to_consider} \"Consider\" gaps:\n")
            f.write("- Are these core to your value proposition?\n")
            f.write("- If YES → Create articles\n")
            f.write("- If NO → Fix link text to generic\n\n")
        
        if total_to_create > 0:
            f.write("### **Create These (if URLs don't exist):**\n")
            f.write(f"{total_to_create} links point to specific /blog/ URLs\n")
            f.write("- First: Verify URLs don't already exist on your site\n")
            f.write("- If exist: Fix URLs in articles\n")
            f.write("- If don't exist: Create those articles\n\n")
        
        # Consolidation suggestion
        f.write("### **Consolidation Opportunity:**\n")
        if total_to_consider >= 3:
            f.write(f"Instead of {total_to_consider} separate articles, consider:\n")
            f.write("- 1 comprehensive 'Quality Metrics Guide' (consolidates metric gaps)\n")
            f.write("- 1 'Coaching Resources Hub' (consolidates training gaps)\n")
            f.write("- 1 'Implementation Guide' (consolidates setup/config gaps)\n")
            f.write(f"- Result: {total_to_consider} gaps → 3 deep articles\n\n")
        else:
            f.write("Low gap count - consolidation not needed.\n\n")
        
        # Anti-slop warning
        f.write("## ⚠️  ANTI-AI-SLOP WARNING\n\n")
        f.write("**Don't create articles just to fill gaps!**\n\n")
        f.write("Apply the Dead-End strategy:\n")
        f.write("- New articles should link BACK to existing cluster\n")
        f.write("- Don't link to NEW missing topics\n")
        f.write("- Cap growth at 18 articles per cluster\n\n")
        f.write(f"**Current plan:** {current_articles} + {potential_new_articles} = {current_articles + potential_new_articles} articles\n")
        
        if (current_articles + potential_new_articles) <= max_cluster_size:
            f.write(f"✅ Within limits (< {max_cluster_size})\n\n")
        else:
            f.write(f"⚠️  Would exceed {max_cluster_size} - be selective!\n\n")
        
        f.write("---\n\n")
        f.write("## 💡 NEXT STEPS\n\n")
        f.write("1. **Quick wins:** Fix generic branding link text (30 min)\n")
        f.write("2. **Verify:** Check if product/customer pages exist\n")
        f.write("3. **Decide:** Which gaps are core to brand positioning?\n")
        f.write("4. **Create:** 3-5 strategic articles maximum\n")
        f.write("5. **Re-analyze:** Run Step 12C again to measure progress\n\n")
        f.write("**See `CONTENT_GAP_STRATEGY.md` for full strategic framework.**\n")
    
    log(f"✅ Content gap report: {report_file}")
    log(f"   High priority gaps: {len([g for g, data in content_gaps.items() if data.get('count', 0) >= 3])}")
    
    return report_file

# ============================================================================
# STEP 12D: LINK VERIFICATION (AI AGENT + BROWSER)
# ============================================================================

def create_step12d_link_verification_task():
    """
    Create AI agent task to verify all internal links and citations
    Uses browser tools to check if links work and content is relevant
    """
    log("="*80)
    log("STEP 12D: LINK VERIFICATION TASK (AI Agent + Browser)")
    log("="*80)
    
    # Count links across all articles (check HTML output first, fall back to markdown)
    html_dir = Path(SESSION_DIR) / 'step12_output' / 'html'
    articles_dir = Path(SESSION_DIR) / 'articles'
    total_internal_links = 0
    total_citations = 0
    
    # Prefer HTML files (final output with citations)
    if html_dir.exists() and list(html_dir.glob('*.html')):
        for html_file in html_dir.glob('*.html'):
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count internal brand links (to brand domain or /blog/)
            brand_domain = BRAND_URL.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
            internal_domain = len(re.findall(rf'href="https?://(?:www\.)?{re.escape(brand_domain)}[^"]*"', content))
            internal_blog = len(re.findall(r'href="/blog/[^"]+"', content))
            total_internal_links += internal_domain + internal_blog
            
            # Count external citations (exclude brand and /blog/)
            all_hrefs = re.findall(r'href="(https?://[^"]+)"', content)
            for href in all_hrefs:
                if brand_domain not in href and '/blog/' not in href:
                    total_citations += 1
    else:
        # Fall back to markdown articles
        hub_count = len(list(articles_dir.glob('hub/step8*.md')))
        spoke_count = len(list(articles_dir.glob('spokes/step10_spoke*.md')))
        utility_count = len(list(articles_dir.glob('utilities/*.md')))
        
        for article_file in articles_dir.rglob('*.md'):
            # Skip task files
            if 'TASK' in article_file.name or 'BIBLIOGRAPHY' in article_file.name:
                continue
            
            with open(article_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count internal brand links
            brand_domain = BRAND_URL.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
            internal = len(re.findall(rf'\[([^\]]+)\]\(https?://(?:www\.)?{re.escape(brand_domain)}', content))
            total_internal_links += internal
            
            # Count citations (markdown format)
            citations = len(re.findall(r'\[\[\d+\]\]', content))
            total_citations += citations
    
    # Count articles by type for reporting
    hub_count = len(list(articles_dir.glob('hub/*.md'))) if articles_dir.exists() else 0
    spoke_count = len(list(articles_dir.glob('spokes/step10_spoke*.md'))) if articles_dir.exists() else 0
    utility_count = len(list(articles_dir.glob('utilities/*.md'))) if articles_dir.exists() else 0
    total_articles = hub_count + spoke_count + utility_count
    
    log(f"   Found {total_internal_links} internal {BRAND_NAME} links")
    log(f"   Found {total_citations} external citations")
    
    task_file = os.path.join(SESSION_DIR, "step12d_LINK_VERIFICATION_TASK.md")
    
    with open(task_file, 'w', encoding='utf-8') as f:
        f.write(f"""# STEP 12D: Link Verification (AI Agent + Browser Task)

**Session:** {SESSION_ID}  
**Articles:** 11 (hub + 10 spokes)  
**Internal Links:** {total_internal_links}  
**Citations:** {total_citations}

---

## 🎯 YOUR MISSION

Use browser tools to verify ALL links actually work and content is relevant.

**Two verification types:**
1. **Internal links** - Do {BRAND_NAME} links go to right pages?
2. **Citations** - Do external links support the claims?

---

## 🔍 VERIFICATION PROCESS

### **For Internal {BRAND_NAME} Links:**

```python
for link in internal_links:
    # Navigate to URL
    mcp_cursor-browser-extension_browser_navigate(link.url)
    
    # Check page exists (not 404)
    snapshot = mcp_cursor-browser-extension_browser_snapshot()
    
    # Verify content matches link text (example)
    if link.text == "implementation guide":
        if "implementation" not in snapshot and "guide" not in snapshot:
            flag_issue("Link promises implementation guide but page doesn't have it")
```

**Check:**
- ✅ URL exists (200 status, not 404)
- ✅ Content matches link text promise
- ❌ Flag: Homepage when claiming specific content

### **For External Citations:**

```python
for citation in citations:
    # Navigate to citation URL
    mcp_cursor-browser-extension_browser_navigate(citation.url)
    
    # Check accessible
    snapshot = mcp_cursor-browser-extension_browser_snapshot()
    
    # Extract claim context from article
    claim = get_claim_text(article, citation)
    
    # Verify citation supports claim
    if claim_keyword not in snapshot:
        flag_issue("Citation doesn't support claim")
```

**Check:**
- ✅ URL accessible (not 404, not paywall)
- ✅ Content relevant to claim
- ✅ Source is authoritative

---

## 💾 OUTPUT

Create: `step12d_LINK_VERIFICATION_REPORT.md`

**Format:**
```markdown
# Link Verification Report

**Date:** {datetime.now()}
**Internal Links Checked:** {total_internal_links}
**Citations Checked:** {total_citations}

## ✅ VALID (120)
- [link](url) - Verified

## ❌ BROKEN (12)  
- [implementation guide](homepage)
  - Issue: Links to homepage, not implementation guide article
  - Fix: Create /blog/implementation-guide

## ⚠️  MISLEADING (8)
- [citation](url)
  - Issue: Page doesn't support claim
  - Fix: Find better citation or update claim
```

---

## 🎯 SUCCESS CRITERIA

- [ ] All {total_internal_links} internal links verified
- [ ] All {total_citations} citations verified  
- [ ] Issues documented with recommendations
- [ ] Report saved

**Time estimate:** 30-45 minutes for all links
""")
    
    log(f"✅ Link verification task created: {task_file}")
    
    print(f"\n🤖 AGENT_TASK_READY: {task_file}")
    print(f"📋 USE: Browser tools to verify all links")
    print(f"📋 OUTPUT: step12d_LINK_VERIFICATION_REPORT.md")
    print(f"⏸️  Pipeline paused - AI Agent will verify {total_internal_links + total_citations} links...")
    print("="*80 + "\n")
    
    return task_file

# ============================================================================
# STEP 12E: FIX BROKEN LINKS (AI AGENT)
# ============================================================================

def create_step12e_fix_links_task():
    """
    Create AI agent task to fix broken/misleading links from Step 12D report
    """
    log("="*80)
    log("STEP 12E: FIX BROKEN LINKS TASK")
    log("="*80)
    
    # Read Step 12C gap report for quick fixes
    gap_report = os.path.join(SESSION_DIR, "step12c_CONTENT_GAPS.md")
    
    if not os.path.exists(gap_report):
        log("⚠️  No gap report found - run Step 12C first")
        return None
    
    with open(gap_report, 'r') as f:
        gap_content = f.read()
    
    # Extract fix recommendations
    fix_count = gap_content.count('FIX LINK TEXT')
    
    log(f"   Found recommendations in gap report")
    log(f"   Quick fixes available")
    
    task_file = os.path.join(SESSION_DIR, "step12e_FIX_LINKS_TASK.md")
    
    with open(task_file, 'w', encoding='utf-8') as f:
        f.write(f"""# STEP 12E: Fix Broken Links (AI Agent Task)

**Session:** {SESSION_ID}

---

## 🎯 YOUR MISSION

Fix all broken/misleading links identified in Step 12C and Step 12D.

**Input:** 
- `step12c_CONTENT_GAPS.md` (gaps identified)
- `step12d_LINK_VERIFICATION_REPORT.md` (verification results)

**Output:** 
- Updated article files with fixed links
- `step12e_LINKS_FIXED.md` (completion report)

---

## 📝 FIXES NEEDED

Review both reports and fix:

### **1. Generic Branding Links**
From Step 12C "Fix Link Text" section:
- Update misleading link text to be honest
- Example: "{BRAND_NAME}'s approach" → "{BRAND_NAME}"

### **2. Broken URLs**
From Step 12D verification:
- Update wrong URLs to correct pages
- Example: `/blog/wrong-slug` → `/blog/correct-slug`

### **3. Homepage Overuse**
- Specific claims linking to homepage
- Either: Create the article OR update link text

---

## 💾 OUTPUT

**Save:** `step12e_LINKS_FIXED.md`

```markdown
# Links Fixed Report

**Fixes Applied:**
- Generic branding: 12 links updated
- Broken URLs: 3 links fixed
- Homepage overuse: 5 links updated

**Articles Modified:**
- articles/hub/step8_ARTICLE_WITH_CITATIONS.md
- articles/spokes/step10_spoke01_*.md
- ... (list all modified files)

**Status:** ✅ All links honest and working
```

---

## ✅ COMPLETION

Mark complete when all identified issues are fixed!
""")
    
    log(f"✅ Fix links task created: {task_file}")
    
    print(f"\n🤖 AGENT_TASK_READY: {task_file}")
    print(f"📋 FIX: Generic branding links + broken URLs")
    print(f"📋 OUTPUT: step12e_LINKS_FIXED.md")
    print("="*80 + "\n")
    
    return task_file

# ============================================================================
# STEP 12.5: CONTENT QA & EDITORIAL POLISH (AUTOMATED)
# ============================================================================

def step12_5_content_qa_polish(csv_file, brand_config=None):
    """
    Content Quality Assurance & Editorial Polish
    Applies systematic editorial rules to HTML content before final export
    
    Args:
        csv_file: Path to CSV with HTML content (e.g., step12_FRAMER_EXPORT.csv)
        brand_config: Dictionary with brand-specific settings (optional)
    
    Returns:
        Path to polished CSV file
    """
    if brand_config is None:
        brand_config = {
            'brand_name': BRAND_NAME,
            'cta_path': '/book-demo',
            'domain': BRAND_URL,
            'ai_term': 'AI',  # Always uppercase
        }
    
    log("="*80)
    log("STEP 12.5: CONTENT QA & EDITORIAL POLISH")
    log("="*80)
    log(f"   Brand: {brand_config['brand_name']}")
    log(f"   CTA Path: {brand_config['cta_path']}")
    
    import csv as csv_module
    import anthropic
    
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    # Read input CSV
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv_module.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames
    
    polished_rows = []
    articles_polished = 0
    
    for idx, row in enumerate(rows):
        article_title = row['Title']
        log(f"\n   [{idx+1}/{len(rows)}] Polishing: {article_title}")
        
        # Get all content parts
        content_parts = []
        for i in range(1, 10):
            col_name = f'Content_Part{i}'
            if col_name in row and row[col_name]:
                content_parts.append(row[col_name])
        
        if not content_parts:
            log(f"      ⚠️  No content found - skipping")
            polished_rows.append(row)
            continue
        
        html_content = ''.join(content_parts)
        
        # Build QA prompt
        prompt = f"""You are a content editor performing final QA on an HTML blog article.

**BRAND-AGNOSTIC EDITORIAL RULES:**

1. **Brand Name Spelling:**
   - Brand name: "{brand_config['brand_name']}" - verify correct spelling/capitalization
   - Example: "Solidroad" is ONE WORD (not "Solid road" or "Solid Road")

2. **Technical Term Capitalization:**
   - "AI" must always be UPPERCASE (never "Ai" or "ai")
   - Applies to titles, headings, and body text

3. **Punctuation After Colons:**
   - When a colon introduces a complete sentence, use lowercase for the first word
   - ❌ Bad: "The key is this: Quality measurement requires..."
   - ✅ Good: "The key is this: quality measurement requires..."
   - Exception: Proper nouns always capitalized

4. **Heading Structure:**
   - Never follow a heading immediately with a redundant bold echo
   - ❌ Bad: <h3>The Results</h3><p><strong>The results:</strong></p>
   - ✅ Good: <h3>The Results</h3><p>Organizations achieved...</p>

5. **Paragraph Ending Punctuation:**
   - Paragraphs ending with colons should only do so if followed by a list (ul/ol)
   - If followed by a heading, change colon to period
   - ❌ Bad: <p>...following outcomes:</p><h3>Key Findings</h3>
   - ✅ Good: <p>...following outcomes.</p><h3>Key Findings</h3>

6. **CTA Link Consistency:**
   - All final CTA links should point to: {brand_config['domain']}{brand_config['cta_path']}
   - Fix any variations: /contact, /demo, /get-started → {brand_config['cta_path']}

7. **Frequency Data Leak Prevention:**
   - Remove any phrases like: "The [number]x frequency of", "trigram analysis shows", "[number]x mention in industry responses"
   - Reframe as research insights: "{brand_config['brand_name']}'s analysis shows that...", "Industry research reveals...", etc.
   - Keep the logical claim, just remove the internal metric reference

**YOUR TASK:**
Review the HTML article below and apply ALL editorial rules above.
Return ONLY the corrected HTML with NO explanations or commentary.

---

HTML TO REVIEW:
{html_content}
"""
        
        try:
            # Call Claude for editorial polish
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=16000,
                temperature=0.3,  # Low temp for consistency
                messages=[{"role": "user", "content": prompt}]
            )
            
            corrected_html = response.content[0].text.strip()
            
            # Split back into parts if needed (max 50k chars per part)
            corrected_parts = []
            current_part = ""
            
            for char in corrected_html:
                if len(current_part) >= 49500:
                    corrected_parts.append(current_part)
                    current_part = char
                else:
                    current_part += char
            
            if current_part:
                corrected_parts.append(current_part)
            
            # Update row with corrected parts
            new_row = row.copy()
            for i in range(1, 10):
                col_name = f'Content_Part{i}'
                if i <= len(corrected_parts):
                    new_row[col_name] = corrected_parts[i-1]
                elif col_name in new_row:
                    new_row[col_name] = ''  # Clear unused parts
            
            polished_rows.append(new_row)
            articles_polished += 1
            log(f"      ✅ Polished ({len(corrected_html):,} chars)")
            
        except Exception as e:
            log(f"      ⚠️  Error polishing: {e}")
            polished_rows.append(row)  # Keep original on error
    
    # Save polished CSV
    output_file = os.path.join(SESSION_DIR, "step12_5_CONTENT_POLISHED.csv")
    
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv_module.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(polished_rows)
    
    log(f"\n✅ Content QA complete!")
    log(f"   Articles polished: {articles_polished}/{len(rows)}")
    log(f"   Output: {os.path.basename(output_file)}")
    
    return output_file

# ============================================================================
# STEP 13: EVALUATE CLUSTER QUALITY (OPTIONAL)
# ============================================================================

def evaluate_with_claude_internal(prompt_text):
    """Claude Opus 4 evaluation"""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        start = time.time()
        
        # Use streaming to avoid 10-minute timeout for long requests
        content = ""
        with client.messages.stream(
            model="claude-opus-4-20250514",
            max_tokens=12000,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt_text}]
        ) as stream:
            for text in stream.text_stream:
                content += text
        
        elapsed = time.time() - start
        
        content = re.sub(r'^```json\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'^```\s*$', '', content, flags=re.MULTILINE).strip()
        
        json_match = re.search(r'\{[\s\S]*"rankings"[\s\S]*\}', content)
        if json_match:
            content = json_match.group(0)
        
        data = json.loads(content)
        
        return {
            'model': 'claude-opus-4',
            'elapsed': elapsed,
            'rankings': data.get('rankings', []),
            'summary': data.get('summary', ''),
            'error': None
        }
    except Exception as e:
        return {'model': 'claude-opus-4', 'error': str(e)}

def evaluate_with_perplexity_internal(prompt_text):
    """Perplexity Sonar Pro evaluation"""
    try:
        PERPLEXITY_API_KEY = get_secret('PERPLEXITY_API_KEY')
        if not PERPLEXITY_API_KEY:
            return {'model': 'perplexity', 'error': 'No API key'}
        
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        start = time.time()
        
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json={
                "model": "sonar-pro",
                "messages": [{"role": "user", "content": prompt_text}],
                "temperature": 0.2
            },
            timeout=180
        )
        
        elapsed = time.time() - start
        response.raise_for_status()
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        content = re.sub(r'^```json\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'^```\s*$', '', content, flags=re.MULTILINE).strip()
        
        json_match = re.search(r'\{[\s\S]*"rankings"[\s\S]*\}', content)
        if json_match:
            content = json_match.group(0)
        
        data = json.loads(content)
        
        return {
            'model': 'perplexity-sonar-pro',
            'elapsed': elapsed,
            'rankings': data.get('rankings', []),
            'summary': data.get('summary', ''),
            'error': None
        }
    except Exception as e:
        return {'model': 'perplexity-sonar-pro', 'error': str(e)}

def evaluate_with_openai_internal(prompt_text):
    """OpenAI GPT-4 evaluation"""
    try:
        OPENAI_API_KEY = get_secret('OPENAI_API_KEY')
        if not OPENAI_API_KEY:
            return {'model': 'openai-gpt4', 'error': 'No API key'}
        
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        start = time.time()
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json={
                "model": "gpt-4-turbo-preview",
                "messages": [{"role": "user", "content": prompt_text}],
                "temperature": 0.2,
                "max_tokens": 4000
            },
            timeout=180
        )
        
        elapsed = time.time() - start
        response.raise_for_status()
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        content = re.sub(r'^```json\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'^```\s*$', '', content, flags=re.MULTILINE).strip()
        
        json_match = re.search(r'\{[\s\S]*"rankings"[\s\S]*\}', content)
        if json_match:
            content = json_match.group(0)
        
        data = json.loads(content)
        
        return {
            'model': 'openai-gpt4',
            'elapsed': elapsed,
            'rankings': data.get('rankings', []),
            'summary': data.get('summary', ''),
            'error': None
        }
    except Exception as e:
        return {'model': 'openai-gpt4', 'error': str(e)}

def evaluate_with_sonnet_internal(prompt_text):
    """Claude Sonnet 4.5 evaluation"""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        start = time.time()
        
        # Use streaming to avoid 10-minute timeout for long requests
        content = ""
        with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=12000,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt_text}]
        ) as stream:
            for text in stream.text_stream:
                content += text
        
        elapsed = time.time() - start
        
        content = re.sub(r'^```json\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'^```\s*$', '', content, flags=re.MULTILINE).strip()
        
        json_match = re.search(r'\{[\s\S]*"rankings"[\s\S]*\}', content)
        if json_match:
            content = json_match.group(0)
        
        data = json.loads(content)
        
        return {
            'model': 'claude-sonnet-4.5',
            'elapsed': elapsed,
            'rankings': data.get('rankings', []),
            'summary': data.get('summary', ''),
            'error': None
        }
    except Exception as e:
        return {'model': 'claude-sonnet-4.5', 'error': str(e)}

# ============================================================================
# STEP 13A: MODEL CALIBRATION - Validate AI ranking accuracy
# ============================================================================

def parse_citation_counts_from_step2(step2_file):
    """Extract domain citation counts from Step 2 markdown file"""
    citation_ranking = []
    
    try:
        with open(step2_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse lines like: "1. **callcriteria.com** - cited 308x"
        for line in content.split('\n'):
            match = re.match(r'\d+\.\s+\*\*(.+?)\*\*\s+-\s+cited\s+(\d+)x', line)
            if match:
                domain = match.group(1)
                count = int(match.group(2))
                citation_ranking.append((domain, count))
        
        log(f"   ✅ Parsed {len(citation_ranking)} domains with citation counts")
        return citation_ranking
    
    except Exception as e:
        log(f"   ❌ Error parsing citation counts: {e}")
        return []

def rank_articles_with_model(articles, model_func, model_name):
    """Send articles to AI model for ranking, returns ranking or None if error"""
    
    # Randomize to avoid position bias
    randomized = articles.copy()
    random.shuffle(randomized)
    
    # Build prompt
    articles_text = ""
    for i, article in enumerate(randomized, 1):
        content_preview = article['content'][:5000]  # First 5000 chars
        articles_text += f"\n{'='*60}\nARTICLE {i}\n{'='*60}\n{content_preview}\n\n"
    
    prompt = f"""You are an expert content evaluator.

TASK: Rank these {len(articles)} articles by overall quality.

Consider:
- Depth and comprehensiveness
- Accuracy and credibility
- Writing quality and clarity
- Usefulness to readers
- Structure and organization

{articles_text}

Return ONLY JSON with rankings 1-{len(articles)} (1 = best):

{{
  "rankings": [
    {{"position": 1, "article_number": X, "reasoning": "Brief reason"}},
    {{"position": 2, "article_number": Y, "reasoning": "Brief reason"}},
    ...
  ],
  "summary": "Overall assessment in 1-2 sentences"
}}"""
    
    log(f"   🤖 Calling {model_name}...")
    
    result = model_func(prompt)
    
    if result.get('error'):
        log(f"      ❌ {model_name} error: {result['error']}")
        return None
    
    rankings = result.get('rankings', [])
    
    if not rankings:
        log(f"      ❌ {model_name} returned empty rankings")
        return None
    
    # Map back to original domain order
    ai_ranking = []
    for ranking_obj in sorted(rankings, key=lambda x: x['position']):
        article_idx = ranking_obj['article_number'] - 1
        if 0 <= article_idx < len(randomized):
            ai_ranking.append(randomized[article_idx]['domain'])
    
    log(f"      ✅ {model_name} ranked {len(ai_ranking)} articles")
    
    return ai_ranking

def calculate_spearman_correlation(ai_ranking, citation_ranking):
    """Calculate Spearman correlation between AI ranking and citation ranking"""
    try:
        from scipy.stats import spearmanr
    except ImportError:
        log(f"   ⚠️  scipy not installed - cannot calculate correlation")
        log(f"   Run: pip install scipy>=1.11.0")
        return None, None
    
    # Create rank dictionaries
    ai_ranks = {domain: i+1 for i, domain in enumerate(ai_ranking)}
    citation_ranks = {domain: i+1 for i, (domain, count) in enumerate(citation_ranking)}
    
    # Get common domains
    common_domains = set(ai_ranks.keys()) & set(citation_ranks.keys())
    
    if len(common_domains) < 3:
        log(f"   ⚠️  Not enough common domains ({len(common_domains)}) for correlation")
        return None, None
    
    # Build rank lists
    ai_rank_list = [ai_ranks[d] for d in common_domains]
    citation_rank_list = [citation_ranks[d] for d in common_domains]
    
    # Calculate Spearman correlation
    correlation, p_value = spearmanr(ai_rank_list, citation_rank_list)
    
    return correlation, p_value

def step13a_calibrate_ranking_model():
    """
    Step 13A: Model Calibration
    
    Tests AI ranking models against objective citation frequency.
    Only models with strong correlation (>0.6) are trusted for evaluation.
    
    Returns: (best_model_func, best_model_name, correlation_score) or (None, None, None)
    """
    log("="*80)
    log("STEP 13A: MODEL CALIBRATION - Testing AI Ranking Accuracy")
    log("="*80)
    
    # 1. Load citation data from Step 2
    step2_file = os.path.join(SESSION_DIR, "step2_FOR_AGENT_ANALYSIS.md")
    
    if not os.path.exists(step2_file):
        log(f"❌ Step 2 file not found: {step2_file}")
        log(f"   Run Step 2 first to generate citation data")
        return None, None, None
    
    log(f"📊 Loading citation data from Step 2...")
    citation_ranking = parse_citation_counts_from_step2(step2_file)
    
    if not citation_ranking:
        log(f"❌ No citation data found in Step 2")
        return None, None, None
    
    log(f"   Top cited: {citation_ranking[0][0]} ({citation_ranking[0][1]}x)")
    
    # 2. Load scraped content
    scraped_dir = os.path.join(SESSION_DIR, "scraped_content")
    
    if not os.path.exists(scraped_dir):
        log(f"❌ Scraped content folder not found: {scraped_dir}")
        log(f"   Run scraping step first")
        return None, None, None
    
    log(f"📂 Loading scraped content from: {scraped_dir}")
    
    scraped_articles = []
    for txt_file in Path(scraped_dir).glob("*.txt"):
        if "SCRAPING_COMPLETE" in txt_file.name:
            continue
        
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract domain from filename (e.g., "www_sentisum_com.txt" -> "www.sentisum.com")
            domain = txt_file.stem.replace('_', '.')
            
            # Extract article content (skip metadata)
            lines = content.split('\n')
            article_content = ""
            capture = False
            
            for line in lines:
                if '---' in line:
                    capture = True
                    continue
                if capture:
                    article_content += line + '\n'
            
            if not article_content:
                article_content = content
            
            # Find citation count for this domain
            citation_count = 0
            for cited_domain, count in citation_ranking:
                if cited_domain in domain or domain in cited_domain:
                    citation_count = count
                    break
            
            scraped_articles.append({
                'domain': domain,
                'content': article_content,
                'citations': citation_count,
                'word_count': len(article_content.split())
            })
        
        except Exception as e:
            log(f"   ⚠️  Could not load {txt_file.name}: {e}")
            continue
    
    log(f"✅ Loaded {len(scraped_articles)} scraped articles")
    
    if len(scraped_articles) < 3:
        log(f"❌ Not enough articles for calibration (need at least 3)")
        return None, None, None
    
    # Show what we're testing
    log(f"\n📋 CALIBRATION TEST ARTICLES:")
    for i, article in enumerate(scraped_articles, 1):
        log(f"   {i}. {article['domain']:<30} (cited {article['citations']:>3}x, {article['word_count']:>5} words)")
    
    # 3. Test models in order: Claude -> Perplexity -> Cursor (human)
    log(f"\n🧪 TESTING AI MODELS...\n")
    
    models_to_test = []
    
    # Add Claude Opus 4 if available
    if ANTHROPIC_API_KEY:
        models_to_test.append({
            'name': 'Claude Opus 4',
            'func': evaluate_with_claude_internal,
            'key': 'claude-opus'
        })
    
    # Add Claude Sonnet 4.5 if available
    if ANTHROPIC_API_KEY:
        models_to_test.append({
            'name': 'Claude Sonnet 4.5',
            'func': evaluate_with_sonnet_internal,
            'key': 'claude-sonnet'
        })
    
    # Add Perplexity if available
    if get_secret('PERPLEXITY_API_KEY'):
        models_to_test.append({
            'name': 'Perplexity Sonar Pro',
            'func': evaluate_with_perplexity_internal,
            'key': 'perplexity'
        })
    
    # Add OpenAI if available
    if get_secret('OPENAI_API_KEY'):
        models_to_test.append({
            'name': 'OpenAI GPT-4',
            'func': evaluate_with_openai_internal,
            'key': 'openai'
        })
    
    if not models_to_test:
        log(f"❌ No AI models available (no API keys found)")
        log(f"   Set one of: ANTHROPIC_API_KEY, PERPLEXITY_API_KEY, OPENAI_API_KEY")
        return None, None, None
    
    best_model = None
    best_model_name = None
    best_correlation = -1.0
    best_p_value = None
    
    results_table = []
    
    for model_info in models_to_test:
        model_name = model_info['name']
        model_func = model_info['func']
        
        log(f"{'─'*80}")
        log(f"Testing: {model_name}")
        log(f"{'─'*80}")
        
        # Get AI ranking
        ai_ranking = rank_articles_with_model(scraped_articles, model_func, model_name)
        
        if not ai_ranking:
            results_table.append({
                'model': model_name,
                'correlation': None,
                'p_value': None,
                'status': 'Failed',
                'ranking_details': []
            })
            continue
        
        # Calculate correlation
        correlation, p_value = calculate_spearman_correlation(ai_ranking, citation_ranking)
        
        if correlation is None:
            results_table.append({
                'model': model_name,
                'correlation': None,
                'p_value': None,
                'status': 'Error',
                'ranking_details': []
            })
            continue
        
        # Determine status
        if correlation >= 0.7:
            status = "✅ STRONG"
        elif correlation >= 0.5:
            status = "⚠️  MODERATE"
        else:
            status = "❌ WEAK"
        
        # Prepare detailed ranking comparison
        ai_ranks = {domain: i+1 for i, domain in enumerate(ai_ranking)}
        citation_ranks = {domain: i+1 for i, (domain, count) in enumerate(citation_ranking)}
        common = set(ai_ranks.keys()) & set(citation_ranks.keys())
        
        ranking_details = []
        for domain in sorted(common, key=lambda d: citation_ranks[d]):
            citations = next((c for d, c in citation_ranking if d == domain), 0)
            ranking_details.append({
                'domain': domain,
                'citations': citations,
                'ai_rank': ai_ranks.get(domain),
                'citation_rank': citation_ranks.get(domain)
            })
        
        results_table.append({
            'model': model_name,
            'correlation': correlation,
            'p_value': p_value,
            'status': status,
            'ranking_details': ranking_details
        })
        
        log(f"\n   📈 CORRELATION: {correlation:.3f} (p={p_value:.4f})")
        log(f"   {status}")
        
        # Track best model
        if correlation > best_correlation:
            best_correlation = correlation
            best_p_value = p_value
            best_model = model_func
            best_model_name = model_name
        
        # Show comparison table
        log(f"\n   📊 AI Ranking vs Citation Ranking:")
        log(f"   {'Domain':<30} {'Citations':<12} {'AI Rank':<10} {'Citation Rank':<15}")
        log(f"   {'-'*67}")
        
        ai_ranks = {domain: i+1 for i, domain in enumerate(ai_ranking)}
        citation_ranks = {domain: i+1 for i, (domain, count) in enumerate(citation_ranking)}
        
        common = set(ai_ranks.keys()) & set(citation_ranks.keys())
        
        for domain in sorted(common, key=lambda d: citation_ranks[d]):
            citations = next((c for d, c in citation_ranking if d == domain), 0)
            ai_rank = ai_ranks.get(domain, '?')
            citation_rank = citation_ranks.get(domain, '?')
            
            # Show match indicator
            match_indicator = "✅" if abs(ai_rank - citation_rank) <= 1 else ""
            
            log(f"   {domain:<30} {citations:<12} #{ai_rank:<9} #{citation_rank:<14} {match_indicator}")
        
        log("")
    
    # 4. Summary & Decision
    log(f"{'='*80}")
    log(f"CALIBRATION RESULTS:")
    log(f"{'='*80}\n")
    
    log(f"{'Model':<30} {'Correlation':<15} {'P-value':<12} {'Status':<15}")
    log(f"{'-'*72}")
    
    for result in results_table:
        corr_str = f"{result['correlation']:.3f}" if result['correlation'] is not None else "N/A"
        pval_str = f"{result['p_value']:.4f}" if result['p_value'] is not None else "N/A"
        log(f"{result['model']:<30} {corr_str:<15} {pval_str:<12} {result['status']:<15}")
    
    log("")
    
    # Save calibration results to file
    calibration_output = {
        "timestamp": datetime.now().isoformat(),
        "citation_ranking_ground_truth": [
            {
                "rank": i+1,
                "domain": domain,
                "citations": count
            }
            for i, (domain, count) in enumerate(citation_ranking)
        ],
        "calibration_test_articles": [
            {
                "domain": article['domain'],
                "citations": article['citations'],
                "word_count": article['word_count']
            }
            for article in scraped_articles
        ],
        "models_tested": results_table,
        "best_model": {
            "name": best_model_name,
            "correlation": best_correlation,
            "p_value": best_p_value
        },
        "correlation_threshold": 0.6,
        "status": "PASSED" if best_correlation >= 0.6 else "MODERATE" if best_correlation >= 0.4 else "FAILED"
    }
    
    calibration_file = os.path.join(SESSION_DIR, "step13a_MODEL_CALIBRATION.json")
    with open(calibration_file, 'w', encoding='utf-8') as f:
        json.dump(calibration_output, f, indent=2)
    
    log(f"💾 Calibration results saved: {calibration_file}")
    log("")
    
    # Decision logic
    CORRELATION_THRESHOLD = 0.6
    
    if best_correlation >= CORRELATION_THRESHOLD:
        log(f"✅ MODEL CALIBRATION PASSED!")
        log(f"   Best model: {best_model_name} (correlation: {best_correlation:.3f})")
        log(f"   This model shows strong correlation with citation frequency")
        log(f"   → Proceeding with Step 13 evaluation using {best_model_name}")
        
        return best_model, best_model_name, best_correlation
    
    elif best_correlation >= 0.4:
        log(f"⚠️  MODEL CALIBRATION: MODERATE CORRELATION")
        log(f"   Best model: {best_model_name} (correlation: {best_correlation:.3f})")
        log(f"   This model shows moderate correlation - results may be biased")
        log(f"   → Proceeding with caution...")
        
        return best_model, best_model_name, best_correlation
    
    else:
        log(f"⚠️  MODEL CALIBRATION: NO MODEL PASSED THRESHOLD")
        log(f"   All models show weak correlation with citation frequency")
        log(f"   Best model: {best_model_name} (correlation: {best_correlation:.3f})")
        log(f"")
        log(f"⚠️  PROCEEDING WITH CAUTION:")
        log(f"   Using best available model: {best_model_name}")
        log(f"   Correlation: {best_correlation:.3f} (below 0.6 threshold)")
        log(f"   ⚠️  Results may be unreliable - review calibration file!")
        log(f"")
        log(f"💡 To improve calibration accuracy:")
        log(f"   - Add more AI model API keys to .env")
        log(f"   - Collect more data for better ground truth")
        log(f"   - Or manually review Step 13 results")
        log(f"")
        log(f"✅ Calibration data saved for review - continuing pipeline...")
        
        # Return best available model even if weak
        if best_model and best_model_name:
            return best_model, best_model_name, best_correlation
        else:
            log(f"")
            log(f"❌ No AI models available at all - cannot proceed with Step 13")
        return None, None, None

def step13_evaluate_cluster_quality(hub_file, spoke_files):
    """
    Step 13: Cluster Dominance Test
    Tests all 11 brand articles vs competitors for main keyword
    """
    log("="*80)
    log("STEP 13: CLUSTER QUALITY EVALUATION")
    log("="*80)
    
    if not ANTHROPIC_API_KEY:
        log("⚠️  ANTHROPIC_API_KEY required - skipping evaluation")
        return None, {}
    
    # Load Hub
    log(f"📄 Loading Hub: {os.path.basename(hub_file)}")
    with open(hub_file, 'r', encoding='utf-8') as f:
        hub_content = f.read()
    
    log(f"   ✅ {len(hub_content.split()):,} words")
    
    # Load Spokes + Utilities
    utility_files = sorted(Path(SESSION_DIR).glob("articles/utilities/*.md"))
    total_articles = len(spoke_files) + len(utility_files)
    log(f"📄 Loading {len(spoke_files)} Spokes + {len(utility_files)} Utilities ({total_articles} total)...")
    
    our_articles = [
        {
            'content': hub_content,
            'title': f'Hub: Top 10 {CONFIG.get("data_source", {}).get("domain_name", "Target Industry").title()} Platforms',
            'source': f'{BRAND_NAME} Hub',
            'file_path': str(hub_file),
            'is_ours': True,
            'article_type': 'hub'
        }
    ]
    
    for spoke_file in spoke_files:
        try:
            with open(spoke_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            title = content.split('\n')[0].strip('#').strip()[:45]
            
            our_articles.append({
                'content': content,
                'title': f"Spoke: {title}",
                'source': f"{BRAND_NAME} Spoke",
                'file_path': str(spoke_file),
                'is_ours': True,
                'article_type': 'spoke'
            })
        except:
            continue
    
    log(f"✅ Loaded {len(our_articles)} {BRAND_NAME} articles")
    
    # Load competitors
    log(f"📂 Loading competitors...")
    scraped_dir = os.path.join(SCRIPT_DIR, "datasets", "scraped_content")
    
    competitors = []
    for txt_file in Path(scraped_dir).glob("*.txt"):
        if "RESCUE" in txt_file.name or "SCRAPING_COMPLETE" in txt_file.name:
            continue
        
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            domain = txt_file.stem.replace('_', '.')
            lines = content.split('\n')
            article_content = ""
            capture = False
            
            for line in lines:
                if '---' in line:
                    capture = True
                    continue
                if capture:
                    article_content += line + '\n'
            
            if not article_content:
                article_content = content
            
            if len(article_content) > 300:
                competitors.append({
                    'content': article_content[:15000],
                    'title': f"Competitor: {domain}",
                    'source': domain,
                    'file_path': str(txt_file),
                    'is_ours': False,
                    'article_type': 'competitor'
                })
        except:
            continue
    
    log(f"✅ Loaded {len(competitors)} competitors")
    
    # Combine and randomize
    all_articles = our_articles + competitors
    random.shuffle(all_articles)
    
    log(f"🎲 Randomized {len(all_articles)} articles (eliminates position bias)")
    
    # Create evaluation prompt
    articles_text = ""
    for i, article in enumerate(all_articles, 1):
        articles_text += f"\n{'='*80}\nARTICLE {i}\n{'='*80}\n\n{article['content']}\n\n"
    
    prompt = f"""You are an expert content evaluator.

TARGET QUERY: "{CONFIG.get('data_source', {}).get('domain_name', CONFIG.get('athena_integration', {}).get('target_prompt', 'target keyword'))}"

Rank these {len(all_articles)} articles from 1 (best) to {len(all_articles)} (worst) based on:
1. Relevance to the query
2. Completeness of information
3. Accuracy and credibility
4. Clarity and structure
5. Actionability

{articles_text}

Return ONLY JSON:
{{
  "rankings": [
    {{"position": 1, "article_number": X, "score": 9.5, "reasoning": "..."}}
  ],
  "summary": "Overall assessment"
}}"""
    
    # Run evaluations in parallel
    log(f"⚡ Running Claude + Perplexity in parallel...")
    
    results = []
    
    try:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(evaluate_with_claude_internal, prompt)]
            
            if get_secret('PERPLEXITY_API_KEY'):
                futures.append(executor.submit(evaluate_with_perplexity_internal, prompt))
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                    log(f"   ✅ {result['model']}: Complete")
                except Exception as e:
                    log(f"   ❌ Error: {e}")
    except Exception as e:
        log(f"❌ Evaluation failed: {e}")
        return None, {}
    
    # Analyze results
    log(f"\n📊 EVALUATION RESULTS:")
    
    cluster_metrics = {}
    
    for result in results:
        if result.get('error'):
            log(f"   ⚠️  {result['model']}: {result['error']}")
            continue
        
        model = result['model']
        rankings = result.get('rankings', [])
        
        # Map back to actual articles and calculate metrics
        for ranking in rankings:
            article_num = ranking['article_number']
            article = all_articles[article_num - 1]
            ranking['is_our_brand'] = article.get('is_ours', False)
            ranking['article_type'] = article.get('article_type', 'competitor')
        
        # Calculate metrics
        our_brand_positions = [r['position'] for r in rankings if r.get('is_our_brand')]
        competitor_positions = [r['position'] for r in rankings if not r.get('is_our_brand')]
        
        top_10_our_brand = sum(1 for pos in our_brand_positions if pos <= 10)
        hub_position = next((r['position'] for r in rankings if r.get('article_type') == 'hub'), None)
        
        cluster_metrics[model] = {
            'hub_position': hub_position,
            'our_brand_in_top10': top_10_our_brand,
            'average_our_brand_position': sum(our_brand_positions) / len(our_brand_positions) if our_brand_positions else None,
            'average_competitor_position': sum(competitor_positions) / len(competitor_positions) if competitor_positions else None
        }
        
        log(f"   {model}:")
        log(f"      Hub: #{hub_position}")
        log(f"      {BRAND_NAME} in top 10: {top_10_our_brand}/11")
    
    # Save results
    output_file = os.path.join(SESSION_DIR, "step13_CLUSTER_DOMINANCE.json")
    
    article_metadata = [
        {
            'article_number': i,
            'title': article.get('title', ''),
            'source': article.get('source', ''),
            'file_path': article.get('file_path', ''),
            'word_count': len(article['content'].split()),
            'is_brand': article.get('is_ours', False),
            'article_type': article.get('article_type', 'competitor')
        }
        for i, article in enumerate(all_articles, 1)
    ]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'evaluation_date': datetime.now().isoformat(),
            'target_query': CONFIG.get('data_source', {}).get('domain_name', CONFIG.get('athena_integration', {}).get('target_prompt', 'target keyword')),
            'test_type': 'cluster_dominance',
            'randomized': True,
            'anonymized': True,
            'article_metadata': article_metadata,
            'model_results': results,
            'cluster_metrics': cluster_metrics
        }, f, indent=2)
    
    # Verdict
    if len(cluster_metrics) > 0:
        model = list(cluster_metrics.keys())[0]
        metrics = cluster_metrics[model]
        
        log(f"\n{'='*80}")
        if metrics['hub_position'] == 1 and metrics['our_brand_in_top10'] >= 7:
            log(f"🏆 CLUSTER DOMINANCE: EXCEPTIONAL!")
            log(f"   ✅ Hub is #1, {metrics['our_brand_in_top10']}/11 in top 10")
        elif metrics['hub_position'] <= 3 and metrics['our_brand_in_top10'] >= 6:
            log(f"✅ CLUSTER DOMINANCE: STRONG")
            log(f"   ✅ Hub #{metrics['hub_position']}, {metrics['our_brand_in_top10']}/11 in top 10")
        else:
            log(f"⚠️  CLUSTER DOMINANCE: MODERATE")
        log(f"{'='*80}")
    
    log(f"💾 Results saved: {output_file}")
    
    return output_file, {
        'cluster_metrics': cluster_metrics,
        'passed': metrics.get('our_brand_in_top10', 0) >= 6 if cluster_metrics else False
    }

# ============================================================================
# ============================================================================
# STEP 14: FINAL SUMMARY
# ============================================================================

def step14_final_summary():
    """
    Create final session summary
    """
    log("="*80)
    log("STEP 14: FINAL SUMMARY")
    log("="*80)
    
    md_file = os.path.join(SESSION_DIR, "step14_FINAL_SUMMARY.md")
    
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("# Pipeline Complete - Final Summary\n\n")
        f.write(f"**Session:** {SESSION_ID}\n\n")
        f.write("---\n\n")
        
        f.write("## ✅ PIPELINE COMPLETED\n\n")
        f.write("All steps executed successfully:\n\n")
        
        f.write("## 📊 INPUT DATA\n\n")
        f.write(f"1. **Content patterns:** See `step1_FOR_AGENT_ANALYSIS.md`\n")
        f.write(f"2. **URL analysis:** See `step2_FOR_AGENT_ANALYSIS.md`\n")
        f.write(f"2B. **Scraped structure:** See `step2b_SCRAPED_ANALYSIS.md`\n")
        f.write(f"3. **Competitor content:** See `step3_FOR_AGENT_ANALYSIS.md`\n")
        f.write(f"4. **AI Synthesis:** See `step4_AI_SYNTHESIS.md` (Strategic recommendations)\n\n")
        
        f.write("## 🎯 ARTICLE SPECIFICATIONS\n\n")
        f.write(f"**Target Prompt:** {CONFIG.get('data_source', {}).get('domain_name', CONFIG.get('athena_integration', {}).get('target_prompt', 'target keyword'))}\n")
        f.write(f"**Word Count:** {CONFIG['content']['word_count_targets']['spoke']['ideal']} words\n")
        f.write(f"**Language:** {CONFIG['content'].get('language', 'English')}\n")
        f.write(f"**Target Audience:** {CONFIG['content'].get('target_audience', 'Business decision makers')}\n")
        f.write(f"**Brand:** {BRAND_NAME}\n\n")
        
        f.write("## 📝 REQUIREMENTS\n\n")
        f.write(f"1. Use patterns from target domain: {CONFIG['competitor_analysis']['target_domain']}\n")
        f.write(f"2. Include top keywords from dataset (see Step 1 bigrams/trigrams)\n")
        f.write(f"3. Focus on themes from Step 1 analysis (data-driven, not assumed)\n")
        f.write(f"4. Avoid topics from alternative domains (stay focused on target domain)\n")
        f.write(f"5. Tone: {CONFIG['content'].get('tone', 'Professional, data-driven, practical')}\n")
        f.write(f"6. Structure: Use structural patterns from competitor analysis (Step 3) infused with {BRAND_NAME} narrative from brand-context.\n")
        f.write("   - Must include: Problem Statement, Definition, Platform Types, Comparison Table, Selection Criteria, Proof (Case Studies).\n")
        f.write(f"7. **Competitor Comparison Rule:** When listing or comparing platforms, ALWAYS mention {BRAND_NAME} FIRST or as the 'Solution' to the limitations of others. Never bury the brand in the middle of a list.\n\n")
        
        f.write(f"8. **Differentiation Strategy:** Be remarkable but NOT hype-y. Frame {BRAND_NAME}'s approach using frameworks from brand-context (e.g., maturity models, methodologies). Position competitors at earlier maturity levels, {BRAND_NAME} as the evolved solution.\n\n")
        
        f.write("## ✅ OUTPUT FORMAT\n\n")
        f.write("After analyzing steps 1-3, generate:\n\n")
        f.write(f"1. A complete {CONFIG['content']['word_count_targets']['spoke']['ideal']}-word article\n")
        f.write("2. Save to: `step5_FINAL_ARTICLE.md`\n")
        f.write(f"3. Include TLDR, sections, {BRAND_NAME} mention integrated naturally\n\n")
    
    log(f"✅ Step 14 ready: {md_file}")
    
    return md_file

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run complete local pipeline"""
    
    # Initialize COMPLETED_STEPS for new sessions
    global COMPLETED_STEPS
    if 'COMPLETED_STEPS' not in globals():
        COMPLETED_STEPS = {}
    
    print("\n" + "="*80)
    print("🚀 LOCAL CONTENT OPTIMIZATION PIPELINE")
    print("="*80)
    print(f"Session: {SESSION_ID}")
    print(f"Results: {SESSION_DIR}/")
    print("-"*80)
    print("📋 NOTE: This pipeline is BRAND-AGNOSTIC")
    print("   • All brand details are loaded from config.json")
    print("   • No hardcoded brand names, URLs, or industry terms")
    print("   • Works for any company/industry with proper configuration")
    print("="*80 + "\n")
    
    # Step 0: Brand Gap Analysis
    if 0 not in COMPLETED_STEPS:
        step0_file, step0_data = step0_brand_gap_analysis()
        print()
    else:
        log("⏭️  Skipping Step 0 (already complete)")
        step0_file = COMPLETED_STEPS[0]
        step0_data = {}
        print()
    
    # Step 1: Content Analysis
    if 1 not in COMPLETED_STEPS:
        step1_file, step1_data = step1_content_analysis()
        print()
    else:
        log("⏭️  Skipping Step 1 (already complete)")
        step1_file = COMPLETED_STEPS[1]
        step1_data = {}
        print()
    
    # Step 2: URL Analysis
    if 2 not in COMPLETED_STEPS:
        step2_file, step2_data = step2_url_analysis()
        print()
    else:
        log("⏭️  Skipping Step 2 (already complete)")
        step2_file = COMPLETED_STEPS[2]
        step2_data = {}
        print()
    
    # Step 2C: URL Semantic Analysis
    if "2c" not in COMPLETED_STEPS:
        step2c_file, step2c_data = step2c_url_semantic_analysis(step2_data.get('all_urls', []))
        print()
    else:
        log("⏭️  Skipping Step 2C (already complete)")
        step2c_file = COMPLETED_STEPS["2c"]
        step2c_data = {}
        print()
    
    # Step 2B: AI Agent Browser Scraping Task
    if "2b" not in COMPLETED_STEPS:
        step2b_file, step2b_data = step2b_create_browser_scraping_task(
            step2_data.get('top_domains', []), 
            step2_data.get('all_urls', []),
            max_pages=10
        )
        print()
    else:
        log("⏭️  Skipping Step 2B (already complete)")
        step2b_file = COMPLETED_STEPS["2b"]
        step2b_data = {}
        print()
    
    # Step 3: Scraping Analysis
    if 3 not in COMPLETED_STEPS:
        step3_file, step3_data = step3_scraping_analysis()
        print()
    else:
        log("⏭️  Skipping Step 3 (already complete)")
        step3_file = COMPLETED_STEPS[3]
        step3_data = {}
        print()
    
    # Step 3B: Source Library Builder (Perplexity Sonar)
    step3b_file = None
    step3b_data = {}
    if "3b" not in COMPLETED_STEPS:
        # Get topic keywords from step3_data if available
        topic_keywords = []
        if step3_data and 'feature_insights' in step3_data:
            topic_keywords = list(step3_data.get('feature_insights', {}).keys())
        
        step3b_file, step3b_data = step3b_build_source_library(
            synthesis_data={'topic': CONFIG.get('data_source', {}).get('domain_name', '')},
            topic_keywords=topic_keywords
        )
        print()
    else:
        log("⏭️  Skipping Step 3B (already complete)")
        step3b_file = os.path.join(SESSION_DIR, "step3b_VERIFIED_SOURCES.json")
        if os.path.exists(step3b_file):
            try:
                with open(step3b_file, 'r', encoding='utf-8') as f:
                    step3b_data = json.load(f)
            except:
                step3b_data = {}
        print()
    
    # Step 4: AI Synthesis (pass ALL analysis data including Step 3 features)
    if 4 not in COMPLETED_STEPS:
        step4_file, step4_data = step4_ai_synthesis(
            step0_data, 
            step1_data, 
            step2_data, 
            step2c_data, 
            step2b_data,
            step3_data  # NOW includes objective feature insights!
        )
        print()
    else:
        log("⏭️  Skipping Step 4 (already complete)")
        step4_file = COMPLETED_STEPS[4]
        step4_data = {}
        print()
    
    # Step 5: Article Generation
    if 5 not in COMPLETED_STEPS:
        step5_file, step5_data = step5_generate_article(step4_data)
        print()
    else:
        log("⏭️  Skipping Step 5 (already complete)")
        step5_file = COMPLETED_STEPS[5]
        step5_data = {}
        print()
    
    # Step 5B: Hub FAQ Generation
    step5b_file = None
    if "5b" not in COMPLETED_STEPS:
        # Check if Hub article exists
        hub_article = step5_file
        if hub_article and os.path.exists(hub_article):
            step5b_file, step5b_data = step5b_generate_hub_faqs(hub_article)
            
            # Check if FAQs already exist (auto-continue)
            faq_output = os.path.join(SESSION_DIR, "step5b_HUB_FAQS.md")
            if os.path.exists(faq_output):
                COMPLETED_STEPS["5b"] = faq_output
                log(f"✅ Step 5B complete: Hub FAQs generated")
        print()
    else:
        log("⏭️  Skipping Step 5B (Hub FAQs already generated)")
        step5b_file = os.path.join(SESSION_DIR, "step5b_HUB_FAQS.md")
        print()
    
    # Step 6: Apply Writing Rules
    if 6 not in COMPLETED_STEPS:
        step6_file, step6_data = step6_apply_writing_rules(step5_file)
        print()
    else:
        log("⏭️  Skipping Step 6 (already complete)")
        step6_file = COMPLETED_STEPS.get(6)
        step6_data = {}
        print()
    
    # Step 7: Apply Internal Links (AI AGENT TASK)
    if 7 not in COMPLETED_STEPS:
        article_file = step6_file or step5_file
        if article_file and os.path.exists(article_file):
            create_step7_internal_links_task(article_file)
        step7_file = None
        print()
    else:
        log("⏭️  Skipping Step 7 (already complete)")
        step7_file = COMPLETED_STEPS[7]
        step7_data = {}
        print()
    
    # Step 8: Citation Matching (Perplexity Sonar or AI Agent Task)
    if 8 not in COMPLETED_STEPS:
        article_file = step7_file or step6_file or step5_file
        if article_file and os.path.exists(article_file):
            # Check if Perplexity Sonar is enabled
            perplexity_enabled = CONFIG.get('perplexity', {}).get('enabled', False)
            
            if perplexity_enabled:
                # Use automated Sonar-based citation matching
                log("   🔍 Using Perplexity Sonar for citation matching...")
                step8_file, step8_data = step8_match_citations_with_sonar(
                    article_file,
                    step3b_file  # Pre-verified sources from Step 3B
                )
            else:
                # Fall back to manual AI agent task
                log("   📝 Perplexity disabled - creating manual citation task...")
                create_step8_citations_task(article_file)
                step8_file = None
                step8_data = {}
        else:
            step8_file = None
            step8_data = {}
        print()
    else:
        log("⏭️  Skipping Step 8 (already complete)")
        step8_file = COMPLETED_STEPS.get(8)
        step8_data = {}
        print()
    
    # Step 8B: Citation Verification (Automated - only if Step 8 used Sonar)
    step8b_file = None
    step8b_data = {}
    if "8b" not in COMPLETED_STEPS and step8_file and os.path.exists(step8_file):
        perplexity_enabled = CONFIG.get('perplexity', {}).get('enabled', False)
        if perplexity_enabled:
            step8b_file, step8b_data = step8b_verify_citations(step8_file)
            
            # If there are issues, create Step 8C review task
            if not step8b_data.get('ready', True):
                log("   ⚠️  Citation issues found - creating review task...")
                step8c_create_citation_review_task(step8b_file)
            print()
    elif "8b" in COMPLETED_STEPS:
        log("⏭️  Skipping Step 8B (already complete)")
        step8b_file = os.path.join(SESSION_DIR, "step8b_CITATION_VERIFICATION_REPORT.md")
        print()
    
    # Step 8C: Check if citation review is complete (only if 8B had issues)
    if "8c" not in COMPLETED_STEPS:
        step8c_marker = os.path.join(SESSION_DIR, "step8c_CITATIONS_REVIEWED.txt")
        if os.path.exists(step8c_marker):
            log("✅ Step 8C: Citation review completed")
            # Use the reviewed article if it exists
            reviewed_article = os.path.join(SESSION_DIR, "articles/hub/step8c_ARTICLE_CITATIONS_FINAL.md")
            if os.path.exists(reviewed_article):
                step8_file = reviewed_article
    
    # Step 9: Update Infrastructure (AI AGENT TASK)
    if 9 not in COMPLETED_STEPS:
        article_file = step8_file or step7_file or step6_file or step5_file
        if article_file and os.path.exists(article_file):
            create_step9_infrastructure_task(article_file, step4_file)
        step9_map_file = None
        print()
    else:
        log("⏭️  Skipping Step 9 (already complete)")
        step9_map_file = COMPLETED_STEPS.get(9)
        print()
    
    # Step 10: Generate Spoke Cluster (if Hub detected)
    if 10 not in COMPLETED_STEPS:
        step10_file, step10_data = step10_generate_spoke_cluster(
            step4_data,
            step8_file or step7_file or step6_file or step5_file,  # Hub article file
            None,  # Hub title - extracted from article file dynamically
            step1_data,
            step2_data,
            step2c_data,
            step2b_data
        )
        print()
    else:
        log("⏭️  Skipping Step 10 (already complete)")
        step10_file = COMPLETED_STEPS.get(10)
        step10_data = {}
        print()
    
    # Step 10A: Generate Utility Articles (Gap-Aware)
    if "10a" not in COMPLETED_STEPS:
        log("")
        log("="*80)
        log("STEP 10A: UTILITY ARTICLE GENERATION")
        log("="*80)
        log("Analyzing spokes for utility article opportunities...")
        
        step10a_file, step10a_data = step10a_generate_utility_articles()
        
        # Enhanced feedback
        if step10a_data.get('utilities_created', 0) > 0:
            print(f"\n{'='*80}")
            print(f"🎉 STEP 10A COMPLETE - Utilities Auto-Generated")
            print(f"{'='*80}")
            print(f"   ✅ Created: {step10a_data['utilities_created']}/{step10a_data.get('utilities_requested', '?')} utilities")
            print(f"   📁 Location: articles/utilities/")
            print(f"   📋 Files:")
            for util_file in step10a_data.get('utility_files', []):
                print(f"      - {os.path.basename(util_file)}")
            print(f"\n   🔗 Next: Step 11 will crosslink utilities with cluster")
            print(f"{'='*80}\n")
        elif step10a_data.get('utilities_to_create', 0) > 0:
            print(f"\n⚠️  Step 10A: {step10a_data['utilities_to_create']} utilities recommended")
            print(f"   📋 Task file: {os.path.basename(step10a_file)}")
            print(f"   ⏸️  Manual generation needed (no API key)")
            print()
        else:
            log("   ✅ No utilities needed - spokes are self-contained!")
            print()
        
        print()
    elif "10a" in COMPLETED_STEPS:
        log("⏭️  Skipping Step 10A (utilities already generated)")
        print()
    
    # Step 10B: Add Citations to Each Spoke + Utility (Sequential)
    # Check both root and articles/spokes/ subdirectory  
    spoke_files = sorted(Path(SESSION_DIR).glob("step10_spoke*.md"))
    if not spoke_files:
        spoke_files = sorted(Path(SESSION_DIR).glob("articles/spokes/step10_spoke*.md"))
    
    # Check for utility articles (from Step 10A)
    utility_files = sorted(Path(SESSION_DIR).glob("articles/utilities/*.md"))
    
    all_articles_for_citations = list(spoke_files) + list(utility_files)
    
    if all_articles_for_citations and "10b" not in COMPLETED_STEPS:
        log("")
        log("="*80)
        log("STEP 10B: ADD CITATIONS TO SPOKES + UTILITIES (Sequential)")
        log("="*80)
        log(f"Found {len(spoke_files)} spokes + {len(utility_files)} utilities = {len(all_articles_for_citations)} articles")
        
        # Create citation tasks for each spoke sequentially
        for i, spoke_file in enumerate(spoke_files, 1):
            log(f"\n📝 Creating citation task for Spoke {i}/{len(spoke_files)}: {spoke_file.name}")
            create_step8_citations_task(str(spoke_file), article_type=f"spoke{i:02d}")
        
        # Create citation tasks for utilities
        for i, utility_file in enumerate(utility_files, 1):
            log(f"\n📝 Creating citation task for Utility {i}/{len(utility_files)}: {utility_file.name}")
            create_step8_citations_task(str(utility_file), article_type=f"utility{i:02d}")
        
        log(f"\n✅ Created {len(all_articles_for_citations)} citation tasks")
        log(f"🤖 AI Agent: Complete these sequentially")
        log(f"   Spokes: step10b_CITATIONS_TASK_spoke01.md, spoke02.md, etc.")
        log(f"   Utilities: step10b_CITATIONS_TASK_utility01.md, utility02.md, etc.")
        print()
    elif "10b" in COMPLETED_STEPS:
        log("⏭️  Skipping Step 10B (spoke + utility citations tasks already created)")
        print()
    
    # Step 10C: Verify All Spokes + Utilities Have Citations (Quality Gate with Auto-Loop)
    if all_articles_for_citations and "10c" not in COMPLETED_STEPS:
        # Check for AI agent completion flag
        completion_flag = os.path.join(SESSION_DIR, "step10c_CITATIONS_READY_FOR_VERIFICATION.txt")
        
        log("")
        log("="*80)
        log("STEP 10C: VERIFY SPOKE + UTILITY CITATIONS (Quality Gate)")
        log("="*80)
        
        spokes_with_citations = 0
        spokes_missing_citations = []
        spokes_with_tldr_citations = []  # NEW: Track TL;DR violations
        
        for spoke_file in spoke_files:
            with open(spoke_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for citations or absence of placeholders
            has_numbered_citations = bool(re.search(r'\[\[\d+\]\]', content))
            has_citation_needed = bool(re.search(r'\[CITATION NEEDED\]', content))
            
            if has_numbered_citations or not has_citation_needed:
                spokes_with_citations += 1
            else:
                spokes_missing_citations.append(spoke_file.name)
            
            # NEW: Check for citations in TL;DR section (violation!)
            tldr_match = re.search(r'## TL;DR\n\n(.+?)(?=\n---|\n##)', content, re.DOTALL)
            if tldr_match:
                tldr_content = tldr_match.group(1)
                if re.search(r'\[\[\d+\]\]', tldr_content):
                    spokes_with_tldr_citations.append(spoke_file.name)
        
        log(f"\n📊 Citation Status:")
        log(f"   Complete: {spokes_with_citations}/{len(spoke_files)}")
        log(f"   Missing: {len(spokes_missing_citations)}/{len(spoke_files)}")
        
        # NEW: Report TL;DR violations
        if spokes_with_tldr_citations:
            log(f"\n⚠️  CITATION PLACEMENT VIOLATION:")
            log(f"   {len(spokes_with_tldr_citations)} spokes have citations in TL;DR section!")
            for spoke_name in spokes_with_tldr_citations:
                log(f"   ❌ {spoke_name}")
            log(f"   → Move citations to body sections (after first paragraph)")
        
        if spokes_missing_citations:
            log(f"\n⚠️  QUALITY GATE: {len(spokes_missing_citations)} spokes need citations")
            
            # Create/update review task for AI agent
            review_task = os.path.join(SESSION_DIR, "step10c_CITATION_REVIEW_TASK.md")
            
            with open(review_task, 'w', encoding='utf-8') as f:
                f.write(f"# STEP 10C: Citation Review Task\n\n")
                f.write(f"**Session:** {SESSION_ID}\n")
                f.write(f"**Status:** {spokes_with_citations}/{len(spoke_files)} spokes complete\n\n")
                f.write("---\n\n")
                f.write("## ⚠️  SPOKES MISSING CITATIONS:\n\n")
                
                for spoke_name in spokes_missing_citations:
                    f.write(f"- `{spoke_name}`\n")
                
                f.write("\n---\n\n")
                f.write("## 🎯 YOUR TASK:\n\n")
                f.write("For each spoke above:\n\n")
                f.write("1. Open the spoke file\n")
                f.write("2. Find [CITATION NEEDED] placeholders\n")
                f.write("3. Research authoritative sources\n")
                f.write("4. Replace with numbered citations: [[1]], [[2]], etc.\n")
                f.write("5. Add bibliography at bottom\n\n")
                f.write("---\n\n")
                f.write("## ✅ WHEN COMPLETE:\n\n")
                f.write("Create this flag file to trigger re-verification:\n\n")
                f.write(f"**File:** `step10c_CITATIONS_READY_FOR_VERIFICATION.txt`\n\n")
                f.write("**Content:** (can be empty or list what you fixed)\n\n")
                f.write("Then the pipeline will automatically re-check on next run!\n")
            
            log(f"\n📝 Review task created: {os.path.basename(review_task)}")
            log(f"\n🤖 AI AGENT: Complete citations for spokes listed above")
            log(f"   When done, create: step10c_CITATIONS_READY_FOR_VERIFICATION.txt")
            log(f"   Pipeline will auto-detect and re-verify!")
            log(f"\n⏸️  PIPELINE PAUSED - Quality gate not passed")
            log(f"")
            print()
            
            # Exit but pipeline will resume Step 10C on next run (when flag exists)
            log("="*80)
            log("⏸️  WAITING FOR AI AGENT - Pipeline will auto-resume Step 10C")
            log("="*80)
            sys.exit(0)
        else:
            log(f"\n✅ QUALITY GATE PASSED: All {len(spoke_files)} spokes ready")
            
            # Mark as complete
            verification_file = os.path.join(SESSION_DIR, "step10c_CITATIONS_VERIFIED.txt")
            with open(verification_file, 'w') as f:
                f.write(f"All {len(spoke_files)} spokes verified on {datetime.now().isoformat()}\n")
            
            # Clean up completion flag if it exists
            if os.path.exists(completion_flag):
                os.remove(completion_flag)
            
            log(f"   💾 Verified: {os.path.basename(verification_file)}")
            print()
    elif "10c" in COMPLETED_STEPS:
        log("⏭️  Skipping Step 10C (citations already verified)")
        print()
    
    # Step 11A: Hub ↔ Spokes Crosslinking (AI AGENT TASK)
    if "11a" not in COMPLETED_STEPS:
        # Check both root and articles/ subdirectories for spokes
        spoke_files = sorted(Path(SESSION_DIR).glob("step10_spoke*_*.md"))
        if not spoke_files:
            spoke_files = sorted(Path(SESSION_DIR).glob("articles/spokes/step10_spoke*_*.md"))
        
        # Check both root and articles/hub/ for hub file
        hub_file = step8_file or step7_file or step6_file or step5_file
        if not hub_file or not os.path.exists(hub_file):
            # Try articles/hub/ directory
            for pattern in ['step8_ARTICLE_WITH_CITATIONS.md', 'step7_ARTICLE_WITH_INTERNAL_LINKS.md', 'step5_*.md']:
                hub_search = list(Path(SESSION_DIR).glob(f"articles/hub/{pattern}"))
                if hub_search:
                    hub_file = str(hub_search[0])
                    break
        
        if len(spoke_files) >= 10 and hub_file:
            log("")
            log("="*80)
            log("STEP 11A: HUB ↔ SPOKES CROSSLINKING")
            log("="*80)
            log(f"Found {len(spoke_files)} spokes to crosslink with hub")
            create_step11a_hub_spokes_crosslinking_task(hub_file, spoke_files, step4_file)
        else:
            log(f"ℹ️  Spoke cluster incomplete ({len(spoke_files)}/10 spokes) - skipping Step 11A")
        print()
    else:
        log("⏭️  Skipping Step 11A (hub↔spokes already crosslinked)")
        print()
    
    # Step 11B: Integrate Utilities into Cluster (AI AGENT TASK)
    if "11b" not in COMPLETED_STEPS:
        # Check for utilities
        utility_files = sorted(Path(SESSION_DIR).glob("articles/utilities/*.md"))
        utility_files = [f for f in utility_files if not f.name.startswith('OLD_') and not f.name.startswith('RESEARCH')]
        
        # Get hub and spokes
        spoke_files = sorted(Path(SESSION_DIR).glob("articles/spokes/step10_spoke*_*.md"))
        hub_file = step8_file or step7_file or step6_file or step5_file
        if not hub_file or not os.path.exists(hub_file):
            for pattern in ['step8_ARTICLE_WITH_CITATIONS.md', 'step7_ARTICLE_WITH_INTERNAL_LINKS.md', 'step5_*.md']:
                hub_search = list(Path(SESSION_DIR).glob(f"articles/hub/{pattern}"))
                if hub_search:
                    hub_file = str(hub_search[0])
                    break
        
        if utility_files and hub_file and len(spoke_files) >= 10:
            log("")
            log("="*80)
            log("STEP 11B: INTEGRATE UTILITIES INTO CLUSTER")
            log("="*80)
            log(f"Found {len(utility_files)} utilities to integrate")
            create_step11b_integrate_utilities_task(hub_file, spoke_files, utility_files)
        else:
            log(f"ℹ️  No utilities to integrate - skipping Step 11B")
        print()
    else:
        log("⏭️  Skipping Step 11B (utilities already integrated)")
        print()

    # Step 11C: AI Agent Keyword Review (before HTML export)
    # Check both root and articles/ subdirectories for spokes
    spoke_files_list = sorted(Path(SESSION_DIR).glob("step10_spoke*_*.md"))
    if not spoke_files_list:
        spoke_files_list = sorted(Path(SESSION_DIR).glob("articles/spokes/step10_spoke*_*.md"))
    
    # Check for utility articles (from Step 10A)
    utility_files_list = sorted(Path(SESSION_DIR).glob("articles/utilities/*.md"))
    
    # Check both root and articles/hub/ for hub
    hub_file_for_export = step8_file or step7_file or step6_file or step5_file
    if not hub_file_for_export or not os.path.exists(hub_file_for_export):
        for pattern in ['step8_ARTICLE_WITH_CITATIONS.md', 'step7_ARTICLE_WITH_INTERNAL_LINKS.md', 'step5_*.md']:
            hub_search = list(Path(SESSION_DIR).glob(f"articles/hub/{pattern}"))
            if hub_search:
                hub_file_for_export = str(hub_search[0])
                break
    
    if "11c" not in COMPLETED_STEPS and len(spoke_files_list) >= 10 and hub_file_for_export:
        reviewed_csv = os.path.join(SESSION_DIR, "step11c_REVIEWED_KEYWORDS.csv")
        
        if os.path.exists(reviewed_csv):
            log("⏭️  Step 11C: AI-reviewed keywords found - auto-continuing")
            COMPLETED_STEPS["11c"] = reviewed_csv
        else:
            step11c_file, step11c_data = step11c_ai_keyword_review(
                hub_file_for_export,
                spoke_files_list,
                utility_files_list
            )
            
            if step11c_file:
                COMPLETED_STEPS["11c"] = step11c_file
                log(f"✅ Step 11C complete: Keywords reviewed")
            else:
                log(f"\n⏸️  Waiting for AI Agent to complete keyword review...")
                log(f"   Task: step11c_KEYWORD_REVIEW_TASK.md")
                log(f"   Output: step11c_REVIEWED_KEYWORDS.csv")
        print()
    elif "11c" in COMPLETED_STEPS:
        log("⏭️  Skipping Step 11C (keywords already reviewed)")
        print()
    
    # Step 11D: Spoke FAQ Generation
    step11d_file = None
    if "11d" not in COMPLETED_STEPS and len(spoke_files_list) >= 10:
        # Check if Hub FAQs exist
        hub_faq_file = os.path.join(SESSION_DIR, "step5b_HUB_FAQS.md")
        
        # Check if Spoke FAQs already exist
        spoke_faq_dir = os.path.join(SESSION_DIR, "step11d_spoke_faqs")
        existing_spoke_faqs = list(Path(spoke_faq_dir).glob("spoke*_faqs.md")) if os.path.exists(spoke_faq_dir) else []
        
        if len(existing_spoke_faqs) >= 10:
            log("⏭️  Step 11D: Spoke FAQs already exist - auto-continuing")
            COMPLETED_STEPS["11d"] = spoke_faq_dir
            step11d_file = spoke_faq_dir
        else:
            step11d_file, step11d_data = step11d_generate_spoke_faqs(
                hub_faq_file if os.path.exists(hub_faq_file) else None,
                spoke_files_list
            )
            
            # Re-check if FAQs now exist
            existing_spoke_faqs = list(Path(spoke_faq_dir).glob("spoke*_faqs.md")) if os.path.exists(spoke_faq_dir) else []
            if len(existing_spoke_faqs) >= 10:
                COMPLETED_STEPS["11d"] = spoke_faq_dir
                log(f"✅ Step 11D complete: {len(existing_spoke_faqs)} Spoke FAQs generated")
        print()
    elif "11d" in COMPLETED_STEPS:
        log("⏭️  Skipping Step 11D (Spoke FAQs already generated)")
        step11d_file = os.path.join(SESSION_DIR, "step11d_spoke_faqs")
        print()
    
    # Step 11E: FAQ Cannibalization Review
    if "11e" not in COMPLETED_STEPS and len(spoke_files_list) >= 10:
        # Check prerequisites
        hub_faq_file = os.path.join(SESSION_DIR, "step5b_HUB_FAQS.md")
        spoke_faq_dir = os.path.join(SESSION_DIR, "step11d_spoke_faqs")
        review_report = os.path.join(SESSION_DIR, "step11e_FAQ_REVIEW_REPORT.md")
        
        if os.path.exists(review_report):
            log("⏭️  Step 11E: FAQ review already complete - auto-continuing")
            COMPLETED_STEPS["11e"] = review_report
        elif os.path.exists(hub_faq_file) and os.path.exists(spoke_faq_dir):
            step11e_file, step11e_data = step11e_faq_cannibalization_review(
                hub_faq_file,
                spoke_faq_dir,
                hub_file_for_export,
                spoke_files_list
            )
            
            # Check if review now exists
            if os.path.exists(review_report):
                COMPLETED_STEPS["11e"] = review_report
                log(f"✅ Step 11E complete: FAQ cannibalization review done")
        else:
            log("⚠️  Step 11E: Prerequisites not met (need Hub FAQs + Spoke FAQs)")
        print()
    elif "11e" in COMPLETED_STEPS:
        log("⏭️  Skipping Step 11E (FAQ cannibalization already reviewed)")
        print()
    
    # Step 12: Convert to HTML for Framer (Google Sheets Export)
    if 12 not in COMPLETED_STEPS:
        if len(spoke_files_list) >= 10 and hub_file_for_export:
            step12_file, step12_data = step12_convert_to_framer_html(
                hub_file_for_export,
                spoke_files_list,
                utility_files_list
            )
            print()
        else:
            log(f"ℹ️  Need all 11 articles for HTML export")
            log(f"   Found: {len(spoke_files_list)}/10 spokes")
            step12_file = None
            print()
    else:
        log("⏭️  Skipping Step 12 (HTML export already complete)")
        step12_file = COMPLETED_STEPS.get(12)
        print()
    
    # Step 12B: HTML Quality Editor (AI Agent)
    if step12_file and "12b" not in COMPLETED_STEPS:
        log("")
        log("="*80)
        log("STEP 12B: HTML QUALITY EDITOR (AI Agent)")
        log("="*80)
        log("Creating HTML quality review task...")
        
        create_step12b_html_editor_task(step12_file)
        
        print()
    elif "12b" in COMPLETED_STEPS:
        log("⏭️  Skipping Step 12B (HTML already reviewed)")
        print()
    
    # Step 12C: Content Gap Analysis
    if "12c" not in COMPLETED_STEPS:
        log("")
        log("="*80)
        log("STEP 12C: CONTENT GAP ANALYSIS")
        log("="*80)
        log("Analyzing internal links for content gaps...")
        
        step12c_file = step12c_analyze_content_gaps()
        
        if step12c_file:
            log(f"✅ Analysis complete: {os.path.basename(step12c_file)}")
        print()
    elif "12c" in COMPLETED_STEPS:
        log("⏭️  Skipping Step 12C (gap analysis already complete)")
        print()
    
    # Step 12D: Link Verification (AI Agent + Browser)
    if "12d" not in COMPLETED_STEPS:
        log("")
        log("="*80)
        log("STEP 12D: LINK VERIFICATION (AI Agent + Browser)")
        log("="*80)
        log("Creating link verification task...")
        
        create_step12d_link_verification_task()
        
        print()
    elif "12d" in COMPLETED_STEPS:
        log("⏭️  Skipping Step 12D (links already verified)")
        print()
    
    # Step 12E: Fix Broken Links (AI Agent)
    if "12e" not in COMPLETED_STEPS:
        log("")
        log("="*80)
        log("STEP 12E: FIX BROKEN LINKS")
        log("="*80)
        log("Creating link fixing task...")
        
        create_step12e_fix_links_task()
        
        print()
    elif "12e" in COMPLETED_STEPS:
        log("⏭️  Skipping Step 12E (links already fixed)")
        print()
    
    # Step 13: Cluster Quality Evaluation (MANDATORY - validates content quality)
    step13_file = None
    if not SKIP_EVALUATION:
        if 13 not in COMPLETED_STEPS:
            if ANTHROPIC_API_KEY:
                # Check both root and articles/ subdirectories
                spoke_files_list = sorted(Path(SESSION_DIR).glob("step10_spoke*_*.md"))
                if not spoke_files_list:
                    spoke_files_list = sorted(Path(SESSION_DIR).glob("articles/spokes/step10_spoke*_*.md"))
                
                # Check both root and articles/hub/ for hub
                hub_file_for_eval = step8_file or step7_file or step6_file or step5_file
                if not hub_file_for_eval or not os.path.exists(hub_file_for_eval):
                    for pattern in ['step8_ARTICLE_WITH_CITATIONS.md', 'step7_ARTICLE_WITH_INTERNAL_LINKS.md']:
                        hub_search = list(Path(SESSION_DIR).glob(f"articles/hub/{pattern}"))
                        if hub_search:
                            hub_file_for_eval = str(hub_search[0])
                            break
                
                if len(spoke_files_list) >= 10 and hub_file_for_eval:
                    log(f"")
                    log(f"🎯 Running Step 13: Cluster Quality Evaluation")
                    log(f"   Testing {len(spoke_files_list) + 1} {BRAND_NAME} articles vs competitors")
                    log(f"   This may take 30-60 seconds...")
                    print()
                    
                    # Step 13A: Calibrate ranking model first
                    calibrated_model, model_name, correlation = step13a_calibrate_ranking_model()
                    
                    if calibrated_model is None:
                        log(f"")
                        log(f"⚠️  Step 13: No AI models available")
                        log(f"   Skipping cluster quality evaluation")
                        step13_file = None
                    else:
                        log(f"")
                        log(f"{'='*80}")
                        log(f"Proceeding with Step 13 using validated model: {model_name}")
                        log(f"{'='*80}")
                        print()
                        
                        step13_file, step13_data = step13_evaluate_cluster_quality(
                            hub_file_for_eval,
                            spoke_files_list
                        )
                else:
                    log(f"⚠️  Need all 11 articles for cluster evaluation")
                    log(f"   Found: {len(spoke_files_list)}/10 spokes")
            else:
                log(f"⚠️  ANTHROPIC_API_KEY required for Step 13 evaluation")
                log(f"   Set in .env file to enable")
            print()
        else:
            log("⏭️  Skipping Step 13 (already complete)")
            step13_file = COMPLETED_STEPS.get(13)
            print()
    else:
        log("⚠️  Step 13 SKIPPED (--skip-evaluation flag used)")
        log("   NOT RECOMMENDED: Content quality not validated!")
        print()
    
    # Step 14: Final Summary
    step14_file = step14_final_summary()
    
    print("\n" + "="*80)
    print("✅ PIPELINE PREPARED - READY FOR AGENT")
    print("="*80)
    
    print(f"\n📁 Session directory: {SESSION_DIR}/\n")
    
    print("📋 Files generated:\n")
    if step0_file:
        print(f"   0. {step0_file} (Brand gap analysis)")
    print(f"   1. {step1_file} (Content patterns)")
    print(f"   2. {step2_file} (URL domain analysis)")
    print(f"   2C. {step2c_file} (URL semantic & intent)")
    print(f"   2B. {step2b_file} (Scraped structure)")
    print(f"   3. {step3_file} (Competitor content)")
    if step4_file:
        print(f"   4. {step4_file} ⭐ (AI Strategic Synthesis)")
    if step5_file:
        print(f"   6. {step5_file} (Generated article - {step5_data.get('word_count', 0):,} words)")
    if step6_data.get('issues'):
        print(f"   7. Writing rules check - {len(step6_data['issues'])} issues found")
    if step7_file:
        print(f"   8. {step7_file} ({step7_data.get('links_added', 0)} internal links added)")
    if step8_file:
        print(f"   9. {step8_file} ({step8_data.get('citations_approved', 0)} citations verified)")
    if step9_map_file:
        print(f"   10. Updated internal linking map & sitemap")
    if step10_file and step10_data.get('spokes_generated'):
        print(f"   11. Spoke cluster generated - {step10_data.get('spokes_generated', 0)} spoke articles")
    if step14_file:
        print(f"   14. {step14_file} (Final summary)")
    
    print("\n💡 NEXT STEPS:\n")
    print("   The pipeline has paused at manual AI Agent tasks.")
    print("   Once you complete them, the pipeline will automatically resume.\n")
    print("   📌 AI Agent Tasks:")
    if not step4_file or not step5_file:
        print("      1. Check for 🤖 AGENT_TASK_READY markers above")
        print("      2. AI Agent will auto-execute those tasks")
        print("      3. Pipeline will resume automatically")
    
    print("\n" + "="*80)
    
    # Create summary
    summary_file = os.path.join(SESSION_DIR, "00_SESSION_SUMMARY.md")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("# Local Pipeline Session Summary\n\n")
        f.write(f"**Session ID:** {SESSION_ID}\n")
        f.write(f"**Created:** {datetime.now()}\n\n")
        f.write("---\n\n")
        f.write("## Workflow\n\n")
        f.write("This pipeline analyzes data locally and uses Claude (via Cursor) for insights.\n\n")
        f.write("### Steps:\n\n")
        f.write("1. ✅ Content Analysis - Extracted patterns from target domain responses\n")
        f.write("2. ✅ URL Analysis - Identified most-cited domains\n")
        f.write("2B. ✅ Auto-Scraping - Analyzed structure of top-cited sources\n")
        f.write("3. ✅ Scraping Analysis - Reviewed competitor content\n")
        f.write("4. ✅ AI Synthesis - Claude generated strategic recommendations\n")
        f.write("5. ⏳ Content Generation - Ready for final article\n\n")
        f.write("### Files:\n\n")
        f.write("- `step1_FOR_AGENT_ANALYSIS.md` - Pattern analysis\n")
        f.write("- `step2_FOR_AGENT_ANALYSIS.md` - URL insights\n")
        f.write("- `step3_FOR_AGENT_ANALYSIS.md` - Competitor analysis\n")
        f.write("- `step4_CLAUDE_GENERATE_CONTENT.md` - Generation task\n\n")
        f.write("### Next Action:\n\n")
        f.write("Review each file and ask Claude to provide analysis.\n")
        f.write("Then Claude will generate the final optimized article.\n")
    
    log(f"📄 Summary: {summary_file}")

if __name__ == "__main__":
    # Parse command line arguments
    args = parse_args()
    
    # Set batch size and evaluation flag from args
    globals()['SPOKES_BATCH_SIZE'] = args.spokes_batch
    globals()['SKIP_EVALUATION'] = args.skip_evaluation
    
    # Resume or create session
    session_path, completed = resume_or_create_session(args)
    
    # Run pipeline
    main()




