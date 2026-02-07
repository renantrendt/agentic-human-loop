---
title: UTILITY ARTICLE GENERATION
order: 14.1
---

# Step 10A: Utility Article Generation

**Function:** `step10a_generate_utility_articles()`  
**Type:** ⭐ AI Agent Task (Manual)  
**Output:** `step10a_UTILITY_GENERATION_TASK.md` → AI agent generates 3-5 utilities

---

## 🤔 Why This Step Exists

**The Problem:**
You just generated 10 spokes. Writers naturally referenced useful resources:

```markdown
Check our [QA Scorecard Template](solidroad.com)
Use our [Metrics Calculator](solidroad.com)
Download [Empathy Markers Guide](solidroad.com)
```

- **Claims:** Specific utility content exists
- **Reality:** Links to homepage (doesn't exist!)
- **User experience:** Frustration, lost credibility

**The Reality:**
Writers know what readers need. When 3 spokes reference "QA Scorecard Template," that's a proven demand signal. But we can't just create 43 articles blindly - that's the AI slop trap.

**The Solution:**
After spokes are generated, analyze gaps, identify high-value utilities (templates, calculators, guides), and create 3-5 strategic articles using the Dead-End strategy (new article A links *back* to Hub A and Hub B. It does *not* link to new missing topics. It closes the loop, effectively "capping" the content sprawl.)

**Without this step:**
- Broken promises (links to templates that don't exist)
- Manual gap analysis (tedious)
- Create utilities too late (after crosslinking/HTML)
- Or create too many (AI slop)

**With this step:**
- Data-driven (gaps from actual spokes)
- Right timing (before crosslinking)
- Controlled (3-5 max, Dead-End strategy)
- High value (templates, guides, calculators)

**This step exists because your spokes tell you what utilities to create. Listen to them, but don't let them lead you into infinite content generation.**

---

## 📝 Overview

Analyzes the 10 generated spokes for referenced utility content that doesn't exist. Creates a **detailed task** for AI agent to generate 3-5 high-value utility articles using the Dead-End strategy to prevent infinite content loops.

**Consistent with Steps 5/10:** Task-based approach (AI agent writes articles)

**Why task-based:**
- AI agent can review spoke context before writing
- Ensures utilities match brand voice
- Allows strategic decisions (skip low-value utilities)
- Consistent pipeline pattern

**Runs after:** Step 10 (spokes generated)  
**Runs before:** Step 11 (crosslinking) - so utilities get linked!

---

## 🎯 What Gets Analyzed

**Step 10A scans spokes for:**

### **High-Value Utility Content:**
- Templates (QA scorecards, checklists, forms)
- Calculators (ROI, metrics, benchmarks)
- Guides (implementation, best practices)
- Resources (downloadable, actionable)

**Filters out:**
- Generic branding ("Solidroad's approach")
- Vague features ("our platform")
- One-off mentions (low demand)

**Example finding:**
```
Spoke 02 references: "QA scorecard template" → Homepage
Spoke 05 references: "QA scorecard template" → Homepage  
Spoke 08 references: "QA scorecard template" → Homepage

Gap: "QA scorecard template" (3 mentions)
Action: ✅ CREATE (proven demand!)
```

---

## 🛡️ The Dead-End Strategy (Why It's Critical)

**The AI Slop Trap:**
```
Round 1: Generate 10 spokes → 27 gaps identified
Round 2: Generate 27 utilities → 81 new gaps!
Round 3: Generate 81 articles → 243 gaps!
∞ Infinite content creation
```

**The Dead-End Solution:**
```
Utility Article Constraints:
1. Links ONLY to existing hub + spokes
2. Does NOT reference new missing topics
3. Closes loops, doesn't open them

Result: Fixed number of articles, no exponential growth
```

### **How Dead-End Works:**

**❌ Standard Article (Opens Loops):**
```markdown
# QA Scorecard Template

Introduction...

For best results, use with our [Advanced Analytics Dashboard](link)... ← NEW GAP!
Consider our [Custom Reporting Tool](link)... ← NEW GAP!
Learn about [Data Integration Guide](link)... ← NEW GAP!

Result: 1 article created → 3 new gaps!
```

**✅ Dead-End Article (Closes Loops):**
```markdown
# QA Scorecard Template

Introduction...

For best results, combine with [conversation analytics](hub)... ← EXISTS!
See also [Agent Performance](spoke-08)... ← EXISTS!
Learn more about [Quality Metrics](spoke-10)... ← EXISTS!

Result: 1 article created → 0 new gaps! ✅
```

**Implementation:**
```
Step 10A prompt includes:

CRITICAL CONSTRAINT - Dead-End Strategy:
- Link ONLY to existing cluster content
- Hub: [hub title]
- Spokes: [list of 10 spoke titles]
- DO NOT reference: New methodologies, new tools, new concepts
- This is a utility "leaf node" - it serves the cluster, doesn't expand it
```

**Why this works:**
- Utility serves existing content (supplements, doesn't compete)
- All outbound links strengthen cluster (not create demands)
- Cluster growth is capped (10 spokes + 5 utilities = 15 max)

---

## ⚙️ How It Works

### 1. Analyze Spoke Gaps
```python
for spoke in 10_spokes:
    links = extract_internal_links(spoke)
    
    for link in links:
        if link.text.contains('template', 'calculator', 'guide'):
            if link.url == homepage:
                utility_gaps[link.text] += 1

# Result: "QA Scorecard Template" (3x), "ROI Calculator" (2x), etc.
```

### 2. Filter to High-Value
```python
high_value = []

for gap, count in utility_gaps:
    if gap_type == 'template' and count >= 1:
        high_value.append(gap)  # Templates always valuable
    elif gap_type == 'guide' and count >= 2:
        high_value.append(gap)  # Guides if 2+ mentions
    elif gap_type == 'calculator':
        high_value.append(gap)  # Calculators always valuable

high_value = high_value[:5]  # Cap at 5
```

### 3. Create Generation Task
```python
task = create_task(
    utilities_to_create=high_value,
    constraint="Dead-End: Link only to hub + existing spokes"
)
```

### 4. Auto-Generate Utilities (Fully Automated!)
```python
if ANTHROPIC_API_KEY:
    # Extract REAL hub title from hub file
    hub_title = extract_title_from("articles/hub/step8_ARTICLE_WITH_CITATIONS.md")
    
    # Extract REAL spoke titles from spoke files
    spoke_titles = [extract_title_from(spoke_file) for spoke_file in spoke_files]
    
    for utility_gap in high_value_gaps:
        # Generate with Claude Sonnet 4
        prompt = f"""
        Generate utility article: {utility_gap}
        
        CRITICAL - Dead-End Strategy:
        Link ONLY to these existing articles:
        - Hub: {hub_title}
        - Spokes: {spoke_titles}
        
        DO NOT reference new topics!
        1,500-2,000 words, practical, actionable.
        """
        
        article = claude_sonnet_4.generate(prompt)
        save_to(f"articles/utilities/{slug}.md")
        
        # Verify Dead-End compliance
        check_for_new_gaps(article)

# Result: 3-5 utilities auto-generated with real titles!
```

**Key difference from Steps 5/10:**
- Steps 5/10: Create task, AI agent manually generates
- Step 10A: **Auto-generates** utilities immediately (no manual step!)
- Uses REAL hub + spoke titles for accurate Dead-End linking

**Why auto-generate here:**
- Utilities are formulaic (templates, guides, calculators)
- Dead-End constraint is clear (link only to existing)
- Low risk (only 3-5 articles)
- Keeps pipeline flowing (no manual intervention)

### 5. Pipeline Continues
```
Step 10A complete (utilities created!)
    ↓
Step 11: Crosslink (10 spokes + 5 utilities = 15 articles)
Step 12: Convert all 15 to HTML
```

---

## 📊 Typical Findings

**Per 10-spoke cluster:**
- Utility gaps identified: 10-15
- High-value utilities: 3-5
- Most common: Templates, calculators, guides
- Created: 3-5 articles (within cluster limits)

**Example utilities:**
1. QA Scorecard Template (mentioned 3x)
2. ROI Calculator (mentioned 2x)
3. Implementation Checklist (mentioned 2x)
4. Metrics Benchmarks Guide (mentioned 1x, but high value)
5. Coaching Best Practices (mentioned 1x, but high value)

---

## ✅ Success Criteria

**After Step 10A (automated):**
- ✅ Spoke gaps analyzed (10 spokes scanned)
- ✅ 3-5 utilities identified (high-value only)
- ✅ Task file created with Dead-End constraints
- ✅ Output paths specified

**After AI agent completes utilities (manual):**
- ✅ 3-5 utilities generated (1,500-2,000 words each)
- ✅ All utilities use Dead-End strategy (link only to hub + spokes)
- ✅ Cluster stays under 18 articles (10 spokes + 5 utilities max)
- ✅ No new gaps created (Dead-End enforced)
- ✅ Completion marker created (`step10a_UTILITIES_COMPLETE.txt`)

**Output Files:**
- `step10a_UTILITY_GENERATION_TASK.md` (task for AI agent)
- `articles/utilities/*.md` (3-5 utilities - after AI agent generates)
- `step10a_UTILITIES_COMPLETE.txt` (completion marker - after AI agent finishes)

**Then utilities ready for Steps 11-12 processing!**

---

## 🚫 Hard Limits (Prevent AI Slop)

**Rule 1: Maximum Utilities**
- 5 utilities maximum per cluster
- NO EXCEPTIONS

**Rule 2: Dead-End Enforcement**
- Every utility MUST link only to existing content
- Checked before accepting article

**Rule 3: Cluster Cap**
- Total articles ≤ 18
- If (10 spokes + utilities) > 18 → Reduce utility count

**Rule 4: High-Value Only**
- Templates ✅ (always valuable)
- Calculators ✅ (always valuable)
- Guides ✅ (if 2+ mentions)
- Generic content ❌ (ignore)

---

## 🎯 Why Timing Matters

**Step 10A runs AFTER spokes but BEFORE crosslinking:**

**Too early (Step 9):**
- Can't analyze gaps (spokes don't exist yet)
- Blind utility generation
- Might create wrong articles

**Just right (Step 10A):**
- ✅ Spokes exist (can analyze gaps)
- ✅ Before crosslinking (utilities get linked)
- ✅ Before HTML (all converted together)

**Too late (Step 12F):**
- ❌ After crosslinking (need to re-link)
- ❌ After HTML (need to re-convert)
- ❌ Inefficient double processing

---

## 🔗 Dead-End Strategy Example

**Utility Article: "QA Scorecard Template"**

**Dead-End Compliant:**
```markdown
# QA Scorecard Template

## How to Use

1. Download template
2. Customize for your [conversation analytics](hub) needs
3. Integrate with [agent performance tracking](spoke-08)

## Best Practices

Based on [quality measurement approaches](spoke-10)...

**Internal links:** Hub + 2 spokes = 3 total
**New gaps created:** 0 ✅
```

**NOT Dead-End Compliant:**
```markdown
# QA Scorecard Template

## Advanced Features

Pair with our [Advanced Analytics Suite](new-gap)... ❌
Use our [Custom Integration Tool](new-gap)... ❌
See [API Documentation](new-gap)... ❌

**Internal links:** 3 NEW missing topics
**New gaps created:** 3 ❌
```

**Enforcement:**
Task explicitly lists existing content to link to. AI agent can ONLY link to listed content.

---

## 💡 Strategic Value

**Utility articles are different from spokes:**

**Spokes:**
- Topical deep-dives
- Keyword-focused
- Educational content

**Utilities:**
- Practical tools
- Download/use-focused
- Conversion-oriented

**Both serve hub but different purposes!**

**Example cluster:**
```
Hub: "Top 10 Conversation Analytics Platforms"
├─ Spokes (10): Topic deep-dives
└─ Utilities (5): Practical tools
   ├─ QA Scorecard Template
   ├─ ROI Calculator
   ├─ Implementation Checklist
   ├─ Metrics Benchmarks
   └─ Coaching Best Practices
```

**Result:** 15 articles covering theory + practice!

---

## 🎓 When Step 10A Skips (Automatic)

**Step 10A automatically skips if:**
- No utility gaps identified (spokes are self-contained)
- Cluster already at capacity (15+ articles)

**Pipeline handles this:**
```python
if no_utility_gaps_found:
    log("✅ No utilities needed - spokes are complete!")
    return None  # Skip to Step 11

# Otherwise: Create task for AI agent
create_task_file(high_value_gaps)
log("🤖 AI agent should now generate utilities")
```

**Automatic decision** - pipeline determines if utilities are needed!

---

## 🚀 Next Steps

After Step 10A completes:
- ✅ Utilities saved to `articles/utilities/`
- ✅ Summary saved to `step10a_UTILITIES_COMPLETE.txt`
- **Step 11:** Automatically includes utilities in crosslinking task
  - Spokes get linked to hub
  - Utilities get linked where naturally relevant
  - Full cluster interconnection (hub + 10 spokes + 3-5 utilities)
- **Step 12:** Automatically includes utilities in HTML export
  - All 13-15 articles converted to HTML
  - Utilities appear in Framer CSV alongside hub/spokes
  - Ready for publishing
- **Step 12C:** Verifies no new gaps created (Dead-End worked!)

**Integration is seamless - utilities flow through the rest of the pipeline automatically!** 

**Dead-End strategy prevents the AI slop trap while serving real user needs!** 🎯

