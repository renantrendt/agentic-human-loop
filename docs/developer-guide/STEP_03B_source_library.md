---
title: SOURCE LIBRARY BUILDER
order: 7.1
---

# Step 3B: Source Library Builder (Perplexity Sonar)

**Function:** `step3b_build_source_library()`  
**Type:** ✅ Automated (requires Perplexity API key)  
**Output:** `step3b_VERIFIED_SOURCES.json`

---

## 🤔 Why This Step Exists

**The Problem:**
LLMs cannot browse the internet. When asked to "cite sources," they generate plausible-sounding URLs that don't exist:
- `gartner.com/en/newsroom/press-releases/2024-ai-speech-recognition-accuracy` ❌
- `forrester.com/report/conversation-analytics-roi-benchmark` ❌

**The Reality:**
Fake citations destroy credibility. One broken link and readers question everything. Worse, Google may penalize pages with dead links. You can't manually verify every citation across 15+ articles.

**The Solution:**
Use Perplexity Sonar (which CAN browse the internet) to discover and verify sources BEFORE article generation. Build a library of real, accessible URLs that can be matched to claims in Step 8.

**Without this step:**
- AI hallucinates citations
- Manual verification needed for every URL
- Broken links in production
- Credibility damage

**With this step:**
- Real URLs from web search
- Pre-verified (HTTP 200)
- Categorized by type
- Ready for automatic matching

**This step exists because real citations require real web access. Sonar has it. Claude doesn't.**

---

## 📝 Overview

Step 3B queries Perplexity Sonar with topic-relevant searches, collects the sources it finds, verifies each URL is accessible, and saves them for use in Step 8 citation matching.

---

## 🎯 Why It Matters

| Without Step 3B | With Step 3B |
|-----------------|--------------|
| AI invents URLs | Real URLs from web search |
| Manual verification | Automated HTTP checks |
| Broken links on publish | Pre-verified sources |
| Generic sources | Categorized by type |

---

## ⚙️ How It Works

```
Topic Keywords (from Step 3)
           ↓
Generate Search Queries (10-15 queries)
           ↓
Query Perplexity Sonar API
           ↓
Collect Sources (URLs, titles, snippets)
           ↓
Deduplicate by URL
           ↓
Verify Each URL (HTTP HEAD → 200?)
           ↓
Filter Blocked Domains (Wikipedia, Reddit, etc.)
           ↓
Categorize Sources
           ↓
Save: step3b_VERIFIED_SOURCES.json
```

---

## 🔧 Configuration

### Enable in `config.json`

```json
{
  "perplexity": {
    "enabled": true,
    "api_key": "pplx-xxxxxxxxxxxxxxxx",
    "model": "sonar",
    "search_recency_filter": "year",
    "max_sources_per_query": 5,
    "timeout_seconds": 30
  },
  "citations": {
    "blocked_domains": [
      "wikipedia.org",
      "reddit.com",
      "quora.com"
    ]
  }
}
```

### Get API Key
1. Go to https://www.perplexity.ai/settings/api
2. Create API key
3. Add to `config.json`

---

## 🔍 Search Query Generation

The step generates queries based on the article topic:

| Query Type | Example |
|------------|---------|
| Industry Reports | `[topic] industry report 2026` |
| Market Research | `[topic] market research statistics` |
| Analyst Reports | `[topic] Gartner Forrester McKinsey report` |
| ROI Studies | `[topic] ROI case study` |
| Business Impact | `[topic] cost reduction statistics` |
| Benchmarks | `[topic] accuracy benchmark study` |
| Trends | `[topic] trends 2026` |

---

## 📄 Output

### `step3b_VERIFIED_SOURCES.json`

```json
{
  "topic": "your topic",
  "generated_at": "2025-11-29T10:30:00Z",
  "queries_used": ["query 1", "query 2", "..."],
  "sources": [
    {
      "url": "https://www.mckinsey.com/...",
      "title": "Article Title",
      "snippet": "Key quote from source...",
      "source": "perplexity_sonar",
      "query": "original search query",
      "verification": {
        "valid": true,
        "status_code": 200,
        "final_url": "https://www.mckinsey.com/..."
      }
    }
  ],
  "categories": {
    "industry_research": [...],
    "roi_studies": [...],
    "case_studies": [...],
    "news_articles": [...],
    "academic": [...],
    "other": [...]
  },
  "stats": {
    "total_found": 47,
    "unique": 35,
    "verified": 28,
    "failed_verification": 7
  }
}
```

---

## 📊 Source Categorization

Sources are automatically categorized for easier matching:

| Category | Detection |
|----------|-----------|
| `industry_research` | URLs from gartner.com, forrester.com, mckinsey.com, idc.com |
| `roi_studies` | Titles containing "ROI", "economic impact", "business case" |
| `case_studies` | Titles containing "case study", "customer story" |
| `academic` | URLs with .edu, arxiv.org, scholar.google |
| `news_articles` | URLs from techcrunch, forbes, hbr.org, wsj.com |
| `other` | Everything else |

---

## ⏭️ Skipped Scenarios

Step 3B creates a placeholder file and continues if:

1. **Perplexity disabled** (`perplexity.enabled = false`)
2. **No API key** (`perplexity.api_key` is empty)

The pipeline will fall back to manual citation tasks in Step 8.

---

## 💰 Cost

| Model | Cost per Query | Typical Article |
|-------|----------------|-----------------|
| `sonar` | ~$0.001 | ~$0.02 (15 queries) |
| `sonar-pro` | ~$0.005 | ~$0.10 (15 queries) |

---

## 🔧 Troubleshooting

### No Sources Found
- Check API key is valid
- Verify topic is specific enough
- Check network connectivity

### All Sources Fail Verification
- Some sites block HEAD requests
- Try with `sonar-pro` for better quality sources

### Rate Limiting
- Step includes 1-second delay between queries
- Increase `timeout_seconds` if needed

---

## ➡️ Next Steps

After Step 3B completes:
1. **Step 4:** AI Synthesis uses topic context
2. **Step 5:** Article generation with `[CLAIM:]` markers
3. **Step 8:** Citation matching uses verified sources from Step 3B
