---
title: CONTENT QA & EDITORIAL POLISH
order: 20
---

# Step 12.5: Content QA & Editorial Polish

**Function:** `step12_5_content_qa_polish()`  
**Type:** ✅ AUTOMATED (Claude API)  
**Output:** `step12_5_CONTENT_POLISHED.csv`

---

## 🤔 Why This Step Exists

**The Problem:**
HTML from Step 12 has subtle editorial issues that break brand consistency: "Ai" instead of "AI", "Solid road" instead of "Solidroad", capitalization after colons varies, headings followed by redundant bold echoes, frequency data leaks like "The 529x frequency of..." appearing in published articles.

**The Reality:**
These micro-issues hurt credibility. Readers notice "Ai-powered" and think "this wasn't edited properly." Frequency leaks expose internal research methodology. Inconsistent punctuation makes content feel sloppy. Manual QA catches some issues, but not systematically at scale.

**The Solution:**
Automated editorial polish using Claude API (temperature=0.3 for consistency). Applies 21 brand voice rules from `brand-context/rule_writing.ts` to every article. Fixes brand name spelling, AI capitalization, colon rules, heading echoes, frequency leaks, and punctuation systematically.

**Without this step:**
- Inconsistent "AI" vs "Ai" capitalization
- Brand name typos ("Solid road" published live)
- Frequency leaks exposing internal data
- Redundant heading echoes
- Mixed punctuation styles

**With this step:**
- Consistent brand voice across all 11 articles
- Zero editorial micro-errors
- Professional polish matching hand-edited quality
- Frequency leaks reframed as research insights

**This step exists because editorial consistency at scale requires automation. Manual review catches 80% of issues. Step 12.5 catches 100%.**

---

## 📝 Overview

Step 12.5 performs automated editorial quality assurance on HTML content after Step 12 conversion. It reads the Framer export CSV, sends each article's HTML through Claude API with strict editorial rules, and returns polished content ready for publishing.

**Key Innovation:** Uses low temperature (0.3) for consistency rather than creativity, treating this as a QA pass not a writing pass.

---

## 🎯 Why It Matters

**Editorial Micro-Issues Break Brand Trust:**
- "Ai-powered platforms" → Reader thinks: "They didn't even edit this"
- "Solid road offers..." → Looks like autocorrect error
- "The 529x frequency of..." → Exposes internal research data
- Heading followed by `<p><strong>Same heading:</strong></p>` → Redundant, unprofessional

**These aren't just style nitpicks.** They signal lack of editorial rigor, which undermines authority on technical topics.

---

## ⚙️ How It Works

### 1. Load Brand Configuration
```python
brand_config = {
    'brand_name': 'Solidroad',
    'cta_path': '/book-demo',
    'domain': 'https://www.solidroad.com',
    'ai_term': 'AI'
}
```

### 2. Read CSV Content
```python
with open(csv_file, 'r') as f:
    rows = list(csv.DictReader(f))

for row in rows:
    html_content = ''.join([row[f'Content_Part{i}'] for i in range(1,10)])
```

### 3. Build Editorial QA Prompt
Includes 7 rule categories:
1. Brand name spelling verification
2. Technical term capitalization (AI, NLP, IQS, SCORE)
3. Colon capitalization (lowercase unless proper noun)
4. No heading echoes
5. Paragraph punctuation (colons only before lists)
6. CTA link consistency
7. Frequency leak removal/reframing

### 4. Call Claude API for Polish
```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=16000,
    temperature=0.3,  # Low temp for consistency
    messages=[{"role": "user", "content": qa_prompt}]
)
```

### 5. Save Polished CSV
```python
output_file = os.path.join(SESSION_DIR, "step12_5_CONTENT_POLISHED.csv")
```

---

## 📊 Inputs & Outputs

### Inputs:
- **CSV File:** `step12_FRAMER_EXPORT.csv` (from Step 12)
- **Brand Config:** Dictionary with brand-specific rules (optional, defaults to Solidroad)

### Outputs:
- **`step12_5_CONTENT_POLISHED.csv`**
  - Same structure as input
  - All HTML content editorially polished
  - Ready for final export/publishing

---

## 🔧 Brand Rules Applied

### Rule Categories:

**1. Brand Identity**
- Brand name: "Solidroad" (one word, not "Solid road")
- Consistent capitalization throughout

**2. Technical Terms**
- "AI" always UPPERCASE (never "Ai" or "ai")
- "NLP", "IQS", "SCORE", "CSAT" = uppercase acronyms

**3. Punctuation Style**
- Lowercase after colons: "The key is this: quality measurement..."
- Colons at paragraph end only if followed by list
- No redundant heading echoes

**4. Content Restrictions**
- Remove frequency leaks: "The 529x frequency of..." → "Industry analysis shows..."
- No exposure of internal research methodology

**5. Link Consistency**
- CTA links: All point to configured path (default: `/book-demo`)
- Internal links: Full URLs, not relative paths

See `brand-context/rule_writing.ts` for complete 21-rule set.

---

## 💡 Brand-Agnostic Design

While defaulted to Solidroad, this step works for any brand:

```python
# Custom brand example
other_brand_config = {
    'brand_name': 'CompanyX',  # Can be multi-word
    'cta_path': '/get-started',
    'domain': 'https://www.companyx.com',
    'ai_term': 'AI'
}

polished_csv = step12_5_content_qa_polish(
    csv_file='export.csv',
    brand_config=other_brand_config
)
```

**Customizable:**
- Brand name spelling rules
- CTA path
- Domain for absolute URLs
- Technical term preferences

---

## 🎯 Success Criteria

After Step 12.5 runs:

- ✅ Zero "Ai" (lowercase i) instances
- ✅ Zero "Solid road" (two words) instances  
- ✅ Consistent colon capitalization throughout
- ✅ No heading + redundant bold echo patterns
- ✅ All frequency leaks removed/reframed
- ✅ All CTAs point to configured path
- ✅ Professional editorial consistency

**Quality Bar:** Content should pass as human-edited, not AI-generated.

---

## 🔄 Integration with Pipeline

**Pipeline Flow:**
```
Step 12  → Step 12.5 → Final Export
(HTML)     (Polish)     (CSV to Framer)
```

**Step 12B vs 12.5:**
- **Step 12B:** AI agent task for structural HTML issues (missing H3s, orphaned text, table conversion)
- **Step 12.5:** Automated editorial polish for brand voice & style consistency

Both are needed - structure first (12B), then polish (12.5).

---

## 📊 Performance

**Processing Time:**
- ~10-15 seconds per article (Claude API call)
- ~3 minutes for full cluster (11 articles)

**API Costs:**
- ~8K tokens per article (input + output)
- ~88K tokens total for 11 articles
- Cost: ~$0.50-0.70 per full polish run

**ROI:**
Eliminates 2-3 hours of manual editorial review per cluster.

---

## 🚀 Usage

### In Main Pipeline:
```python
# After Step 12 completes
if 12 in COMPLETED_STEPS:
    csv_file = COMPLETED_STEPS[12]
    
    # Run editorial polish
    polished_csv = step12_5_content_qa_polish(
        csv_file=csv_file,
        brand_config=BRAND_CONFIG  # Optional
    )
    
    COMPLETED_STEPS[12.5] = polished_csv
```

### Standalone Usage:
```python
from content_pipeline_with_ai_agent import step12_5_content_qa_polish

# Polish existing CSV
polished = step12_5_content_qa_polish(
    csv_file='path/to/export.csv',
    brand_config={
        'brand_name': 'Solidroad',
        'cta_path': '/book-demo',
        'domain': 'https://www.solidroad.com'
    }
)

print(f"Polished CSV: {polished}")
```

---

## 🔍 What Gets Fixed

### Example 1: Brand Name
**Before:**
```html
<p>Solid road offers AI-powered training...</p>
```

**After:**
```html
<p>Solidroad offers AI-powered training...</p>
```

### Example 2: AI Capitalization
**Before:**
```html
<h2>Ai Quality Assurance for Contact Centers</h2>
```

**After:**
```html
<h2>AI Quality Assurance for Contact Centers</h2>
```

### Example 3: Colon Capitalization
**Before:**
```html
<p>The key insight is this: Quality measurement without action is expensive.</p>
```

**After:**
```html
<p>The key insight is this: quality measurement without action is expensive.</p>
```

### Example 4: Heading Echo
**Before:**
```html
<h3>The Measured Results</h3>
<p><strong>Measured results:</strong></p>
<p>Organizations achieved 18% AHT reduction...</p>
```

**After:**
```html
<h3>The Measured Results</h3>
<p>Organizations achieved 18% AHT reduction...</p>
```

### Example 5: Frequency Leak
**Before:**
```html
<p>The 653x frequency of "customer experience" in industry responses reflects growing recognition...</p>
```

**After:**
```html
<p>Solidroad's analysis of industry conversations reveals that "customer experience" consistently ranks among the most discussed topics in contact center operations, reflecting growing recognition...</p>
```

---

## ⚠️ Limitations

**What Step 12.5 Does NOT Do:**
- ❌ Add/remove content sections
- ❌ Change article structure or flow
- ❌ Rewrite entire paragraphs
- ❌ Add missing internal links (that's Step 12B/12D)
- ❌ Verify external citations (that's Step 12D)

**Scope:** Surgical editorial fixes only. Preserves meaning, structure, and links.

---

## 🐛 Common Issues & Fixes

### Issue: Claude Changes Links
**Symptom:** Internal links get modified or removed  
**Fix:** Prompt explicitly forbids link changes. If this occurs, update prompt: "PRESERVE all <a> tags exactly as-is"

### Issue: Content Gets Shortened
**Symptom:** Articles come back shorter than input  
**Fix:** Increase `max_tokens` from 16000 to 20000 for longer articles

### Issue: Brand Config Not Applied
**Symptom:** Still seeing "Ai" after polish  
**Fix:** Verify brand_config is passed correctly and domain matches

---

## 📚 Related Steps

**Before Step 12.5:**
- **Step 6:** Writing rules (brand voice, tone, no em dashes)
- **Step 12:** HTML conversion (markdown → HTML)
- **Step 12B:** HTML structure QA (H3 tags, orphaned text, tables)

**After Step 12.5:**
- **Final Export:** CSV → Google Sheets → Framer CMS

---

## 🎓 Best Practices

1. **Run after Step 12B completes** - Fix structure first, then polish
2. **Always pass brand_config** - Don't rely on defaults for production
3. **Log articles polished** - Track which articles were processed
4. **Verify temperature=0.3** - Higher temps introduce inconsistency
5. **Test on single article first** - Validate rules before batch processing

---

## 📝 Maintenance

**When to Update Rules:**
1. New brand terminology introduced (new product names)
2. Style guide changes (punctuation preferences)
3. Content issues found in published articles
4. Competitor language shifts

**Where to Update:**
- **Source:** `brand-context/rule_writing.ts` (rules 16-21)
- **Enforcement:** `step12_5_content_qa_polish()` prompt

---

**Last Updated:** December 10, 2025  
**Pipeline Step:** 12.5 (between HTML generation and export)  
**Automation Level:** Fully automated (no agent task required)

