---
title: INTERNAL LINKS
order: 11
---

# Step 7: Internal Links

**Function:** `create_step7_internal_links_task()`  
**Type:** AI Agent Task  
**Output:** `step7_INTERNAL_LINKS_TASK.md` → `step7_ARTICLE_WITH_INTERNAL_LINKS.md`

---

## 🤔 Why This Step Exists

**The Problem:**
Your article is an island. No links to other Solidroad content. No PageRank distribution. No topic relationship signals. Google sees isolated content—not a content ecosystem.

**The Reality:**
Internal linking is SEO 101. Hub should link to all 10 spokes. Spokes should link back to hub. Google crawls these connections and understands "this site owns the entire conversation analytics topic cluster."

**The Solution:**
Add 8-12 contextual internal links. Not keyword-stuffed forced links—natural mentions where it makes sense. AI agent reads context and places links where they add value.

**Without this step:**
- Isolated article (no topic authority signal)
- Zero PageRank distribution
- Missed user journey opportunities

**With this step:**
- Hub ↔ Spoke network established
- PageRank flows through cluster
- Users discover related content naturally

**This step exists because articles don't rank alone—clusters rank. Internal links tell Google "we own this entire topic, not just one keyword." That's topical authority.**

---

## 📝 Overview

Creates an AI agent task to add 8-12 contextually relevant internal links to the article.

**AI agent identifies best placement for internal links based on context and available link inventory.**

---

## 🎯 Why It Matters

**SEO Impact:**
- Distributes PageRank across site
- Helps Google understand topic relationships
- Improves crawlability and indexation
- Boosts rankings for linked pages

**Why AI Agent (Not Automated):**
- **Context awareness:** AI understands best placement (not just keyword matching)
- **Natural integration:** Links flow with content, not forced
- **Varied anchor text:** AI uses different phrasing for same target
- **Quality judgment:** AI avoids over-linking or awkward placements

---

## ⚙️ How It Works

### 1. Create AI Agent Task
```python
create_step7_internal_links_task(article_file)
→ Outputs: step7_INTERNAL_LINKS_TASK.md
```

### 2. Task Provides Link Inventory
The task file includes:
- Product pages (solidroad.com/products/...)
- Blog posts (solidroad.com/blog/...)
- Hub articles (if part of cluster)
- Spoke articles (if part of cluster)

### 3. AI Agent Adds Links
AI agent:
- Reads the article content
- Reviews available link inventory
- Identifies contextual placement opportunities
- Adds 8-12 links with varied anchor text
- Ensures natural distribution (not clustered)
- Saves to: `step7_ARTICLE_WITH_INTERNAL_LINKS.md`

### 4. Pipeline Detects Completion
```python
if os.path.exists("step7_ARTICLE_WITH_INTERNAL_LINKS.md"):
    ✅ Step 7 complete
    → Proceed to Step 8 (citations)
```

---

## 📋 What AI Agent Receives

**Task File:** `step7_INTERNAL_LINKS_TASK.md`

**Contains:**
- Input article filename
- Available internal links (products, blog posts, hub, spokes)
- Link placement rules
- Quality standards (8-12 links, varied anchor text)

**AI Agent Must:**
1. Read the article
2. Identify contextual placement opportunities
3. Add links naturally (not forced)
4. Use varied anchor text
5. Save to `step7_ARTICLE_WITH_INTERNAL_LINKS.md`

---

## ✅ Quality Standards

**Link Count:** 8-12 internal links
**Distribution:** Spread throughout article (not clustered)
**Anchor Text:** Varied (not repetitive)
**Context:** Natural fit with surrounding text
**Priority:** Product pages > Hub > Spokes > Blog

---

## 🎯 Current Implementation

**Step 7 is an AI AGENT TASK**, not automated!

The pipeline:
1. Creates task file with available links
2. Pauses for AI agent to complete
3. Detects completion when output file exists
4. Proceeds to Step 8

This gives better quality than keyword-matching automation!
# Before match: Check for ']('
# After match: Check for ')'
# Ensures we don't double-link

if '](' not in before_text and ')' not in after_text:
    # Safe to link
```

### 4. Add Markdown Link
```python
matched_text = match.group()  # "agent performance"
article_content = article_content[:match.start()] + \
                  f'[{matched_text}]({url})' + \
                  article_content[match.end():]
```

### 5. Log and Report
```python
links_added += 1
link_log.append(f"GENERAL: {matched_text} -> {url}")
```

---

## 📊 Inputs & Outputs

### Inputs:
- Article file (from Step 6 or Step 5)
- `internal_linking_map.json`
- Synthesis data (for cluster/spoke context)

### Outputs:
**`step7_ARTICLE_WITH_LINKS.md`:**
- Same article content
- Internal links added as markdown `[text](url)`

**`step7_INTERNAL_LINKS_REPORT.md`:**
```markdown
## Summary:
- Links Added: 3

## Links Applied:
- GENERAL: agent performance -> /blog/improve-agent-performance
- GENERAL: sentiment analysis -> /blog/sentiment-analysis-call-center
- GENERAL: qa automation -> /blog/qa-automation-guide
```

---

## 🚨 Quality Considerations

### Not a Hard Blocker:
This step doesn't trigger rescue tasks because:
- Internal linking is optimization (not content creation)
- Can be added manually post-publish
- Gracefully skips if linking map missing

### Quality Indicators:
- **Good:** 3-5 internal links per article
- **Better:** 5-7 internal links strategically placed
- **Excessive:** 10+ links (feels spammy)

---

## 🔧 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| No links added | No keyword matches | Check if linking map has relevant entries |
| Too many links | Same keyword repeated | Already limited to first match only |
| Broken links | URL in map doesn't exist | Validate map has published URLs only |
| Link in wrong place | Keyword appears in heading | Could enhance with context check |

---

## 📈 Internal Linking Best Practices

### 1. Distribute Links Naturally
**Bad:**
```markdown
## Related Resources
- [Link 1]
- [Link 2]
- [Link 3]
```
All clustered at end.

**Good:**
```markdown
## Agent Performance
For coaching specifically, see our [agent performance guide](url).

## Sentiment Analysis
Emotion detection helps... (read more about [sentiment analysis](url))

## QA Automation
Automated scorecards reduce... using [qa automation](url) tools.
```
Distributed throughout content.

### 2. Contextual Anchor Text
**Bad:**
```markdown
Click [here](url) for more info.
Learn more about this [topic](url).
```

**Good:**
```markdown
[Agent performance analytics](url) improve coaching workflows.
[Sentiment analysis tools](url) detect customer emotions.
```
Keyword-rich, contextual.

### 3. Link Hierarchy
**Priority:**
1. Hub links to all spokes (distribution)
2. Spokes link to Hub (authority flow)
3. Spokes link to related spokes (horizontal)
4. Avoid circular loops

---

## 💡 How to Improve

### Enhancement 1: Smart Link Placement
Avoid linking in:
- Headings (bad UX)
- First paragraph (save for intro flow)
- Last paragraph (keep for CTA)

Prefer linking in:
- Middle sections
- After explaining concept
- Where it adds value

### Enhancement 2: Link Diversity
```python
# Don't always link first match
# If keyword appears 5x, link 2nd or 3rd occurrence
# Varies anchor text
```

### Enhancement 3: Cluster-Aware Linking
```python
if article_is_hub:
    # Link to ALL spokes (10 links)
elif article_is_spoke:
    # Link to Hub + 1-2 related spokes (3-4 links)
```

### Enhancement 4: Link Validation
```python
# Before adding link, verify:
# 1. Target URL exists (published)
# 2. Not already linked elsewhere in article
# 3. Contextually relevant (not forced)
```

---

## 🎓 SEO Strategy

### Internal Link Types:

**1. Navigational:**
- Hub → Spokes
- "For deep-dive on [topic], see our [guide](url)"

**2. Contextual:**
- Within explanation
- "This is why [concept](url) matters"

**3. Related:**
- Spoke → Spoke (same cluster)
- "Similar to [related topic](url)"

### Link Equity Distribution:

```
Hub Article (High Authority)
  ↓ (distributes authority)
Spoke 1, Spoke 2, Spoke 3...
  ↑ (flows authority back)
Hub Article (Authority strengthened)
```

**Virtuous cycle:** Hub empowers spokes, spokes strengthen hub

---

## 🔗 Data Flow

```
Step 6: Article with brand voice
  ↓
Step 7: Load internal linking map
  ↓
Match keywords in article
  ↓
Add markdown links [text](url)
  ↓
Save linked article
  ↓
Step 8: Add external citations
```

---

## 📋 Linking Strategy

### For Hub Articles:
- Link to 5-10 spokes (if available in map)
- Distribute throughout article
- Use varied anchor text

### For Spoke Articles:
- Link to parent Hub (always)
- Link to 1-2 related spokes (same cluster)
- Total: 3-5 internal links

### General Articles:
- Link to relevant published content
- Follow keyword matching from map
- Respect "published" status only

---

## 🔗 Related Steps

- **Requires:** Step 6 (article), internal_linking_map.json
- **Feeds:** Step 8 (citations), Step 9 (infrastructure)
- **Enhanced by:** Step 10 (spoke cluster creates more link opportunities)

---

**Internal linking = SEO foundation. Don't skip this.** 🔗

**Next:** [STEP_08_citations.md](STEP_08_citations.md)


