---
title: CITATION WORKFLOW REDESIGN
order: 12.0
---

# Citation Workflow Redesign: Perplexity Sonar Integration

**Type:** 📋 Architecture Document  
**Related Steps:** Step 3B, Step 8, Step 8B, Step 8C  
**Status:** ✅ Implemented

---

## 🤔 Why This Redesign Exists

**The Problem:**
The existing citation workflow asks Claude to "find sources" for claims in articles. Since LLMs cannot browse the internet, they generate plausible-sounding URLs that don't exist.

**Example of hallucinated citations found in production:**
- `trainingjournal.com/articles/features/impact-feedback-timing-agent-performance` ❌
- `forrester.com/report/conversation-analytics-roi-benchmark` ❌
- `icmi.com/resources/remote-contact-center-workforce-trends` ❌
- `gartner.com/en/newsroom/press-releases/2024-ai-speech-recognition-accuracy` ❌

**The Reality:**
One broken link destroys credibility. Readers click, get a 404, and question everything. Google may penalize pages with dead external links. Manual verification doesn't scale across 15+ articles per cluster.

**The Solution:**
Use Perplexity Sonar (which CAN browse the internet) to:
1. Discover real sources BEFORE article generation
2. Match claims to verified URLs
3. Automatically verify all citations work

**Without this redesign:**
- 100% of citations are hallucinated
- Manual verification required
- Broken links in production
- Credibility damage

**With this redesign:**
- 0% hallucinated URLs
- Automated verification
- Pre-verified source library
- Quality gate before publish

**This redesign exists because LLMs can't browse the web. Perplexity Sonar can.**

---

## 📝 Overview

This document outlines the complete redesign of the citation workflow to eliminate AI-hallucinated citations by integrating Perplexity Sonar for real-time web search and source verification.

---

## 🎯 Root Cause Analysis

### Before (Broken)
```
Claude → "Here's a citation" → HALLUCINATED URL 🚨
         (Cannot access internet)
```

### After (Fixed)
```
Perplexity Sonar → Searches real web → Returns ACTUAL sources ✅
                   (Has internet access)
```

---

## 🏗️ Architecture Overview

```
┌────────────────────────────────────────────────────────────────────┐
│           CITATION WORKFLOW v2 (WITH PERPLEXITY SONAR)             │
└────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────┐
                    │   Config Setup      │
                    │   (Sonar API Key)   │
                    └──────────┬──────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 3B: SOURCE LIBRARY BUILDER (NEW)                           │
│  ─────────────────────────────────────                           │
│  Tool: Perplexity Sonar                                          │
│                                                                  │
│  • Query Sonar for topic-relevant sources                        │
│  • Build verified source library BEFORE article generation       │
│  • Extract key claims, dates, URLs                               │
│                                                                  │
│  Output: step3b_VERIFIED_SOURCES.json                            │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 5: ARTICLE GENERATION (MODIFIED)                           │
│  ─────────────────────────────────────                           │
│  Tool: Claude                                                    │
│                                                                  │
│  • Write article with [CLAIM: description] markers               │
│  • DO NOT generate citations                                     │
│  • DO NOT invent URLs                                            │
│                                                                  │
│  Output: step5_ARTICLE_WITH_CLAIMS.md                            │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 8: CITATION MATCHING (REDESIGNED)                          │
│  ──────────────────────────────────────                          │
│  Tool: Perplexity Sonar + Claude                                 │
│                                                                  │
│  • For each [CLAIM] marker, query Sonar for real source          │
│  • Match claims to verified sources                              │
│  • Replace markers with real citations                           │
│  • Flag unverifiable claims                                      │
│                                                                  │
│  Output: step8_ARTICLE_WITH_CITATIONS.md                         │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 8B: AUTOMATED VERIFICATION (NEW)                           │
│  ─────────────────────────────────────                           │
│  Tool: HTTP requests + Perplexity Sonar                          │
│                                                                  │
│  • HTTP HEAD check all citation URLs (200 = valid)               │
│  • Content verification (does page contain claimed stat?)        │
│  • Freshness check (source < 2 years old?)                       │
│                                                                  │
│  Output: step8b_CITATION_VERIFICATION_REPORT.md                  │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 8C: CITATION REVIEW (AI AGENT TASK)                        │
│  ────────────────────────────────────────                        │
│  Tool: AI Agent (Claude in Cursor)                               │
│                                                                  │
│  • Review flagged issues from Step 8B                            │
│  • Handle broken links (find alternatives)                       │
│  • Handle unverified claims (rewrite or remove)                  │
│  • Handle outdated sources (find newer versions)                 │
│                                                                  │
│  Output: step8c_CITATIONS_FINAL.md                               │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Configuration

### Add to `brand-context/config.json`

```json
{
  "perplexity": {
    "enabled": true,
    "api_key": "pplx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "model": "sonar",
    "model_pro": "sonar-pro",
    "search_recency_filter": "year",
    "max_sources_per_query": 5,
    "timeout_seconds": 30
  },
  "citations": {
    "min_sources_per_article": 5,
    "max_source_age_years": 2,
    "require_verification": true,
    "allowed_domains": [
      "gartner.com",
      "forrester.com",
      "mckinsey.com",
      "hbr.org",
      "harvard.edu",
      "mit.edu",
      "forbes.com",
      "techcrunch.com"
    ],
    "blocked_domains": [
      "wikipedia.org",
      "reddit.com",
      "quora.com"
    ]
  }
}
```

---

## 📋 Step-by-Step Implementation

### Step 3B: Source Library Builder

**Purpose:** Build a verified source library BEFORE article generation, ensuring all citations come from real, accessible URLs.

**See:** [STEP_03B_source_library.md](STEP_03B_source_library.md)

```python
def step3b_build_source_library(synthesis_data, topic_keywords):
    """
    Use Perplexity Sonar to discover and verify sources for the article topic.
    """
    # Generate search queries based on topic
    search_queries = generate_source_queries(synthesis_data, topic_keywords)
    
    # Query Sonar for each
    all_sources = []
    for query in search_queries:
        sources = query_perplexity_sonar(query, api_key, model)
        all_sources.extend(sources)
    
    # Deduplicate and verify
    unique_sources = deduplicate_sources(all_sources)
    verified_sources = [s for s in unique_sources if verify_source_url(s['url'])['valid']]
    
    # Save to JSON
    save_to_file("step3b_VERIFIED_SOURCES.json", verified_sources)
```

---

### Step 5: Article Generation (Modified)

**Changes:**
- Remove all instructions to "cite sources"
- Add `[CLAIM: description]` marker format
- Explicitly forbid URL generation

**Modified Prompt Section:**

```python
citation_instructions = """
## CITATION RULES (CRITICAL):

DO NOT generate any URLs or citations in this article.
DO NOT invent source names or report titles.
DO NOT write things like "according to Gartner" or "Forrester reports".

Instead, when you make a claim that would need a citation:
1. Write the claim naturally
2. Add a [CLAIM: brief description] marker after it

EXAMPLE:
❌ WRONG: "Companies see 20-30% cost reduction (Gartner, 2024)"
❌ WRONG: "According to [Forrester](https://forrester.com/report), ROI is 312%"

✅ CORRECT: "Organizations implementing this technology see significant cost reduction 
   [CLAIM: technology cost reduction statistics]."

✅ CORRECT: "Organizations report significant ROI improvements 
   [CLAIM: technology ROI data]."

The [CLAIM] markers will be replaced with real, verified citations in a later step.
"""
```

---

### Step 8: Citation Matching (Redesigned)

**Purpose:** Match `[CLAIM: ...]` markers to verified sources from Step 3B, using Perplexity Sonar to find additional sources if needed.

**See:** [STEP_08_citations.md](STEP_08_citations.md)

```python
def step8_match_citations(article_file, sources_file=None):
    """
    Match [CLAIM: ...] markers in article to verified sources.
    """
    # Extract all [CLAIM: ...] markers
    claims = re.findall(r'\[CLAIM:\s*([^\]]+)\]', article_content)
    
    for claim in claims:
        # Try pre-verified sources first
        matched = find_matching_source(claim, verified_sources)
        
        if not matched:
            # Use Sonar to find a source
            matched = find_source_with_sonar(claim, api_key)
        
        if matched:
            # Replace marker with citation
            replace_claim_with_citation(claim, matched)
        else:
            # Mark as unverified
            mark_as_unverified(claim)
```

---

### Step 8B: Automated Verification

**Purpose:** Final automated check of all citation URLs before publishing.

**See:** [STEP_08B_citation_verification.md](STEP_08B_citation_verification.md)

```python
def step8b_verify_citations(article_file):
    """
    Verify all citation URLs in the article are accessible.
    """
    urls = extract_all_urls(article_content)
    
    results = {'valid': [], 'broken': [], 'redirected': []}
    
    for url in urls:
        verification = verify_source_url(url)
        categorize_result(url, verification, results)
    
    # Check for remaining [UNVERIFIED: ...] markers
    unverified = re.findall(r'\[UNVERIFIED:\s*([^\]]+)\]', article_content)
    
    # Generate report
    is_ready = len(results['broken']) == 0 and len(unverified) == 0
    generate_verification_report(results, unverified, is_ready)
```

---

### Step 8C: Citation Review (AI Agent Task)

**Purpose:** Handle edge cases that require human/AI judgment.

**See:** [STEP_08C_citation_review.md](STEP_08C_citation_review.md)

```python
def step8c_create_citation_review_task(verification_report_file):
    """
    Create AI agent task to review and fix citation issues.
    Only triggers if Step 8B found issues.
    """
    if no_issues_found:
        return  # Skip - no review needed
    
    create_task_file("""
    ## Instructions
    
    ### For Broken Links:
    - Search for the article title
    - Check archive.org for cached version
    - Find alternative source
    
    ### For Unverified Claims:
    - Search for a real source
    - Rewrite to be more general
    - Remove if not essential
    """)
```

---

## 💰 Cost Estimates

| Step | Sonar Queries | Model | Est. Cost |
|------|---------------|-------|-----------|
| Step 3B | 10-15 queries | sonar | ~$0.02 |
| Step 8 | 15-25 claims | sonar | ~$0.03 |
| **Total per article** | 25-40 queries | - | **~$0.05** |

For `sonar-pro` (better accuracy): ~$0.25 per article

---

## ✅ Implementation Checklist

- [x] Add Perplexity API key to `config.json`
- [x] Implement `step3b_build_source_library()`
- [x] Modify Step 5 prompt to use `[CLAIM:]` markers
- [x] Implement `step8_match_citations_with_sonar()`
- [x] Implement `step8b_verify_citations()`
- [x] Implement `step8c_create_citation_review_task()`
- [x] Update pipeline flow in `main()`
- [x] Add step completion markers for 3b, 8b, 8c
- [ ] Test end-to-end with sample article
- [x] Update documentation index

---

## 📊 Success Metrics

After implementation, measure:

1. **Citation Accuracy:** 0% hallucinated URLs (vs current ~100%)
2. **Verification Pass Rate:** >95% URLs return 200
3. **Source Quality:** >80% from authoritative domains
4. **Processing Time:** <5 minutes for citation matching
5. **Cost per Article:** <$0.50

---

## 🔄 Rollback Plan

If issues arise:
1. Disable Sonar integration in `config.json` (`"perplexity.enabled": false`)
2. Pipeline falls back to manual `[CITATION NEEDED]` markers
3. Manual citation process continues via Step 8 AI Agent task

---

## ➡️ Next Steps

1. **Get Perplexity API key** from https://www.perplexity.ai/settings/api
2. **Add to config.json** with `"enabled": true`
3. **Run pipeline** - Sonar integration is automatic
4. **Monitor** verification reports for quality

---

## 📚 Related Documentation

- [STEP_03B_source_library.md](STEP_03B_source_library.md) - Source discovery details
- [STEP_08B_citation_verification.md](STEP_08B_citation_verification.md) - URL verification details
- [STEP_08C_citation_review.md](STEP_08C_citation_review.md) - AI Agent review task details
