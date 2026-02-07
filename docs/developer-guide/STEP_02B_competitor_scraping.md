---
title: COMPETITOR SCRAPING
order: 6
---

# Step 2B: AI Agent Browser Scraping

**Function:** `step2b_create_browser_scraping_task()`  
**Type:** AI Agent Task (Browser Automation)  
**Output:** `step2b_BROWSER_SCRAPING_TASK.md` + `scraped_content/` directory

---

## 🤔 Why This Step Exists

**The Problem:**
You know WHO the competitors are (Step 2). But you don't know WHAT makes their content rank. What structure do they use? How long are their articles? What angles do they take?

**The Reality:**
Observe.ai's article isn't ranked #1 by accident. It has 17 H2 sections, 2,850 words, specific positioning. You need to see what winning content looks like—not guess.

**The Solution:**
Scrape the top 10 competitors. Get the full content. Analyze word counts, structure patterns, content themes. Reverse-engineer what works.

**Without this step:**
- No competitive benchmark (is 2,000 words enough?)
- No structure reference (how many sections?)
- Flying blind (hope your format works)

**With this step:**
- 7-10 full competitor articles scraped
- Average word count: 2,450 words (your target +10%)
- Common structure: 17.6 H2 sections (you need 15-18)

**This step exists because winners leave clues. Scrape them. Study them. Beat them.**

---

## 📝 Overview

Creates an AI agent task to scrape the top 10 most-cited competitor URLs using browser automation tools.

**This is critical competitive intelligence.**

**New Approach (2025-11-21):** Instead of automated requests/BeautifulSoup scraping (which often failed), Step 2B now creates a planned AI agent task from the start.

---

## 🎯 Why It Matters

**What you learn:**
- **Word count benchmarks:** How long should your article be?
- **Structure patterns:** How many H2 sections win rankings?
- **Content themes:** What topics do competitors cover?
- **Content gaps:** What do they cover? What do they miss?
- **SEO tactics:** What on-page optimization do they use?

**Impact on quality:**
Without competitor intel → You're guessing  
With 7-10 scraped articles → You have data-backed structure strategy

---

## ⚙️ How It Works

### 1. Select Top Domains
```python
top_domain_list = [domain for domain, count in top_domains[:10]]
# e.g., ['callminer.com', 'convin.ai', 'qualtrics.com', ...]
```

### 2. Find URLs for Each Domain
```python
urls_to_scrape = []
for domain in top_domain_list:
    for url in all_urls:
        if domain in url.lower():
            urls_to_scrape.append({'domain': domain, 'url': url})
            break  # One URL per domain
```

Result: 10 URLs to scrape (one per top competitor)

### 3. Check if Already Complete
```python
scraped_files = list(Path(full_content_dir).glob("*.txt"))
completion_marker = os.path.join(full_content_dir, "SCRAPING_COMPLETE.txt")

if os.path.exists(completion_marker) or len(scraped_files) >= 7:
    # Already done - load and analyze existing files
    return md_file, scraped_data
```

### 4. Create AI Agent Task
```python
task_file = os.path.join(SESSION_DIR, "step2b_BROWSER_SCRAPING_TASK.md")

# Write comprehensive task file with:
# - List of URLs to scrape
# - Browser automation code examples
# - File format requirements
# - Quality standards
# - Completion instructions
```

### 5. Signal AI Agent
```python
print(f"🤖 AGENT_TASK_READY: {task_file}")
print(f"📋 OUTPUT_DIRECTORY: {full_content_dir}/")
print(f"📋 COMPLETION_MARKER: {completion_marker}")
```

Pipeline pauses here, waiting for AI agent to complete scraping.

---

## 📥 Inputs

**From Step 2:**
- `top_domains` - List of (domain, count) tuples
- `all_urls` - List of all cited URLs

**Parameters:**
- `max_pages=10` - How many competitors to scrape

---

## 📤 Outputs

### If Already Complete:
**File:** `step2b_SCRAPED_ANALYSIS.md`
```markdown
---
title: Competitor Scraping
---

# Step 2B: Competitor Content (Browser Scraped by AI Agent)

## Scraping Summary
- Pages Successfully Scraped: 7 (via AI Agent Browser)
- Average Word Count: 4,879 words

### 1. callminer.com
- URL: https://callminer.com/...
- Word Count: 1,564

(continues for all scraped competitors)

## FOR CLAUDE TO ANALYZE:
1. Content Length Benchmark: What's the target word count?
2. Structure Pattern: How many sections should we use?
3. Competitive Angles: What unique approaches do top pages use?
```

**Data:** `scraped_data` list with domain, URL, word count for each

### If Not Complete:
**File:** `step2b_BROWSER_SCRAPING_TASK.md`

**Contains:**
- Mission statement
- List of 10 URLs to scrape
- Browser automation code examples
- File format template
- Quality standards (500+ words per article)
- Completion marker instructions

**AI Agent Signal:**
```
🤖 AGENT_TASK_READY: step2b_BROWSER_SCRAPING_TASK.md
```

---

## 🚧 Quality Gates

### Pre-Execution:
✅ Top domains identified from Step 2  
✅ URLs mapped to domains  
✅ Output directory created

### Post-Execution (AI Agent Must Meet):
✅ **Minimum 70% success rate** (7/10 URLs)  
✅ **Each article ≥ 500 words**  
✅ **Proper file format** (URL, Domain, Word Count header)  
✅ **Completion marker created** (`SCRAPING_COMPLETE.txt`)

If AI agent scrapes < 7 URLs → Quality gate fails → Must complete more

---

## 🤖 AI Agent Instructions

### Browser Automation Method:

For each URL in the task file, AI agent should:

**1. Navigate:**
```python
mcp_cursor-browser-extension_browser_navigate(url)
```

**2. Extract Content:**
```python
mcp_cursor-browser-extension_browser_evaluate(
    function: '''
    () => {
        const elements = document.querySelectorAll('p, h1, h2, h3, h4, li');
        let texts = [];
        elements.forEach(el => {
            const text = el.textContent.trim();
            if (text.length > 20) texts.push(text);
        });
        const fullText = texts.join(' ');
        return {
            fullText: fullText,
            wordCount: fullText.split(' ').length
        };
    }
    '''
)
```

**3. Save to File:**
```python
# Filename: scraped_content/[domain_with_underscores].txt
# Format:
"""
URL: https://example.com/article
Domain: example.com
Scraped: 2025-11-21 02:00:00
Word Count: 1,564
--------------------------------------------------------------------------------

[Full article content here...]
"""
```

**4. After Scraping 7+ URLs:**
Create completion marker:
```
File: scraped_content/SCRAPING_COMPLETE.txt
Content: List of successfully scraped domains
```

---

## 🔧 Common Issues & Solutions

### Issue 1: Cookie/GDPR Popups Block Content
**Solution:**
```python
# Before extracting, close popup
mcp_cursor-browser-extension_browser_click(
    element="Accept cookies button",
    ref="[button_ref]"
)
```

### Issue 2: Content Behind Login/Paywall
**Solution:**
- Try Archive.org Wayback Machine
- Find alternative URL for same competitor
- Skip and move to next (if 7+ already scraped)

### Issue 3: JavaScript-Heavy Page
**Solution:**
```python
# Wait for content to load
mcp_cursor-browser-extension_browser_wait_for(time=3)

# Then extract
mcp_cursor-browser-extension_browser_evaluate(...)
```

### Issue 4: Incomplete Content Extraction
**Solution:**
```python
# Try alternative selectors
const elements = document.querySelectorAll('article, main, .content');
// Or get all text
const fullText = document.body.innerText;
```

---

## 📊 Success Metrics

**Target:**
- 7-10 URLs scraped (70-100% success rate)
- Average 2,000+ words per article
- Full content captured (not just snippets)

**Minimum:**
- 7 URLs (70% rate)
- 500+ words per article
- Complete paragraphs and headings

**Exceptional:**
- 10/10 URLs (100% rate)
- 3,000+ words average
- Structure metadata captured (H1/H2 counts, link density)

---

## 🚀 How to Improve

### Enhancement 1: Parallel Scraping
AI agent could scrape multiple URLs simultaneously using parallel browser tabs.

### Enhancement 2: Structure Analysis
Extract not just content but:
- H1/H2/H3 hierarchy
- Internal vs external link counts
- Image/video presence
- Word count by section

### Enhancement 3: Smart Retry
If a URL fails, try:
1. Different URL from same competitor
2. Archive.org historical snapshot
3. Related article on same topic

### Enhancement 4: Content Quality Scoring
Auto-score scraped content:
- Readability metrics
- Keyword density
- Structure quality
- Use top-scored articles as primary reference

---

## 📋 Task File Structure

The AI agent receives a comprehensive task file with:

**1. Mission Statement**
- Number of URLs to scrape
- Success rate requirement (70%)

**2. URL List**
```markdown
1. **callminer.com**: https://callminer.com/conversation-analytics/...
2. **convin.ai**: https://convin.ai/products/conversation-analytics...
(10 total)
```

**3. Browser Automation Code**
- Ready-to-use JavaScript extraction function
- File format template
- Naming conventions

**4. Quality Standards**
- 500+ words minimum
- Full content (not snippets)
- Proper metadata headers

**5. Completion Instructions**
- How to mark task complete
- Where to save completion marker

---

## 🔄 Integration with Step 3

**Flow:**
```
Step 2B: Creates browser scraping task
   ↓
AI Agent: Scrapes 7-10 URLs + creates marker
   ↓
Step 3: Detects completion marker
   ↓
Step 3: Loads and analyzes scraped content
```

Step 3 will **wait** if:
- < 5 scraped files exist
- No completion marker found

This ensures clean dependency chain.

---

## 💡 Why Browser Automation vs Requests?

**Old Way (requests + BeautifulSoup):**
- ❌ Blocked by anti-scraping (403, 429 errors)
- ❌ Can't handle JavaScript-rendered content
- ❌ Network permission issues in sandbox
- ❌ ~10% success rate

**New Way (Browser Automation):**
- ✅ Handles JavaScript-rendered pages
- ✅ Bypasses many anti-scraping measures
- ✅ Can interact with page (close popups, scroll)
- ✅ ~70-90% success rate
- ✅ No network permission errors (browser handles it)

---

## 🎯 Key Takeaway

**Step 2B is now a planned AI agent task, not automated scraping.**

It creates a task file upfront and waits for the AI agent to complete it using browser tools. This is more reliable and aligns with the AI-first philosophy.

**No more rescue tasks for scraping failures - it's a planned task from the start.** ✅
