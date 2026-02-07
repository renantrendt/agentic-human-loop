---
title: URL ANALYSIS
order: 4
---

# Step 2: URL Analysis

**Function:** `step2_url_analysis()`  
**Type:** Automated  
**Output:** `step2_FOR_AGENT_ANALYSIS.md`

---

## 🤔 Why This Step Exists

**The Problem:**
Who are you even competing against? Which companies actually rank? Which ones do AI models trust enough to cite?

**The Reality:**
AI models cite observe.ai 234 times, maestroqa 189 times, gong 156 times. Those aren't just citations—those are rankings. That's who owns the space.

**The Solution:**
Parse every citation. Count domain frequency. The most-cited domains = the most authoritative competitors. That's your hit list.

**Without this step:**
- Competing blindly (don't know the field)
- Scraping random competitors (waste of time)
- No competitive intelligence

**With this step:**
- Top 20 cited domains ranked by authority
- Clear competitors to analyze (observe.ai, maestroqa)
- Data-backed target list for scraping

**This step exists because you don't fight everyone—you fight the top 10. Citations reveal who actually matters. The rest is noise.**

---

## 📝 Overview

Analyzes which domains are most frequently cited in call-center QA responses to identify authority sources and competitor landscape.

---

## 🎯 Why It Matters

**What it reveals:**
- Which competitors are most authoritative (cited most often)
- What types of content get cited (blogs, guides, comparisons)
- Who owns mindshare in conversation analytics space
- Citation gaps (topics under-cited = opportunities)

**Strategic value:**
- **Competitive intelligence:** Know who you're competing against
- **Authority benchmarks:** These domains rank highly
- **Content types:** What formats win citations
- **Partnership opportunities:** Domains to potentially collaborate with

---

## ⚙️ How It Works

### 1. Extract URLs from Sources Column
```python
for sources_text in target_df['Sources']:
    urls = str(sources_text).split(';')
    all_urls.extend([u.strip() for u in urls if u.strip()])
```

### 2. Parse Domains
```python
parsed = urlparse(url)
domain = parsed.netloc.replace('www.', '')
```

### 3. Count Domain Frequency
```python
domain_counts = Counter()
for url in all_urls:
    domain_counts[domain] += 1

top_domains = domain_counts.most_common(20)
```

### 4. Generate Analysis Report
- Top 20 most-cited domains with frequencies
- Questions for AI agent analysis

---

## 📊 Inputs & Outputs

### Inputs:
- Target domain responses (from Step 1)
- `Sources` column from CSV

### Outputs:
**`step2_FOR_AGENT_ANALYSIS.md`:**
```markdown
## 📊 Most Cited Domains in Call Center QA Responses

Total URLs analyzed: 3,456

1. **observe.ai** - cited 234x
2. **maestroqa.com** - cited 189x
3. **gong.io** - cited 156x
...

## ❓ FOR CLAUDE TO ANALYZE:
1. Which domains are most authoritative?
2. What types of content are being cited?
3. Who are the main competitors?
4. What content gaps exist?
```

**Data returned:**
```python
{
    'top_domains': [(domain, count), ...],
    'all_urls': [url1, url2, ...],
    'url_df': DataFrame with URLs
}
```

---

## 🔧 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Low URL count | Responses lack sources | Check if 'Sources' column populated |
| Generic domains | Not call-center QA specific | Verify Step 1 categorization worked |
| Parsing errors | Malformed URLs | Already handled with try/except |
| No competitor domains | Wrong dataset | Verify CSV is correct topic |

---

## 📈 Example Output

```markdown
1. **observe.ai** - cited 234x
2. **maestroqa.com** - cited 189x
3. **gong.io** - cited 156x
4. **dialpad.com** - cited 142x
5. **callminer.com** - cited 128x
```

**Insights:**
- Observe.ai is market leader (most cited)
- Gong is strong in conversation intelligence
- These are your main competitors to analyze

---

## 💡 How to Improve

### Enhancement 1: URL Path Analysis
Extract content types from paths:
```python
# /blog/best-conversation-analytics-platforms → "best" listicle
# /guides/implementation → Implementation guide
# /vs/observe-ai-alternatives → Comparison page
```

### Enhancement 2: Domain Authority Check
Query Moz/Ahrefs API for DA scores:
```python
for domain in top_domains:
    da_score = get_domain_authority(domain)
    # Prioritize high-DA domains for scraping
```

### Enhancement 3: Citation Context
Extract HOW domains are cited:
```python
# "According to Observe.ai..." → Authoritative cite
# "Similar to Gong..." → Comparison cite
# "Unlike MaestroQA..." → Differentiation cite
```

### Enhancement 4: Recency Check
Favor recently published URLs:
```python
# Extract dates from URL paths
# /blog/2025/conversation-analytics → Recent
# /blog/2022/call-center-qa → Outdated
```

---

## 🎓 Strategic Insights

### High Citation Count (100+):
**These are your main competitors**
- Scrape their content in Step 2B
- Analyze their positioning
- Find their weaknesses

### Medium Citation (50-100):
**Secondary competitors**
- Monitor for trends
- Potential partnership targets

### Low Citation (<50):
**Niche players or new entrants**
- Watch for innovations
- Might have unique angles

---

## 🔗 Data Flow

```
Step 1: Call-center QA responses (696)
  ↓
Step 2: Extract cited URLs (3,456 total)
  ↓
Parse domains → Count frequencies
  ↓
Top 20 domains identified
  ↓
Step 2B: Scrape top domains for content analysis
  ↓
Step 4: Use competitor landscape in synthesis
```

---

## 🔗 Related Steps

- **Requires:** Step 1 (filtered responses)
- **Feeds:** Step 2B (URLs to scrape), Step 4 (competitor landscape)
- **Parallel:** Step 2C (semantic URL analysis)

---

**Next:** [STEP_02C_url_semantic_analysis.md](STEP_02C_url_semantic_analysis.md)


