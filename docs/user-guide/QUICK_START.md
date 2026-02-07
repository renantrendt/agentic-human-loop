---
title: QUICK START
order: 1
---

# 🚀 Quick Start - ZERO COMPROMISE Pipeline

## 🆕 WHAT'S NEW (November 2025 Update)

**Major Enhancements:**
- ✅ **Session Resumption:** `--resume` flag skips completed steps (saves time!)
- ✅ **Steps 7-9 Now AI Agent Tasks:** Strategic linking, real citations, intelligent infrastructure
- ✅ **25+ Internal Links from Sitemap:** Product pages, blog posts, customer stories loaded
- ✅ **No Citations in TL;DR/Intro:** Rule enforced in Step 8
- ✅ **Hub Articles Flexible:** 3,000-6,000+ words (no artificial limits!)
- ✅ **Batched Spoke Generation:** Generate 3 at a time with review checkpoints
- ✅ **Step 11 - Cluster Cross-Linking:** ~50+ links across all 11 articles

**Total AI Agent Tasks:** 10-11 (Steps 2B, 4, 5, 6, 7, 8, 9, 11, 12B)  
**Total Pipeline Steps:** 15 (Steps 0-14)  
**Automated Steps:** 0-3, 10, 12A, 13, 14

---

## ⚡ TL;DR

```bash
cd /Users/renanserrano/script-nata

# Create new session
python3 agentic-human-loop/content_pipeline_with_ai_agent.py

# Resume latest session (recommended after completing AI tasks)
python3 agentic-human-loop/content_pipeline_with_ai_agent.py --resume

# Batched spoke generation (3 at a time)
python3 agentic-human-loop/content_pipeline_with_ai_agent.py --resume --spokes-batch 3
```

**Watch for TWO types of signals:**
- `🤖 AGENT_TASK_READY` → AI synthesis/generation needed
- `🚨 RESCUE_TASK_READY` → Quality issue needs fixing

**Philosophy:** We NEVER skip steps. We demand AI agent rescue for any failures.

**NEW:** Use `--resume` to skip completed steps and continue where you left off!

---

## 🎯 Your Role as AI Agent

When you see this in logs:
```
🤖 AGENT_TASK_READY: /path/to/step4_SYNTHESIS_TASK.md
📋 OUTPUT_FILE: step4_AGENT_SYNTHESIS.md
⏸️  Pipeline paused - waiting for AI Agent...
```

**Do this:**
1. Read the task file (contains full prompt)
2. Execute the analysis/generation
3. Save result with the exact OUTPUT_FILE name
4. Pipeline auto-resumes

---

## 📋 AI Agent Tasks (2 Types)

### Type 1: PLANNED Tasks (9-10 Total)
These are expected AI agent interventions:

**Task 1: Step 2B - Browser Scraping**  
**Input:** `step2b_BROWSER_SCRAPING_TASK.md`  
**Output:** `scraped_content/*.txt` + `SCRAPING_COMPLETE.txt`  
**Action:** Scrape 7-10 competitor URLs using browser automation tools

**Task 2: Step 4 - AI Synthesis**  
**Input:** `step4_SYNTHESIS_TASK.md`  
**Output:** `step4_AGENT_SYNTHESIS.md`  
**Action:** Synthesize all analysis → strategic recommendations + Hub vs Spoke decision

**Task 3: Step 5 - Article Generation**  
**Input:** `step5_ARTICLE_GENERATION_TASK.md`  
**Output:** `step5_GENERATED_ARTICLE.md`  
**Action:** Generate Hub (3,000-6,000 words) or Spoke (1,500-2,000 words)

**Task 4: Step 6 - Apply Writing Rules**  
**Input:** `step6_WRITING_RULES_TASK.md`  
**Output:** `step6_ARTICLE_RULES_APPLIED.md`  
**Action:** Apply Solidroad's 15 brand writing rules to article

**Task 5: Step 7 - Strategic Internal Links** 🆕  
**Input:** `step7_INTERNAL_LINKS_TASK.md`  
**Output:** `step7_ARTICLE_WITH_INTERNAL_LINKS.md`  
**Action:** Add 8-12 contextual links using 25+ URLs from sitemap

**Task 6: Step 8 - Research & Add Citations** 🆕  
**Input:** `step8_CITATIONS_TASK.md`  
**Output:** `step8_ARTICLE_WITH_CITATIONS.md` + bibliography  
**Action:** Web search for authoritative sources, replace `[CITATION NEEDED]` (NO citations in TL;DR/intro!)

**Task 7: Step 9 - Infrastructure Update** 🆕  
**Input:** `step9_INFRASTRUCTURE_TASK.md`  
**Output:** `step9_UPDATED_internal_linking_map.json` + sitemap  
**Action:** Intelligent Hub/Spoke registration in content architecture

**Task 8: Step 10 - Generate Spoke Cluster** (If Hub detected)  
**Input:** `step10_SPOKE_CLUSTER_TASK.md`  
**Output:** 10 spoke article files (1,500-2,000 words each)  
**Action:** Batched generation (3 at a time) with review checkpoints, keyword matrix, brand insight distribution

**Task 9: Step 11 - Cluster Cross-Linking** 🆕 (After all 10 spokes)  
**Input:** `step11_CLUSTER_CROSSLINKING_TASK.md` (dynamically generated with contextual guidance)  
**Output:** Hub + 10 spokes updated with ~50+ internal links  
**Action:** Connect all 11 articles (Hub → each spoke, spoke → Hub + related spokes)

**Note:** Task file provides WHERE to link each spoke in Hub based on topic. AI agent reads context and adds links intelligently (not keyword matching).

**Task 10: Step 12B - Generate Metadata** 🆕  
**Input:** `step12b_METADATA_TASK.md` (shows relevant bigrams/trigrams per article)  
**Output:** `step12_ARTICLE_METADATA.json`  
**Action:** Write 150-160 char SEO descriptions using high-frequency n-grams from dataset

### Type 2: RESCUE Tasks (Variable)
These trigger when quality gates fail:

**Examples:**
- `RESCUE_STEP1_INSUFFICIENT_DATA.md` - Need more responses
- `RESCUE_STEP5_ARTICLE_QUALITY_FAIL.md` - Article doesn't meet standards

**Signal:** `🚨 RESCUE_TASK_READY`  
**Action:** Fix the blocking issue, save solution, re-run pipeline

**Note:** Step 2B no longer creates rescue tasks - it creates a planned AI agent task instead.

---

## 📁 Where Everything Lives

```
agentic-human-loop/
├── content_pipeline_with_ai_agent.py           ← Run this
├── results/
│   └── local_pipeline/
│       └── session_YYYYMMDD_HHMMSS/   ← All outputs here
│           ├── step0_BRAND_GAP_ANALYSIS.md
│           ├── step1_FOR_AGENT_ANALYSIS.md
│           ├── step2_FOR_AGENT_ANALYSIS.md
│           ├── step2c_URL_SEMANTIC_ANALYSIS.md
│           ├── step2b_SCRAPED_ANALYSIS.md
│           ├── step3_FOR_AGENT_ANALYSIS.md
│           ├── step4_SYNTHESIS_TASK.md       ← AI reads this
│           ├── step4_AGENT_SYNTHESIS.md      ← AI writes this
│           ├── step6_ARTICLE_GENERATION_TASK.md
│           ├── step6_GENERATED_ARTICLE.md
│           ├── step7_WRITING_RULES_TASK.md
│           ├── step7_ARTICLE_RULES_APPLIED.md
│           ├── step8_ARTICLE_WITH_LINKS.md
│           ├── step9_CITATIONS_REPORT.md
│           └── 00_SESSION_SUMMARY.md
```

---

## ✅ Pre-Flight Check

**Required:**
- [ ] CSV exists: `datasets/conversation-analytics-platform.csv`
- [ ] **Brand config:** `brand-context/config.json` (copy from config.json.example if first time)

**Two Setup Options:**

### **Option A: Athena-First (Minimal - 3 values!)** ✅ RECOMMENDED
```json
{
  "athena_integration": {
    "website_id": "your-athena-website-id"
  },
  "publishing": {
    "author_name": "Your Name",
    "google_sheets": {"spreadsheet_id": "ID", "sheet_name": "Sheet1"}
  }
}
```
**Pipeline fetches brand info from Athena automatically!**

### **Option B: Manual (13 values)**
Fill in all brand, competitor, and publishing details manually

**Configuration check:**
```bash
# Verify config exists
cat agentic-human-loop/brand-context/config.json | grep "name"

# Should show your brand name
```

**Optional (but recommended):**
- [ ] Brand voice file: `brand-context/solidroad` (or your company name)
- [ ] Draft rules: `brand-context/rule_draft.ts`
- [ ] Writing rules: `brand-context/rule_writing.ts`
- [ ] Internal linking map: `brand-context/internal_linking_map.json`

**For other companies:**
- Update config.json with your brand name, URL, author
- Create your brand voice file (follow `solidroad` format)
- Update sitemap with your URLs

---

## 🔥 Common Issues

| Issue | Solution |
|-------|----------|
| "CSV file not found" | Check path: `datasets/conversation-analytics-platform.csv` |
| "Permission denied .env" | ✅ Already fixed - ignore this |
| Scraping timeouts | ✅ Non-critical - pipeline continues |
| "Synthesis file not found" | AI agent hasn't completed Step 4 yet |

---

## 📊 Success Looks Like

```
[HH:MM:SS] ================================================================================
[HH:MM:SS] STEP 0: BRAND GAP ANALYSIS
[HH:MM:SS] ================================================================================
[HH:MM:SS] Loaded 50,000 responses
[HH:MM:SS] ✅ Step 0 complete: /path/to/step0_BRAND_GAP_ANALYSIS.md
[HH:MM:SS]    Brand mention rate: 2.3%

[HH:MM:SS] ================================================================================
[HH:MM:SS] STEP 1: CONTENT ANALYSIS (Local CSV)
[HH:MM:SS] ================================================================================
[HH:MM:SS] Loading /path/to/conversation-analytics-platform.csv...
[HH:MM:SS] ✅ Loaded 50,000 responses
[HH:MM:SS] Categorizing by source citations...
[HH:MM:SS] ✅ Found 12,450 call center QA domain responses
...

🤖 AGENT_TASK_READY: step4_SYNTHESIS_TASK.md     ← YOUR TURN!
📋 OUTPUT_FILE: step4_AGENT_SYNTHESIS.md
⏸️  Pipeline paused - waiting for AI Agent to complete synthesis...
```

## 💡 Pro Tips

1. **Use session resumption:** 🆕
   ```bash
   # After completing any AI agent task, resume (skips completed steps)
   python3 content_pipeline_with_ai_agent.py --resume
   ```
   **Saves 60-90 seconds** by skipping Steps 0-3 analysis!

2. **Monitor logs in real-time:**
   ```bash
   python3 content_pipeline_with_ai_agent.py 2>&1 | tee pipeline.log
   ```

3. **Batch spoke generation for quality control:** 🆕
   ```bash
   # Generate 3 spokes, review, continue (recommended)
   python3 content_pipeline_with_ai_agent.py --resume --spokes-batch 3
   ```
   **Prevents overwhelming 10-spoke generation at once!**

4. **Parallel execution:**
   - Complete multiple AI tasks before re-running
   - Pipeline checks for all expected files and continues

---

## 📚 Full Documentation

- **⚡ START HERE:** `QUICK_START.md` (this file)
- **🎯 PHILOSOPHY:** `ZERO_COMPROMISE_MODE.md` (read this to understand why)
- **🔧 Technical Details:** `PIPELINE_BREAKING_POINTS_ANALYSIS.md`
- **📝 Changelog:** `AI_AGENT_IMPROVEMENTS_SUMMARY.md`
- **💻 Reference Code:** `04_local_pipeline_RESILIENT.py`

---

## 🔥 Remember

**We're Solidroad. We don't ship "good enough".**  
**We ship exceptional or we ship nothing.**

---

## 📰 Step 12: Publishing to Framer

After completing all 11 articles, Step 12 automatically converts to HTML:

**Step 12A (Automated):**
- Converts markdown → HTML
- Fixes internal links (file refs → /blog/ URLs)
- Chunks large content (multi-column format for >50k chars)
- Generates CSV: `step12_FRAMER_EXPORT.csv`

**Step 12B (AI Agent Task):**
- Write SEO descriptions (150-160 chars)
- Use bigrams/trigrams from dataset
- Update CSV Description column

**CSV Format:**
- Columns: Title, Date, Author, **Description**, Content_Part1, Content_Part2
- Description: Plain text meta descriptions
- Content: HTML (split if >50k chars)

**Publishing (when ready):**
```bash
# Append to Google Sheets (OAuth2 - no setup if already authenticated)
python3 agentic-human-loop/publishing/append_to_google_sheets.py
```

**Requirements:** OAuth2 (first run opens browser for authentication)  
**See:** `publishing/OAUTH_QUICK_START.md` for details

---

## 🎯 Step 13: Content Quality Evaluation (MANDATORY)

After all content is generated, Step 13 automatically validates quality:

**Runs automatically** (no flag needed)

**Tests:** All 11 Solidroad articles vs 7 competitors for main keyword

**Requirements:** ANTHROPIC_API_KEY + PERPLEXITY_API_KEY in .env

**Expected Results:**
- Hub ranks #1 (both models)
- 7/11 Solidroad articles in top 10 (70% dominance)
- Cluster strategy validated

**Output:** `step13_CLUSTER_DOMINANCE.json`

**To skip (NOT recommended):**
```bash
python3 agentic-human-loop/content_pipeline_with_ai_agent.py --resume --skip-evaluation
```

**See:** `../developer-guide/STEP_13_evaluation.md` for details

---

**Ready?** Run the script and watch for:
- `🤖 AGENT_TASK_READY` (planned tasks)
- `🚨 RESCUE_TASK_READY` (quality gates)

