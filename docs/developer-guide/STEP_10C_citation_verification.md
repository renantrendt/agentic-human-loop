---
title: CITATION VERIFICATION
order: 16
---

# Step 10C: Verify Spoke Citations (Quality Gate)

**Function:** Automated verification with smart loop  
**Type:** Quality Gate (Automated with AI agent feedback loop)  
**Output:** `step10c_CITATIONS_VERIFIED.txt` (if pass) or `step10c_CITATION_REVIEW_TASK.md` (if fail)

---

## 🤔 Why This Step Exists

**The Problem:**
You asked AI agent to add citations to 10 spokes (Step 10B). Did they actually do it? Did they skip any? How do you know all 10 are done before proceeding?

**The Reality:**
Manual tracking sucks. "Did I finish spoke 7?" "Which ones still need citations?" Humans forget. Mistakes happen. You need automated verification.

**The Solution:**
Quality gate that automatically checks all 10 spokes. Passes only when EVERY spoke has citations. If incomplete, creates updated task showing exactly which ones still need work. Smart loop re-checks when AI agent signals done.

**Without this step:**
- Manual verification (error-prone)
- Publishing incomplete content (some spokes missing citations)
- No forcing function (easy to skip)

**With this step:**
- Automated verification (can't proceed until done)
- Clear progress tracking (3/10 complete → 7/10 → 10/10)
- Pipeline enforces quality (zero compromise)

**This step exists because quality gates prevent mistakes. You don't guess if citations are done—the pipeline verifies it. If it's not done, you can't proceed. That's zero compromise.**

---

## 📝 Overview

Automatically checks if all 10 spokes have proper citations. If any are missing, creates a review task for AI agent and halts the pipeline. When AI agent fixes issues and sets a flag, pipeline auto-detects and re-verifies.

**Smart loop:** Pipeline automatically re-checks when AI agent signals completion, no manual tracking needed!

---

## 🎯 Why It Matters

**Quality Gate Purpose:**
- Ensures no article proceeds without citations
- Maintains content credibility standards
- Prevents publishing incomplete content

**Smart Loop Benefit:**
- AI agent doesn't need to remember what's done
- Pipeline automatically re-verifies
- Progress is incremental (3/10 → 7/10 → 10/10)
- No manual coordination needed

---

## ⚙️ How It Works

### 1. Automated Verification Check
```python
for spoke_file in spoke_files:
    content = open(spoke_file).read()
    
    # Check for actual citations
    has_citations = bool(re.search(r'\[\[\d+\]\]', content))
    
    # Check for placeholders
    has_placeholders = bool(re.search(r'\[CITATION NEEDED\]', content))
    
    if has_citations or not has_placeholders:
        ✅ PASS
    else:
        ❌ FAIL - needs citations
```

### 2A. If ALL Pass
```python
✅ Create: step10c_CITATIONS_VERIFIED.txt
→ Mark Step 10C complete
→ Proceed to Step 11 (crosslinking)
```

### 2B. If ANY Fail
```python
⚠️ Create: step10c_CITATION_REVIEW_TASK.md
   Contains:
   - List of spokes missing citations
   - Instructions for AI agent
   - Flag filename to create when done

⏸️ HALT pipeline (sys.exit(0))
```

---

## 🔄 The Smart Loop

### **First Run:**
```
Step 10C: Check citations
   Status: 0/10 complete
   
   Creates: step10c_CITATION_REVIEW_TASK.md
   "Spokes missing citations:
    - spoke01 (has 3 [CITATION NEEDED])
    - spoke02 (has 0 citations)
    - spoke03 (has 0 citations)
    ...
    
   🎯 YOUR TASK: Add citations
   ✅ WHEN DONE: Create step10c_CITATIONS_READY_FOR_VERIFICATION.txt"
   
⏸️ Pipeline halts
```

### **AI Agent Works:**
```
🤖 Fixes spoke01, spoke02, spoke03
   Creates: step10c_CITATIONS_READY_FOR_VERIFICATION.txt
```

### **Second Run (Auto-Triggered):**
```bash
python3 content_pipeline_with_ai_agent.py --resume
```

```
Step 10C: Detects flag file exists
   → Re-checks all spokes
   Status: 3/10 complete ✅ (was 0/10!)
   
   Updates: step10c_CITATION_REVIEW_TASK.md
   "Spokes STILL missing citations:
    - spoke04
    - spoke05
    ...
    (only 7 remaining, was 10)"
   
⏸️ Pipeline halts again (but made progress!)
```

### **Third Run:**
```
🤖 AI agent fixes 4 more spokes
   Updates flag

→ --resume

Step 10C: Re-checks
   Status: 7/10 complete
   
Still 3 missing... loop continues
```

### **Final Run:**
```
Step 10C: Re-checks
   Status: 10/10 complete! ✅
   
✅ QUALITY GATE PASSED
💾 Creates: step10c_CITATIONS_VERIFIED.txt
🧹 Deletes flag (cleanup)

→ Proceeds to Step 11 ✅
```

---

## 🎯 Key Features

### **Automatic Re-Verification**
- AI agent creates flag: `step10c_CITATIONS_READY_FOR_VERIFICATION.txt`
- Pipeline detects flag on --resume
- Automatically re-runs Step 10C check
- No manual coordination needed!

### **Incremental Progress**
- First check: 0/10 ❌
- Second check: 3/10 ⚠️ (progress!)
- Third check: 7/10 ⚠️ (more progress!)
- Final check: 10/10 ✅ (done!)

### **Always Up-to-Date Task**
- Review task updates each run
- Shows current missing spokes
- Removes completed ones from list

---

## 📊 What Gets Checked

**For each spoke, verifies:**

| Check | Pass Condition |
|-------|----------------|
| Has numbered citations | `[[1]]`, `[[2]]`, `[[3]]` found ✅ |
| No placeholders | No `[CITATION NEEDED]` found ✅ |

**Pass if EITHER:**
- Spoke has numbered citations, OR
- Spoke has no [CITATION NEEDED] placeholders

**Fail if:**
- Spoke has [CITATION NEEDED] but no numbered citations

---

## 🔧 Files Created

**On Failure:**
- `step10c_CITATION_REVIEW_TASK.md` - Lists what needs fixing

**On Success:**
- `step10c_CITATIONS_VERIFIED.txt` - Marks quality gate passed

**AI Agent Flag:**
- `step10c_CITATIONS_READY_FOR_VERIFICATION.txt` - Triggers re-check

---

## 💡 Pro Tips

**For AI Agent:**
1. Fix spokes in batches (3-4 at a time)
2. Create flag after each batch
3. Pipeline will show incremental progress

**For Pipeline:**
- Each --resume automatically re-checks
- No need to manually track progress
- Review task always shows current status

---

## 🎓 FAQ

**Q: What if I fix all spokes but forget to create the flag?**  
A: Just --resume anyway - Step 10C will check files directly, not just the flag.

**Q: Can I delete the flag file?**  
A: Yes - it's just a signal. Pipeline checks actual spoke files for citations.

**Q: What if only 1 spoke is missing?**  
A: Review task will show just that one spoke. Fix it and --resume.

**Q: Does this work for the hub too?**  
A: No - hub citations are handled in Step 8. This is only for spokes.

---

## 🚀 Next Steps

After Step 10C passes:
- ✅ All 11 articles have citations (hub + 10 spokes)
- → Proceed to Step 11 (cluster crosslinking)
- → Proceed to Step 12 (HTML export)
- → Proceed to Step 13 (quality evaluation)

**Bottom Line:** Step 10C ensures quality before publishing. No incomplete articles slip through! 🎯

