---
title: SCRAPING ANALYSIS
order: 7
---

# Step 3: Scraping Analysis

**Function:** `step3_scraping_analysis()`  
**Type:** Automated  
**Output:** `step3_FOR_AGENT_ANALYSIS.md`

---

## 🤔 Why This Step Exists

**The Problem:**
You have 8 competitor articles scraped (9KB-10KB each). That's 80KB of raw text. What do you DO with it? How do you turn data into strategy?

**The Reality:**
Patterns exist in that content. 8/10 competitors cover feature comparisons. 6/10 have pricing tables. Only 2/10 mention automated remediation. That last one? That's your differentiation opportunity.

**The Solution:**
Analyze all scraped content for common themes, tone patterns, structure, and—most importantly—gaps. What do they ALL cover (table stakes)? What does NOBODY cover (blue ocean)?

**Without this step:**
- Raw scraped files sit unused (wasted effort)
- No competitive positioning strategy
- Miss the white space opportunities

**With this step:**
- Common themes identified (you must cover these)
- Content gaps revealed (your differentiation angle)
- Competitive blueprint complete

**This step exists because having competitor data isn't enough. You need to extract strategy from it. What to emulate. What to avoid. What to own.**

---

## 📝 Overview

Analyzes the full content of scraped competitor articles (from Step 2B) to identify themes, tone, structure, and content gaps.

**Transforms raw scraped data into actionable competitive intelligence.**

---

## 🎯 Why It Matters

**What it reveals:**
- **Content themes:** What topics do winning articles cover?
- **Tone & style:** Formal vs conversational? Technical vs business?
- **Structure patterns:** How do they organize content?
- **Unique angles:** What perspectives do they take?
- **Content gaps:** What's missing that we could add?

**Strategic value:**
This is your competitive blueprint:
- What to emulate (proven patterns)
- What to differentiate (unique angles)
- What to avoid (overused tactics)

---

## ⚙️ How It Works

### 0. Wait for Step 2B Completion (NEW - 2025-11-21)

**Dependency Check:**
```python
scraped_files = [f for f in Path(current_scraped_dir).glob("*.txt") 
                 if f.name != "SCRAPING_COMPLETE.txt"]
completion_marker = os.path.join(current_scraped_dir, "SCRAPING_COMPLETE.txt")

min_required = 5

if len(scraped_files) < min_required and not os.path.exists(completion_marker):
    log("⚠️  Waiting for Step 2B AI agent to complete scraping task")
    return None, {'waiting_for_step2b': True}
```

**Resume Conditions:**
- 5+ scraped files exist, OR
- `SCRAPING_COMPLETE.txt` marker exists

**Why this matters:**  
Step 3 won't analyze an empty directory. It waits for Step 2B AI agent to finish scraping before proceeding.

**What you'll see:**
```
[HH:MM:SS] STEP 3: SCRAPING ANALYSIS
[HH:MM:SS] ⚠️  Insufficient scraped data: 0/5 files
[HH:MM:SS]    Waiting for Step 2B AI agent to complete scraping task
[HH:MM:SS]    Task file should be: step2b_BROWSER_SCRAPING_TASK.md
```

### 1. Locate Scraped Content Directory
```python
current_scraped_dir = os.path.join(SESSION_DIR, "scraped_content")
```

### 2. Load All Scraped Files
```python
scraped_files = list(Path(current_scraped_dir).glob("*.txt"))
# Excludes SCRAPING_COMPLETE.txt marker file
```

### 3. Parse File Format
```python
# Custom format from Step 2B:
# URL: [url]
# Domain: [domain]
# Scraped: [date]
# Word Count: [count]
# ----------------
# [FULL CONTENT]
```

### 4. Extract Metadata
```python
for filepath in scraped_files:
    content = read_file(filepath)
    
    # Parse header
    url = extract_line_starting_with('URL:')
    domain = extract_line_starting_with('Domain:')
    
    # Find content after separator line
    actual_content = content.split('---...')[1]
    
    competitor_data.append({
        'domain': domain,
        'url': url,
        'word_count': len(actual_content.split()),
        'content_preview': actual_content[:2000]
    })
```

### 5. Create Analysis Report
```markdown
## 📚 Scraped Competitor Content

Total competitors scraped: 8

### 1. observe.ai
- Word count: 2,850 words
- Content preview: [first 2000 chars]

### 2. maestroqa.com
- Word count: 2,340 words
- Content preview: [first 2000 chars]

...

## ❓ FOR CLAUDE TO ANALYZE:
1. What themes do competitors focus on?
2. What tone/style do they use?
3. How do they structure content?
4. What unique angles do they take?
5. What content gaps exist?
```

---

## 📊 Inputs & Outputs

### Inputs:
- `scraped_content/` directory (from Step 2B)
- Text files with full competitor articles

### Outputs:
**`step3_FOR_AGENT_ANALYSIS.md`:**
- Competitor count
- Per-competitor breakdown
- Content previews (first 2,000 chars)
- Analysis questions

**Data returned:**
```python
{
    'competitor_count': 8,
    'competitors': [
        {
            'domain': 'observe.ai',
            'url': '...',
            'word_count': 2850,
            'content_length': 15420,
            'content_preview': '...'
        },
        ...
    ]
}
```

---

## 🚨 Quality Considerations

### Not a Hard Blocker:
```python
if not os.path.exists(current_scraped_dir):
    ⚠️ Warning, returns None (non-critical)
```

**Why:** 
- Competitor analysis enhances quality but isn't mandatory
- Could proceed with just Step 1 keyword data
- However, quality will be lower without competitor intel

**Best practice:** Always run Step 2B successfully before Step 3

---

## 🔧 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| No scraped files | Step 2B failed or skipped | Re-run Step 2B with network access |
| Empty content | Parsing error | Check file format matches expected |
| Gibberish preview | Encoding issue | UTF-8 should handle this |
| Low competitor count | Low scraping success in Step 2B | Trigger rescue task in Step 2B |

---

## 📈 What AI Agent Analyzes

### Theme Analysis:
**Question:** What topics do competitors focus on?

**Example findings:**
- 8/10 articles cover "platform selection criteria"
- 6/10 include comparison tables
- 4/10 discuss implementation challenges
- Only 2/10 mention automated remediation ← **Gap!**

### Tone Analysis:
**Question:** What writing style do they use?

**Example findings:**
- Mostly formal, feature-list style
- Heavy use of "you" (Buyer POV)
- Generic advice (not industry-specific)
- Little differentiation between articles

### Structure Analysis:
**Question:** How do they organize content?

**Common pattern:**
1. What is X?
2. Why X matters
3. Key features
4. Platform comparison
5. How to choose
6. Conclusion

### Gap Analysis:
**Question:** What's missing?

**Opportunities:**
- No one discusses "insight-to-action gap"
- Light on implementation details
- Missing: Training/remediation aspects
- Weak on ROI quantification

---

## 💡 How to Improve

### Enhancement 1: Automated Theme Extraction
Use NLP to identify topics:
```python
from sklearn.feature_extraction.text import TfidfVectorizer

tfidf = TfidfVectorizer(max_features=20)
themes = tfidf.fit_transform([comp['content'] for comp in competitors])

# Top themes across all competitors
common_themes = tfidf.get_feature_names_out()
```

### Enhancement 2: Sentiment Analysis
Detect tone computationally:
```python
from textblob import TextBlob

for competitor in competitors:
    sentiment = TextBlob(competitor['content']).sentiment
    # Polarity: Neutral, positive, or negative?
    # Subjectivity: Factual vs opinion-based?
```

### Enhancement 3: Section Extraction
Parse H2 headings from scraped content:
```python
h2_headings = re.findall(r'##\s+([^\n]+)', content)
# See what section titles competitors use
# Pattern: Most use "Key Features", "Benefits", "Comparison"
```

### Enhancement 4: Unique Phrase Detection
Find phrases only 1-2 competitors use:
```python
# These are differentiation opportunities
# If only Observe.ai mentions "automated QA" → we should too
```

---

## 🎓 Competitive Intelligence Framework

### Content Audit Matrix:

| Competitor | Word Count | Themes | Unique Angle | Gaps |
|------------|-----------|--------|--------------|------|
| Observe.ai | 2,850 | Platform features, pricing | "Automated QA" | No remediation |
| MaestroQA | 2,340 | Scorecard templates | "Custom workflows" | No training |
| Gong | 2,680 | Revenue intelligence | "Deal insights" | Call center weak |

**Synthesis:**
- Match: Platform features (table stakes)
- Differentiate: Add remediation/training (Solidroad unique)
- Avoid: Revenue focus (not our vertical)

---

## 🔗 Data Flow

```
Step 2B: Scrapes 10 competitor articles
  ↓
Saves full content to scraped_content/
  ↓
Step 3: Loads and analyzes scraped files
  ↓
Extracts: Themes, tone, structure, gaps
  ↓
Creates analysis report with previews
  ↓
Step 4: AI agent synthesizes competitive insights
  ↓
Step 5: Article includes differentiation based on gaps
```

---

## 📋 Analysis Checklist

For AI agent reviewing Step 3:
- [ ] Read all competitor content previews
- [ ] Identify common themes (appears in 5+ articles)
- [ ] Note unique angles (only 1-2 competitors)
- [ ] List content gaps (no one covers X)
- [ ] Assess tone/style (formal vs casual)
- [ ] Extract structural patterns (section order)

**Use this to inform Step 4 synthesis.**

---

## 🎓 Strategic Application

### Common Themes → Table Stakes
If 8/10 competitors cover it, **you must too**:
- Platform features
- Use case examples
- Selection criteria

### Unique Angles → Differentiation
If only 1-2 competitors mention it:
- **Opportunity:** Emphasize if it's your strength
- **Avoid:** If it's not your focus (e.g., revenue intelligence for Gong)

### Content Gaps → Blue Ocean
If 0/10 competitors cover it:
- **Insight-to-action gap** ← Solidroad's core message
- **Automated remediation** ← Our differentiator
- **Training loops** ← What we do that analytics-only platforms don't

**This is where you win.**

---

## 🔗 Related Steps

- **Requires:** Step 2B (scraped content directory)
- **Feeds:** Step 4 (competitive positioning)
- **Impact:** Differentiates Solidroad content from competitors

---

**Competitive analysis = Strategic advantage** 🎯

**Next:** [STEP_04_ai_synthesis.md](STEP_04_ai_synthesis.md)


