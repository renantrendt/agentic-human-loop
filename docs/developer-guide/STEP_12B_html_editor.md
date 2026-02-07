---
title: HTML QUALITY EDITOR
order: 19
---

# Step 12B: HTML Quality Editor

**Function:** `create_step12b_html_editor_task()`  
**Type:** AI Agent Task  
**Output:** `step12b_HTML_EDITOR_TASK.md` → `step12b_HTML_CLEANED.csv`

---

## 🤔 Why This Step Exists

**The Problem:**
Automated markdown→HTML conversion has blind spots. It misses H3 subsections. Leaves text orphaned (not wrapped in `<p>` tags). Doesn't convert tables. Framer renders broken HTML = broken published pages.

**The Reality:**
HTML quality matters. Missing H3s = lost content hierarchy. Orphaned text = rendering errors. Unconverted markdown tables = ugly raw syntax visible to users. You can't publish this.

**The Solution:**
AI agent reviews every HTML conversion. Adds missing H3 tags. Wraps orphaned text. Converts tables to proper HTML. Validates links. Removes metadata leakage. Makes it publish-ready.

**Without this step:**
- Broken HTML published (bad user experience)
- Content hierarchy lost (missing H3s)
- Tables show as markdown syntax (unprofessional)

**With this step:**
- Clean, valid HTML (perfect Framer rendering)
- Complete heading hierarchy (H1 → H2 → H3)
- Professional tables (proper HTML structure)

**This step exists because automated conversion is 90% there. This step fixes the last 10% that breaks publishing. Quality control before going live.**

---

## 📝 Overview

After Step 12 converts Markdown to HTML, Step 12B creates an AI agent task to review and fix HTML conversion issues. The automated markdown→HTML conversion has limitations (missing H3 tags, orphaned text, table conversion), so AI agent reviews and fixes these before publishing.

---

## 🎯 Why It Matters

**Without HTML Review:**
- ❌ Missing `<h3>` tags (subsections lost)
- ❌ Orphaned text (not wrapped in `<p>` tags)
- ❌ Markdown tables not converted to HTML
- ❌ Malformed tags break Framer rendering
- ❌ Metadata leaks into published content

**With HTML Review:**
- ✅ Complete heading hierarchy (H1, H2, H3)
- ✅ All text properly wrapped in `<p>` tags
- ✅ Tables converted to proper HTML
- ✅ Clean, valid HTML
- ✅ Ready for Framer CMS

---

## 🔍 Issues Detected & Fixed

### **1. Missing H3 Tags**

**Problem:** Subsection headings lost during conversion
```html
<!-- BROKEN -->
<h2>Key Features to Evaluate</h2>
<p>Content about AI transcription...</p>
<p>Content about sentiment analysis...</p>

<!-- FIXED -->
<h2>Key Features to Evaluate</h2>
<h3>AI-Powered Transcription</h3>
<p>Content about AI transcription...</p>
<h3>Sentiment Analysis</h3>
<p>Content about sentiment analysis...</p>
```

### **2. Orphaned Text (Missing Paragraph Tags)**

**Problem:** Text between elements not wrapped
```html
<!-- BROKEN -->
</p>
<strong>Important:</strong> This is critical.
<p>Next paragraph...</p>

<!-- FIXED -->
</p>
<p><strong>Important:</strong> This is critical.</p>
<p>Next paragraph...</p>
```

### **3. Markdown Tables Not Converted**

**Problem:** Table syntax left as markdown
```html
<!-- BROKEN -->
| Platform | Best For |
|----------|----------|
| Solidroad | Training |

<!-- FIXED -->
<table>
  <tr><th>Platform</th><th>Best For</th></tr>
  <tr><td>Solidroad</td><td>Training</td></tr>
</table>
```

### **4. Broken Links**

**Problem:** Empty href attributes
```html
<!-- BROKEN -->
<a href="">Click here</a>

<!-- FIXED -->
<a href="/blog/article-slug">Click here</a>
```

### **5. Metadata Not Removed**

**Problem:** Internal metadata in HTML
```html
<!-- BROKEN -->
<p><strong>Primary Keywords:</strong> conversation analytics...</p>
<p><strong>Word Count:</strong> 4,500 words</p>

<!-- FIXED -->
(Removed entirely - metadata is internal only)
```

---

## ⚙️ How It Works

### 1. Automated Analysis
```python
# Script analyzes HTML in CSV
for article in articles:
    html = article['Content_Part1']
    
    # Check for:
    - Missing <h3> tags (should exist if >5000 chars)
    - Orphaned text (not in <p> tags)
    - Markdown tables (| --- |)
    - Broken links (<a href="">)
    - Metadata present
```

### 2. Create Task File
```python
create_step12b_html_editor_task(csv_file)
→ Outputs: step12b_HTML_EDITOR_TASK.md

Contains:
- List of articles with issues
- Specific issues per article
- HTML quality checklist
- Common fix examples
```

### 3. AI Agent Reviews & Fixes
```
🤖 AI Agent:
   1. Opens step12_FRAMER_EXPORT.csv
   2. For each article with issues:
      - Fix missing <h3> tags
      - Wrap orphaned text in <p>
      - Convert tables to HTML
      - Validate links
      - Remove metadata
   3. Saves cleaned CSV: step12b_HTML_CLEANED.csv
```

### 4. Pipeline Detects Completion
```python
if os.path.exists("step12b_HTML_CLEANED.csv"):
    ✅ HTML review complete
    → Proceed to Step 13 (evaluation)
```

---

## ✅ Quality Checklist

**For each article, AI agent verifies:**

### **Structure**
- [ ] Has `<h2>` section headings
- [ ] Has `<h3>` subsection headings where needed
- [ ] Heading hierarchy correct (H1→H2→H3)
- [ ] No empty headings (`<h2></h2>`)

### **Paragraphs**
- [ ] ALL text wrapped in `<p>` tags
- [ ] No orphaned text between tags
- [ ] Paragraphs properly closed
- [ ] No malformed tags

### **Tables**
- [ ] Markdown tables → HTML `<table>`
- [ ] Proper structure: `<tr><th><td>`
- [ ] Headers use `<th>` tags
- [ ] No leftover `|---|` markdown

### **Links**
- [ ] No broken links (`href=""`)
- [ ] All links valid and complete
- [ ] External links have full URLs
- [ ] Internal links use `/blog/slug` format

### **Lists**
- [ ] `<li>` only inside `<ul>` or `<ol>`
- [ ] Lists properly opened/closed
- [ ] No orphaned list items

### **Cleanup**
- [ ] Metadata removed (Keywords, Links, Word Count)
- [ ] Horizontal rules removed (`<hr>`)
- [ ] No markdown syntax remaining (`**`, `##`)
- [ ] HTML entities correct (`&amp;`, `&lt;`)

---

## 🔧 Common Fixes

### **Add Missing H3s**
Look for subsection patterns in content:
- "How X Works" → `<h3>How X Works</h3>`
- List of features → Add H3 per feature
- Numbered steps → H3 per step

### **Wrap Orphaned Text**
```html
<!-- Find patterns like: -->
</p>
Text here
<p>

<!-- Wrap in <p>: -->
</p>
<p>Text here</p>
<p>
```

### **Convert Tables**
```
Markdown: | Col1 | Col2 |
HTML:     <table><tr><th>Col1</th>...
```

---

## 📊 Typical Issues Per Article

**Hub articles (4000+ words):**
- 5-10 missing H3 tags
- 2-3 orphaned text sections
- 1 table needing conversion
- 0-1 broken links

**Spoke articles (1500-2000 words):**
- 2-4 missing H3 tags
- 1-2 orphaned text sections
- 0-1 tables
- 0 broken links

**Total time:** 10-15 minutes per article × 11 = ~2 hours

---

## 🎯 Success Criteria

**Step 12B complete when:**
- ✅ `step12b_HTML_CLEANED.csv` exists
- ✅ All 11 articles reviewed
- ✅ All HTML structure issues fixed
- ✅ No markdown syntax remaining
- ✅ Ready to publish to Framer

---

## 🚀 Next Steps

After Step 12B:
- ✅ HTML is clean and valid
- → Step 13: Quality evaluation
- → Publishing: Upload to Google Sheets/Framer

**The HTML is now publication-ready!** 🎯

