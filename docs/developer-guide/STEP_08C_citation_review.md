---
title: CITATION REVIEW
order: 12.2
---

# Step 8C: Citation Review (AI Agent Task)

**Function:** `step8c_create_citation_review_task()`  
**Type:** ⭐ AI Agent Task (conditional)  
**Output:** 
- `step8c_CITATION_REVIEW_TASK.md` - Instructions for AI agent
- `articles/hub/step8c_ARTICLE_CITATIONS_FINAL.md` - Fixed article (AI agent creates this)
- `step8c_CITATIONS_REVIEWED.txt` - Completion marker (AI agent creates this)

---

## 🤔 Why This Step Exists

**The Problem:**
Automated citation matching (Step 8) and verification (Step 8B) handle most cases, but some require human/AI judgment:
- Broken links need alternatives or removal
- Unverified claims need sources or rewrites
- Edge cases: redirects, paywalls, regional blocks

**The Reality:**
Not every citation problem has an automated solution. A broken McKinsey link might need a replacement from BCG. An unverified statistic might need to be rewritten as general knowledge.

**The Solution:**
Create an AI Agent task ONLY when Step 8B finds issues. The agent reviews each problem and applies the appropriate fix.

**Without this step:**
- Broken links published
- Unverified claims remain
- No quality gate

**With this step:**
- Human/AI judgment applied
- Every issue addressed
- Quality assured before publish

**This step exists because automation handles 90% of cases. The AI Agent handles the other 10%.**

---

## 📝 Overview

Step 8C is a conditional AI Agent task. It only triggers when Step 8B's verification report shows broken links or unverified claims. The AI Agent reviews each issue and fixes it.

---

## 🎯 When It Triggers

Step 8C **only** creates a task when Step 8B reports:
- ❌ Broken citations > 0, OR
- 🔍 Unverified claims > 0

If Step 8B verdict is "READY FOR PUBLISHING," Step 8C is skipped entirely.

---

## 📄 Task File

### `step8c_CITATION_REVIEW_TASK.md`

```markdown
# STEP 8C: Citation Review Task (AI Agent)

**Session:** session_20251129_xxx
**Generated:** 2025-11-29T10:30:00Z

---

## 🎯 YOUR MISSION

Review and fix citation issues identified in the verification report.

---

## Verification Report

[Full report from Step 8B embedded here]

---

## Instructions

### For Broken Links:

1. **Try to find the correct URL:**
   - Search for the article title
   - Check archive.org for cached version
   - Find alternative source with same information

2. **If no alternative found:**
   - Remove the citation
   - Rewrite the sentence to not require a citation
   - Or mark as general knowledge if appropriate

### For Unverified Claims:

1. **Search for a real source:**
   - Use web search to find supporting data
   - Prefer authoritative sources (Gartner, Forrester, academic)
   - Ensure the source actually contains the claimed information

2. **If no source exists:**
   - Rewrite the claim to be more general
   - Remove specific numbers/percentages
   - Or remove the claim entirely if not essential

---

## Output

Save the fixed article to: `articles/hub/step8c_ARTICLE_CITATIONS_FINAL.md`

Mark this task complete by creating: `step8c_CITATIONS_REVIEWED.txt`
```

---

## 🔧 AI Agent Actions

### For Broken Links

| Scenario | Action |
|----------|--------|
| URL moved | Find new URL via search |
| Page deleted | Check archive.org |
| Site down | Find alternative source |
| No alternative | Remove citation, rewrite sentence |

### For Unverified Claims

| Scenario | Action |
|----------|--------|
| Source exists | Search and add citation |
| Claim is common knowledge | Remove marker, keep text |
| Claim is dubious | Rewrite to be more general |
| Claim is false | Remove entirely |

---

## ✅ Completion

### Required Files

1. **Fixed Article:** `articles/hub/step8c_ARTICLE_CITATIONS_FINAL.md`
2. **Completion Marker:** `step8c_CITATIONS_REVIEWED.txt`

### Marker File Contents

```
Citation review completed.
Broken links fixed: 1
Unverified claims resolved: 3
Date: 2025-11-29T10:45:00Z
```

---

## ⚙️ Pipeline Behavior

### Before 8C Complete
Pipeline pauses at Step 8C, waiting for marker file.

### After 8C Complete
1. Pipeline detects `step8c_CITATIONS_REVIEWED.txt`
2. Uses `step8c_ARTICLE_CITATIONS_FINAL.md` as the article
3. Continues to Step 9 (Infrastructure)

---

## 💡 Best Practices

### Finding Alternative Sources

1. **Google the claim** - Often finds the original source
2. **Check competitor articles** - They may cite the same data
3. **Use Perplexity** - Ask directly for sources on the topic
4. **Academic sources** - Google Scholar for research papers

### Rewriting Claims

**Before (specific, needs citation):**
> "Organizations see 23.5% cost reduction when implementing this technology."

**After (general, no citation needed):**
> "Organizations typically report significant cost savings after implementation."

### When to Remove

Remove claims that:
- Cannot be verified
- Are outdated (>3 years old)
- Come from unreliable sources
- Don't add value to the article

---

## 🔧 Troubleshooting

### Task Not Created
Step 8B found no issues. Check `step8b_CITATION_VERIFICATION_REPORT.md` to confirm.

### Pipeline Stuck at 8C
Create the marker file: `step8c_CITATIONS_REVIEWED.txt`

### Fixed Article Not Used
Ensure file is saved to exact path: `articles/hub/step8c_ARTICLE_CITATIONS_FINAL.md`
