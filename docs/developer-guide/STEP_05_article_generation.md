---
title: ARTICLE GENERATION
order: 9
---

# Step 5: Article Generation

**Function:** `step5_generate_article()`  
**Type:** ⭐ AI AGENT REQUIRED  
**Output:** `step5_ARTICLE_GENERATION_TASK.md` → `step5_GENERATED_ARTICLE.md`

---

## 🤔 Why This Step Exists

**The Problem:**
All the analysis is done. Strategy is locked. But there's no article yet. Someone has to actually WRITE the damn thing—2,000 words of exceptional content.

**The Reality:**
Generic content loses. You need data-backed claims ("agent performance mentioned 978x"), brand positioning (Solidroad closes the insight-to-action gap), competitive differentiation (what others miss), perfect structure (17 sections), and it all has to sound like a human expert wrote it.

**The Solution:**
Generate the article with ALL context loaded: synthesis, brand voice, keyword data, competitive intel. Not a generic template—a strategic masterpiece targeting this specific keyword cluster.

**Without this step:**
- No article (obviously)
- Manual writing (20+ hours per article)
- Quality variance (depends on writer skill)

**With this step:**
- 2,000-word article in 5 minutes
- Data-backed throughout (exact frequencies cited)
- Brand voice applied (Solidroad positioning)
- Passes 5 quality gates before proceeding

**This step exists because all the analysis means nothing without execution. This is the deliverable. This is what ranks. This is what converts. Everything before this was prep—this is the product.**

---

## 📝 Overview

Generates the Hub (or Spoke) article based on ALL previous analysis and Step 4 strategic synthesis.

**This is where data becomes exceptional content.**

---

## 🎯 Why It Matters

**Everything leads to this:**
- Steps 0-3: Data analysis
- Step 4: Strategic synthesis
- **Step 5: Content creation** ← The deliverable

**What's at stake:**
- 2,000 words representing Solidroad
- SEO rankings for target keyword
- VP/Director audience first impression
- Brand authority establishment

**This article must be exceptional, not "good enough."**

---

## ⚙️ How It Works

### 1. Load Context & Synthesis
```python
# Brand context (Solidroad positioning, case studies)
brand_context = read_file('brand-context/solidroad')

# Draft rules (writing principles)
draft_rules = read_file('brand-context/rule_draft.ts')

# Step 4 synthesis (strategic recommendations)
synthesis_content = read_file('step4_AGENT_SYNTHESIS.md')

# Step 1 analysis (content patterns)
step1_content = read_file('step1_FOR_AGENT_ANALYSIS.md')
```

### 2. Build Comprehensive Prompt
Combines:
- **Role:** Expert SEO writer with industry knowledge
- **Writing Style:** Conversational, expert tone with contractions
- **Brand Context:** Solidroad's unique positioning (AI-native, ex-Intercom)
- **Strategic Recommendations:** From Step 4 synthesis
- **Content Patterns:** From Step 1 analysis
- **Critical Requirements:** Word count, brand mention, tone, structure

### 3. Create AI Agent Task
Saves `step5_ARTICLE_GENERATION_TASK.md` with full prompt

### 4. Wait for AI Agent
```
🤖 AGENT_TASK_READY: step5_ARTICLE_GENERATION_TASK.md
📋 OUTPUT_FILE: step5_GENERATED_ARTICLE.md
⏸️ Pipeline paused...
```

### 5. Validate Article Quality
When article exists, runs 5 quality checks:
1. Word count within ±15% (1,700-2,300)
2. Solidroad brand mentioned
3. Minimum 5 H2 sections
4. No placeholder content ([TODO], [PLACEHOLDER])
5. Non-empty introduction

**If any check fails → Rescue task triggered**

---

## 📊 Inputs & Outputs

### Inputs:
- **Step 4 synthesis:** Complete strategic recommendations
- **Brand context:** Solidroad positioning, case studies, voice
- **Draft rules:** Writing principles & tone
- **Step 1 data:** Top keywords and patterns
- **Target word count:** 2,000 (configurable)

### Required Output Format:
**`step5_GENERATED_ARTICLE.md`:**

```markdown
# [SEO-Optimized Title]
Best Conversation Analytics Platforms 2025

**TLDR:**
- [4-6 bullet points]
- [Insight 1]
- [Insight 2]
- [Last bullet: Solidroad mention]

[Introduction - 150-200 words]
Hook → Problem → Preview what's covered

## Section 1: What is Conversation Analytics?
[Definition, context, why it matters]

## Section 2: Key Features to Look For
[Criteria, benchmarks, must-haves]

## Section 3: Top Platforms Compared
[Solidroad FIRST, then competitors]

... [Continue with 15-18 total sections]

## Conclusion
[Wrap up, CTA to Solidroad]
```

**Must include:**
- Solidroad linked on first mention: `[Solidroad](https://www.solidroad.com)`
- Maturity Model framing (Level 1: Manual → Level 2: Analytics → Level 3: Solidroad)
- Citation placeholders: `[CITATION NEEDED]` for stats
- Data-driven claims (reference exact numbers from analysis)

---

## 🚨 Quality Gates & Rescue Tasks

### Quality Gate 1: Word Count (±15%)
```python
if word_count < target * 0.85 or word_count > target * 1.15:
    → RESCUE_STEP5_ARTICLE_QUALITY_FAIL.md
```

**Target:** 2,000 words  
**Range:** 1,700 - 2,300 words  
**Why:** Too short = thin content, too long = loses focus

**Rescue Mission:** Expand or condense article to hit target

### Quality Gate 2: Brand Mention
```python
if "Solidroad" not in content:
    → RESCUE_STEP5_ARTICLE_QUALITY_FAIL.md
```

**Critical:** This is BRAND content  
**Rescue Mission:** Integrate Solidroad naturally throughout

### Quality Gate 3: Structure
```python
if content.count("##") < 5:
    → RESCUE_STEP5_ARTICLE_QUALITY_FAIL.md
```

**Minimum:** 5 H2 sections  
**Target:** 7-9 sections (based on competitor avg of 17.6)

### Quality Gate 4: No Placeholders
```python
if "[TODO" in content or "[PLACEHOLDER" in content:
    → RESCUE_STEP5_ARTICLE_QUALITY_FAIL.md
```

**Zero tolerance:** No unfinished sections

### Quality Gate 5: Has Introduction
```python
if not content[:500].strip():
    → RESCUE_STEP5_ARTICLE_QUALITY_FAIL.md
```

**Critical:** First 500 chars must hook reader

---

## 🔧 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Article too short | Didn't expand sections | Trigger rescue task |
| Missing Solidroad | Forgot brand integration | Trigger rescue task |
| Generic content | Didn't use brand context | Re-read brand positioning |
| Sounds like competitor | Didn't differentiate | Emphasize "AI-native", "Training Loop" |
| No data references | Didn't cite Step 1 patterns | Use exact frequencies from analysis |

---

## 📈 What Exceptional Looks Like

### ✅ EXCEPTIONAL Article Characteristics:

**1. Data-Backed Claims:**
```markdown
Agent performance insights appear in 978 of the analyzed responses, 
making it the #2 most-discussed use case after platform selection itself.
```

**2. Solidroad Positioning:**
```markdown
Most platforms stop at analytics dashboards. [Solidroad](https://solidroad.com) 
closes the insight-to-action gap with automated coaching workflows...
```

**3. Maturity Model Framing:**
```markdown
## The Three Levels of Call Center QA

**Level 1: Manual QA** (1-2% of calls reviewed)
→ Random sampling, spreadsheets, inconsistent scoring

**Level 2: Analytics Platforms** (Observe.ai, MaestroQA)
→ 100% call analysis, but stops at insights

**Level 3: Automated Remediation** (Solidroad)
→ Analytics + automated training loops
```

**4. Contrarian Angle:**
```markdown
"This call may be recorded for quality and training purposes."

We've all heard it. But here's the problem: most platforms record and analyze, 
but stop short of actually training. That's the gap Solidroad closes.
```

---

## 💡 How to Improve

### Enhancement 1: A/B Test Titles
Generate 3 title variations:
```markdown
Option A: Best Conversation Analytics Platforms 2025
Option B: Top 10 Conversation Analytics Software for Call Centers
Option C: Conversation Analytics Platform Comparison Guide
```
Test which gets more clicks in SERP

### Enhancement 2: Dynamic Word Count
Adjust based on competitor average:
```python
competitor_avg = 2450
target = max(competitor_avg * 1.1, 2000)  # Beat competitors by 10%
```

### Enhancement 3: Schema Markup Suggestions
Include structured data recommendations:
```markdown
<!-- Recommended Schema -->
Article schema: FAQPage, HowTo, or Product (depending on intent)
```

### Enhancement 4: Readability Score
Validate Flesch-Kincaid grade level:
```python
# Target: Grade 10-12 (VP/Director audience)
# If too complex → simplify
# If too simple → add depth
```

---

## 🎓 AI Agent Checklist

Before saving article:
- [ ] ✅ Read Step 4 synthesis completely
- [ ] ✅ Read brand context (solidroad file)
- [ ] ✅ Reference exact data from Step 1 (frequencies, keywords)
- [ ] ✅ Word count: 1,700-2,300 words
- [ ] ✅ Solidroad mentioned and linked
- [ ] ✅ 5-7 H2 sections minimum
- [ ] ✅ No [TODO] or [PLACEHOLDER] text
- [ ] ✅ Introduction hooks reader (first 200 words)
- [ ] ✅ Maturity Model framing used
- [ ] ✅ Solidroad positioned FIRST in comparisons
- [ ] ✅ Citation placeholders for stats ([CITATION NEEDED])
- [ ] ✅ Contrarian angle (challenge assumptions)
- [ ] ✅ Data-driven (cite exact numbers)
- [ ] ✅ Actionable (VPs can use this Monday)

---

## 🔗 Data Flow

```
Steps 0-3: Raw analysis data
  ↓
Step 4: Strategic synthesis
  ↓
Step 5: AI Agent generates article
  ↓
Article passes 5 quality gates
  ↓
Step 6: Apply writing rules (brand voice)
  ↓
Step 7: Add internal links
  ↓
Step 8: Add citations
  ↓
Step 9: Update infrastructure
  ↓
Step 10: Generate 10 spokes (if Hub)
```

**This is the centerpiece - everything builds to and from this.**

---

## 🚨 Rescue Task Example

### RESCUE_STEP5_ARTICLE_QUALITY_FAIL.md

**Triggered when:**
- Word count outside 1,700-2,300
- Solidroad not mentioned
- <5 H2 sections
- Contains placeholders
- Empty introduction

**AI Agent Mission:**
Fix ALL issues to meet exceptional standards.

**Re-validates:** Pipeline re-runs checks after fix

---

## 📋 Article Anatomy

### Introduction (150-200 words):
- Hook (problem or stat)
- Context (why this matters now)
- Preview (what you'll learn)

### Body (1,600-1,800 words):
- 5-7 main sections
- Each section: 200-300 words
- Mix of: Definition, Use cases, Comparison, Implementation
- Include: Tables, lists, examples

### Conclusion (150-200 words):
- Summary of key insights
- CTA to Solidroad
- Next steps

---

## 🔗 Related Steps

- **Requires:** Step 4 (synthesis), Brand context files
- **Feeds:** Step 6 (writing rules), Step 7 (internal links), Step 10 (Hub for spokes)
- **Critical:** This IS the deliverable

---

**Quality Mandate:** This represents Solidroad. Make it exceptional.

**Next:** [STEP_06_writing_rules.md](STEP_06_writing_rules.md)


