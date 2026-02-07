# Content Pipeline with AI Agent - ZERO COMPROMISE MODE

📐 **[View the Architecture Diagram →](https://renantrendt.github.io/agentic-human-loop/docs/ARCHITECTURE.html)**


**Status:** ✅ Production Ready  
**Mode:** Cursor AI Agent (No API Keys Required)  
**Mission:** Create exceptional SEO content for Solidroad

---

## 🚀 Quick Start

```bash
cd /Users/renanserrano/script-nata

# Create new session
python3 agentic-human-loop/content_pipeline_with_ai_agent.py

# Resume latest session (after completing AI tasks)
python3 agentic-human-loop/content_pipeline_with_ai_agent.py --resume

# Resume specific session
python3 agentic-human-loop/content_pipeline_with_ai_agent.py --resume session_YYYYMMDD_HHMMSS

# Generate spokes in batches of 3 (recommended)
python3 agentic-human-loop/content_pipeline_with_ai_agent.py --resume --spokes-batch 3

# Quality evaluation runs automatically (Step 13)
# Secrets loaded from GCP Secret Manager (or .env for local dev)
```

**Watch for:**
- `🤖 AGENT_TASK_READY` → AI synthesis/generation needed
- `🚨 RESCUE_TASK_READY` → Quality issue needs fixing

---

## 📁 Repository Structure

```
agentic-human-loop/
│
├── 📄 content_pipeline_with_ai_agent.py   ← THE MAIN SCRIPT
├── 📖 README.md                           ← THIS FILE (start here)
├── 📂 docs/                               ← ALL DOCUMENTATION
│   ├── user-guide/                        ← FOR USERS (3 files)
│   │   ├── QUICK_START.md                 ← How to run the pipeline
│   │   ├── AI_AGENT_EXECUTION_PROMPTS.md  ← Ready-to-use prompts
│   │   └── ZERO_COMPROMISE_MODE.md        ← Philosophy & rescue tasks
│   ├── developer-guide/                   ← FOR DEVELOPERS (19 files)
│   └── doc-visualizer/                    ← Visual docs browser (Next.js)
│   ├── 00_INDEX.md                        ← Start here for deep-dive
│   ├── STEP_00_brand_gap_analysis.md      ← Per-step technical docs
│   ├── STEP_01_content_analysis.md
│   ├── STEP_02_url_analysis.md
│   ├── STEP_02B_competitor_scraping.md
│   ├── STEP_02C_url_semantic_analysis.md
│   ├── STEP_03_scraping_analysis.md
│   ├── STEP_04_ai_synthesis.md            ⭐ AI agent task
│   ├── STEP_05_article_generation.md      ⭐ AI agent task
│   ├── STEP_06_writing_rules.md           ⭐ AI agent task
│   ├── STEP_07_internal_links.md
│   ├── STEP_08_citations.md
│   ├── STEP_09_infrastructure.md
│   ├── STEP_10_spoke_cluster.md           ⭐ AI agent task
│   ├── STEP_11_final_summary.md
│   └── HUB_SPOKE_STRATEGY_ANALYSIS.md     ← Strategic analysis
│
├── 📂 brand-context/                      ← BRAND RULES
│   ├── solidroad                          ← Brand voice & positioning
│   ├── rule_draft.ts                      ← Draft agent rules
│   ├── rule_writing.ts                    ← 15 writing rules
│   ├── rule_citations.md                  ← Citation guidelines
│   ├── internal_linking_map.json          ← Internal link strategy
│   └── sitemap                            ← Site structure
│
├── 📂 datasets/                           ← INPUT DATA
│   └── conversation-analytics-platform.csv
│
├── 📂 publishing/                         ← PUBLISHING TOOLS
│   ├── append_to_google_sheets.py         ← Google Sheets publisher
│   └── README.md                           ← Publishing setup guide
│
└── 📂 results/local_pipeline/             ← PIPELINE OUTPUTS
    └── session_YYYYMMDD_HHMMSS/           ← Per-session results
        └── step14a_FRAMER_EXPORT.csv       ← HTML export (auto-generated)
```

---

## 🎯 What This Pipeline Does

### Phase 1: Analysis (Steps 0-2C)
1. **Brand Gap Analysis** - Measure Solidroad vs competitor visibility
2. **Content Pattern Analysis** - Extract keywords from 696+ responses
3. **URL Analysis** - Identify most-cited domains
4. **URL Semantic Analysis** - Search intent classification

### Phase 2: AI Agent Tasks (Steps 2B, 4-6)
5. **Browser Scraping** - Scrape 7-10 competitors (AI agent browser tools)
6. **Competitor Analysis** - Analyze scraped content (waits for Step 2B)
7. **AI Synthesis** - Strategic recommendations (AI agent required)
8. **Article Generation** - Hub article (3,000-6,000 words) or Spoke (1,500-2,000 words)
9. **Writing Rules** - Apply brand voice (AI agent required)

### Phase 3: Optimization (Steps 7-9) - AI AGENT TASKS
10. **Strategic Internal Links** - Add 8-12 contextual links from sitemap (AI agent required)
11. **Research & Add Citations** - Web search for authoritative sources, NO citations in TL;DR/intro (AI agent required)
12. **Intelligent Infrastructure** - Hub/Spoke registration in linking map (AI agent required)

### Phase 4: Cluster Building (Steps 10-11)
13. **Spoke Cluster Generation** - Generate 10 supporting spokes if Hub detected (AI agent required, batched)
14. **Cluster Crosslinking** - Connect Hub ↔ Spokes + cross-spoke links (25-30 total links, AI agent required)

### Phase 5: Publishing (Steps 12A-12B)
15. **HTML Conversion** - Convert markdown to Framer-compatible HTML, fix internal links, export to CSV with structure metadata (automated)
16. **Metadata Generation** - AI agent writes SEO descriptions using bigrams/trigrams from dataset (AI agent required)

**CSV Structure (Visual Content Map):**
- Columns: Title, Date, Author, **Prompt**, **Article_Type**, **Hub_Title**, **Related_Spokes**, **Final_URL**, Description, Content
- Google Sheets becomes visual Hub/Spoke map (no separate JSON file!)
- See content structure at a glance

### Phase 6: Quality Validation (Step 13 - MANDATORY)
16. **Content Quality Evaluation** - Multi-model validation (Claude + Perplexity) validates #1 rankings

---

## 🔥 Zero Compromise Philosophy

**We NEVER skip steps.**

- CSV missing? → AI agent rescue task (find data)
- Scraping fails? → AI agent rescue task (manual retrieval)
- Low quality? → AI agent rescue task (fix it)
- Insufficient data? → AI agent rescue task (augment it)

**Quality gates at every critical step. Block until exceptional.**

---

## 📋 AI Agent Tasks

### Planned Tasks (11-12 Total):
1. **Step 2B:** Browser scrape competitors → 7-10 competitor URLs
2. **Step 4:** Synthesize analysis → strategic recommendations + Hub vs Spoke decision
3. **Step 5:** Generate article → Hub (3,000-6,000 words) or Spoke (1,500-2,000 words)
4. **Step 6:** Apply writing rules → brand alignment (15 rules enforced)
5. **Step 7:** Strategic internal links → 8-12 contextual links from sitemap (25+ URLs available)
6. **Step 8:** Research & add citations → Replace `[CITATION NEEDED]` with real sources (NO citations in TL;DR/intro!)
7. **Step 9:** Infrastructure update → Intelligent Hub/Spoke registration
8. **Step 10:** Generate 10 spokes → Batched generation with review checkpoints (if Hub)
9. **Step 10B-C:** Add & verify spoke citations → All 10 spokes get proper citations (AI agent required)
10. **Step 11:** Cluster crosslinking → Add Hub ↔ Spoke + cross-spoke links (~25-30 total links, AI agent required)
11. **Step 12B:** HTML quality review → Fix conversion issues (AI agent required)
12. **Step 12D:** Link verification → Test all internal links & citations work (AI agent required)

### Rescue Tasks (Variable):
- Triggered when quality gates fail
- Creates detailed mission brief
- Blocks pipeline until resolved

---

## 📖 Documentation

### 👤 USER GUIDE (For Running the Pipeline)
**Start here:** [`docs/user-guide/QUICK_START.md`](docs/user-guide/QUICK_START.md) - How to run the pipeline  
**Strategy:** [`docs/user-guide/HUB_SPOKE_STRATEGY_ANALYSIS.md`](docs/user-guide/HUB_SPOKE_STRATEGY_ANALYSIS.md) - Hub & Spoke architecture explained  
**Philosophy:** [`docs/user-guide/ZERO_COMPROMISE_MODE.md`](docs/user-guide/ZERO_COMPROMISE_MODE.md) - Why we never compromise  
**Prompts:** [`docs/user-guide/AI_AGENT_EXECUTION_PROMPTS.md`](docs/user-guide/AI_AGENT_EXECUTION_PROMPTS.md) - Copy-paste prompts for AI agent

### 🛠️ DEVELOPER GUIDE (For Understanding/Improving)
**Navigation:** [`docs/developer-guide/00_INDEX.md`](docs/developer-guide/00_INDEX.md) - Start here for technical deep-dive  
**Per-step docs:** [`docs/developer-guide/STEP_XX_*.md`](docs/developer-guide/) - Technical guides (one per step)

**Each developer guide now includes:**
- **🤔 Why This Step Exists** - Foundational "why" (problem/reality/solution)
- **📝 Overview** - What it does in one sentence
- **🎯 Why It Matters** - Impact on content quality
- **⚙️ How It Works** - Technical implementation
- **📊 Inputs/Outputs** - Data flow
- **🚨 Quality Gates** - What must pass to proceed
- **🔧 Common Issues** - Troubleshooting
- **💡 How to Improve** - Enhancement opportunities

> **NEW (Nov 2024):** All step documentation now starts with "Why This Step Exists" - a no-bullshit explanation of the fundamental reason each step is in the pipeline. Understand the problem being solved before diving into implementation.

---

## ✅ Requirements

**Critical:**
- Python 3.9+
- **Brand configuration:** `brand-context/config.json` ← Configure your brand!

**Data Source (choose one):**
- **Option A (Athena):** Enable `athena_integration` in config → No CSV needed! ✅ RECOMMENDED
- **Option B (CSV):** Provide `datasets/conversation-analytics-platform.csv`

**Dependencies:**
```
pandas, requests, beautifulsoup4, python-dotenv
```

**For Publishing:**
```
google-auth, google-auth-oauthlib, google-auth-httplib2, google-api-python-client
```

**Optional (improves quality):**
- Brand context files in `brand-context/`
- Network access for scraping (Step 2B)

### 🔐 Secrets Management

API keys are managed via **GCP Secret Manager** (project `athena-hq`).  
Scripts use `get_secret()` from `autonomous/secrets.py` which checks env vars first, then falls back to Secret Manager.

**Local dev:** Use a `.env` file as before — `get_secret()` picks it up from env.  
**Production:** No `.env` on disk. Secrets fetched from GCP at runtime.

```bash
# First-time setup: push .env secrets to GCP Secret Manager
pip install google-cloud-secret-manager
python3 scripts/setup_secrets.py --dry-run   # preview
python3 scripts/setup_secrets.py             # push to GCP

# Grant your service account access
python3 scripts/setup_secrets.py --grant-access YOUR_SA@PROJECT.iam.gserviceaccount.com
```

**Required secrets:** `ANTHROPIC_API_KEY`, `RESEND_API_KEY`, `YOUTUBE_API_KEY`, `FRAMER_API_KEY`  
**Optional:** `PERPLEXITY_API_KEY`, `OPENAI_API_KEY` (for multi-model evaluation in Step 13)

---

## 🌍 **UNIVERSAL PIPELINE - Works for Any Company**

This pipeline is **brand-agnostic** with **Athena-first configuration**!

### **🎯 Two Setup Modes:**

#### **Mode 1: Athena-First (Recommended)** ✅
Provide just 3 values, pipeline fetches everything else from AthenaHQ:

```json
{
  "athena_integration": {
    "website_id": "your-athena-website-id"
  },
  "publishing": {
    "author_name": "Your Name",
    "google_sheets": {
      "spreadsheet_id": "YOUR_SHEET_ID",
      "sheet_name": "Sheet1"
    }
  }
}
```

**Pipeline auto-fills from Athena:**
- ✅ Brand name, URL, keywords (from Athena settings)
- ✅ Competitors (23+ with identifiers)
- ✅ Language, personas, locations
- ✅ Category & tags (from dataset bigrams/trigrams)

**Result:** Only 3 values needed! (77% reduction)

#### **Mode 2: Manual Configuration**
Provide all values in config.json if not using Athena:

```json
{
  "brand": {
    "name": "Your Company",
    "url": "https://yourcompany.com",
    "keywords": ["yourcompany"]
  },
  "competitor_analysis": {
    "target_domain": "your_industry",
    "domain_keywords": {"your_industry": ["competitor1", ...]}
  },
  "publishing": {...}
}
```

### **Quick Setup for Other Companies:**

**1. Copy configuration template:**
```bash
cp agentic-human-loop/brand-context/config.json.example agentic-human-loop/brand-context/config.json
```

**2. Update config.json:**
```json
{
  "brand": {
    "name": "Your Company",
    "url": "https://yourcompany.com",
    "author_name": "Your Name",
    "keywords": ["yourcompany", "your company"],
    "default_product_links": [...]
  },
  "competitor_analysis": {
    "target_domain": "your_industry",
    "domain_keywords": {
      "your_industry": ["competitor1", "competitor2", ...]
    }
  },
  "publishing": {
    "google_sheets": {
      "spreadsheet_id": "YOUR_SHEET_ID",
      "sheet_name": "Sheet1"
    }
  }
}
```

**3. Run pipeline:**
```bash
python3 agentic-human-loop/content_pipeline_with_ai_agent.py
```

**Everything adapts to your brand automatically!** ✅

### **What's Configurable:**
- ✅ Brand name, URL, author (appears in all content)
- ✅ Brand keywords (for gap analysis)
- ✅ Product URLs (for internal linking)
- ✅ Competitor list (for content differentiation)
- ✅ Google Sheets publishing destination
- ✅ Word count targets (hub/spoke)
- ✅ Default category and tags

### **What Works Out of the Box:**
- ✅ Content generation (AI adapts to your brand voice file)
- ✅ Quality evaluation (works for any content cluster)
- ✅ Publishing workflow (OAuth2 for any Google account)
- ✅ All 15 pipeline steps

**See:** `brand-context/README.md` for complete configuration guide  
**See:** `CONFIGURATION_GUIDE.md` for configuration modes  
**See:** `ATHENA_INTEGRATION_GUIDE.md` for Athena setup

---

## 🎯 **FOR AGENCIES:**

**Managing multiple clients:**

```bash
# Client A: Solidroad
brand-context/config-solidroad.json

# Client B: Another Company  
brand-context/config-clientb.json

# Switch clients:
cp brand-context/config-clientb.json brand-context/config.json
python3 agentic-human-loop/content_pipeline_with_ai_agent.py
```

**Result:** Generate content for Client B using their branding! ✅

---

## 🎯 Success Looks Like

**Output:**
- 1 Hub article (3,000-6,000 words - comprehensive pillar content)
- 10 spoke articles (1,500-2,000 words each - focused deep-dives)
- ~50+ internal links interconnecting all 11 articles
- Real citations from authoritative sources (ICMI, Gartner, Forrester)
- Intelligent content hub architecture (Hub ↔ Spokes)

**Result:**
- Solidroad dominates entire keyword cluster (11 unique keywords)
- 11 SERP positions instead of 1
- Topical authority established through dense internal linking
- Brand visibility improves from 0.1% to 5%+ (data-backed positioning)
- VP/Director audience served with exceptional content

---

## 🔥 Remember

**We're Solidroad.**  
**We ship exceptional or we ship nothing.**

No compromises. No shortcuts. Excellence every time.

---

## 📞 Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| "CSV not found" | Check `datasets/conversation-analytics-platform.csv` |
| API key not found | Check GCP Secret Manager or local `.env` — see Secrets Management section |
| Scraping timeout | Rescue task created - manual retrieval required |
| Pipeline blocks | Read rescue/task file, complete mission, re-run |

---

---

## 🔗 **PUBLISHING WORKFLOW**

### **Step 1: Publish to Google Sheets**
```bash
python3 publishing/append_to_google_sheets.py
```
**Result:** Articles published to Sheets → Framer auto-syncs

### **Step 2: Sync to Athena (Optional)**
```bash
# Enable in config.json first
python3 publishing/sync_to_athena.py
```
**Result:** Keywords + URLs registered in Athena for tracking

**See:** `publishing/README.md` for setup guides

---

**Ready?** → [`docs/user-guide/QUICK_START.md`](docs/user-guide/QUICK_START.md)

