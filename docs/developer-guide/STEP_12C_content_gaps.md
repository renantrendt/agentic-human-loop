---
title: CONTENT GAP ANALYSIS
order: 20
---

# Step 12C: Content Gap Analysis

**Function:** `step12c_analyze_content_gaps()`  
**Type:** Automated  
**Output:** `step12c_CONTENT_GAPS.md` (content roadmap)

---

## 🤔 Why This Step Exists

**The Problem:**
You just published 11 articles with 141 internal links. But some of those links are bullshit. They say "[Solidroad's SCORE methodology]" but link to the homepage. They promise specific content, then deliver nothing. Users click, get frustrated, bounce.

**The Reality:**
Content clusters create organic linking opportunities. Writers naturally reference "IQS framework" or "QA scorecard templates" in articles. But those articles don't exist yet. So they link to the homepage or make up URLs. You're creating link rot before you even publish.

**The Solution:**
Analyze every internal link in the cluster. Find all the gaps where link text promises content that doesn't exist. Rank them by frequency—if 5 articles mention "IQS framework," that's your next article to write. Content gaps become your content roadmap.

**Without this step:**
- Broken promises (link text lies about destination)
- Manual review nightmare (141 links to check manually?)
- No content roadmap (what should we write next?)
- Link quality degrades over time

**With this step:**
- All gaps identified automatically (141 links analyzed in seconds)
- Prioritized by demand (5 mentions = higher priority than 1)
- Quick wins flagged (wrong URLs to existing content)
- Data-driven roadmap (write what's already being referenced)

**This step exists because your articles tell you what content to create next. If 5 articles reference "IQS framework," readers clearly want that content. Stop guessing—analyze the gaps and build what's already in demand.**

---

## 📝 Overview

Analyzes all internal links in published articles to identify content gaps, broken promises, and missing pages. Creates a prioritized roadmap of what content to create next based on what's already being referenced.

**Turns link quality issues into content strategy.**

---

## 🎯 Why It Matters

**User Experience Impact:**
- Broken link promises = frustrated users
- "SCORE methodology" → homepage = bad UX
- Users bounce, engagement drops
- Trust erodes

**SEO Impact:**
- Poor user signals (high bounce rate from internal clicks)
- Missed keyword opportunities (gaps = topics people want)
- Weak internal linking (can't link to content that doesn't exist)
- Lower topical authority (incomplete coverage)

**Content Strategy Impact:**
- Data shows what readers want (5 mentions = strong demand signal)
- Prioritized roadmap (create high-frequency gaps first)
- Stop guessing (your articles tell you what to write next)

---

## ⚙️ How It Works

### 1. Collect Existing Pages
```python
existing_pages = {
    '/',
    '/products', '/pricing', '/contact',
    '/blog/hub-article-slug',
    '/blog/spoke-01-slug',
    ... (all articles we have)
}
```

### 2. Extract All Internal Links
```python
for article in all_articles:
    links = find_links_to_solidroad(article)
    
    for link in links:
        if link.url == homepage:
            if link.text != 'Solidroad':
                # Gap: Specific content claimed but goes to homepage
                content_gaps[link.text] += 1
        
        elif link.url not in existing_pages:
            # Gap: Links to page we don't have
            content_gaps[link.text] += 1
```

### 3. Rank by Frequency
```python
# Most mentioned = highest priority
gaps_ranked = content_gaps.most_common()
# e.g., "IQS framework" mentioned 5x = create this first!
```

### 4. Generate Report
```python
Output: step12c_CONTENT_GAPS.md

Contains:
- Summary table (top 10-15 gaps)
- Full list with examples
- Recommendations (create vs fix)
```

---

## 📊 Example Output

```markdown
# Content Gap Analysis

**Total Links:** 141
**Content Gaps:** 31

## 📋 TOP CONTENT GAPS

| Gap | Mentions | Action |
|-----|----------|--------|
| Integrated Quality Score (IQS) | 5x | Create article |
| SCORE methodology | 3x | Create article |
| insight-to-action gap | 3x | Update URL (already Spoke 01!) |
| QA scorecard template | 3x | Create article |
...

## 🎯 RECOMMENDATIONS

High priority (3+ mentions):
- Create: /blog/integrated-quality-score (5x)
- Create: /blog/score-methodology (3x)
- Fix URL: Update insight-to-action-gap links to correct slug
...
```

---

## 🔍 What Gets Flagged

### **Homepage Overuse**
```markdown
[specific topic](https://www.solidroad.com)
```
- Link text is specific
- URL is generic homepage
- **Gap:** Need dedicated article

### **Missing Pages**
```markdown
[topic](/blog/article-that-doesnt-exist)
```
- URL points to page we don't have
- **Gap:** Create that article

### **Not Flagged (Valid)**
```markdown
[Solidroad](https://www.solidroad.com)  ← OK, honest link text
[hub article](/blog/existing-slug)     ← OK, page exists
```

---

## 📋 Output Format

### **Summary Table**
Top 10-15 most-mentioned gaps in table format

### **Full Details**
Each gap shows:
- How many times mentioned
- Which articles reference it
- Example links
- Recommendation

### **Quick Wins**
Easy fixes identified (e.g., "already have this article, just fix URL")

---

## 🎯 How to Use the Report

### **For Content Planning:**
- **Most mentioned gaps = highest ROI** articles to create
- Prioritize topics referenced 3+ times
- These are proven needs (multiple articles want to link there!)

### **For Link Quality:**
- Fix "quick wins" first (wrong URLs to existing content)
- Verify product pages exist
- Update homepage links to be honest

### **For SEO:**
- Broken internal links hurt rankings
- Missing content = missed keyword opportunities
- Content gaps show what readers want

---

## 💡 How to Improve

### Enhancement 1: External Gap Analysis
```python
# Check external links too
for link in external_links:
    if link.returns_404():
        broken_links[link.url] += 1
```

### Enhancement 2: Historical Gap Tracking
```python
# Track which gaps get filled over time
gap_history = {
    'IQS framework': {
        'first_identified': '2025-11-21',
        'mentions': 5,
        'status': 'created',
        'filled_date': '2025-11-25'
    }
}
```

### Enhancement 3: Auto-Suggest Titles
```python
# Generate article titles from gap text
gap = "Solidroad's SCORE methodology"
suggested_title = "The SCORE Methodology: Solidroad's Approach to QA"
```

### Enhancement 4: Competitive Gap Analysis
```python
# Compare to competitor content
competitor_has = ['IQS', 'SCORE', 'QA templates']
we_have = ['Hub', 'Spokes']
competitive_gaps = competitor_has - we_have
```

---

## 🔧 Typical Findings

**Per 10-article cluster:**
- 100-150 total internal links
- 20-40 content gaps identified
- 5-10 high-priority gaps (3+ mentions)
- 2-3 quick wins (wrong URLs to existing content)

**Most Common Gap Types:**
- Methodology articles (IQS, SCORE)
- Feature deep-dives (specific product capabilities)
- Template/resource pages (QA scorecards, checklists)
- Comparison articles (Solidroad vs alternatives)

---

## ✅ Success Criteria

- ✅ All articles analyzed
- ✅ All internal links extracted
- ✅ Gaps ranked by frequency
- ✅ Report generated with recommendations
- ✅ Quick wins identified

**Output:** Clear content roadmap based on what's already being referenced!

---

## 🎓 Strategic Value

**Content gaps are demand signals:**
- If 5 articles reference "IQS framework" → readers clearly want that content
- If 3 articles mention "QA scorecard templates" → proven need
- Frequency = priority (create most-mentioned gaps first)

**This is organic content discovery:**
- Writers naturally link to concepts they discuss
- Those links reveal what content readers need
- Much better signal than "let's brainstorm topics"

**Gap analysis > keyword research:**
- Keyword research shows search volume
- Gap analysis shows what YOUR readers want in YOUR context
- Gaps are proven opportunities (already being referenced!)

---

## 🔗 Related Steps

- **Requires:** Step 7 (internal links), Step 12 (HTML export)
- **Feeds:** Content roadmap for next cluster generation
- **Impact:** Guides future content creation priorities

---

## 🚀 Next Steps

After Step 12C:
1. Review `step12c_CONTENT_GAPS.md`
2. Fix quick wins (wrong URLs to existing content)
3. Create high-priority missing articles (3+ mentions first)
4. Re-run gap analysis after creating content (measure progress!)

**Iterative improvement:**
- First cluster: 31 gaps identified
- Create 5 high-priority articles
- Second cluster: 18 gaps (13 filled!)
- Create 3 more articles
- Third cluster: 8 gaps (23 filled!)

**Goal:** Zero gaps = perfect internal linking ecosystem!

---

**Your articles tell you what to write next. Listen to them.** 🎯

