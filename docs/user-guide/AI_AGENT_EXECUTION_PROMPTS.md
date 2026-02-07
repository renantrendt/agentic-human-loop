---
title: AI AGENT PROMPTS
order: 4
---

# AI Agent Execution Prompts

**Purpose:** Optimal prompts to give Claude/AI agent for running the content pipeline  
**Last Updated:** 2025-11-21

---

## 🎯 RECOMMENDED: Optimal Balance (UPDATED)

Use this prompt for best results:

```
Run the content pipeline as the AI agent. Monitor the execution, and when you see:

1. 🤖 AGENT_TASK_READY signals → Read the task file and execute it
2. 🚨 RESCUE_TASK_READY signals → Read the rescue task and solve the problem

Execute ALL AI agent tasks (Steps 4-11) without asking for permission between steps.

Use --resume flag after completing tasks to skip already-done steps.

For Step 7: Add 8-12 strategic internal links using the 25+ URLs from sitemap (not just homepage).
For Step 8: Research real citations, but NO citations in TL;DR or first paragraph.
For Step 10: Generate spokes in batches of 3, read synthesis + brand-context/solidroad before each batch.
For Step 11: Cross-link entire cluster after all 10 spokes complete (~50+ internal links).

Goal: Complete pipeline with 1 Hub article (3,000-6,000 words) + 10 spoke articles (1,500-2,000 each), all interconnected.

Do not stop until all quality gates are passed and the cluster is cross-linked.
```

**Why this works:**
- ✅ Clear role definition (AI agent)
- ✅ Signals to watch for (both types)
- ✅ Explicit permission to continue without asking
- ✅ Session resumption guidance (--resume flag)
- ✅ New strategic tasks emphasized (Steps 7-9: linking, citations, infrastructure)
- ✅ Batched spoke generation (quality control)
- ✅ Citation rule specified (no TL;DR/intro citations)
- ✅ Clear success criteria (11 articles + 50+ cross-links)
- ✅ Quality mandate (all gates passed)

---

## 📋 DETAILED: Maximum Clarity

Use this if you want step-by-step instructions included:

```
You are the AI agent for the content pipeline. Your mission:

1. **Execute the pipeline:**
   Run: python3 renan-v2-scripts/content_pipeline_with_ai_agent.py

2. **Monitor for signals:**
   - 🤖 AGENT_TASK_READY → Execute task immediately
   - 🚨 RESCUE_TASK_READY → Solve problem before continuing

3. **Complete ALL 9 AI agent tasks:**
   - Step 4: Synthesize analysis into strategic recommendations
     → Save to: step4_AGENT_SYNTHESIS.md
   - Step 5: Generate Hub (3,000-6,000 words) or Spoke (1,500-2,000 words)
     → Save to: step5_GENERATED_ARTICLE.md
   - Step 6: Apply 15 brand writing rules
     → Save to: step6_ARTICLE_RULES_APPLIED.md
   - Step 7: Add 8-12 strategic internal links from sitemap (25+ URLs available) 🆕
     → Save to: step7_ARTICLE_WITH_INTERNAL_LINKS.md
   - Step 8: Research & add real citations (NO citations in TL;DR/intro!) 🆕
     → Save to: step8_ARTICLE_WITH_CITATIONS.md + bibliography
   - Step 9: Intelligent Hub/Spoke infrastructure registration 🆕
     → Save to: step9_UPDATED_internal_linking_map.json + sitemap
   - Step 10: Generate 10 spokes in batches (if Hub), read brand-context before each batch 🆕
     → Save to: step10_spoke01-10_*.md
   - Step 11: Cross-link entire cluster (~50+ links across 11 articles) 🆕
     → Save to: step11_HUB_WITH_SPOKE_LINKS.md + step11_spoke01-10_WITH_LINKS.md

4. **Use browser automation when needed:**
   If Step 2B scraping fails (<70% success rate), use Cursor browser tools:
   - Navigate to failed URLs
   - Extract content using browser_evaluate()
   - Save to scraped_content/[domain].txt

5. **Quality standards:**
   - Every quality gate must pass (no exceptions)
   - No placeholders, TODOs, or unfinished sections
   - Solidroad brand naturally integrated throughout
   - Data-backed claims (cite exact frequencies from analysis)
   - Zero compromises - exceptional or nothing

6. **Don't stop until:**
   - All 11 articles generated (1 Hub + 10 Spokes)
   - All articles interconnected with internal links
   - Hub has 10 links (1 to each spoke)
   - Each spoke has 3-4 links (Hub + 1-2 related spokes)
   - Infrastructure updated (linking map + sitemap)
   - Session summary shows completion
   - No rescue tasks outstanding

Follow the zero compromise philosophy: demand excellence at every step.

Expected total output: ~22,000 words of exceptional, SEO-optimized content.
```

**Why this works:**
- ✅ Extremely explicit about each step
- ✅ Specifies exact filenames
- ✅ Includes browser automation details
- ✅ Lists all quality standards
- ✅ Clear completion criteria
- ✅ Word count target mentioned

---

## ⚡ MINIMAL: Trust Mode

Use this if you want minimal instructions:

```
Run content_pipeline_with_ai_agent.py as the AI agent. 

Execute all tasks when signaled. Use browser automation if scraping fails. 

Generate 1 Hub + 10 spokes. Add internal links between all 11 articles. 

Zero compromises - exceptional quality only.
```

**Why this works:**
- ✅ Assumes AI agent understands the system
- ✅ Minimal cognitive load
- ✅ Clear quality expectation
- ✅ Trusts AI to read task files for details

**Use when:** You've already run the pipeline before and understand the flow

---

## 🚀 FIRST-TIME EXECUTION: Comprehensive

Use this for the very first run to ensure understanding:

```
You are the AI agent responsible for executing the content pipeline.

**Context:**
- This pipeline creates exceptional SEO content for Solidroad
- It uses a "zero compromise" philosophy (never skip steps)
- You'll be signaled when manual intervention is needed

**Your Role:**

1. **Start the pipeline:**
   ```bash
   python3 renan-v2-scripts/content_pipeline_with_ai_agent.py
   ```

2. **Monitor execution for TWO types of signals:**
   
   **Signal Type 1: Planned AI Tasks**
   ```
   🤖 AGENT_TASK_READY: step4_SYNTHESIS_TASK.md
   📋 OUTPUT_FILE: step4_AGENT_SYNTHESIS.md
   ⏸️ Pipeline paused...
   ```
   
   **Action:** 
   - Read the task file (contains full prompt)
   - Execute the analysis/generation
   - Save with exact OUTPUT_FILE name
   - Re-run pipeline (or continue monitoring)

   **Signal Type 2: Rescue Tasks**
   ```
   🚨 RESCUE_TASK_READY: RESCUE_STEP1_INSUFFICIENT_DATA.md
   💾 Solution File: supplemental_data.csv
   ⏸️ Pipeline BLOCKED...
   ```
   
   **Action:**
   - Read rescue task (contains strategies)
   - Execute solution
   - Save solution to exact filename
   - Re-run pipeline

3. **Execute ALL 5-6 AI agent tasks:**

   **Task 1: Step 2B - Browser Scraping** (NEW)
   - Navigate to 7-10 competitor URLs
   - Use browser_navigate() + browser_evaluate()
   - Extract full article content
   - Save to scraped_content/[domain].txt
   - Create SCRAPING_COMPLETE.txt marker

   **Task 1: Step 2B - Browser Scraping**
   - Navigate to 7-10 competitor URLs
   - Use browser_navigate() + browser_evaluate()
   - Extract full article content
   - Save to: `scraped_content/[domain].txt`
   - Create: `SCRAPING_COMPLETE.txt` marker

   **Task 2: Step 4 - AI Synthesis**
   - Read ALL analysis files (step0-step3)
   - Synthesize into strategic recommendations
   - Decide: Hub or Spoke?
   - If Hub: Suggest 10 spoke topics
   - Reference EXACT data (frequencies, percentages)
   - Save to: `step4_AGENT_SYNTHESIS.md`

   **Task 3: Step 5 - Hub Article Generation**
   - Read synthesis + brand context
   - Generate 2,000-word article
   - Include: TLDR, intro, 7-9 sections, conclusion
   - Solidroad mentioned & linked
   - Data-backed claims with [CITATION NEEDED]
   - Save to: `step5_GENERATED_ARTICLE.md`

   **Task 4: Step 6 - Apply Writing Rules**
   - Read article + 15 writing rules
   - Fix: comma splices, em dashes, "you/your" overuse
   - Align with Solidroad voice
   - Save to: `step6_ARTICLE_RULES_APPLIED.md`

   **Task 5: Step 9 - Register Spoke** (Only if Spoke detected)
   - Read `internal_linking_map.json`
   - Analyze article topic vs existing clusters
   - Add spoke to appropriate cluster
   - Save to: `step9_UPDATED_internal_linking_map.json`

   **Task 6: Step 10 - Generate Spoke Cluster** (Only if Hub detected)
   - Generate 10 spoke articles (1,500-2,000 words each)
   - Each targets unique long-tail keyword
   - Save to: `step10_spoke01-10_*.md`
   - **Then add internal links:**
     - Update Hub: Add 10 links (1 to each spoke)
     - Update each Spoke: Add links to Hub + 1-2 related spokes
   - Update infrastructure (linking map + sitemap)

4. **Browser Automation (if needed):**
   
   If scraping fails in Step 2B:
   ```
   For each failed URL:
   - mcp_cursor-browser-extension_browser_navigate(url)
   - mcp_cursor-browser-extension_browser_snapshot()
   - mcp_cursor-browser-extension_browser_evaluate() to extract text
   - Save to: scraped_content/[domain].txt
   ```

5. **Quality Gates - MUST PASS:**
   - Step 1: 100+ call-center QA responses ✅
   - Step 2B: 70%+ scraping success rate ✅
   - Step 5: Word count 1,700-2,300 ✅
   - Step 5: Solidroad mentioned ✅
   - Step 5: 5+ H2 sections ✅
   - Step 5: No placeholders ✅
   
   **If any gate fails → Rescue task triggered → Fix it**

6. **Success Criteria:**
   - ✅ 1 Hub article (2,500 words)
   - ✅ 10 spoke articles (1,500-2,000 words each)
   - ✅ 50+ internal links between all 11 articles
   - ✅ 3-5 external citations per article
   - ✅ Infrastructure updated
   - ✅ No rescue tasks outstanding
   - ✅ Session summary generated

7. **Philosophy:**
   Zero compromises. If quality is insufficient, STOP and fix it.
   We're Solidroad - we ship exceptional or we ship nothing.

**Expected completion:** 11 exceptional articles (~22,000 words total)

Ready? Execute the pipeline and let's create world-class content.
```

**Why this works:**
- ✅ Perfect for first-time execution
- ✅ Explains both signal types
- ✅ Details all 4 AI tasks
- ✅ Browser automation instructions
- ✅ Quality gates listed
- ✅ Success criteria explicit
- ✅ Philosophy reinforced

---

## 🔥 ZERO COMPROMISE MODE: Aggressive

Use this when you want to emphasize quality over speed:

```
Execute content_pipeline_with_ai_agent.py with ZERO COMPROMISE MODE active.

**Rules:**
1. NEVER skip a quality gate - block and fix
2. NEVER accept "good enough" - demand exceptional
3. NEVER leave TODOs or placeholders
4. NEVER generate generic content - use Solidroad's unique positioning

**Execution:**
- Run pipeline
- Complete ALL 4 AI agent tasks (synthesis, article, rules, spokes)
- Use browser automation for failed scrapes
- Generate 11 exceptional articles
- Add 50+ strategic internal links
- Validate quality at each step

**If you encounter:**
- Insufficient data → Augment it
- Scraping fails → Browser automation
- Article quality low → Fix it
- Keyword cannibalization → Revise spoke topics

**Success = 11 articles that would make a VP of CX bookmark them.**

Ship excellence or ship nothing. 

Let's go.
```

**Why this works:**
- ✅ Emphasizes zero compromise philosophy
- ✅ Sets aggressive quality expectations
- ✅ Short but powerful
- ✅ Clear success metric (VP would bookmark)

---

## 📊 COMPARISON TABLE

| Prompt Type | Length | Detail Level | Best For | Success Rate |
|-------------|--------|--------------|----------|--------------|
| **Optimal** | Medium | Balanced | Most situations | 95% |
| **Detailed** | Long | High | First-time execution | 98% |
| **Minimal** | Short | Low | Repeat runs | 85% |
| **Comprehensive** | Very Long | Maximum | Complex requirements | 99% |
| **Zero Compromise** | Medium | Philosophy-focused | Quality-critical | 90% |

---

## 💡 CUSTOMIZATION

### Add if you want specific behavior:

**For testing (skip Step 10):**
```
+ Skip spoke generation (Step 10) for this run - Hub article only.
```

**For resume from checkpoint:**
```
+ Pipeline was interrupted. Resume from last checkpoint. Check session directory for completed steps.
```

**For specific keyword:**
```
+ Target keyword: "conversation analytics platform"
+ Ensure synthesis uses this as primary keyword.
```

**For specific word count:**
```
+ Hub article: 2,500 words (not 2,000)
+ Spokes: 1,800 words each (not 1,500-2,000 range)
```

---

## ✅ RECOMMENDED PROMPT (Copy-Paste Ready)

```
Run the content pipeline as the AI agent. Monitor the execution, and when you see:

1. 🤖 AGENT_TASK_READY signals → Read the task file and execute it
2. 🚨 RESCUE_TASK_READY signals → Read the rescue task and solve the problem

Execute ALL AI agent tasks (Steps 4, 5, 6, and 10 if Hub detected) without asking for permission between steps.

For Step 10 spoke generation: Use browser automation tools if scraping fails.

Goal: Complete pipeline with 1 Hub article + 10 spoke articles, all interconnected with internal links.

Do not stop until all quality gates are passed and the session summary shows completion.
```

---

## 🎓 What Happens After You Give This Prompt

### Step-by-Step Execution:

1. **I'll run the pipeline script**
   ```bash
   python3 content_pipeline_with_ai_agent.py
   ```

2. **Monitor logs in real-time**
   - Steps 0-3 run automatically (data analysis)
   - Log quality gate results

3. **When Step 4 signals:**
   ```
   🤖 AGENT_TASK_READY: step4_SYNTHESIS_TASK.md
   ```
   - I'll read the task file
   - Analyze ALL data from steps 0-3
   - Generate strategic synthesis
   - Save to `step4_AGENT_SYNTHESIS.md`

4. **Continue to Step 5:**
   - Read synthesis + brand context
   - Generate 2,000-word Hub article
   - Save to `step5_GENERATED_ARTICLE.md`

5. **Continue to Step 6:**
   - Apply 15 writing rules
   - Save to `step6_ARTICLE_RULES_APPLIED.md`

6. **Steps 7-9 run automatically**
   - Internal links added
   - Citations verified
   - Infrastructure updated

7. **Step 10 triggers (if Hub):**
   ```
   🤖 AGENT_TASK_READY: SPOKE CLUSTER GENERATION
   ```
   - Generate 10 spoke articles
   - Add internal links between all 11
   - Update infrastructure

8. **Final summary generated**
   - Session complete
   - 11 articles ready
   - Report all outputs

---

## 🚨 What to Do If...

### Pipeline Blocks with Rescue Task:
**You'll see:**
```
🚨 RESCUE_TASK_READY: RESCUE_STEP2B_SCRAPING_INSUFFICIENT.md
```

**I'll:**
1. Read the rescue task file
2. Use browser automation to extract competitor content
3. Save to required filename
4. Re-run pipeline automatically

### Quality Gate Fails:
**You'll see:**
```
🚨 RESCUE_TASK_READY: RESCUE_STEP5_ARTICLE_QUALITY_FAIL.md
```

**I'll:**
1. Read what quality checks failed
2. Fix the article to meet standards
3. Save corrected version
4. Re-run validation

---

## 📊 Expected Timeline

### With Optimal Prompt:

**Steps 0-3 (Automated):** 2-5 minutes
- Data analysis, URL extraction, scraping

**Step 4 (AI Synthesis):** 3-5 minutes
- Read 6 analysis files, synthesize strategy

**Step 5 (Article Generation):** 5-10 minutes
- 2,000-word article with research

**Step 6 (Writing Rules):** 2-3 minutes
- Apply brand voice corrections

**Steps 7-9 (Automated):** 1-2 minutes
- Internal links, citations, infrastructure

**Step 10 (Spoke Cluster):** 30-60 minutes
- 10 articles × 3-5 min each
- Internal linking phase

**Total:** 45-90 minutes for complete 11-article cluster

---

## 🎯 Success Indicators

### During Execution:
```
✅ Step 1 complete - QUALITY GATE PASSED
✅ Step 2B complete - QUALITY GATE PASSED
   Successfully scraped: 8/10 URLs (80%)
🤖 AGENT_TASK_READY: step4_SYNTHESIS_TASK.md
```

### After Completion:
```
✅ PIPELINE PREPARED - READY FOR AGENT

📁 Session directory: results/local_pipeline/session_20251121_143022/

📋 Files generated:
   0. Brand gap analysis
   1. Content patterns (696 responses)
   2. URL analysis (3,456 URLs)
   4. AI Strategic Synthesis ⭐
   5. Generated article (2,150 words) ⭐
   6. Rules applied ⭐
   7. Internal links added (4 links)
   8. Citations verified (3 approved)
   9. Infrastructure updated
   10. Spoke cluster generated (10 articles) ⭐
   11. Final summary
```

---

## 🔥 Quality Assurance

### I Will Validate:

**At Step 5 (Article):**
- [ ] Word count: 1,700-2,300 ✅
- [ ] Solidroad mentioned ✅
- [ ] 5+ H2 sections ✅
- [ ] No placeholders ✅
- [ ] Non-empty intro ✅

**At Step 10 (Spokes):**
- [ ] All 10 unique keywords ✅
- [ ] No cannibalization (<5% risk) ✅
- [ ] Each 1,500-2,000 words ✅
- [ ] Internal links added ✅

**Overall:**
- [ ] All quality gates passed ✅
- [ ] No rescue tasks outstanding ✅
- [ ] Exceptional quality delivered ✅

---

## 📚 Reference Documentation

**Before running, read:**
- [`../README.md`](../README.md) - Pipeline overview
- [`QUICK_START.md`](QUICK_START.md) - Operational guide
- [`ZERO_COMPROMISE_MODE.md`](ZERO_COMPROMISE_MODE.md) - Philosophy

**During execution, reference:**
- [`../script-docs/00_INDEX.md`](../script-docs/00_INDEX.md) - Step-by-step guides

---

## ✅ FINAL RECOMMENDATION (UPDATED)

**Copy this prompt:**

```
Run the content pipeline as the AI agent. Monitor the execution, and when you see:

1. 🤖 AGENT_TASK_READY signals → Read the task file and execute it
2. 🚨 RESCUE_TASK_READY signals → Read the rescue task and solve the problem

Execute ALL AI agent tasks (Steps 4-11) without asking for permission between steps.

Use --resume flag after completing tasks to skip already-done work and save time.

For Step 7: Add 8-12 strategic internal links from the 25+ sitemap URLs (not just homepage).
For Step 8: Research authoritative citations (Gartner, ICMI, Forrester), but NO citations in TL;DR or first paragraph.
For Step 10: Generate spokes in batches of 3. Before each batch, read synthesis + Step 1 analysis + brand-context/solidroad for unique insights.
For Step 11: Cross-link all 11 articles (~50+ internal links total).

Goal: Complete pipeline with 1 Hub (3,000-6,000 words) + 10 spokes (1,500-2,000 each), fully cross-linked.

Do not stop until all quality gates are passed, cluster is cross-linked, and session shows completion.
```

**Then sit back and let the AI agent work!** 🚀

---

## 🆕 ENHANCED FEATURES (November 2025 Update)

### Session Resumption
```bash
# Resume where you left off (skips completed steps)
python3 content_pipeline_with_ai_agent.py --resume
```
**Benefit:** Skips Steps 0-5 if already done (saves 60-90 seconds!)

### Strategic Internal Linking (Step 7)
- **25+ URLs loaded from sitemap** (not just homepage!)
- Product pages, blog posts, customer stories, resources
- AI agent adds 8-12 contextually relevant links

### Citation Research (Step 8)
- **NEW RULE:** NO external citations in TL;DR or first paragraph
- AI agent web searches for authoritative sources (ICMI, Gartner, Forrester)
- Replaces ALL `[CITATION NEEDED]` markers with real citations

### Batched Spoke Generation (Step 10)
```bash
# Generate 3 spokes at a time (recommended)
python3 content_pipeline_with_ai_agent.py --resume --spokes-batch 3
```
**Workflow:**
1. Generate Spokes 1-3
2. **CHECKPOINT:** Review for cannibalization, data usage, brand context
3. Generate Spokes 4-6
4. **CHECKPOINT:** Cross-batch validation
5. Continue until all 10 complete

**Before each batch, AI agent must read:**
- `step4_AGENT_SYNTHESIS.md` (strategy refresh)
- `step1_FOR_AGENT_ANALYSIS.md` (n-gram frequencies)
- **`brand-context/solidroad`** (unique insights: IQS, SCORE, Crypto.com case study)
- Previous spokes (anti-cannibalization)

### Cluster Cross-Linking (Step 11)
- After all 10 spokes generated → Step 11 task created
- Update Hub with 10 links (1 to each spoke)
- Update each spoke with Hub link + 1-2 related spoke links
- **Total:** ~50+ internal links across 11-article cluster

### Word Count Flexibility
- **Hub articles:** 3,000-6,000+ words (comprehensive pillar content, no upper limit!)
- **Spoke articles:** 1,500-2,000 words (focused deep-dive)

---

**File:** `docs/AI_AGENT_EXECUTION_PROMPTS.md`

