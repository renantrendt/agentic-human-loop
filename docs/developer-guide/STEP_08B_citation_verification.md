---
title: CITATION VERIFICATION
order: 12.1
---

# Step 8B: Citation Verification (Automated)

**Function:** `step8b_verify_citations()`  
**Type:** ✅ Automated  
**Output:** `step8b_CITATION_VERIFICATION_REPORT.md`

---

## 🤔 Why This Step Exists

**The Problem:**
Even with Perplexity Sonar finding real sources, URLs can:
- Become broken between discovery and publishing
- Redirect to different locations
- Be blocked by certain networks

**The Reality:**
A single broken link damages credibility. Readers click, get a 404, and question everything else. Google may also penalize pages with dead external links.

**The Solution:**
Automatically verify every external URL before publishing. HTTP HEAD requests are fast and catch dead links before they go live.

**Without this step:**
- Broken links slip through
- Manual checking required
- Credibility risk
- SEO penalty risk

**With this step:**
- Every URL verified
- Broken links flagged
- Redirects detected
- Quality gate before publish

**This step exists because verification is cheap. Broken links are expensive.**

---

## 📝 Overview

Step 8B extracts all external URLs from the article, makes HTTP HEAD requests to verify accessibility, and generates a report categorizing URLs as valid, broken, or redirected.

---

## 🎯 Why It Matters

| Status | Meaning | Action |
|--------|---------|--------|
| ✅ Valid | URL returns 200 | Good to publish |
| ↪️ Redirected | URL redirects | Consider updating |
| ❌ Broken | URL returns 4xx/5xx | Must fix |
| 🔍 Unverified | `[UNVERIFIED:]` marker | Need source or rewrite |

---

## ⚙️ How It Works

```
Article with Citations (from Step 8)
           ↓
Extract All External URLs
           ↓
Filter Out Brand URLs (internal links OK)
           ↓
HTTP HEAD Request Each URL
           ↓
Categorize: Valid / Broken / Redirected
           ↓
Check for [UNVERIFIED: ...] Markers
           ↓
Generate Verification Report
           ↓
If Issues Found → Create Step 8C Task
```

---

## 🔧 When It Runs

Step 8B only runs when:
1. **Perplexity is enabled** (`perplexity.enabled = true`)
2. **Step 8 completed** (article with citations exists)

If Perplexity is disabled, Step 8 creates a manual task instead, and 8B is skipped.

---

## 📄 Output

### `step8b_CITATION_VERIFICATION_REPORT.md`

```markdown
# Citation Verification Report

**Generated:** 2025-11-29T10:30:00Z
**Article:** step8_ARTICLE_WITH_CITATIONS.md

---

## Summary

| Status | Count |
|--------|-------|
| ✅ Valid | 12 |
| ↪️ Redirected | 2 |
| ❌ Broken | 1 |
| 🔍 Unverified Claims | 3 |

---

## Valid Citations (12)

- ✅ https://www.mckinsey.com/article...
- ✅ https://hbr.org/2024/...
...

## Redirected URLs (2)

- ↪️ https://old-url.com/article
  → https://new-url.com/article

## Broken Citations (1)

- ❌ https://broken-link.com/page
  Error: connection_error

## Unverified Claims (3)

- 🔍 industry adoption rate statistics
- 🔍 cost savings percentage

---

## Verdict

❌ **NOT READY** - Fix issues above before publishing.
```

---

## ✅ Verdict Logic

### READY FOR PUBLISHING
- Zero broken links
- Zero unverified claims

### NOT READY
- Any broken links found, OR
- Any `[UNVERIFIED: ...]` markers remain

---

## ➡️ What Happens Next

### If Ready (✅)
Pipeline continues to Step 9 (Infrastructure)

### If Not Ready (❌)
Step 8C is triggered:
- Creates `step8c_CITATION_REVIEW_TASK.md`
- AI Agent reviews and fixes issues
- Pipeline pauses until `step8c_CITATIONS_REVIEWED.txt` exists

---

## 🔧 Troubleshooting

### False Positives (Valid URLs Marked Broken)
Some websites block HEAD requests. The URL may work in a browser but fail verification.

**Solution:** AI Agent in Step 8C can verify manually and keep the URL.

### Many Redirects
Normal for older sources. Consider updating to final URLs for cleaner references.

### Unverified Claims
These are `[CLAIM: ...]` markers that Sonar couldn't find sources for.

**Options:**
1. Search manually for a source
2. Rewrite claim to be more general
3. Remove the specific statistic

---

## 🔧 Configuration

No additional configuration needed. Step 8B uses the same settings as Step 8.

The brand URL is automatically excluded from external URL checks:
```python
brand_url = CONFIG.get('brand', {}).get('url', '')
external_urls = [u for u in urls if brand_domain not in u]
```

---

## 💰 Cost

**Free** - Step 8B only makes HTTP HEAD requests, no API calls.
