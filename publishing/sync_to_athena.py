#!/usr/bin/env python3
"""
Sync Published Content to AthenaHQ
Sends prompts (keywords) and content (article URLs) to Athena for tracking

USAGE:
  python3 publishing/sync_to_athena.py

REQUIREMENTS:
  - brand-context/config.json with athena_integration.website_id
  - step12_FRAMER_EXPORT.csv from latest session
  - Athena API running (localhost:3000 or production)
"""

import os
import sys
import csv
import json
import re
import requests
from pathlib import Path

print("\n🔗 ATHENA CONTENT SYNC")
print("="*80)

# Load configuration
script_dir = Path(__file__).parent.parent
config_file = script_dir / 'brand-context' / 'config.json'

try:
    with open(config_file, 'r') as f:
        CONFIG = json.load(f)
except FileNotFoundError:
    print(f"❌ Config not found: {config_file}")
    sys.exit(1)

# Check if Athena enabled
athena_config = CONFIG.get('athena_integration', {})
website_id = athena_config.get('website_id')
vercel_share_token = athena_config.get('vercel_share_token')

if not website_id:
    print("❌ Athena integration not configured")
    print("   Add 'athena_integration.website_id' to config.json")
    print("   Or set enabled=false if not using Athena")
    sys.exit(1)

api_url = athena_config.get('api_url', 'http://localhost:3000/api/webhooks')

def build_athena_url(base_api_url, path, vercel_token=None):
    """
    Build Athena webhook URL, adding Vercel share token when present.
    Example: /settings → /settings?_vercel_share=TOKEN
    """
    url = f"{base_api_url.rstrip('/')}{path}"
    if vercel_token:
        sep = '&' if '?' in url else '?'
        url = f"{url}{sep}_vercel_share={vercel_token}"
    return url

print(f"✅ Athena configured")
print(f"   API: {api_url}")
print(f"   Website ID: {website_id[:20]}...")

# Find session with CSV (prefer one with reviewed keywords, then latest)
results_dir = script_dir / 'results' / 'local_pipeline'
sessions = sorted(results_dir.glob('session_*'), reverse=True)  # newest first

if not sessions:
    print("\n❌ No sessions found")
    print("   Run pipeline first to generate content")
    sys.exit(1)

# First pass: find session with reviewed keywords CSV
csv_file = None
latest_session = None
for session in sessions:
    potential_csv = session / 'step12_FRAMER_EXPORT.csv'
    reviewed_keywords = session / 'step11c_REVIEWED_KEYWORDS.csv'
    if potential_csv.exists() and reviewed_keywords.exists():
        csv_file = potential_csv
        latest_session = session
        print(f"   ✅ Found session with reviewed keywords: {session.name}")
        break

# Second pass: fallback to any session with CSV
if not csv_file:
    for session in sessions:
        potential_csv = session / 'step12_FRAMER_EXPORT.csv'
        if potential_csv.exists():
            csv_file = potential_csv
            latest_session = session
            break

if not csv_file:
    print(f"\n❌ No session has step12_FRAMER_EXPORT.csv")
    print("   Run pipeline through Step 12 first")
    print(f"   Checked {len(sessions)} sessions")
    sys.exit(1)

print(f"📁 Found CSV: {csv_file.name}")
print(f"   Session: {latest_session.name}")

# 1. Fetch Athena settings
print(f"\n🔍 Fetching Athena settings...")

try:
    response = requests.get(
        build_athena_url(api_url, "/settings", vercel_share_token),
        headers={"Authorization": f"Bearer {website_id}"},
        timeout=10
    )
    response.raise_for_status()
    
    athena_settings = response.json()
    
    print(f"✅ Settings loaded:")
    print(f"   Website: {athena_settings['websiteName']}")
    print(f"   Language: {athena_settings['defaultLanguage']}")
    print(f"   Personas: {len(athena_settings.get('personas', []))}")
    
    # Extract for webhooks
    personas = ','.join([p['name'] for p in athena_settings.get('personas', [])])
    persona_desc = ','.join([p.get('description', '') for p in athena_settings.get('personas', [])])
    language = athena_settings.get('defaultLanguage', 'English')
    country = athena_settings.get('baseLocation', 'United States')
    
except Exception as e:
    print(f"⚠️  Could not fetch settings: {e}")
    print(f"   Using defaults")
    personas = ""
    persona_desc = ""
    language = "English"
    country = "United States"

# Helpers
def extract_prompt_values(article_row):
    """Return list of prompt keywords for a CSV row."""
    raw_prompt = (article_row.get('Prompt') or '').strip()
    if raw_prompt:
        keywords = [kw.strip() for kw in re.split(r'[,\|]', raw_prompt) if kw.strip()]
        if keywords:
            return keywords
    # Fallback to article title
    return [article_row.get('Title', '')]

def determine_topic(article_row, default_topic):
    """Use Hub_Title as topic, fallback to article title or default."""
    hub_title = (article_row.get('Hub_Title') or '').strip()
    if hub_title:
        return hub_title
    title = (article_row.get('Title') or '').strip()
    if title:
        return title
    return default_topic

# 2. Read CSV
print(f"\n📄 Reading CSV...")

articles = []
with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        articles.append(row)

print(f"   ✅ {len(articles)} articles loaded")

for i, article in enumerate(articles, 1):
    article_type = article.get('Article_Type', 'UNKNOWN')
    title_preview = article['Title'][:45]
    print(f"      {i}. [{article_type}] {title_preview}...")

# 3. Send Prompts Webhook
print(f"\n📤 Syncing {len(articles)} prompts to Athena...")

category = CONFIG.get('content', {}).get('default_category', 'General')

prompts_entries = []
for article in articles:
    topic = determine_topic(article, category)
    for keyword in extract_prompt_values(article):
        prompts_entries.append({
            "prompt": keyword,
            "topic": topic,
            "language": language,
            "personas": personas,
            "personaDescriptions": persona_desc,
            "country": country
        })

prompts_payload = {
    "prompts": prompts_entries
}

try:
    response = requests.post(
        build_athena_url(api_url, "/prompts", vercel_share_token),
        headers={
            "Authorization": f"Bearer {website_id}",
            "Content-Type": "application/json"
        },
        json=prompts_payload,
        timeout=30
    )
    response.raise_for_status()
    
    result = response.json()
    
    print(f"✅ Prompts synced:")
    print(f"   Created: {result.get('created', 0)}")
    print(f"   Skipped: {result.get('skipped', 0)} (already exist)")
    
    if result.get('details'):
        details = result['details']
        if details.get('newTopics'):
            print(f"   New topics: {details['newTopics']}")
        if details.get('newPersonas'):
            print(f"   New personas: {details['newPersonas']}")
    
except Exception as e:
    print(f"❌ Prompts webhook failed: {e}")
    if hasattr(e, 'response'):
        try:
            print(f"   Response: {e.response.json()}")
        except:
            pass

# 4. Send Content Webhook
print(f"\n📤 Syncing {len(articles)} content URLs to Athena...")

content_payload = {
    "content": [
        {
            "title": article['Title'],
            "url": article.get('Final_URL', '').replace('https://', '').replace('http://', '')
        }
        for article in articles
        if article.get('Final_URL')
    ]
}

try:
    response = requests.post(
        build_athena_url(api_url, "/content", vercel_share_token),
        headers={
            "Authorization": f"Bearer {website_id}",
            "Content-Type": "application/json"
        },
        json=content_payload,
        timeout=30
    )
    response.raise_for_status()
    
    result = response.json()
    
    print(f"✅ Content synced:")
    print(f"   Created: {result.get('created', 0)}")
    print(f"   Updated: {result.get('updated', 0)}")
    print(f"   Skipped: {result.get('skipped', 0)} (already exist)")
    
except Exception as e:
    print(f"❌ Content webhook failed: {e}")
    if hasattr(e, 'response'):
        try:
            print(f"   Response: {e.response.json()}")
        except:
            pass

# 5. Check for zero-mention prompts (optional)
print(f"\n🔍 Checking prompt status in Athena...")

try:
    # Fetch first page of prompts
    response = requests.get(
        build_athena_url(api_url, "/prompts/list", vercel_share_token),
        headers={"Authorization": f"Bearer {website_id}"},
        params={
            "page": 1,
            "limit": 1000,
            "status": "all",
            "type": "all",
            "sortBy": "created",
            "sortOrder": "desc"
        },
        timeout=60
    )
    response.raise_for_status()
    
    data = response.json()
    all_prompts = data['prompts']
    
    # Find our prompts
    our_prompts_text = [a.get('Prompt', '') for a in articles]
    
    synced_prompts = [
        p for p in all_prompts 
        if p['prompt'] in our_prompts_text
    ]
    
    zero_response = [p for p in synced_prompts if p['metrics']['totalResponses'] == 0]
    with_data = [p for p in synced_prompts if p['metrics']['totalResponses'] > 0]
    
    print(f"\n📊 PROMPT STATUS:")
    print(f"   Total synced: {len(synced_prompts)}/{len(articles)}")
    print(f"   With data: {len(with_data)}")
    print(f"   Need data: {len(zero_response)}")
    
    if zero_response:
        print(f"\n⚠️  PROMPTS NEEDING DATA COLLECTION:")
        for p in zero_response[:5]:
            print(f"      - '{p['prompt']}'")
        if len(zero_response) > 5:
            print(f"      ... and {len(zero_response) - 5} more")
    
    if with_data:
        print(f"\n✅ PROMPTS WITH DATA:")
        for p in with_data[:3]:
            m = p['metrics']
            print(f"      - '{p['prompt'][:45]}...'")
            print(f"        Responses: {m['totalResponses']}, Brand: {m['brandMentions']} ({m['mentionRate']:.1f}%)")

except Exception as e:
    print(f"⚠️  Could not check prompt status: {e}")

# Final summary
print(f"\n{'='*80}")
print(f"✅ ATHENA SYNC COMPLETE!")
print(f"{'='*80}")
print(f"\n📋 NEXT STEPS:")
print(f"   1. Check Athena dashboard for synced content")
print(f"   2. Monitor prompt performance (brand mention rates)")
print(f"   3. Collect data for zero-mention prompts")
print(f"   4. Re-run pipeline when you have more data")
print(f"\n{'='*80}\n")

