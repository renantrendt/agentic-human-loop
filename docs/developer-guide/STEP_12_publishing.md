---
title: HTML EXPORT & METADATA
order: 18
---

# Step 12: HTML Export & Metadata Generation

**Functions:** `step12_convert_to_framer_html()` + AI Agent Task  
**Type:** ✅ AUTOMATED + 🤖 AI AGENT  
**Output:** CSV for publishing + Metadata JSON

---

## 🤔 Why This Step Exists

**The Problem:**
You have 11 markdown articles. Framer needs HTML. Internal links reference local files (.md), not URLs. You need to manually convert everything, fix all links, write meta descriptions. That's 5+ hours of work.

**The Reality:**
Publishing friction kills momentum. Manual HTML conversion = errors. Broken internal links = bad UX. Missing meta descriptions = lower CTR. You need automation.

**The Solution:**
Convert markdown → HTML automatically. Fix all internal links (file refs → /blog/ URLs). Generate SEO meta descriptions using data-driven n-grams. Export to CSV for Google Sheets → Framer import.

**Without this step:**
- Manual HTML conversion (5+ hours)
- Broken internal links (Hub ↔ Spoke connections break)
- Generic meta descriptions (low search CTR)

**With this step:**
- Automated HTML conversion (2 minutes)
- All links fixed automatically (Hub ↔ Spoke work perfectly)
- Data-driven meta descriptions (incorporate top bigrams)

**This step exists because publishing should be 1 command, not 5 hours of manual work. Markdown → HTML → CSV → Framer. Automated.**

---

## 📝 Overview

Step 12 prepares all 11 articles for publishing to Framer CMS via Google Sheets. It has two parts:

**Step 12A (Automated):** HTML conversion  
**Step 12B (AI Agent Task):** Metadata generation with semantic n-grams

---

## ⚙️ Step 12A: HTML Conversion (Automated)

### What It Does:

1. **Converts Markdown → HTML**
   - Headers, bold, italic, lists
   - Links, paragraphs
   - No wrapper tags (`<html>`, `<head>`, `<body>`)

2. **Fixes Internal Links**
   - File refs → `/blog/` URLs
   - Example: `[text](step10_spoke01_*.md)` → `<a href="/blog/ai-quality-assurance...">text</a>`

3. **Chunks Large Content**
   - If article >50,000 chars (Google Sheets limit)
   - Splits at `<h2>` section boundaries
   - Outputs multiple Content_Part columns

4. **Cleans Metadata**
   - Removes metadata section (Primary Keywords, Word Count, etc.)
   - Removes horizontal rules (`<p>---</p>`)

5. **Injects FAQPage Schema (NEW!)**
   - Reads FAQs from Step 5B (Hub) and Step 11D (Spokes)
   - Generates JSON-LD structured data
   - Appends `<script type="application/ld+json">` to HTML
   - Enables Google FAQ rich snippets
   - **Note:** Utilities don't get FAQs (Dead-End strategy)

6. **Exports CSV**
   - Format: `Title, Date, Author, Content_Part1, Content_Part2, ...`
   - Ready for Google Sheets import

**Output:** `step12_FRAMER_EXPORT.csv`

---

## 📋 FAQPage Schema Injection

### How It Works:

Step 12 automatically loads FAQ files from earlier steps:
- **Hub:** `step5b_HUB_FAQS.md` → 3-5 broad FAQs
- **Spokes:** `step11d_spoke_faqs/spoke01_faqs.md` through `spoke10_faqs.md` → 2-3 specific FAQs each
- **Utilities:** No FAQs (per Dead-End strategy)

### Generated Schema Example:

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What is conversation analytics?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Conversation analytics is the process of analyzing customer interactions..."
      }
    },
    {
      "@type": "Question",
      "name": "Why is conversation analytics important?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Call centers generate thousands of interactions daily..."
      }
    }
  ]
}
```

### SEO Benefits:

- **Rich Snippets:** FAQs appear directly in Google search results
- **Increased CTR:** FAQ rich results take more SERP real estate
- **"People Also Ask" Integration:** Questions may appear in PAA boxes
- **Voice Search:** FAQ schema helps voice assistants answer questions

### Prerequisites:

For schema injection to work, these steps must be complete:
- Step 5B: Hub FAQ Generation
- Step 11D: Spoke FAQ Generation
- Step 11E: FAQ Cannibalization Review (ensures no overlap)

If FAQ files don't exist, HTML is generated without schema (graceful fallback).

---

## 🤖 Step 12B: Metadata Generation (AI Agent Task)

### What It Does:

**Creates task file:** `step12b_METADATA_TASK.md`

**For each article, shows:**
- Article title and type (Hub/Spoke)
- First paragraph (context)
- **Relevant bigrams/trigrams from dataset**
- Instructions to write 150-160 char description

**Example Task Section:**
```markdown
### Article 1: Top 10 Conversation Analytics Platforms

**Relevant n-grams:**
- 'conversation analytics' (2990x)
- 'conversation analytics platform' (707x)
- 'agent performance' (978x)
- 'sentiment analysis' (786x)
- 'quality assurance' (734x)

WRITE DESCRIPTION (150-160 chars):
- Incorporate 2-3 n-grams naturally
- Compelling and actionable
- Mention Solidroad if space
- SEO-optimized
```

### AI Agent Writes:

```json
{
  "articles": [
    {
      "title": "Top 10 Conversation Analytics Platforms for 2025",
      "slug": "top-conversation-analytics-platforms-2025",
      "description": "Compare conversation analytics platforms for agent performance and quality assurance. Solidroad ranks #1 for closing the insight-to-action gap.",
      "author": "Renan Serrano",
      "date": "11/21/2025"
    }
  ]
}
```

**Description uses:** 3 bigrams (conversation analytics, agent performance, quality assurance) naturally!

**Output:** `step12_ARTICLE_METADATA.json`

---

## 📊 Multi-Column CSV Format

**For large articles (>50k chars):**

```csv
Title,Date,Author,Content_Part1,Content_Part2
"Hub",11/21/2025,Renan Serrano,"<h2>Intro</h2>...","<h2>Conclusion</h2>..."
```

**Hub:** 64k chars → Split into 2 parts (38k + 26k)  
**Spokes:** <20k chars → Single Content_Part1 column

**In Framer:** Concatenate Part1 + Part2 for full content

---

## 🔗 Internal Link Fixing

**Before (Markdown):**
```markdown
[Hub article](step8_ARTICLE_WITH_CITATIONS.md)
```

**After (HTML):**
```html
<a href="/blog/top-conversation-analytics-platforms-2025">Hub article</a>
```

**All links use flat `/blog/` structure!** ✅

---

## 🎯 Why Bigrams/Trigrams Matter

**Dataset shows:**
- "conversation analytics" appears 2,990x in AI responses
- "conversation analytics platform" appears 707x
- "agent performance" appears 978x

**AI-generated descriptions that include these terms:**
- ✅ Match what people actually search
- ✅ Semantically aligned with market language
- ✅ Higher CTR in search results
- ✅ Data-driven (not guessing keywords)

---

## ✅ Success Criteria

**Step 12A Complete:**
- ✅ 11 articles converted to HTML
- ✅ All internal links fixed to `/blog/` URLs
- ✅ Large content chunked (<50k per cell)
- ✅ Metadata sections removed
- ✅ FAQPage schema injected (Hub + Spokes, not Utilities)
- ✅ CSV generated

**Step 12B Complete:**
- ✅ 11 meta descriptions written (150-160 chars each)
- ✅ Descriptions incorporate 2-3 dataset n-grams
- ✅ SEO-optimized and compelling
- ✅ Metadata JSON saved

---

## 🚀 Next Steps

**After Step 12:**
- Step 13: Quality evaluation (mandatory)
- Publishing: Append to Google Sheets
- Framer: Import and publish

---

**See Also:** `publishing/README.md` for Google Sheets publishing workflow

