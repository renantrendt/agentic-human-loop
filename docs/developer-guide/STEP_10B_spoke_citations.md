---
title: SPOKE CITATIONS
order: 15
---

# Step 10B: Add Citations to Spokes

**Function:** Sequential citation task creation  
**Type:** AI Agent Tasks (10 tasks, one per spoke)  
**Output:** `step10b_CITATIONS_TASK_spoke01.md` through `spoke10.md`

---

## 🤔 Why This Step Exists

**The Problem:**
You just generated 10 spoke articles (Step 10). They're good. But they have [CITATION NEEDED] placeholders everywhere. You can't publish unsourced claims.

**The Reality:**
The hub got citations in Step 8 (before spokes existed). Now you have 10 new articles that need the same treatment. That's 30-50 claims that need authoritative sources.

**The Solution:**
Create individual citation tasks for each spoke. AI agent goes through all 10, finds sources, replaces placeholders, adds bibliographies. Sequential but systematic.

**Without this step:**
- 10 spokes with unsourced claims (low credibility)
- Publishing incomplete content (quality risk)
- Manual citation research (20+ hours of work)

**With this step:**
- All 10 spokes get proper citations
- External authority established (E-E-A-T boost)
- Systematic process (nothing forgotten)

**This step exists because the hub getting citations isn't enough. Every spoke needs the same level of authority. 11 articles, all cited, all credible.**

---

## 📝 Overview

After Step 10 generates 10 spoke articles, Step 10B creates individual citation tasks for each spoke. AI agent completes these sequentially, adding external citations to establish credibility and authority.

---

## 🎯 Why It Matters

**Without Citations:**
- ❌ Spokes lack credibility signals
- ❌ No external validation of claims
- ❌ Weaker E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness)
- ❌ Google may view content as opinion vs fact-based

**With Citations:**
- ✅ External validation from authoritative sources
- ✅ Stronger E-E-A-T signals
- ✅ Better rankings (cited content ranks higher)
- ✅ User trust (readers see sources backing claims)

---

## ⚙️ How It Works

### 1. Pipeline Detects Spokes
```python
spoke_files = sorted(Path(SESSION_DIR).glob("step10_spoke*.md"))
# Finds all generated spokes (01-10)
```

### 2. Creates Individual Citation Tasks
```python
for i, spoke_file in enumerate(spoke_files, 1):
    create_step8_citations_task(spoke_file, article_type=f"spoke{i:02d}")
    
    # Outputs:
    # step10b_CITATIONS_TASK_spoke01.md
    # step10b_CITATIONS_TASK_spoke02.md
    # ...
    # step10b_CITATIONS_TASK_spoke10.md
```

### 3. Each Task Contains
- Input spoke filename
- Number of [CITATION NEEDED] placeholders found
- Instructions for finding authoritative sources
- Output filename (update spoke in place)
- Quality standards

### 4. AI Agent Completes Sequentially
```
🤖 AI Agent workflow:
   For each task (spoke01 → spoke10):
      1. Open spoke file
      2. Find [CITATION NEEDED] markers
      3. Research authoritative sources
      4. Replace with numbered citations [[1]], [[2]], etc.
      5. Add bibliography at bottom
      6. Save updated spoke
```

---

## 📋 Task File Format

**Example: `step10b_CITATIONS_TASK_spoke01.md`**

```markdown
# STEP 8: Research & Add External Citations

**Article Type:** SPOKE01

## 🎯 YOUR TASK

Research authoritative sources and replace ALL [CITATION NEEDED] markers.

**Input Article:** step10_spoke01_ai-quality-assurance-insight-to-action-gap.md
**Output Article:** step10_spoke01_ai-quality-assurance-insight-to-action-gap.md
**Citations Found:** 3 placeholders

## ⚠️ CRITICAL RULES

- NO citations in TL;DR or first paragraph
- Use authoritative sources (research, industry reports, reputable publications)
- Add bibliography at bottom with full URLs
```

---

## ✅ Success Criteria

**For Step 10B to Complete:**
- ✅ 10 citation task files created
- ✅ Each task has correct input/output filenames
- ✅ Tasks logged to console

**What Happens Next:**
- Pipeline proceeds to Step 10C (verification)
- Step 10C checks if AI agent completed the work
- If incomplete, creates review task and waits
- If complete, marks 10C as done and proceeds

---

## 🔄 Sequential Processing

**Why Sequential (Not Batch)?**

1. **Quality focus:** AI agent can focus on one article at a time
2. **Error handling:** Easier to identify which spoke has issues
3. **Progress tracking:** Can see 3/10 done, 7 remaining
4. **Flexibility:** Can pause/resume between spokes

**Estimated Time:** 5-10 minutes per spoke × 10 = 50-100 minutes total

---

## 🎓 FAQ

**Q: Can I skip citations for spokes?**  
A: No - Step 10C quality gate enforces citations. Spokes without citations block pipeline.

**Q: How many citations per spoke?**  
A: Typically 3-5 for 1,500-2,000 word spokes. More for complex topics.

**Q: What if a spoke has no [CITATION NEEDED]?**  
A: Step 10C will pass it automatically. Only spokes with placeholders need citations.

**Q: Can I do them out of order?**  
A: Yes! Tasks are independent. Do spoke05 first if you want.

---

## 🚀 Next Steps

After Step 10B creates tasks:
1. AI agent completes citation tasks
2. Step 10C verifies all spokes
3. If verified → Step 11 (crosslinking)
4. If not → Loop back with review task

**Bottom Line:** Step 10B sets up the work, Step 10C verifies it's done!

