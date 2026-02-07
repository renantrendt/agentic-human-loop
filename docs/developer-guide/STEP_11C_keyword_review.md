---
title: AI KEYWORD REVIEW
order: 17.1
---

# Step 11C: AI Agent Keyword Review

**Function:** `step11c_ai_keyword_review()`

**Type:** ⭐ AI Agent Task  
**Output:** 
- `step11c_KEYWORD_REVIEW_TASK.md` - Instructions for AI agent
- `step11c_KEYWORDS_TEMPLATE.csv` - Pre-filled template with extracted keywords
- `step11c_REVIEWED_KEYWORDS.csv` - Final reviewed keywords (AI agent creates this)

---

## 🤔 Why This Step Exists

**The Problem:**
Keywords extracted automatically from markdown (`**Primary Keywords:**`) are often:
- Missing long-tail variations that capture search intent
- Including irrelevant or generic terms
- Not prioritized by search volume/importance
- Sometimes containing brand names (we don't need to rank for our own brand)

**The Reality:**
Keywords sent to Athena become the prompts that track ranking performance. Bad keywords = tracking the wrong searches. Missing long-tail = missing 70% of actual search traffic. Brand keywords = wasted tracking (you already rank #1 for your brand).

**The Solution:**
An AI agent reviews and optimizes keywords before they're exported to CSV and sent to Athena:
1. **Ensure head keywords** (short, high-volume competitive terms)
2. **Add long-tail variations** (question-based, year-specific, intent-driven)
3. **Remove irrelevant keywords** (generic, duplicate, off-topic)
4. **Reorder by priority** (head keywords first, then long-tail)
5. **Filter brand keywords** (remove brand name variations)

**Without this step:**
- Tracking wrong keywords in Athena
- Missing long-tail search opportunities
- Wasted effort on brand keywords
- Poor SEO signal alignment

**With this step:**
- Optimized keyword set per article
- Long-tail variations captured
- Priority ordering for tracking
- Clean, brand-free keyword lists

---

## 📝 Overview

**Step 11C runs BEFORE Step 12 (HTML export).**

The pipeline:
1. Extracts keywords from all markdown files
2. Creates a review task for the AI agent
3. AI agent reviews and optimizes keywords
4. Saves `step11c_REVIEWED_KEYWORDS.csv`
5. Pipeline auto-continues to Step 12
6. Step 12 uses reviewed keywords instead of raw extraction

**Time:** 15-30 minutes for AI agent review

---

## 🎯 AI Agent Review Criteria

### 1. USE NICHE-SPECIFIC Head Keywords (NOT Ultra-Generic)

Every article needs 1-2 **niche-specific head keywords** - these are industry-focused terms you can actually rank for:

```
⚠️ AVOID ultra-generic (impossible to rank):
❌ Single-word keywords: "analytics", "software", "platform", "AI", "automation"
❌ Ultra-broad terms with 50K+ monthly searches
❌ Keywords that Wikipedia/Forbes/major publications dominate

✅ ADD industry context to make keywords rankable:
❌ "[generic term]"           → ✅ "[generic term] + [your industry]"
❌ "analytics"                → ✅ "[your industry] analytics software"
❌ "AI tools"                 → ✅ "AI tools for [specific use case]"
❌ "automation"               → ✅ "[industry] automation platform"
❌ "software"                 → ✅ "[topic] software for [industry]"
```

**Good niche-specific head keywords (2-4 words):**
```
Pattern: [topic] + [industry/use-case]
Pattern: [topic] + software/platform/tools

✅ "[your topic] platform"
✅ "[your topic] software"
✅ "[your topic] tools"
✅ "[industry] [topic]"
✅ "[topic] for [use case]"
```

**Why niche-specific head keywords:**
- Actually rankable (not competing with Wikipedia, Forbes, IBM)
- Still have decent search volume (500-5K/mo)
- Establish authority in YOUR specific niche
- Attract qualified traffic (people looking for your solution)

**Head keyword characteristics:**
- 2-4 words (not 1 word!)
- Industry/niche specific to YOUR business
- Rankable within 6-12 months
- Search volume 500-10K/mo (not 100K+)

### 2. ADD Long-Tail Variations (Intent-Based)

For each article, add 2-3 **long-tail keywords** - these are specific, intent-driven queries with HIGH conversion:

```
Niche Head: "conversation analytics platform"
Long-tail variations:
- "best conversation analytics platform for call centers" (industry + modifier)
- "how to choose conversation analytics platform 2025" (question + year)
- "conversation analytics platform comparison guide" (intent-based)
```

**Long-tail characteristics:**
- 5+ words
- Specific search intent (someone ready to buy/decide)
- Low competition, HIGH conversion
- Question-based or problem-based

**Long-tail patterns that WORK:**
```
Question-based:
- "how to choose [topic]"
- "what is [topic] and how does it work"
- "how to implement [topic] in call centers"

Year-specific:
- "best [topic] tools 2025"
- "[topic] trends 2025"
- "top [topic] software 2025"

Problem-based:
- "why [topic] doesn't improve performance"
- "[topic] not working solutions"
- "how to get ROI from [topic]"

Comparison:
- "[topic A] vs [topic B]"
- "[topic] alternatives"
- "best [topic] for [use case]"
```

### 3. REMOVE Irrelevant Keywords

Remove keywords that:
- Are too generic ("analytics", "platform", "software")
- Don't match the article content
- Are duplicates or near-duplicates
- Have no search intent

### 4. REORDER by Priority

Order keywords by importance:
1. **HEAD keywords first** (1-2 high-volume competitive terms)
2. **Secondary keywords** - supporting terms
3. **Long-tail variations** - specific queries last

### 5. FILTER Brand Keywords

**REMOVE** any keyword containing the brand name:

```
❌ "solidroad conversation analytics"
❌ "solidroad platform"
❌ "solidroad vs competitors"

✅ "conversation analytics platform"
✅ "best conversation analytics"
```

**Why?** You already rank #1 for your brand. Tracking brand keywords wastes Athena slots.

---

## ⚙️ How It Works

### 1. Extract Keywords from All Articles

```python
# For each article (hub, spokes, utilities)
hub_keywords = extract_primary_keywords(hub_md)
# Returns: ['conversation analytics platform', 'agent performance', ...]

spoke_keywords = extract_primary_keywords(spoke_md)
# Returns: ['improving agent performance', 'agent optimization', ...]
```

### 2. Create AI Agent Task

```python
task_file = "step11c_KEYWORD_REVIEW_TASK.md"

# Contains:
# - Review criteria (add long-tail, remove irrelevant, etc.)
# - All articles with their extracted keywords
# - Content preview for context
# - Output format instructions
```

### 3. Create Template CSV

```python
template_csv = "step11c_KEYWORDS_TEMPLATE.csv"

# Pre-filled with extracted keywords as starting point:
# File,Title,Type,Reviewed_Keywords
# step8_ARTICLE.md,"Hub Title",HUB,"keyword1, keyword2"
```

### 4. AI Agent Reviews and Saves

AI agent:
1. Reads task file
2. Reviews each article's keywords
3. Applies all 4 criteria
4. Saves `step11c_REVIEWED_KEYWORDS.csv`

### 5. Pipeline Auto-Continues

```python
# Step 12 loads reviewed keywords
reviewed_keywords_map = load_reviewed_keywords(SESSION_DIR)

# Uses reviewed keywords instead of raw extraction
if reviewed_keywords_map and filename in reviewed_keywords_map:
    keywords = reviewed_keywords_map[filename]
else:
    keywords = extract_primary_keywords(markdown)  # fallback
```

---

## 📊 Inputs & Outputs

### Inputs:
- **Hub file:** From Step 8/10
- **Spoke files:** From Step 10
- **Utility files:** From Step 10A (optional)

### Outputs:

**Task File:** `step11c_KEYWORD_REVIEW_TASK.md`
- Review criteria
- All articles with extracted keywords
- Content previews
- Output format instructions

**Template CSV:** `step11c_KEYWORDS_TEMPLATE.csv`
- Pre-filled with extracted keywords
- AI agent can edit directly

**Reviewed CSV:** `step11c_REVIEWED_KEYWORDS.csv` (AI agent creates)
- Final optimized keywords
- Used by Step 12 for CSV export

---

## 📋 CSV Format

### Input Template:

```csv
File,Title,Type,Reviewed_Keywords
step8_ARTICLE_WITH_CITATIONS.md,"Top 10 Conversation Analytics Platforms for 2025",HUB,"conversation analytics platform, agent performance, sentiment analysis"
step10_spoke01_ai-quality-assurance.md,"AI Quality Assurance: Closing the Insight-to-Action Gap",SPOKE_01,"AI quality assurance, contact center QA, insight-to-action gap"
```

### Output (After Review):

```csv
File,Title,Type,Reviewed_Keywords
step8_ARTICLE_WITH_CITATIONS.md,"Top 10 Conversation Analytics Platforms for 2025",HUB,"conversation analytics, conversation analytics platform, best conversation analytics tools 2025, how to choose conversation analytics, agent performance optimization, sentiment analysis call center"
step10_spoke01_ai-quality-assurance.md,"AI Quality Assurance: Closing the Insight-to-Action Gap",SPOKE_01,"call center QA, quality assurance, AI quality assurance contact center, automated QA for call centers, insight-to-action gap customer service"
```

**Note:** 
- HEAD keywords first ("conversation analytics", "call center QA")
- 5-8 keywords per article (1-2 head + 2-3 long-tail + supporting)
- Do NOT include article title (added automatically later)
- Do NOT include brand name

---

## 🚨 AI Agent Responsibilities

### Your Mission:

**1. Read the Task File**
- Understand all 4 review criteria
- Review each article's extracted keywords
- Check content preview for context

**2. For Each Article:**

```markdown
### Article: AI Quality Assurance

**Extracted Keywords:**
- AI quality assurance
- contact center QA
- insight-to-action gap

**Your Review:**
1. ✅ Keep: "AI quality assurance" (primary)
2. ✅ Keep: "contact center QA" (secondary)
3. ✅ Keep: "insight-to-action gap" (specific concept)
4. ➕ Add: "AI quality assurance contact center" (long-tail)
5. ➕ Add: "automated QA for call centers" (question-based)
6. ➕ Add: "quality assurance automation 2025" (year-specific)

**Final Keywords:** AI quality assurance, contact center QA, insight-to-action gap, AI quality assurance contact center, automated QA for call centers, quality assurance automation 2025
```

**3. Check for Brand Keywords**

```markdown
❌ REMOVE: "solidroad quality assurance"
❌ REMOVE: "solidroad platform"
✅ KEEP: "quality assurance platform" (no brand)
```

**4. Save the CSV**

Save as `step11c_REVIEWED_KEYWORDS.csv` in the session folder.

---

## 🚨 Quality Gates

### Critical Rules:

**Keyword Structure (per article):**
- 5-8 keywords total
- 1-2 NICHE HEAD keywords (2-4 words, industry-specific) - MUST be first
- 2-3 long-tail variations (5+ words, intent-based)
- Supporting keywords to fill out

**Niche Head Keywords Required:**
- Every article MUST have at least 1 niche-specific head keyword
- Head keywords = 2-4 words, industry-focused, RANKABLE
- ✅ Good: "conversation analytics platform", "call center QA software"
- ❌ Bad: "NLP", "analytics", "contact center", "remote work"

**Ultra-Generic Keywords BANNED:**
- ❌ Single-word keywords (except brand-specific terms)
- ❌ Keywords with 50K+ monthly searches (unrankable)
- ❌ Keywords outside the industry niche

**No Brand Keywords:**
- Check for brand name variations
- Remove all brand-containing keywords

**No Title Duplication:**
- Don't include article title as keyword
- Title is added automatically by Step 12

**Comma Separation:**
- Keywords separated by commas
- No trailing commas
- Trim whitespace

---

## 🔧 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Too few keywords | Didn't add long-tail | Add 2-3 variations per article |
| Brand in keywords | Missed brand filter | Search for brand name, remove |
| Duplicate keywords | Similar terms | De-duplicate, keep most specific |
| Wrong CSV format | Extra columns/rows | Follow exact format: File,Title,Type,Reviewed_Keywords |

---

## 📈 Expected Keyword Improvements

### Before Review:

```
Hub: conversation analytics platform, agent performance, sentiment analysis
(3 mid-level keywords, no clear head terms, no long-tail)
```

### After Review:

```
Hub: conversation analytics, speech analytics, conversation analytics platform, best conversation analytics tools 2025, how to choose conversation analytics platform, agent performance optimization call center
(6 optimized keywords: 2 head + 4 long-tail/supporting)
```

**Improvement:**
- HEAD keywords added first ("conversation analytics", "speech analytics")
- +3 long-tail variations for specific intent
- Balanced mix: competitive terms + specific queries
- Year-specific and question-based targeting

---

## 💡 Keyword Ranking Probability Guide

### ⚠️ Ultra-Generic Keywords (AVOID)

These keywords are **impossible to rank for** - dominated by Wikipedia, Forbes, major tech companies:

| Keyword Type | Example | Monthly Volume | Competition | Ranking Chance | Verdict |
|--------------|---------|---------------|-------------|----------------|---------|
| Single-word | "analytics" | 100K+ | Extreme | < 1% | ❌ AVOID |
| Single-word | "software" | 500K+ | Extreme | < 1% | ❌ AVOID |
| Single-word | "AI" | 1M+ | Extreme | < 0.1% | ❌ AVOID |
| Broad concept | "automation" | 50K+ | Extreme | < 1% | ❌ AVOID |
| Broad concept | "customer experience" | 30K+ | Extreme | < 1% | ❌ AVOID |
| Broad concept | "remote work" | 50K+ | Extreme | < 1% | ❌ AVOID |

### ✅ Niche-Specific Head Keywords (USE THESE)

These are **rankable** - specific enough to compete, broad enough for volume:

| Keyword Pattern | Example | Monthly Volume | Competition | Ranking Chance | Verdict |
|-----------------|---------|---------------|-------------|----------------|---------|
| [topic] + platform | "[your topic] platform" | 1K-5K | Medium | 20-35% | ✅ USE |
| [topic] + software | "[your topic] software" | 500-5K | Medium | 25-40% | ✅ USE |
| [topic] + tools | "[your topic] tools" | 500-2K | Medium | 30-45% | ✅ USE |
| [industry] + [topic] | "[industry] [topic]" | 1K-3K | Medium-High | 15-25% | ✅ USE |
| [topic] + for + [use case] | "[topic] for [use case]" | 200-1K | Low-Medium | 35-55% | ✅ USE |

### 🎯 Long-Tail Keywords (HIGHEST CONVERSION)

These **will rank** and convert visitors to customers:

| Keyword Pattern | Example | Monthly Volume | Competition | Ranking Chance | Verdict |
|-----------------|---------|---------------|-------------|----------------|---------|
| best + [topic] + 2025 | "best [topic] tools 2025" | 100-500 | Low | 60-80% | 🎯 PRIORITY |
| how to choose + [topic] | "how to choose [topic]" | 50-200 | Low | 70-90% | 🎯 PRIORITY |
| [topic A] vs [topic B] | "[topic] vs [alternative]" | 100-300 | Low | 65-85% | 🎯 PRIORITY |
| [topic] + for + [specific industry] | "[topic] for [industry] 2025" | 50-150 | Low | 75-90% | 🎯 PRIORITY |

---

## 💡 The Three-Tier Keyword Strategy

### Tier 1: Niche Head Keywords (2-4 words)
- **Purpose:** Build topical authority in your specific niche
- **Volume:** 500-5K/mo
- **Timeline:** 6-12 months to rank
- **Examples:** "conversation analytics platform", "call center QA software"

### Tier 2: Supporting Keywords (3-5 words)
- **Purpose:** Cover related topics, internal linking opportunities
- **Volume:** 200-1K/mo
- **Timeline:** 3-6 months to rank
- **Examples:** "agent performance optimization", "sentiment analysis call center"

### Tier 3: Long-Tail Keywords (5+ words)
- **Purpose:** Capture high-intent traffic, quick wins
- **Volume:** 50-500/mo
- **Timeline:** 1-3 months to rank
- **Examples:** "how to improve call center agent performance 2025"

---

### ❌ What NOT to Do:

```
❌ Single-word keywords     → "analytics", "software", "AI", "automation"
❌ Ultra-broad concepts     → "customer experience", "remote work", "quality"
❌ No industry context      → "[topic]" without specifying your niche
❌ Wikipedia-dominated      → Any term where Wikipedia is #1 result
❌ 50K+ monthly searches    → You can't compete with Fortune 500 companies
```

### ✅ What TO Do:

```
✅ Add industry context     → "[topic] for [your industry]"
✅ Add product type         → "[topic] software" or "[topic] platform"
✅ Add use case             → "[topic] for [specific use case]"
✅ Add year for freshness   → "best [topic] 2025"
✅ Add comparison intent    → "[topic A] vs [topic B]"
```

**The Formula:**
```
Generic keyword + Industry/Use-case context = Rankable keyword

❌ "analytics"
✅ "analytics" + "for [your industry]" = "[your industry] analytics software"
```

**Year-Specific Strategy:**
- **Jan-Oct:** Use CURRENT year → "[topic] 2025"
- **Nov-Dec:** Use NEXT year → "[topic] 2026"
- "best [topic] [TARGET_YEAR]"
- "[topic] trends [TARGET_YEAR]"

**Why Nov-Dec = Next Year?**
- Users searching late in year want future-relevant content
- "Best tools 2026" in Nov 2025 captures Jan search intent
- Higher CTR when new year arrives

**🎯 Month Hack (CTR Boost):**
For competitive niches (Finance, Tech), add "(Updated Month)" to title tags:
- Example: "Best Apps 2025 (Updated November)"
- Signals freshness and increases click-through rate

**⚠️ URL Rule:** NEVER put month or year in URLs (evergreen URLs only)

**Industry-Specific:**
- "[topic] for call centers"
- "[topic] customer service"
- "[topic] contact center"

**Comparison:**
- "[topic] vs [alternative]"
- "[topic] comparison"
- "[topic] alternatives"

---

## 🔗 Data Flow

```
Step 11A/B: Cluster crosslinking complete
  ↓
Step 11C: Extract keywords from all articles
  ↓
Create AI agent task (step11c_KEYWORD_REVIEW_TASK.md)
  ↓
AI agent reviews keywords (adds long-tail, removes brand, reorders)
  ↓
AI agent saves step11c_REVIEWED_KEYWORDS.csv
  ↓
Pipeline auto-continues
  ↓
Step 12: Uses reviewed keywords for CSV export
  ↓
Athena sync: Optimized keywords tracked
```

---

## 📋 AI Agent Workflow

**Step 1: Read Task (5 minutes)**
1. Open `step11c_KEYWORD_REVIEW_TASK.md`
2. Understand review criteria
3. Note brand name to filter

**Step 2: Review Each Article (15-20 minutes)**
1. Open `step11c_KEYWORDS_TEMPLATE.csv`
2. For each row:
   - Review extracted keywords
   - Add 2-3 long-tail variations
   - Remove irrelevant/brand keywords
   - Reorder by priority
3. Update `Reviewed_Keywords` column

**Step 3: Save Output (2 minutes)**
1. Save as `step11c_REVIEWED_KEYWORDS.csv`
2. Verify format (4 columns, comma-separated keywords)

**Total Time: ~25 minutes**

---

## 🔗 Related Steps

- **Requires:** Step 10/10A (articles generated)
- **After:** Step 11A/11B (crosslinking complete)
- **Before:** Step 12 (HTML export)
- **Feeds:** Athena keyword tracking

---

## ✅ Completion Checklist

- [ ] All articles have 5-8 keywords
- [ ] Each article has 1-2 NICHE HEAD keywords (2-4 words, industry-specific) FIRST
- [ ] Each article has 2-3 long-tail variations (5+ words)
- [ ] Keywords ordered: NICHE HEAD → supporting → long-tail
- [ ] ❌ NO ultra-generic keywords (NLP, remote work, contact center, analytics)
- [ ] ❌ NO single-word keywords
- [ ] ❌ NO brand name in any keyword
- [ ] No article titles as keywords
- [ ] CSV format correct (File,Title,Type,Reviewed_Keywords)
- [ ] File saved as `step11c_REVIEWED_KEYWORDS.csv`

---

**Niche-specific keywords = actually ranking. Ultra-generic keywords = wasted tracking. Focus on terms you can WIN, not terms that sound impressive.** 🎯🔑

