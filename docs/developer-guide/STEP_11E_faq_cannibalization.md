---
title: FAQ CANNIBALIZATION REVIEW
order: 17.3
---

# Step 11E: FAQ Cannibalization Review

**Function:** `step11e_faq_cannibalization_review()`  
**Type:** ⭐ AI AGENT REQUIRED  
**Output:** `step11e_FAQ_REVIEW_TASK.md` → `step11e_FAQ_REVIEW_REPORT.md` + fixed files

---

## 🤔 Why This Step Exists

**The Problem:**
You now have:
- 3-5 Hub FAQs (Step 5B)
- 20-30 Spoke FAQs (Step 11D)

That's 25-35 FAQs across 11 articles. Even with careful generation, overlap sneaks in:
- Hub FAQ: "How do I cancel subscriptions?"
- Spoke H2: "How to Cancel Subscriptions" 

Google sees both pages answering the same question. It gets confused. Often, it ranks neither well.

**The Reality:**
This is the #1 mistake "Programmatic SEO" makes. Generate content at scale, don't check for overlap, end up with 50 pages competing against each other. Your own content becomes your biggest competitor.

**The Solution:**
Final safety net. AI agent reviews ALL FAQs + ALL H2 headings. Finds overlap. Applies the fix:
- **Hub overlaps Spoke?** → Make Hub answer brief (1 sentence) + link to Spoke
- **Spoke overlaps Spoke?** → Remove from less relevant Spoke
- **FAQ overlaps H2?** → Remove the FAQ (H2 already handles it)

**Without this step:**
- Cannibalization sneaks through
- Google ranks neither page well
- Wasted effort on duplicate content

**With this step:**
- Zero internal competition
- Each question answered in exactly one place
- Clear hierarchy: Hub (brief) → Spoke (deep)

**This step exists because humans (and AI) make mistakes. This is the quality gate that catches them.**

---

## 📝 Overview

Reviews all FAQs across the cluster for overlap with each other AND with H2 headings. Applies fixes to ensure each question is answered in exactly one place, with the right depth.

**Timing:** After Step 11D (all FAQs exist), before Step 12 (publishing)  
**Focus:** Validation and correction, not generation

---

## 🎯 Why It Matters

### The Cannibalization Trap (Real Example)

**Scenario:**
```
Hub Page: "Subscription Management"
  └── FAQ: "How do I cancel subscriptions?"
  
Spoke Page: "How to Cancel Subscriptions"
  └── H2: "How do I cancel subscriptions?"
  └── FAQ: "Can I cancel anytime?"
```

**What Google sees:**
- Page A answers "How do I cancel subscriptions?"
- Page B answers "How do I cancel subscriptions?"
- ...which one should I rank? 🤷

**Result:** Neither ranks well. Traffic goes to competitors.

### The Fix (Applied by This Step)

```
Hub Page: "Subscription Management"
  └── FAQ: "How do I cancel subscriptions?"
        Answer: "You can cancel manually or use an app. 
                [Read our full guide on canceling →]"  ← BRIEF + LINK
  
Spoke Page: "How to Cancel Subscriptions"
  └── H2: "Step-by-step cancellation process"  ← DEEP DIVE
  └── FAQ: "Can I cancel anytime?" ← UNIQUE
```

**What Google sees:**
- Hub gives overview, links to Spoke
- Spoke owns the detailed answer
- Clear hierarchy, no confusion

---

## ⚙️ How It Works

### 1. Load All FAQs and H2s
```python
# Hub FAQs
hub_faqs = extract_faqs('step5b_HUB_FAQS.md')

# Spoke FAQs (10 files)
spoke_faqs = {}
for i in range(1, 11):
    spoke_faqs[i] = extract_faqs(f'step11d_spoke_faqs/spoke{i:02d}_faqs.md')

# All H2 headings (Hub + 10 Spokes)
hub_h2s = extract_h2s('step8_ARTICLE_WITH_CITATIONS.md')
spoke_h2s = {}
for i in range(1, 11):
    spoke_h2s[i] = extract_h2s(f'articles/spokes/step10_spoke{i:02d}*.md')
```

### 2. Create Comparison Matrix
```python
all_questions = hub_faqs + flatten(spoke_faqs) + hub_h2s + flatten(spoke_h2s)

# Find similar pairs
overlaps = []
for i, q1 in enumerate(all_questions):
    for j, q2 in enumerate(all_questions):
        if i < j and semantic_similarity(q1, q2) > 0.75:
            overlaps.append({
                'question1': q1,
                'question2': q2,
                'source1': get_source(q1),
                'source2': get_source(q2),
                'similarity': similarity_score
            })
```

### 3. Create AI Agent Task
```python
task = f"""
# FAQ Cannibalization Review

## Your Mission
Review all FAQs and H2 headings for overlap. Apply fixes.

## Current Inventory

### Hub FAQs (step5b_HUB_FAQS.md)
{hub_faqs}

### Spoke FAQs
{spoke_faqs_formatted}

### Hub H2 Headings
{hub_h2s}

### Spoke H2 Headings
{spoke_h2s_formatted}

---

## Potential Overlaps Detected
{overlaps_formatted}

---

## Fix Rules

### Rule 1: Hub FAQ overlaps Spoke H2?
**Fix:** Make Hub FAQ brief (1 sentence) + add link to Spoke
```markdown
### [Question]?
Brief answer in one sentence. [Read the full guide →](spoke-url)
```

### Rule 2: Hub FAQ overlaps Spoke FAQ?
**Fix:** Remove Spoke FAQ (Hub already handles it)
Or if Spoke FAQ is more specific, keep Spoke, make Hub brief + link.

### Rule 3: Spoke FAQ overlaps Spoke FAQ?
**Fix:** Keep FAQ in the MORE RELEVANT Spoke only.
Relevance = which Spoke's primary keyword better matches the question?

### Rule 4: FAQ overlaps H2 in SAME article?
**Fix:** Remove the FAQ. The H2 section already answers it.

### Rule 5: FAQ answer could be its own article?
**Fix:** Flag for review. If answer needs 500+ words, it's a Spoke topic, not an FAQ.

---

## Output Required

### 1. Review Report (step11e_FAQ_REVIEW_REPORT.md)
```markdown
# FAQ Cannibalization Review Report

## Overlaps Found: [X]
## Fixes Applied: [Y]

### Fix 1: [Description]
- Source: Hub FAQ
- Overlaps with: Spoke 04 H2
- Action: Made Hub brief + added link

### Fix 2: [Description]
...
```

### 2. Updated FAQ Files (only if changes needed)
Save corrected versions with `_FIXED` suffix:
- `step5b_HUB_FAQS_FIXED.md`
- `step11d_spoke_faqs/spoke04_faqs_FIXED.md`
- etc.

If no changes needed for a file, don't create _FIXED version.

"""
```

### 4. Wait for AI Agent
```
🤖 AGENT_TASK_READY: step11e_FAQ_REVIEW_TASK.md
📋 OUTPUT_FILES: step11e_FAQ_REVIEW_REPORT.md + *_FIXED.md files
⏸️ Pipeline paused...
```

### 5. Apply Fixes
```python
# Replace original files with fixed versions
if exists('step5b_HUB_FAQS_FIXED.md'):
    move('step5b_HUB_FAQS_FIXED.md', 'step5b_HUB_FAQS.md')

for i in range(1, 11):
    fixed = f'step11d_spoke_faqs/spoke{i:02d}_faqs_FIXED.md'
    if exists(fixed):
        move(fixed, f'step11d_spoke_faqs/spoke{i:02d}_faqs.md')

log("✅ FAQ cannibalization fixes applied")
```

---

## 📊 Inputs & Outputs

### Inputs:
- `step5b_HUB_FAQS.md` — Hub FAQs
- `step11d_spoke_faqs/*.md` — Spoke FAQs (10 files)
- Hub article (for H2 extraction)
- Spoke articles (for H2 extraction)

### Outputs:
- `step11e_FAQ_REVIEW_TASK.md` — Task file
- `step11e_FAQ_REVIEW_REPORT.md` — What was found and fixed
- `*_FIXED.md` files — Corrected FAQ files (only if changes needed)

### Report Format:
```markdown
# FAQ Cannibalization Review Report

## Summary
- **Total FAQs reviewed:** 28
- **Overlaps detected:** 4
- **Fixes applied:** 4
- **Files modified:** 2

---

## Overlaps & Fixes

### Overlap 1: Hub FAQ ↔ Spoke 04 H2
**Hub FAQ:** "How do you measure agent performance?"
**Spoke 04 H2:** "How to Measure Agent Performance Metrics"
**Similarity:** 87%

**Fix Applied:**
- Hub FAQ answer shortened to 1 sentence
- Added link: "See our [complete metrics guide](spoke04-url)"

**Before:**
```
### How do you measure agent performance?
Agent performance is measured through a combination of quantitative metrics 
(handle time, resolution rate, hold time) and qualitative assessments 
(tone, empathy, accuracy). Modern platforms like Solidroad automate this 
by analyzing 100% of calls and scoring against customizable criteria...
[200 more words]
```

**After:**
```
### How do you measure agent performance?
Combine quantitative metrics (handle time, resolution rate) with qualitative 
scoring (tone, empathy). [See our complete metrics guide →](spoke04-url)
```

---

### Overlap 2: Spoke 03 FAQ ↔ Spoke 07 FAQ
**Spoke 03 FAQ:** "What's a good CSAT score for call centers?"
**Spoke 07 FAQ:** "What CSAT score should call centers target?"
**Similarity:** 91%

**Fix Applied:**
- Removed from Spoke 03 (less relevant)
- Kept in Spoke 07 (primary keyword: "CSAT improvement")

---

## No Changes Needed
- Hub FAQs 1, 2, 4, 5: Unique ✓
- Spokes 01, 02, 05, 06, 08, 09, 10: No overlaps ✓
```

---

## 🚨 Quality Gates

### Gate 1: All Overlaps Addressed
```python
report = read_file('step11e_FAQ_REVIEW_REPORT.md')
if 'Overlaps detected: 0' not in report:
    # Overlaps found - verify fixes were applied
    if 'Fixes applied: 0' in report:
        → RESCUE: "Overlaps detected but no fixes applied"
```

### Gate 2: No High-Similarity Pairs Remaining
```python
# Re-run similarity check after fixes
remaining_overlaps = find_overlaps(threshold=0.75)
if remaining_overlaps:
    → RESCUE: f"Still {len(remaining_overlaps)} overlaps after fixes"
```

### Gate 3: Hub FAQs Stay Brief
```python
hub_faqs = read_file('step5b_HUB_FAQS.md')
for faq in extract_faqs(hub_faqs):
    if len(faq.answer.split()) > 50:
        # Check if it should link to Spoke
        if has_related_spoke(faq.question):
            → RESCUE: "Hub FAQ too long - should be brief + link"
```

---

## 🔧 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Too many overlaps | FAQs generated without checking | Re-run 5B/11D with stricter prompts |
| Fixes not applied | Agent only reported, didn't fix | Require _FIXED files in task |
| Hub still too long | Agent didn't shorten enough | Enforce 50-word max for Hub FAQs |
| Removed wrong FAQ | Agent picked less relevant Spoke | Override with manual decision |

---

## 💡 The Hierarchy Principle

**Every question should be answered in exactly ONE place:**

| Question Type | Where It Lives | Depth |
|---------------|----------------|-------|
| "What is X?" | Hub FAQ | 2-3 sentences |
| "How do I do X?" | Spoke H2 | Full section |
| "What if [edge case]?" | Spoke FAQ | 2-3 sentences |

**If Hub and Spoke both answer the same question:**
- Hub: Brief (1 sentence) + "Learn more →" link
- Spoke: Full explanation

**This creates a funnel:**
```
User searches broad query → Lands on Hub → 
  Sees brief FAQ → Clicks link →
    Lands on Spoke → Gets full answer
```

---

## 🎓 AI Agent Checklist

Before completing review:
- [ ] ✅ Read ALL Hub FAQs
- [ ] ✅ Read ALL Spoke FAQs (10 files)
- [ ] ✅ Read ALL H2 headings (Hub + Spokes)
- [ ] ✅ Identify overlaps (>75% similarity)
- [ ] ✅ Apply Rule 1-5 fixes for each overlap
- [ ] ✅ Create _FIXED files for changed FAQs
- [ ] ✅ Create comprehensive report
- [ ] ✅ Verify no high-similarity pairs remain

---

## 🔗 Data Flow

```
Step 5B: Hub FAQs generated
    ↓
Step 11D: Spoke FAQs generated
    ↓
Step 11E: Cannibalization review (THIS STEP)
         - Compares all FAQs + H2s
         - Finds overlaps
         - Applies fixes
         - Outputs clean FAQ files
    ↓
Step 12: HTML export
         - Merges FAQs into articles
         - Adds FAQPage schema
         - Zero cannibalization guaranteed
```

---

## 🔗 Related Steps

- **Requires:** Step 5B (Hub FAQs), Step 11D (Spoke FAQs)
- **Feeds:** Step 12 (publishing with clean FAQs)
- **Purpose:** Quality gate before publishing

---

## 🚀 Expected Output

**Input:** 25-35 FAQs + 50+ H2 headings  
**Overlaps found:** Typically 2-5 (10-15%)  
**Fixes applied:** All overlaps resolved  
**Result:** Zero internal cannibalization  

**Every question answered once, in the right place, with the right depth.** ✅

---

**Next Step:** [STEP_12_publishing.md](STEP_12_publishing.md)

