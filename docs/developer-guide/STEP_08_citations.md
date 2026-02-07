---
title: CITATIONS
order: 12
---

# Step 8: External Citations

**Function:** `step8_find_citations()`  
**Type:** Automated (calls external script)  
**Output:** `step8_CITATIONS_REPORT.md`, `citations_report.json`

---

## 🤔 Why This Step Exists

**The Problem:**
Your article says "Manual QA teams review only 1-2% of calls." Okay. Says who? No source? That's an opinion, not a fact. Google (and readers) don't trust unsourced claims.

**The Reality:**
E-E-A-T (Experience, Expertise, Authoritativeness, Trust) matters. External citations from high-authority domains (Gartner, Forrester, industry research) validate your claims. "Trust me" < "According to Gartner..."

**The Solution:**
Find authoritative sources for every factual claim. Add citations to industry research, case studies, competitor data. 3-5 quality citations = credibility boost.

**Without this step:**
- Unsourced claims (readers skeptical)
- Lower E-E-A-T signals (Google penalty risk)
- No external validation (just your opinion)

**With this step:**
- Claims backed by authority sources
- Higher trust signals (Google rewards this)
- Professional credibility established

**This step exists because opinions lose to facts. And facts need sources. Citations turn "trust me" into "the data shows." That's the difference.**

---

## 📝 Overview

Runs `citation_finder.py` to find and verify external citations for factual claims in the article, ensuring authority and trustworthiness.

**Adds external authority to support claims.**

---

## 🎯 Why It Matters

**SEO Impact:**
- External links to authoritative sources = Trust signal
- Citations validate claims = E-E-A-T (Experience, Expertise, Authoritativeness, Trust)
- Proper sourcing = Reduced risk of penalties

**Content Quality:**
- Uncited stats = "Trust me bro"
- Cited stats = Verifiable facts
- 3-5 quality citations = Industry standard

**Legal/Reputation:**
- Wrong stat without source = Liability
- Cited source = Defensible claim

---

## ⚙️ How It Works

### 1. Check for Citation Finder Script
```python
citation_finder_path = '../renan-v1-scripts/citation_finder.py'

if not os.path.exists(citation_finder_path):
    ⚠️ Skip step (optional dependency)
```

### 2. Convert Markdown to HTML
```python
# citation_finder.py expects HTML input
html_content = md_content.replace('\n## ', '\n<h2>')
```

**Why:** Legacy tool compatibility

### 3. Run Citation Finder
```python
subprocess.run([
    'python3', citation_finder_path,
    '--input', temp_html,
    '--scraped-dir', scraped_dir,
    '--output', citations_output
], timeout=300)
```

### 4. Parse Results
```python
citations_data = json.load('citations_report.json')

approved = citations_data.get('citations_approved', 0)
rejected = citations_data.get('citations_rejected', 0)
```

### 5. Generate Report
```markdown
## Summary:
- Claims Found: 12
- Citations Approved: 4
- Citations Rejected: 8
- Coverage: 33.3%
- Target: 3-5 external links
- Status: ✅ Good (within range)
```

---

## 📊 Inputs & Outputs

### Inputs:
- Article file (from Step 7)
- `scraped_content/` directory (source pool)
- `citation_finder.py` script (external dependency)

### Outputs:
**`citations_report.json`:**
```json
{
  "total_claims_found": 12,
  "citations_approved": 4,
  "citations_rejected": 8,
  "coverage_percentage": 33.3,
  "citations": [
    {
      "claim": "Manual QA teams review only 1-2% of calls",
      "url": "https://observe.ai/research/qa-coverage",
      "source_api": "scraped_content",
      "domain_authority": "75"
    },
    ...
  ],
  "rejected_citations": [
    {
      "claim": "...",
      "rejection_reason": "Low domain authority"
    }
  ]
}
```

**`step8_CITATIONS_REPORT.md`:**
- Summary statistics
- Approved citations (with DA scores)
- Rejected citations (with reasons)

---

## 🚨 Quality Considerations

### Not a Hard Blocker:
This step is optional because:
- External script dependency (might not exist)
- Citations can be added manually post-publish
- Gracefully skips if citation_finder.py not found

### Quality Target:
- **Good:** 3-5 external citations
- **Acceptable:** 2-3 citations (better than none)
- **Insufficient:** 0-1 citations (low authority signal)
- **Excessive:** 10+ citations (feels like research paper, not blog)

---

## 🔧 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| citation_finder.py not found | Script in different location | Update path or skip step |
| Timeout (>300s) | Large article + many claims | Increase timeout or optimize script |
| All rejected | Low-DA sources in scraped dir | Scrape higher-authority competitors |
| No claims found | Article lacks specific stats | Add more data-backed claims |

---

## 📈 Citation Guidelines

### What to Cite:

**1. Statistics:**
```markdown
Manual QA teams review only 1-2% of calls [CITATION NEEDED]
→ Find source from industry report or competitor article
```

**2. Industry Benchmarks:**
```markdown
Conversation analytics improve CSAT by 18-30% [CITATION NEEDED]
→ Link to case study or research
```

**3. Regulatory/Compliance:**
```markdown
PCI DSS requires call recording for payment processing [CITATION NEEDED]
→ Link to official compliance documentation
```

### What NOT to Cite:

**1. Common Knowledge:**
```markdown
Call centers handle customer support
→ No citation needed (obvious)
```

**2. Your Own Claims:**
```markdown
Solidroad automates coaching workflows
→ Link to own case study (not external citation)
```

**3. Opinions:**
```markdown
Most platforms stop at analytics
→ Your analysis-based opinion (not fact requiring citation)
```

---

## 💡 How to Improve

### Enhancement 1: Pre-Citation Finding
Run BEFORE article generation:
```python
# Step 4 synthesis identifies key claims
# Step 4.5: Find citations for claims
# Step 5: Generate article WITH citations already
```

### Enhancement 2: Domain Authority Validation
Only accept high-DA sources:
```python
if source_da < 50:
    reject_citation("Low domain authority")
```

### Enhancement 3: Citation Freshness
Prefer recent sources:
```python
if source_date < '2023-01-01':
    ⚠️ Warning: Outdated source (>2 years old)
```

### Enhancement 4: Multiple Source Validation
Cross-reference claims:
```python
# If claim appears in 2+ sources → Higher confidence
# If claim appears in 1 source only → Verify or use [CITATION NEEDED]
```

---

## 🎓 Citation Strategy

### Approved Citation Criteria:

**Source Quality:**
- Domain Authority: 50+ (preferably 60+)
- Source type: Industry research, official documentation, reputable publications
- Recency: Published within 2 years (for stats)

**Claim Match:**
- Citation supports the exact claim made
- No misrepresentation
- Context preserved

**Examples:**
- ✅ Gartner research report (DA: 92)
- ✅ Forrester analyst blog (DA: 88)
- ✅ Observe.ai case study (DA: 75)
- ❌ Random blog comment (DA: 23)
- ❌ Competitor marketing page (biased)

---

## 🔗 Data Flow

```
Step 5/6: Article with [CITATION NEEDED] placeholders
  ↓
Step 7: Article with internal links
  ↓
Step 8: Run citation_finder.py
  ↓
Search scraped content for matching claims
  ↓
Validate domain authority
  ↓
Approve or reject citations
  ↓
Generate report (4 approved, 8 rejected)
  ↓
AI agent manually adds approved citations to article
  OR
  Step 9 proceeds (citations added post-publish)
```

---

## 📋 Post-Citation Workflow

**If citations found:**
1. Review `step8_CITATIONS_REPORT.md`
2. Manually add approved citations to article:
   ```markdown
   Manual QA teams review only 1-2% of calls[^1]
   
   [^1]: [Observe.ai Research Report](https://observe.ai/research)
   ```
3. Replace `[CITATION NEEDED]` placeholders

**If no citations found:**
1. Note which claims need citations
2. Manually research sources
3. Add citations post-publish
4. Or use `[CITATION NEEDED]` as reminder for content team

---

## 🔗 Related Steps

- **Requires:** Step 7 (article), scraped_content/ (source pool), citation_finder.py (external)
- **Feeds:** Manual citation addition (not automated yet)
- **Optional:** Can skip if script not found

---

## 🛠️ Technical Details

### citation_finder.py (External Script)

**What it does:**
- Parses article for factual claims (stats, benchmarks)
- Searches scraped competitor content for matching claims
- Validates domain authority of sources
- Returns approved/rejected citations

**Not part of main pipeline:**
- Separate script in `renan-v1-scripts/`
- Can be enhanced or replaced
- Optional dependency

---

**External citations = Authority building** 📚

**Next:** [STEP_09_infrastructure.md](STEP_09_infrastructure.md)


