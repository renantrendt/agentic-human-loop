---
title: WRITING RULES
order: 10
---

# Step 6: Writing Rules

**Function:** `step6_apply_writing_rules()`  
**Type:** ⭐ AI AGENT REQUIRED  
**Output:** `step6_WRITING_RULES_TASK.md` → `step6_ARTICLE_RULES_APPLIED.md`

---

## 🤔 Why This Step Exists

**The Problem:**
The article from Step 5 is good. But it's generic good. It could be from any company. It has AI tells (em dashes, comma splices, "you/your" everywhere). It doesn't sound like Solidroad.

**The Reality:**
Brand voice matters. VPs can spot generic AI content instantly. Em dashes scream "ChatGPT wrote this." "You/your" everywhere feels salesy, not strategic. Healthcare mentions? Wrong vertical—Solidroad is sales/support, not healthcare.

**The Solution:**
Apply 15 surgical brand rules. Remove em dashes. Fix comma splices. Replace "you" with "teams." Cut healthcare mentions. Add contractions. Make it sound unmistakably like Solidroad wrote it.

**Without this step:**
- Generic AI voice (could be anyone's content)
- Reader skepticism (they know AI wrote it)
- Brand misalignment (doesn't match company voice)

**With this step:**
- Solidroad voice throughout
- No AI tells (passes human writing test)
- Brand-aligned language (our positioning clear)

**This step exists because good content isn't enough. It needs to sound like US. This is the difference between content and SOLIDROAD content.**

---

## 📝 Overview

Applies Solidroad's 15 brand writing rules to align the article with company voice, tone, and style guidelines.

**Transforms good content into SOLIDROAD content.**

---

## 🎯 Why It Matters

**Generic article** = Could be from any company  
**Solidroad article** = Unmistakably ours

**What it fixes:**
- AI writing patterns (em dashes, comma splices)
- Buyer POV violations ("you/your" → "teams/leaders")
- Healthcare mentions (avoid per brand rules)
- Generic phrasing → Solidroad-specific voice

**Brand alignment = Authenticity = Trust = Conversions**

---

## ⚙️ How It Works

### 1. Load Writing Rules
```python
writing_rules_path = 'brand-context/rule_writing.ts'
writing_rules_content = read_file(writing_rules_path)
```

**15 Rules Include:**
- No em dashes (use colons/parentheses)
- No comma splices (use periods/semicolons)
- Avoid "you/your" (use "teams", "leaders")
- No healthcare mentions (per vertical scope)
- Active voice over passive
- Short paragraphs (3-4 sentences max)
- Contractions encouraged (you're, don't, can't)
- etc.

### 2. Quick Validation Scan
```python
# Check 1: Comma splices
comma_splice_pattern = r'(\w+),\s+(it\'s|they\'re|we\'re)'
splices = re.findall(comma_splice_pattern, article_content)

# Check 2: Em dashes
em_dash_count = article_content.count('—')

# Check 3: "You/your" overuse
you_matches = re.findall(r'\b(you|your)\b', article_content)

# Check 4: Healthcare mentions
if 'healthcare' in article_content.lower() or 'hipaa' in content:
```

### 3. Create AI Agent Task
Generates `step6_WRITING_RULES_TASK.md` with:
- Full writing rules (all 15)
- Quick validation results (issues found)
- Instructions to apply rules surgically
- Output filename

### 4. Signal AI Agent
```
🤖 AGENT_TASK_READY: step6_WRITING_RULES_TASK.md
📋 OUTPUT_FILE: step6_ARTICLE_RULES_APPLIED.md
```

### 5. Validate When Complete
Checks if `step6_ARTICLE_RULES_APPLIED.md` exists

---

## 📊 The 15 Writing Rules (Summary)

### Grammar & Style:
1. **No em dashes** (—) → Use colons or parentheses
2. **No comma splices** → Use periods or semicolons
3. **Active voice** → Passive only when necessary
4. **Varied sentence length** → Mix short punchy + longer flowing

### Voice & Tone:
5. **Conversational expert** → Use contractions (you're, don't)
6. **Avoid buzzwords** → Say "training" not "upskilling"
7. **Simple language** → Explain like to a colleague
8. **Relatable metaphors** → Sparingly, when they add value

### Brand Specifics:
9. **No "you/your" overuse** → Use "teams", "leaders", "organizations"
10. **Avoid healthcare** → Use "regulated industries" instead
11. **No IT jargon** → Keep it operational (VP audience)
12. **Solidroad positioning** → "AI-native" not "AI-powered"

### Structure:
13. **Short paragraphs** → 3-4 sentences max
14. **No link clustering** → Distribute throughout
15. **Scannable** → Use bullets, headers, bold

---

## 🚨 AI Agent Responsibilities

### Your Mission:

**1. Read Writing Rules Completely**
- All 15 rules in `brand-context/rule_writing.ts`
- Understand rationale for each
- Note examples of violations

**2. Review Quick Validation**
- Comma splices found? (how many)
- Em dashes present? (count)
- "You/your" overused? (threshold: >10)
- Healthcare mentioned? (should be 0)

**3. Apply Rules Surgically**
- Fix each violation
- Maintain article meaning
- Keep formatting intact (headings, bullets, links)
- Don't over-correct (some "you" is okay in quotes)

**4. Validate Before Saving**
- Re-run quick validation mentally
- Check brand voice sounds authentic
- Ensure readability maintained

**5. Save Result**
- File: `step6_ARTICLE_RULES_APPLIED.md`
- Same structure as input
- Rules applied throughout

---

## 🚨 Quality Gates

### Pre-Application Validation:
```python
if not article_file or not os.path.exists(article_file):
    ⚠️ Skip step (article doesn't exist yet)
```

### Post-Application (Manual):
AI agent should verify:
- [ ] ✅ All em dashes removed
- [ ] ✅ Comma splices fixed
- [ ] ✅ "You/your" reduced to <10 instances
- [ ] ✅ No healthcare mentions
- [ ] ✅ Active voice dominant
- [ ] ✅ Contractions used naturally
- [ ] ✅ Solidroad voice recognizable

---

## 🔧 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Rules file not found | Missing brand-context/ | Non-critical, skips step |
| Over-correction | Too aggressive editing | Apply rules surgically, not globally |
| Lost meaning | Changed too much | Maintain original insights |
| Sounds robotic | Removed all conversational tone | Keep contractions, flow |

---

## 📈 Before & After Examples

### Example 1: Em Dash Removal

**Before:**
```
Conversation analytics platforms—especially AI-powered ones—can transform QA.
```

**After:**
```
Conversation analytics platforms (especially AI-powered ones) can transform QA.
```

### Example 2: Comma Splice Fix

**Before:**
```
The platform analyzes calls, it provides insights in real-time.
```

**After:**
```
The platform analyzes calls and provides insights in real-time.
```
or
```
The platform analyzes calls. It provides insights in real-time.
```

### Example 3: Buyer POV Adjustment

**Before:**
```
When you implement conversation analytics, you'll see immediate ROI in your QA processes.
```

**After:**
```
When teams implement conversation analytics, leaders see immediate ROI in QA processes.
```

### Example 4: Healthcare Removal

**Before:**
```
Conversation analytics works for healthcare, financial services, and retail.
```

**After:**
```
Conversation analytics works for regulated industries, financial services, and retail.
```

---

## 💡 How to Improve

### Enhancement 1: Automated Rule Checker
Run regex patterns to auto-detect violations:
```python
violations = {
    'em_dashes': content.count('—'),
    'comma_splices': len(re.findall(comma_splice_pattern, content)),
    'you_count': len(re.findall(r'\byou\b', content)),
    'healthcare': 'healthcare' in content.lower()
}

if any(violations.values()):
    create_detailed_fix_list()
```

### Enhancement 2: Voice Consistency Score
Measure adherence to brand voice:
```python
# Check for Solidroad signature phrases:
signature_phrases = [
    "this call may be recorded",
    "insight-to-action gap",
    "ai-native",
    "ex-intercom"
]

brand_voice_score = sum(phrase in content for phrase in signature_phrases)
```

### Enhancement 3: Readability Validation
```python
from textstat import flesch_reading_ease

score = flesch_reading_ease(content)
# Target: 60-70 (Standard, VP-readable)
```

### Enhancement 4: Tone Analysis
Check for unwanted patterns:
```python
hype_words = ['revolutionary', 'game-changing', 'disrupting']
corporate_speak = ['leverage', 'synergy', 'best-in-class']

if any(word in content.lower() for word in hype_words + corporate_speak):
    ⚠️ Warning: Tone violation
```

---

## 🎓 Strategic Rationale

### Why These Rules Matter:

**Rule: No em dashes**
- Em dashes = AI writing tell
- Authentic writing uses colons/parentheses
- Readers subconsciously detect AI

**Rule: Avoid "you/your"**
- B2B audience = teams, not individuals
- "You" feels salesy
- "Teams" feels strategic

**Rule: No healthcare**
- Solidroad focuses on sales/support
- Healthcare is regulated niche (different needs)
- Keeps brand positioning clear

**Rule: Conversational expert**
- VPs want peer-level discussion
- Not marketing fluff
- Not academic jargon
- Professional coffee conversation

---

## 🔗 Data Flow

```
Step 5: Generated article (raw)
  ↓
Step 6: Load 15 writing rules
  ↓
Quick validation (detect violations)
  ↓
AI Agent applies rules surgically
  ↓
Article aligned with Solidroad voice
  ↓
Step 7: Add internal links
```

**Input:** Good article  
**Output:** Solidroad article

---

## 📋 AI Agent Workflow

**Phase 1: Preparation**
1. Read `step6_WRITING_RULES_TASK.md`
2. Review all 15 rules
3. Note quick validation issues

**Phase 2: Application**
4. Go through article section by section
5. Apply relevant rules to each paragraph
6. Fix violations while preserving meaning

**Phase 3: Validation**
7. Re-read for brand voice consistency
8. Check if sounds authentic (not robotic)
9. Verify all headings/links intact

**Phase 4: Delivery**
10. Save to `step6_ARTICLE_RULES_APPLIED.md`

---

## 🔗 Related Steps

- **Requires:** Step 5 (generated article)
- **Feeds:** Step 7 (internal links), Step 8 (citations)
- **Optional:** Can skip if rule file missing (degrades quality)

---

**This step ensures every article sounds unmistakably like Solidroad.** 🎯

**Next:** [STEP_07_internal_links.md](STEP_07_internal_links.md)


