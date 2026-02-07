---
title: URL SEMANTIC ANALYSIS
order: 5
---

# Step 2C: URL Semantic Analysis

**Function:** `step2c_url_semantic_analysis()`  
**Type:** Automated  
**Output:** `step2c_URL_SEMANTIC_ANALYSIS.md`

---

## 🤔 Why This Step Exists

**The Problem:**
Should your article be titled "Best Platforms" or "How to Choose a Platform" or "Platform Comparison Guide"? Wrong choice = wrong format = wrong rankings.

**The Reality:**
URLs reveal intent. If 48% of ranking URLs contain "best" or "top," that's the dominant intent. That's what Google expects. That's what you write.

**The Solution:**
Parse all 3,456 URLs. Extract semantic keywords from paths. Classify search intent. Comparative 48%? Write a comparison listicle.

**Without this step:**
- Title format guessing (might pick the wrong angle)
- Content mismatch (learning guide for comparison intent)
- Lower rankings (format doesn't match intent)

**With this step:**
- Clear dominant intent (Comparative 48.3%)
- Winning URL patterns identified
- Data-backed title format decision

**This step exists because URLs don't lie. They reveal what Google ranks for specific intents. Match the pattern, win the ranking.**

---

## 📝 Overview

Extracts semantic keywords from URL paths and classifies search intent to understand what content types rank best.

**Decodes the URL structure patterns of ranking pages.**

---

## 🎯 Why It Matters

**What URLs reveal:**
- Search intent (Comparative 48% vs Learning 32%)
- Winning URL patterns ("best-X" vs "how-to-X")
- Semantic keywords in paths (what Google sees as relevant)
- Content format that ranks (listicles vs guides vs comparisons)

**Strategic value:**
- **Title strategy:** Match winning URL patterns
- **Content format:** Listicle, guide, or comparison?
- **User intent:** What are they looking for?
- **Spoke ideas:** Long-tail variations in URL paths

---

## ⚙️ How It Works

### 1. Extract Semantic Content from URLs
```python
parsed = urlparse(url)
path = parsed.path.strip('/')
# Example: /blog/2025/best-conversation-analytics-platforms
# Extract: "best conversation analytics platforms"
```

**Cleanup:**
- Remove non-semantic prefixes ('blog', 'article', '2025', etc.)
- Replace separators (/, -, _) with spaces
- Lowercase normalization

### 2. Classify Search Intent
```python
words = semantic.split()

if any(w in words[:2] for w in ['best', 'top', 'compare', 'vs']):
    intent = 'Comparative/Selection'
elif any(w in words[:2] for w in ['how', 'what', 'guide']):
    intent = 'Learning/Education'
elif any(w in semantic for w in ['pricing', 'trial', 'free']):
    intent = 'Acquisition/Obtaining'
elif any(w in semantic for w in ['improve', 'optimize']):
    intent = 'Optimization/Improvement'
```

### 3. Calculate Intent Distribution
```python
intent_summary = url_df.groupby('search_intent')['count'].agg(['sum', 'count'])
# Comparative: 48.3%
# Learning: 32.1%
# Acquisition: 12.5%
# Others: 7.1%
```

### 4. Extract Top Keywords
```python
# From all semantic content in URL paths
keyword_counts = Counter(all_keywords)
top_keywords = keyword_counts.most_common(20)
```

---

## 📊 Inputs & Outputs

### Inputs:
- All URLs from Step 2 (3,456 URLs)

### Outputs:
**`step2c_URL_SEMANTIC_ANALYSIS.md`:**
```markdown
## 📊 Search Intent Distribution

| Intent | Mentions | URLs | % |
|--------|----------|------|---|
| Comparative/Selection | 1,234 | 45 | 48.3% |
| Learning/Education | 821 | 32 | 32.1% |
| Acquisition | 318 | 15 | 12.5% |
| Others | 183 | 8 | 7.1% |

## 🔑 Top 20 Keywords from URL Paths

1. `analytics` - 856x
2. `conversation` - 743x
3. `platform` - 521x
4. `software` - 398x
5. `best` - 287x
...

## 📋 Top 10 URLs by Intent

### Comparative/Selection:
- /best-conversation-analytics-platforms-2025 (12x)
- /conversation-analytics-software-comparison (8x)
...
```

---

## 🚨 No Quality Gates (Analysis Only)

This step doesn't have quality gates because:
- URL analysis doesn't fail (uses existing data)
- Intent classification always produces result
- Even with low URL count, provides insights

**However:** If Step 2 had very few URLs (<50), this analysis may be limited.

---

## 🔧 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Low semantic extraction | URLs lack keywords | Check URL structure (some use IDs not keywords) |
| All "Others" intent | Generic URL paths | Normal for some domains (ID-based URLs) |
| Duplicate keywords | Similar URL patterns | Already de-duplicated in Counter |

---

## 📈 Example Insights

### Intent Distribution:
```
Comparative: 48.3% ← DOMINANT
Learning: 32.1%
Acquisition: 12.5%
```

**Strategic decision:**
- Use "Best X" or "Top X" title format (matches dominant intent)
- Include comparison table (what users expect)
- Address selection criteria

### Top Keywords:
```
1. `analytics` - 856x
2. `conversation` - 743x
3. `best` - 287x
```

**Title strategy:**
- Include "conversation analytics" (high frequency)
- Use "best" modifier (matches intent)
- Result: "Best Conversation Analytics Platforms 2025"

---

## 💡 How to Improve

### Enhancement 1: Search Volume Integration
Query Google Keyword Planner API:
```python
for keyword in top_keywords:
    volume = get_search_volume(keyword)
    competition = get_competition_level(keyword)
    # Prioritize: High volume + low competition
```

### Enhancement 2: SERP Position Tracking
Check where these URLs actually rank:
```python
# Which URLs rank #1-3?
# What patterns do top rankers share?
```

### Enhancement 3: Temporal Analysis
Track URL freshness:
```python
# Extract dates from paths
# /2025/conversation-analytics → Fresh
# /2022/call-center-qa → Outdated
# Insight: Freshness matters for "best" queries
```

### Enhancement 4: Multi-language Detection
Identify localized versions:
```python
# /en/conversation-analytics
# /pt/analise-conversacao
# Opportunity: Create localized content
```

---

## 🎓 Strategic Frameworks

### Intent → Content Format Matrix:

| Intent | Format | Title Pattern | Structure |
|--------|--------|---------------|-----------|
| Comparative (48%) | Listicle | "Best X", "Top X" | Comparison table |
| Learning (32%) | Guide | "How to X", "X Guide" | Step-by-step |
| Acquisition (12%) | Landing | "X Pricing", "X Free Trial" | Features + CTA |
| Optimization (8%) | Tutorial | "Improve X", "Optimize X" | Before/after |

**Use this to match Hub format to dominant intent.**

### URL Pattern Winners:
```
High Frequency Patterns:
- /best-[topic]-platforms → Comparative
- /how-to-[action] → Learning
- /[topic]-vs-[alternative] → Comparison
- /what-is-[concept] → Informational
```

**Apply to Hub URL:**
- If Comparative dominant → Use "best-conversation-analytics-platforms"
- If Learning dominant → Use "conversation-analytics-guide"

---

## 🔗 Data Flow

```
Step 2: All URLs extracted (3,456)
  ↓
Step 2C: Extract semantic keywords from paths
  ↓
Classify search intent per URL
  ↓
Calculate intent distribution (Comparative 48%)
  ↓
Extract top keywords (analytics, conversation, best...)
  ↓
Step 4: Use intent to determine content format
  ↓
Step 5: Apply winning URL pattern to Hub title
  ↓
Step 10: Apply to spoke URL structures
```

---

## 📋 Quality Checklist

Quality indicators (not gates):
- [ ] ✅ Intent distribution has clear dominant (>40%)
- [ ] ✅ Top keywords are topic-relevant (not generic)
- [ ] ✅ URL patterns identifiable (not all ID-based)
- [ ] ⚠️ If all "Others", URLs may be low-quality

---

## 🎓 Real-World Application

### Example: Hub Title Decision

**Data:**
- Dominant intent: Comparative (48.3%)
- Top URL keywords: "best", "analytics", "platform"
- Winning pattern: `/best-[topic]-platforms-2025`

**Recommended Hub Title:**
"Best Conversation Analytics Platforms 2025"

**Recommended Hub URL:**
`/blog/best-conversation-analytics-platforms-2025`

### Example: Spoke Titles

**Data:**
- Learning intent (32.1%)
- URL pattern: `/how-to-[action]`

**Recommended Spoke:**
"How to Choose a Conversation Analytics Platform"

**URL:**
`/blog/how-to-choose-conversation-analytics-platform`

---

## 🔗 Related Steps

- **Requires:** Step 2 (all URLs)
- **Parallel:** Step 2B (scraping)
- **Feeds:** Step 4 (intent-based content strategy)
- **Impact:** Title format, content type, URL structure

---

## 📊 Output Structure

**step2c_URL_SEMANTIC_ANALYSIS.md contains:**
1. Intent distribution table
2. Top 20 semantic keywords
3. Top 10 URLs per intent category
4. Analysis questions for AI agent

**AI agent uses this to:**
- Decide content format (listicle vs guide)
- Choose title pattern (Best X vs How to X)
- Match user intent expectations

---

**Next:** [STEP_03_scraping_analysis.md](STEP_03_scraping_analysis.md)


