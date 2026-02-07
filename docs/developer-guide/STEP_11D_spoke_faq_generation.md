---
title: SPOKE FAQ GENERATION
order: 17.2
---

# Step 11D: Spoke FAQ Generation

**Function:** `step11d_generate_spoke_faqs()`  
**Type:** ⭐ AI AGENT REQUIRED  
**Output:** `step11d_SPOKE_FAQ_TASK.md` → `step11d_spoke_faqs/` (10 files)

---

## 🤔 Why This Step Exists

**The Problem:**
Spoke articles target long-tail keywords, but they're missing the "People Also Ask" (PAA) opportunity. Google shows PAA boxes for specific queries — if you don't have FAQs, competitors steal those snippets.

**The Reality:**
Spoke FAQs are fundamentally different from Hub FAQs:
- **Hub FAQs:** "What is conversation analytics?" (broad)
- **Spoke FAQs:** "Does Netflix charge a cancellation fee?" (specific)

If you put specific questions in the Hub, you cannibalize your Spokes. If you put broad questions in Spokes, you cannibalize your Hub. Each page type needs its own FAQ strategy.

**The Solution:**
Generate 2-3 **specific, nitty-gritty FAQs** for each of the 10 Spoke articles. These target PAA snippets for long-tail queries. The AI agent reads the existing Hub FAQs to ensure zero overlap.

**Without this step:**
- Miss PAA snippet opportunities (competitors win)
- Spokes feel incomplete (no quick answers)
- Risk putting specific Qs in Hub (cannibalization)

**With this step:**
- Each Spoke targets 2-3 PAA queries
- Clear separation: Hub = broad, Spokes = specific
- 20-30 additional ranking opportunities across cluster

**This step exists because Spoke FAQs capture the long-tail. Hub FAQs capture the head. Together, they own the entire question landscape.**

---

## 📝 Overview

Generates 2-3 **specific, topic-focused FAQs** for each of the 10 Spoke articles. The AI agent processes all Spokes in sequence, ensuring no overlap with Hub FAQs or between Spokes.

**Timing:** After Step 11C (keyword review), before Step 11E (cannibalization check)  
**Focus:** 10 articles × 2-3 FAQs = 20-30 FAQs total

---

## 🎯 Why It Matters

### SEO Impact:
- **PAA snippets:** Specific questions = featured in Google's "People Also Ask"
- **Long-tail coverage:** Each FAQ targets a micro-query
- **SERP real estate:** 10 Spokes × 2-3 FAQs = 20-30 snippet opportunities

### Content Strategy Impact:
- **Clear boundaries:** Spokes own specific questions, Hub owns broad ones
- **No cannibalization:** Hub FAQs are read first, Spoke FAQs avoid overlap
- **Cluster completeness:** Every angle of the topic has an FAQ somewhere

### User Impact:
- Quick answers to specific questions
- No hunting through long articles for simple facts
- Professional, comprehensive Spoke pages

---

## ⚙️ How It Works

### 1. Load Hub FAQs First
```python
# CRITICAL: Read Hub FAQs to prevent overlap
hub_faqs = read_file('step5b_HUB_FAQS.md')
hub_questions = extract_questions(hub_faqs)

# Example: ["What is conversation analytics?", "Why is it important?", ...]
```

### 2. Load All Spoke Articles
```python
spoke_files = glob('articles/spokes/step10_spoke*.md')
# 10 spoke articles
```

### 3. Create Sequential Task
```python
task = f"""
# Spoke FAQ Generation Task

## Context
- Hub FAQs already exist (DO NOT REPEAT THESE)
- You will generate FAQs for 10 Spoke articles
- Each Spoke gets 2-3 specific FAQs

## Hub FAQs (ALREADY ANSWERED - DO NOT REPEAT)
{hub_questions}

## Your Mission

For EACH Spoke article below, generate 2-3 FAQs.

### Spoke FAQ Requirements

#### ✅ DO: Specific, Nitty-Gritty Questions
- "Can I get a refund for a partial month?"
- "Does [service] charge a cancellation fee?"
- "How long does [process] take?"
- "What happens if [edge case]?"

#### ❌ DON'T: Broad, Definitional Questions
- "What is [topic]?" → Already in Hub
- "Why is [topic] important?" → Already in Hub
- "Who uses [topic]?" → Already in Hub

#### ❌ DON'T: Questions That Deserve Their Own Article
- If the answer needs 500+ words → It's a new Spoke, not an FAQ

---

## Spoke 1: {spoke1_title}

**Primary Keyword:** {spoke1_keyword}
**First Paragraph:** {spoke1_intro}

Generate 2-3 FAQs specific to THIS topic:
- Question must be answerable in 2-3 sentences
- Question must be unique (not in Hub, not in other Spokes)
- Question should target a PAA opportunity

[OUTPUT FORMAT]
### [Specific Question]?
[2-3 sentence answer]

---

## Spoke 2: {spoke2_title}
... (repeat for all 10 spokes)

"""
```

### 4. Wait for AI Agent
```
🤖 AGENT_TASK_READY: step11d_SPOKE_FAQ_TASK.md
📋 OUTPUT_FOLDER: step11d_spoke_faqs/
⏸️ Pipeline paused...
```

### 5. Validate Each Spoke's FAQs
```python
for spoke_num in range(1, 11):
    faqs = read_file(f'step11d_spoke_faqs/spoke{spoke_num:02d}_faqs.md')
    
    # Count FAQs
    faq_count = faqs.count('### ')
    if faq_count < 2 or faq_count > 3:
        trigger_rescue(f"Spoke {spoke_num}: Need 2-3 FAQs, got {faq_count}")
    
    # Check for Hub question overlap
    for hub_q in hub_questions:
        if similar(hub_q, faqs):
            trigger_rescue(f"Spoke {spoke_num}: Overlaps with Hub FAQ")
```

---

## 📊 Inputs & Outputs

### Inputs:
- `step5b_HUB_FAQS.md` — Hub FAQs (to avoid overlap)
- `articles/spokes/step10_spoke*.md` — 10 Spoke articles
- `brand-context/solidroad` — Brand positioning
- `step4_AGENT_SYNTHESIS.md` — Keyword strategy

### Outputs:
- `step11d_SPOKE_FAQ_TASK.md` — Task file for AI agent
- `step11d_spoke_faqs/spoke01_faqs.md` through `spoke10_faqs.md`

### Output Format (per Spoke):
```markdown
# Spoke 04: Agent Performance Improvement - FAQs

## Frequently Asked Questions

### How often should agent performance be reviewed?
Best practice is weekly coaching sessions based on call analytics data. 
Daily spot-checks work for new agents, while tenured agents benefit from 
trend analysis over 2-4 week periods.

### What metrics matter most for agent coaching?
Focus on leading indicators: handle time variance, first-call resolution 
rate, and sentiment trajectory. Lagging indicators like CSAT confirm 
improvement but don't guide coaching conversations.

### Can conversation analytics replace manual QA entirely?
Not entirely — human judgment matters for edge cases and brand voice. 
However, analytics can automate 80-90% of scoring, freeing QA managers 
to focus on coaching instead of listening to calls.
```

---

## 🚨 Quality Gates

### Gate 1: FAQ Count (2-3 per Spoke)
```python
if faq_count < 2:
    → RESCUE: "Too few FAQs - add specific questions for PAA"
if faq_count > 3:
    → RESCUE: "Too many FAQs - keep focused, save for other content"
```

### Gate 2: No Hub Overlap
```python
for spoke_faq in spoke_faqs:
    for hub_faq in hub_faqs:
        if semantic_similarity(spoke_faq, hub_faq) > 0.8:
            → RESCUE: "FAQ too similar to Hub - make more specific"
```

### Gate 3: No Cross-Spoke Overlap
```python
all_spoke_faqs = flatten(spoke_faqs)
for i, faq1 in enumerate(all_spoke_faqs):
    for j, faq2 in enumerate(all_spoke_faqs):
        if i != j and semantic_similarity(faq1, faq2) > 0.8:
            → RESCUE: "FAQs overlap between Spokes - differentiate"
```

### Gate 4: Specificity Check
```python
broad_patterns = ['what is', 'why is', 'who uses', 'what are the benefits']
for faq in spoke_faqs:
    if any(pattern in faq.lower() for pattern in broad_patterns):
        → RESCUE: "Question too broad - belongs in Hub, not Spoke"
```

---

## 🔧 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| FAQs overlap with Hub | Agent didn't read Hub FAQs | Re-run with Hub FAQs prominently displayed |
| FAQs too broad | Agent defaulted to generic | Emphasize "specific, nitty-gritty" |
| Same FAQ in multiple Spokes | Topics overlap | Assign to most relevant Spoke only |
| Answer too long | Question deserves own article | Convert to Spoke topic, remove from FAQ |

---

## 💡 Examples

### ✅ GOOD Spoke FAQs (Specific)

**Spoke: "How to Cancel Netflix"**
1. "Can I get a refund for a partial month?" — Billing edge case ✓
2. "Does Netflix charge a cancellation fee?" — Specific fear ✓
3. "Will I lose my watch history if I cancel?" — User concern ✓

**Spoke: "Agent Performance Improvement"**
1. "How often should agent performance be reviewed?" — Implementation ✓
2. "What metrics matter most for coaching?" — Tactical ✓

### ❌ BAD Spoke FAQs (Too Broad or Overlap)

1. "What is conversation analytics?" — Belongs in Hub
2. "Why is agent performance important?" — Belongs in Hub
3. "What are the benefits of quality assurance?" — Belongs in Hub
4. "How do I use Solidroad?" — Belongs on product docs

---

## 🎯 PAA Targeting Strategy

**How to find good Spoke FAQ questions:**

### Method 1: Google's "People Also Ask"
Search the Spoke's primary keyword, note PAA questions:
```
Search: "how to improve agent performance call center"
PAA: "How do you measure agent performance?"
PAA: "What is a good call handling time?"
PAA: "How often should agents be coached?"
```

### Method 2: Question Modifiers
Take the Spoke topic, add question words:
- **How long** does [process] take?
- **How much** does [thing] cost?
- **What happens if** [edge case]?
- **Can I** [action] without [constraint]?
- **Does** [service] charge for [feature]?

### Method 3: User Fears/Concerns
What would stop someone from taking action?
- Hidden fees?
- Data loss?
- Time commitment?
- Compatibility issues?

---

## 📋 Batch Processing Strategy

**Why process all 10 Spokes in one task?**

1. **Context retention:** Agent remembers what's been asked
2. **Cross-Spoke awareness:** Avoids overlap between Spokes
3. **Efficiency:** One task file, one review cycle
4. **Consistency:** Same voice across all FAQs

**Alternative (if agent struggles):**
Split into 2 batches of 5 Spokes each. Add "Review previous batch" instruction.

---

## 🎓 AI Agent Checklist

Before saving Spoke FAQs:
- [ ] ✅ Read ALL Hub FAQs first
- [ ] ✅ 2-3 FAQs per Spoke (not more)
- [ ] ✅ No overlap with Hub questions
- [ ] ✅ No overlap between Spokes
- [ ] ✅ All questions are specific/tactical
- [ ] ✅ No "What is X?" definitional questions
- [ ] ✅ Each answer is 2-3 sentences
- [ ] ✅ Answers are actionable, not vague

---

## 🔗 Data Flow

```
Step 5B: Hub FAQs generated (broad questions)
    ↓
Step 10: 10 Spoke articles generated
    ↓
Step 11C: Keyword review complete
    ↓
Step 11D: Spoke FAQs generated (THIS STEP)
         - Reads Hub FAQs (avoids overlap)
         - Processes 10 Spokes sequentially
         - Outputs 20-30 specific FAQs
    ↓
Step 11E: FAQ cannibalization check (final validation)
    ↓
Step 12: HTML export (adds FAQPage schema to each article)
```

---

## 🔗 Related Steps

- **Requires:** Step 5B (Hub FAQs), Step 10 (Spoke articles), Step 11C (keywords)
- **Feeds:** Step 11E (cannibalization check), Step 12 (schema generation)
- **Validates:** Step 11E confirms no overlap

---

## 🚀 Expected Output

**Input:** 10 Spoke articles + Hub FAQs  
**Output:** 20-30 specific FAQs (2-3 per Spoke)  
**PAA Opportunities:** 20-30 potential featured snippets  
**Cannibalization Risk:** 0% (Hub questions excluded)

**Each Spoke now has quick answers to specific user questions!** 🎯

---

**Next Step:** [STEP_11E_faq_cannibalization.md](STEP_11E_faq_cannibalization.md)

