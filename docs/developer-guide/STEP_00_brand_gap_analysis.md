---
title: BRAND GAP ANALYSIS
order: 1
---

# Step 0: Brand Gap Analysis

**Function:** `step0_brand_gap_analysis()`  
**Type:** Automated  
**Output:** `step0_BRAND_GAP_ANALYSIS.md`

---

## 🤔 Why This Step Exists

**The Problem:**
You're creating content in a void. No idea if you're winning or losing brand visibility. Competitors dominate AI responses while you're invisible.

**The Reality:**
Every time someone asks AI about conversation analytics, competitors get mentioned. Your brand doesn't. That's not a coincidence—it's a content gap.

**The Solution:**
Measure the gap. If you're mentioned in 2% of responses vs competitors at 45%, you know exactly how far behind you are—and what keywords they "own" that you need to steal.

**Without this step:**
- Blind content strategy (guessing what works)
- No benchmark for improvement
- Can't prove content ROI

**With this step:**
- Objective baseline (2.3% mention rate)
- Competitor keyword intel (what to target)
- Clear success metric (improve from 2% → 20%+)

**This step exists because you can't improve what you don't measure. And you can't steal competitor keywords if you don't know which ones they own.**

---

## 📝 Overview

Analyzes how often Solidroad is mentioned vs competitors in AI responses to measure brand visibility gaps.

---

## 🎯 Why It Matters

**Strategic Context:**
If AI models rarely mention Solidroad (e.g., 2% of responses), it signals:
- Low brand authority in training data
- Competitors dominating mindshare
- Content gap opportunities to fill

**SEO Impact:**
Creating content around competitor keywords can "steal" their visibility.

---

## ⚙️ How It Works

### 1. Load CSV Data
```python
df = pd.read_csv(CSV_FILE)
```

### 2. Detect Brand Mentions
```python
brand_keywords = ['solidroad', 'solid road']
df['brand_mentioned'] = df['Response'].apply(has_brand_mention)
```

### 3. Detect Competitor Mentions
```python
competitor_keywords = ['observe.ai', 'maestroqa', 'gong', 'chorus', ...]
df['competitor_mentioned'] = df['Response'].apply(has_competitor_mention)
```

### 4. Calculate Statistics
- Brand-only responses
- Competitor-only responses
- Generic (neither)
- Percentage breakdown

### 5. Extract Competitor Keywords
- Bigrams from competitor responses
- Top 20 keywords they "own"
- Opportunities for Solidroad to target

---

## 📊 Inputs & Outputs

### Inputs:
- **CSV File:** `datasets/conversation-analytics-platform.csv`
- **Columns:** `Response` (required), `Sources` (optional)

### Outputs:
- **`step0_BRAND_GAP_ANALYSIS.md`**
  - Brand mention rate (e.g., 2.3%)
  - Competitor mention rate (e.g., 45.6%)
  - Top 20 competitor keywords
  - Strategic recommendations

---

## 🚨 Quality Gates & Rescue Tasks

### Quality Gate 1: CSV Exists
```python
if not os.path.exists(CSV_FILE):
    → RESCUE_STEP0_CSV_MISSING.md
```

**Rescue Mission:** Find or create dataset  
**Quality Standard:** 1,000+ responses, 100+ call-center QA domain

### Quality Gate 2: CSV Parseable
```python
try:
    df = pd.read_csv(CSV_FILE)
except:
    → RESCUE_STEP0_CSV_CORRUPT.md
```

**Rescue Mission:** Fix CSV format (encoding, delimiters, etc.)

### Soft Check: Response Column
```python
if 'Response' not in df.columns:
    ⚠️ Warning, skips step (non-critical)
```

---

## 🔧 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| CSV not found | Wrong path | Update `CSV_FILE` in script or trigger rescue |
| Permission denied | .env file locked | Already handled - graceful skip |
| No brand mentions | Low visibility | Expected - analysis shows the gap |
| 100% generic | Wrong dataset | Verify CSV is call-center QA domain |

---

## 📈 Example Output

```markdown
## 📊 Brand Visibility

- Total Responses: 820
- Brand Mentioned (Solidroad): 19 (2.3%)
- Competitors Mentioned: 374 (45.6%)
- Generic (No brands): 427 (52.1%)

⚠️ Warning: Low brand visibility (<5%). Focus on improving brand authority.

## 🎯 Top Keywords in Competitor Responses

1. `agent performance` - 245x
2. `quality assurance` - 198x
3. `conversation analytics` - 187x
...
```

---

## 💡 How to Improve

### Enhancement 1: Expand Competitor List
Add more competitors to `competitor_keywords`:
```python
competitor_keywords = [
    'observe.ai', 'maestroqa', 'gong', 'chorus',
    'cresta.ai', 'balto.ai', 'tethr.com', ...  # Add more
]
```

### Enhancement 2: Track Sentiment
Analyze HOW competitors are mentioned (positive vs negative):
```python
# Is competitor mentioned with "best", "top", "leading"?
# Or with "lacks", "missing", "doesn't"?
```

### Enhancement 3: Time-Series Analysis
If CSV has dates, track brand visibility trends over time.

### Enhancement 4: Phrase Analysis
Extract full competitor phrases:
```python
# "Observe.ai is the leader in..."
# "MaestroQA offers..."
# "Unlike Gong, Solidroad..."
```

---

## 🎓 Strategic Insights

### If Brand Rate < 3%:
**Problem:** Solidroad barely exists in AI training data  
**Action:** Create authoritative content targeting competitor keywords

### If Competitor Rate > 40%:
**Opportunity:** High competitive landscape = valuable keywords  
**Action:** Steal their keywords with better content

### Top Competitor Keywords:
**Use these in your article** to capture spillover traffic

---

## 🔗 Related Steps

- **Next:** Step 1 (Content Analysis) - Uses same CSV
- **Informs:** Step 4 (AI Synthesis) - Brand gap insights feed strategy
- **Impact:** Step 5 (Article Generation) - Competitor keywords integrated

---

**File:** `script-docs/STEP_00_brand_gap_analysis.md`


