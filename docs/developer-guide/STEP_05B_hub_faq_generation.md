---
title: HUB FAQ GENERATION
order: 9.1
---

# Step 5B: Hub FAQ Generation

**Function:** `step5b_generate_hub_faqs()`  
**Type:** ⭐ AI AGENT REQUIRED  
**Output:** `step5b_HUB_FAQ_TASK.md` → `step5b_HUB_FAQS.md`

---

## 🤔 Why This Step Exists

**The Problem:**
Hub articles often have thin content — they're comprehensive overviews that link to deeper content. Google sees a page with lists of links and thinks "meh, low value." FAQs add the text depth Google needs to rank the page.

**The Reality:**
Not all FAQs are created equal. Copy-pasting the same "What is [brand]?" question across 50 pages creates boilerplate content. Google ignores this at best, penalizes at worst. Hub FAQs must be **broad, category-level questions** — not implementation details.

**The Solution:**
Generate 3-5 unique FAQs for the Hub article immediately after it's created. These FAQs answer "why" and "what" questions — definitional, category-wide. Specific "how-to" questions belong in Spokes (Step 11D), not here.

**Without this step:**
- Hub has thin content (just links)
- No FAQPage schema = no rich snippets
- Miss "People Also Ask" opportunities for broad queries

**With this step:**
- Hub gains 300-500 words of high-value text
- FAQPage schema enables rich snippets
- Broad questions answered once, in the right place
- Spoke FAQs (Step 11D) can safely go deep without overlap

**This step exists because Hub FAQs are different from Spoke FAQs. Hubs answer "what is X?" — Spokes answer "how do I do Y?" Mixing them creates cannibalization.**

---

## 📝 Overview

Generates 3-5 **broad, definitional FAQs** for the Hub article created in Step 5. These FAQs add text depth and target category-level "People Also Ask" queries.

**Timing:** Immediately after Step 5 (Hub article exists)  
**Focus:** One article, one task, 3-5 FAQs

---

## 🎯 Why It Matters

### SEO Impact:
- **Text depth:** Hubs often lack word count (link lists don't count)
- **Rich snippets:** FAQPage schema = appear in Google's FAQ boxes
- **PAA targeting:** Broad questions like "Why is budgeting important?"

### Content Strategy Impact:
- **Sets the boundary:** Hub FAQs are broad → Spoke FAQs can go specific
- **Prevents cannibalization:** "What is X?" answered once, in the Hub
- **Consistent voice:** Same AI agent, same brand context, same session

### User Impact:
- Quick answers for broad questions
- Clear path to Spokes for specific questions
- Professional, authoritative Hub page

---

## ⚙️ How It Works

### 1. Wait for Hub Article
```python
# Step 5 must complete first
hub_article = read_file('step5_GENERATED_ARTICLE.md')
if not hub_article:
    return "Waiting for Step 5..."
```

### 2. Load Context
```python
# Brand context (avoid generic questions)
brand_context = read_file('brand-context/solidroad')

# Step 4 synthesis (keyword focus)
synthesis = read_file('step4_AGENT_SYNTHESIS.md')

# Step 1 data (what people actually ask)
step1_data = read_file('step1_FOR_AGENT_ANALYSIS.md')
```

### 3. Create AI Agent Task
```python
task = f"""
# Hub FAQ Generation Task

## Context
Hub Article: {hub_title}
Primary Keyword: {primary_keyword}

## Your Mission
Generate 3-5 FAQs for this Hub article.

## FAQ Requirements

### ✅ DO: Broad, Definitional Questions
- "What is [topic]?"
- "Why is [topic] important?"
- "What are the benefits of [topic]?"
- "Who needs [topic]?"

### ❌ DON'T: Specific, How-To Questions
- "How do I set up [feature]?" → Belongs in Spoke
- "What's the best [tool] for [task]?" → Belongs in Spoke
- "How much does [brand] cost?" → Belongs on pricing page

### ❌ DON'T: Brand-Specific Questions (Unless Hub IS about brand)
- "Is [brand] free?" → Product page
- "How do I cancel [brand]?" → Support page

## Output Format

```markdown
## Frequently Asked Questions

### [Question 1]?
[Answer: 2-3 sentences, factual, links to Spokes if relevant]

### [Question 2]?
[Answer: 2-3 sentences]

... (3-5 total)
```

## Quality Checklist
- [ ] 3-5 FAQs (no more, no less)
- [ ] All questions are broad/definitional
- [ ] No specific how-to questions
- [ ] Each answer is 2-3 sentences
- [ ] Answers can reference Spokes (coming later) with placeholders
"""
```

### 4. Wait for AI Agent
```
🤖 AGENT_TASK_READY: step5b_HUB_FAQ_TASK.md
📋 OUTPUT_FILE: step5b_HUB_FAQS.md
⏸️ Pipeline paused...
```

### 5. Validate FAQs
```python
faqs = read_file('step5b_HUB_FAQS.md')

# Count FAQs (### headings)
faq_count = faqs.count('### ')
if faq_count < 3 or faq_count > 5:
    trigger_rescue("FAQ count must be 3-5")

# Check for how-to questions (red flag)
how_to_patterns = ['how do i', 'how to', 'step-by-step', 'tutorial']
for pattern in how_to_patterns:
    if pattern in faqs.lower():
        trigger_rescue(f"Found specific question: {pattern}")
```

---

## 📊 Inputs & Outputs

### Inputs:
- `step5_GENERATED_ARTICLE.md` — The Hub article
- `brand-context/solidroad` — Brand positioning
- `step4_AGENT_SYNTHESIS.md` — Keyword strategy
- `step1_FOR_AGENT_ANALYSIS.md` — N-gram data (what people ask)

### Outputs:
- `step5b_HUB_FAQ_TASK.md` — Task file for AI agent
- `step5b_HUB_FAQS.md` — 3-5 FAQs in markdown format

### Output Format:
```markdown
## Frequently Asked Questions

### What is conversation analytics?
Conversation analytics is the process of analyzing customer interactions 
(calls, chats, emails) to extract insights about agent performance, 
customer sentiment, and service quality. Unlike traditional QA that samples 
1-2% of calls, modern platforms analyze 100% of interactions.

### Why is conversation analytics important for call centers?
Call centers generate thousands of interactions daily, but most insights 
are lost without systematic analysis. Conversation analytics surfaces 
patterns in customer complaints, agent behaviors, and process gaps that 
manual review would miss.

### Who benefits from conversation analytics?
QA managers, team leads, and operations directors benefit most. QA managers 
get automated scoring, team leads get coaching insights, and directors get 
visibility into trends across the entire organization.
```

---

## 🚨 Quality Gates

### Gate 1: FAQ Count (3-5)
```python
if faq_count < 3:
    → RESCUE: "Too few FAQs - add more broad questions"
if faq_count > 5:
    → RESCUE: "Too many FAQs - Hub should stay focused"
```

### Gate 2: No How-To Questions
```python
how_to_flags = ['how do i', 'how to', 'step by step', 'tutorial', 'guide to']
if any(flag in faq_text.lower() for flag in how_to_flags):
    → RESCUE: "Found specific question - move to Spoke FAQ"
```

### Gate 3: Answer Length
```python
for answer in answers:
    if len(answer.split()) < 20:
        → RESCUE: "Answer too short - expand to 2-3 sentences"
    if len(answer.split()) > 100:
        → RESCUE: "Answer too long - keep brief, link to Spoke"
```

---

## 🔧 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Questions too specific | Agent mixed Hub/Spoke intent | Re-read task, emphasize "broad only" |
| Generic questions | Didn't use brand context | Reference specific industry/use case |
| Too many FAQs | Agent over-delivered | Keep best 5, save others for Spokes |
| Answers too long | Trying to be comprehensive | Brief answer + "Learn more in [Spoke]" |

---

## 💡 Examples

### ✅ GOOD Hub FAQs (Broad)

**Hub: "Conversation Analytics Platforms"**

1. "What is conversation analytics?" — Definitional ✓
2. "Why do call centers need conversation analytics?" — Category-level ✓
3. "What's the difference between conversation analytics and speech analytics?" — Comparison ✓
4. "Who uses conversation analytics platforms?" — Audience ✓

### ❌ BAD Hub FAQs (Too Specific)

1. "How do I set up Solidroad?" — Product-specific, belongs on docs
2. "What's the best conversation analytics tool for small teams?" — Belongs in Spoke
3. "How much does conversation analytics cost?" — Pricing page
4. "How do I cancel my subscription?" — Support page

---

## 🎓 AI Agent Checklist

Before saving FAQs:
- [ ] ✅ Read Hub article completely
- [ ] ✅ Read brand context
- [ ] ✅ 3-5 FAQs only (not more)
- [ ] ✅ All questions are broad/definitional
- [ ] ✅ No "how to" or step-by-step questions
- [ ] ✅ Each answer is 2-3 sentences
- [ ] ✅ Answers are factual, not salesy
- [ ] ✅ Can reference future Spokes with placeholders

---

## 🔗 Data Flow

```
Step 5: Hub article generated
    ↓
Step 5B: Hub FAQs generated (THIS STEP)
    ↓
Step 6: Writing rules applied to Hub + FAQs
    ↓
... (Steps 7-10A) ...
    ↓
Step 11D: Spoke FAQs generated (reads Hub FAQs to avoid overlap)
    ↓
Step 11E: FAQ cannibalization check (final validation)
    ↓
Step 12: HTML export (adds FAQPage schema)
```

---

## 🔗 Related Steps

- **Requires:** Step 5 (Hub article must exist)
- **Feeds:** Step 6 (writing rules), Step 11D (Spoke FAQs reference these), Step 12 (schema)
- **Validates:** Step 11E (cannibalization check)

---

## 🚀 Why Separate from Step 5?

**Could we just add FAQs in Step 5?**

Technically yes, but:
1. **Focus:** Step 5 is already complex (2,000 words, brand voice, data integration)
2. **Quality:** Adding FAQs to Step 5 prompt = agent rushes them
3. **Flexibility:** Separate step = can iterate on FAQ strategy independently
4. **Debugging:** If FAQs are bad, you know exactly where to fix

**One task, one focus, one output.**

---

**Next Step:** [STEP_06_writing_rules.md](STEP_06_writing_rules.md)

