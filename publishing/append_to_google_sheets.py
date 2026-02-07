#!/usr/bin/env python3
"""
Append Articles to Google Sheets - OAuth2 Version (Multi-User)
Reads CSV from Step 12 and appends to Google Sheets WITHOUT deleting existing rows

ADVANTAGES:
- Easy team onboarding (clone → run → allow → done)
- Each user authenticates with their own Google account
- OAuth credentials safe to commit to git
- No service account JSON sharing

FIRST RUN:
- Opens browser for Google sign-in
- User clicks "Allow"
- Token saved locally (token.pickle)

SUBSEQUENT RUNS:
- Uses saved token (no browser)
- Auto-refreshes if expired
"""

import os
import sys
import csv
import pickle
from pathlib import Path

print("\n📊 GOOGLE SHEETS PUBLISHER - OAuth2 (Multi-User)")
print("="*80)

# Check for required packages
try:
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    print("✅ Google API packages available")
except ImportError:
    print("❌ Missing Google API packages")
    print("   Install: pip3 install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)

# Load configuration
import json

config_file = Path(__file__).parent.parent / 'brand-context' / 'config.json'

try:
    with open(config_file, 'r', encoding='utf-8') as f:
        CONFIG = json.load(f)
except FileNotFoundError:
    print(f"❌ Configuration file not found: {config_file}")
    print(f"   Copy brand-context/config.json.example to brand-context/config.json")
    sys.exit(1)

# Configuration from config.json
SPREADSHEET_ID = CONFIG['publishing']['google_sheets']['spreadsheet_id']
SHEET_NAME = CONFIG['publishing']['google_sheets']['sheet_name']
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Paths
script_dir = Path(__file__).parent.parent
project_root = script_dir.parent
oauth_creds_file = project_root / 'oauth_credentials.json'
token_file = project_root / 'token.pickle'

# Find session CSV - accept command line argument or use latest
results_dir = script_dir / "results" / "local_pipeline"

if len(sys.argv) > 1:
    # Use provided session directory
    session_path = Path(sys.argv[1])
    if session_path.is_absolute():
        latest_session = session_path
    else:
        latest_session = script_dir / sys.argv[1]
else:
    # Find latest session
    sessions = sorted(results_dir.glob("session_*"))
    if not sessions:
        print("❌ No sessions found")
        sys.exit(1)
    latest_session = sessions[-1]

csv_file = latest_session / "step12_FRAMER_EXPORT.csv"

if not csv_file.exists():
    print(f"❌ CSV not found: {csv_file}")
    print("   Run pipeline first to generate Step 12 CSV")
    sys.exit(1)

print(f"📁 Found CSV: {csv_file.name}")
print(f"   Session: {latest_session.name}")

# Check for OAuth credentials
if not oauth_creds_file.exists():
    print(f"\n❌ OAuth credentials not found")
    print(f"   Expected: {oauth_creds_file}")
    print(f"\n📋 SETUP REQUIRED:")
    print(f"   1. Go to https://console.cloud.google.com/")
    print(f"   2. Create OAuth 2.0 Client ID (Desktop app)")
    print(f"   3. Download credentials JSON")
    print(f"   4. Save as: {oauth_creds_file}")
    print(f"\n   See publishing/README.md for detailed steps")
    sys.exit(1)

print(f"✅ OAuth credentials found")

# Authenticate with OAuth2
print(f"\n🔐 Authenticating...")

creds = None

# Check if we have a saved token from previous run
if token_file.exists():
    print(f"   📋 Loading saved token...")
    with open(token_file, 'rb') as token:
        creds = pickle.load(token)

# If no valid credentials, do OAuth flow
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        # Refresh expired token
        print(f"   🔄 Refreshing expired token...")
        try:
            creds.refresh(Request())
            print(f"   ✅ Token refreshed")
        except Exception as e:
            print(f"   ⚠️  Refresh failed: {e}")
            print(f"   Will re-authenticate...")
            creds = None
    
    if not creds:
        # FIRST TIME or refresh failed: Open browser for consent
        print(f"\n{'='*80}")
        print(f"🌐 FIRST TIME AUTHENTICATION")
        print(f"{'='*80}")
        print(f"A browser window will open in 3 seconds...")
        print(f"Steps:")
        print(f"  1. Sign in with your Google account")
        print(f"  2. Click 'Allow' to grant access")
        print(f"  3. Return to this terminal")
        print(f"{'='*80}\n")
        
        import time
        time.sleep(3)
        
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(oauth_creds_file),
                SCOPES
            )
            creds = flow.run_local_server(
                port=0,
                success_message='✅ Authentication successful! You can close this window and return to terminal.'
            )
            
            print(f"\n✅ Authentication successful!")
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            sys.exit(1)
    
    # Save token for next time
    print(f"   💾 Saving token for future use...")
    with open(token_file, 'wb') as token:
        pickle.dump(creds, token)
    
    print(f"   ✅ Token saved to: {token_file.name}")
    print(f"   (Next run won't need browser!)")

else:
    print(f"   ✅ Using saved token (no browser needed)")

# Build Google Sheets service
try:
    service = build('sheets', 'v4', credentials=creds)
    print(f"✅ Connected to Google Sheets API")
except Exception as e:
    print(f"❌ Failed to connect: {e}")
    sys.exit(1)

# Read CSV
print(f"\n📄 Reading CSV...")
articles = []

with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        articles.append(row)

print(f"   ✅ {len(articles)} articles loaded")

for i, article in enumerate(articles, 1):
    title_preview = article['Title'][:50]
    print(f"      {i}. {title_preview}...")

# Check existing sheet data
print(f"\n📊 Checking existing sheet...")
try:
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f'{SHEET_NAME}!A:A'
    ).execute()
    
    existing_rows = len(result.get('values', [])) - 1  # Minus header
    print(f"   ✅ {existing_rows} existing articles in sheet")
except Exception as e:
    print(f"   ⚠️  Could not read sheet: {e}")
    existing_rows = 0

# Determine how many Content_Part columns we have
sample_article = articles[0]
part_columns = [key for key in sample_article.keys() if key.startswith('Content_Part')]
num_parts = len(part_columns)

print(f"   📊 Detected {num_parts} content part columns")

# Check if Description column exists
has_description = 'Description' in sample_article

# Convert to values array (dynamic columns!)
values = []
for article in articles:
    row = [
        article['Title'],
        article['Date'],
        article['Author'],
        article.get('Prompt', ''),
        article.get('Article_Type', ''),
        article.get('Hub_Title', ''),
        article.get('Related_Spokes', ''),
        article.get('Final_URL', ''),
        article.get('Description', '')
    ]
    
    # Add all Content_Part columns
    for i in range(1, num_parts + 1):
        part_key = f'Content_Part{i}'
        row.append(article.get(part_key, ''))
    
    values.append(row)

print(f"\n⚡ Appending {len(values)} new articles...")
print(f"   (Existing {existing_rows} rows will be preserved)")

# CRITICAL: Use INSERT_ROWS to APPEND (not overwrite!)
body = {'values': values}

# Calculate column range
# A=Title, B=Date, C=Author, D=Primary_Keyword, E=Article_Type, F=Hub_Title, G=Related_Spokes, H=Final_URL, I=Description, J+=Content_Parts
base_columns = 9  # Title through Description
last_column_index = base_columns + num_parts
last_column_letter = chr(64 + last_column_index)

print(f"   📋 Columns: Title, Date, Author, Prompt, Type, Hub, Related, URL, Description, Content_Part1-{num_parts}")
print(f"   📋 Appending to range A:{last_column_letter}")

try:
    result = service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f'{SHEET_NAME}!A:{last_column_letter}',
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',  # KEY: Appends instead of overwriting!
        body=body
    ).execute()
    
    updated_rows = result.get('updates', {}).get('updatedRows', 0)
    
    print(f"\n{'='*80}")
    print(f"✅ SUCCESS!")
    print(f"{'='*80}")
    print(f"Appended: {updated_rows} new rows")
    print(f"Preserved: {existing_rows} existing rows")
    print(f"Total now: {existing_rows + updated_rows} articles in sheet")
    
    print(f"\n🔗 View sheet:")
    print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
    
    print(f"\n📋 NEXT STEPS:")
    print(f"   1. ✅ Google Sheet updated")
    print(f"   2. Framer will auto-sync from sheet")
    print(f"   3. Review articles in Framer CMS")
    print(f"   4. Publish to solidroad.com/blog/")
    
    print(f"\n{'='*80}")
    print(f"✅ PUBLISHING COMPLETE!")
    print(f"{'='*80}\n")
    
except Exception as e:
    print(f"\n❌ Failed to append: {e}")
    print(f"\n⚠️  Common issues:")
    print(f"   - You don't have edit access to the sheet")
    print(f"   - Sheet name incorrect (currently: '{SHEET_NAME}')")
    print(f"   - Spreadsheet ID incorrect")
    print(f"\n   Check sheet URL and permissions, then try again")
    sys.exit(1)

