---
title: LINK VERIFICATION
order: 20.1
---

# Step 12D: Link Verification

**Function:** `create_step12d_link_verification_task()`  
**Type:** AI Agent Task (Browser Automation)  
**Output:** `step12d_LINK_VERIFICATION_TASK.md` → `step12d_LINK_VERIFICATION_REPORT.md`

---

## 🤔 Why This Step Exists

**The Problem:**
You just published 11 articles with 141 internal links and 30+ citations. But you don't know if they actually work:

```markdown
[Solidroad's SCORE methodology](https://www.solidroad.com)
```
- **Claims:** Specific SCORE methodology content
- **Reality:** Might be 404, or just homepage, or wrong page
- **User experience:** Click → disappointment → bounce

**The Reality:**
Links break. Writers make mistakes. URLs change. What worked when you wrote it might be broken when published. And citations - are they accessible? Do they actually support your claims? Or did you cite something irrelevant?

**Without this step:**
- ❌ Broken links in published content
- ❌ Misleading links (homepage when promising specific content)
- ❌ Bad citations (don't support claims)
- ❌ Poor user experience
- ❌ SEO penalty (broken links hurt rankings)

**With this step:**
- ✅ All links verified before publishing
- ✅ Citations actually support claims
- ✅ Issues documented with fix recommendations
- ✅ Professional quality control

**This step exists because link quality matters. One broken link = lost user. Ten broken links = lost credibility. Verify everything before publishing.**

---

## 📝 Overview

AI agent uses browser automation to test every internal link and citation URL, checking if:
1. Page exists (not 404)
2. Content matches link text promise
3. Citations support the claims

**Turns link quality from assumption to verification.**

---

## 🎯 What Gets Verified

### **1. Internal Solidroad Links (~141 links)**

**Checks:**
- URL returns 200 (not 404)
- Page content matches link text
- Not misleading (specific claim → homepage)

**Example verification:**
```python
Link: [IQS framework](https://www.solidroad.com/blog/iqs-framework)

Checks:
✅ URL exists? (navigate and check)
✅ Page discusses IQS? (search page content)
❌ If 404 → Flag as broken
❌ If homepage → Flag as misleading
```

### **2. External Citations (~30 citations)**

**Checks:**
- URL accessible (not 404, not paywall)
- Source is authoritative (check domain)
- Content supports the claim (keyword verification)

**Example verification:**
```python
Claim: "Research shows 10-15% improvement..."
Citation: [[1]](https://www.trainingjournal.com/article)

Checks:
✅ URL accessible?
✅ Page contains "10-15%" or "improvement"?
✅ Source is credible (trainingjournal.com = yes)?
❌ If paywall → Flag (users can't verify)
❌ If no mention of claim → Flag (citation doesn't support)
```

### **3. Cross-Article Links**

**Checks:**
- Slug matches actual article title
- Link goes to correct hub/spoke

---

## ⚙️ How It Works

### 1. Task Creation (Automated)
```python
create_step12d_link_verification_task()
→ Counts all links in articles
→ Creates verification task with instructions
```

### 2. AI Agent Executes (Browser Automation)
```python
For each link:
  1. mcp_cursor-browser-extension_browser_navigate(url)
  2. Check if page loads (200 vs 404)
  3. mcp_cursor-browser-extension_browser_snapshot()
  4. Verify content matches link text
  5. Record: valid, broken, or misleading
```

### 3. Report Generated
```
step12d_LINK_VERIFICATION_REPORT.md

Contains:
- Valid links count
- Broken links (with fix recommendations)
- Misleading links (claim vs reality)
- Citation issues (doesn't support claim)
```

### 4. Pipeline Detects Completion
```python
if os.path.exists("step12d_LINK_VERIFICATION_REPORT.md"):
    ✅ Links verified
    → Proceed to Step 13 (evaluation)
```

---

## 🚨 Common Issues Found

### **Issue 1: Homepage Overuse**
```markdown
[SCORE methodology](https://www.solidroad.com)
```
- ❌ Link text is specific
- ❌ URL is generic homepage
- ✅ **Fix:** Create `/blog/score-methodology` OR update link text

### **Issue 2: Wrong Slugs**
```markdown
[How to choose platform](/blog/choosing-platform)
```
- ❌ Slug doesn't match actual article
- ✅ Actual: `/blog/how-to-choose-conversation-analytics-platform`
- ✅ **Fix:** Update slug to match

### **Issue 3: Citation Doesn't Support Claim**
```markdown
"Studies show 90% improvement" [[1]](study-url)
```
- ❌ Navigate to URL → Page says "80-85% improvement"
- ✅ **Fix:** Update claim to match citation OR find better citation

### **Issue 4: Paywalled Citations**
```markdown
[[1]](https://paywalled-journal.com/article)
```
- ❌ Users can't verify (behind paywall)
- ✅ **Fix:** Find open-access alternative

---

## 📊 Typical Results

**Per 11-article cluster:**
- Total links: 140-150
- Valid: 110-120 (80%)
- Issues: 20-30 (20%)

**Issue breakdown:**
- Homepage overuse: 10-15 links
- Broken URLs: 2-5 links
- Wrong slugs: 3-5 links
- Citation issues: 2-3 citations

**Fix time:** 1-2 hours to resolve all issues

---

## 🎯 Success Criteria

- ✅ All internal links verified
- ✅ All citations verified
- ✅ Report generated with issues + fixes
- ✅ No broken links in published content

**Output:** Professional link quality before publishing!

---

## 🔗 Related Steps

- **Requires:** Step 12 (HTML export), Step 12C (gap analysis)
- **Complements:** Step 12C identifies missing destinations, 12D verifies existing links work
- **Before:** Step 13 (evaluation) - fix links before quality check

---

## 🚀 Next Steps

After Step 12D:
1. Review `step12d_LINK_VERIFICATION_REPORT.md`
2. Fix broken links (update URLs or create content)
3. Fix misleading links (update text or destinations)
4. Fix citation issues (better sources or updated claims)
5. Re-run Step 12D to verify fixes

**Loop until all links verified!**

---

**No broken links in published content. Ever.** 🎯

