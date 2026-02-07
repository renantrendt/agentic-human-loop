---
title: SPOKE CLUSTER
order: 14
---

# Step 10: Spoke Cluster Generation

**Function:** `step10_generate_spoke_cluster()`  
**Type:** ⭐ AI AGENT REQUIRED (If Hub Detected)  
**Output:** 10 spoke articles + linking infrastructure updates

---

## 🤔 Why This Step Exists

**The Problem:**
Publishing a single article = competing for 1 keyword. Google sees isolated content.

**The Reality:**
Your competitors aren't just writing one article—they're building content ecosystems. One listicle article can't establish topical authority. You're bringing a knife to a gunfight.

**The Solution:**
Hub & Spoke architecture. 1 comprehensive hub + 10 supporting spokes = 11 ranking opportunities. Google sees you as THE authority on the entire topic cluster, not just one keyword.

**Without this step:**
- You rank for 1 keyword (maybe)
- No topical authority signal
- Competitors with content clusters dominate you
- Missed opportunity to own the entire buyer journey

**With this step:**
- 11 articles covering the full keyword ecosystem
- Topical authority established
- Internal linking network strengthens all pieces
- Solidroad dominates the entire "conversation analytics" space

**This step exists because single articles don't win anymore. Clusters do.**

---

## 📝 Overview

If Step 4 synthesis identifies the article as a **Hub (Pillar Content)**, this step automatically generates 10 supporting spoke articles to establish topical authority.

**Goal:** Dominate entire keyword cluster with interconnected content ecosystem.

---

## 🎯 Why It Matters

### SEO Impact:
- **1 Hub article** = 1 ranking opportunity
- **1 Hub + 10 Spokes** = 11 ranking opportunities
- **11 interconnected articles** = Topical authority signal to Google

### Business Impact:
- Cover entire buyer journey (awareness → consideration → decision)
- Answer specific questions prospects search for
- Establish Solidroad as THE authority on conversation analytics

### User Impact:
- Hub: Entry point for broad searches
- Spokes: Deep dives answering specific questions
- Natural progression through content

---

## ⚙️ How It Works

### 1. Detect Hub Article
```python
if 'cluster (hub)' in synthesis_text.lower():
    is_hub = True
    # Proceed with spoke generation
else:
    is_hub = False
    # Skip (this is a spoke itself)
```

### 2. Extract Spoke Topics
**From Step 4 synthesis:**
```markdown
**Potential Spokes:**
1. How to Choose a Conversation Analytics Platform
2. Implementation Guide
3. ROI Calculator
...
```

**Fallback (if <10 suggested):**
Uses data-driven topics from Step 1 bigrams:
- Agent performance (978 mentions)
- Sentiment analysis (786 mentions)
- Quality assurance (734 mentions)
- etc.

### 3. Create AI Agent Task
Generates `step10_SPOKE_CLUSTER_TASK.md` with:
- 10 spoke titles & primary keywords
- Data sources for each spoke
- Anti-cannibalization checklist
- Internal linking strategy
- Quality gates

### 4. Signal AI Agent
```
🤖 AGENT_TASK_READY: SPOKE CLUSTER GENERATION
📊 Spokes to Generate: 10
🎯 Hub Article: [title]
⏸️ Pipeline paused...
```

### 5. Validate When Complete
Checks if all 10 spokes exist + keyword overlap validation

---

## 📊 The 10 Spoke Articles

### Category 1: Implementation (3 spokes)
1. **How to Choose** - Decision framework
2. **Implementation Guide** - Rollout steps
3. **ROI Calculator** - Cost-benefit analysis

### Category 2: Use Cases (4 spokes)
4. **Agent Performance** - Coaching workflows (978 mentions!)
5. **Sentiment Analysis** - Emotion detection (786 mentions!)
6. **QA Automation** - Scorecard automation (734 mentions!)
7. **CSAT Improvement** - Detractor identification (529 mentions!)

### Category 3: Comparisons (2 spokes)
8. **vs Conversation Intelligence** - Feature comparison (732 mentions!)
9. **vs Speech Analytics** - Technology differences (397 mentions!)

### Category 4: Advanced (1 spoke)
10. **AI vs Traditional QA** - Solidroad's AI-native positioning

**Each targets a UNIQUE long-tail keyword** - no cannibalization!

---

## 🚨 AI Agent Mission (Batched Generation with Review Checkpoints)

### CRITICAL: Read Before EACH Batch

**Mandatory files to read before generating any spoke:**
1. `step4_AGENT_SYNTHESIS.md` - Keyword strategy refresh
2. `step1_FOR_AGENT_ANALYSIS.md` - N-gram frequencies (978x, 786x, etc.)
3. **`brand-context/solidroad`** ⭐ - Unique insights (IQS, SCORE, Crypto.com case study)
4. `step3_FOR_AGENT_ANALYSIS.md` - Competitor patterns
5. Previous spokes in batch - Anti-cannibalization check

### Batch 1: Spokes 1-3

**Generate Spoke 1:**
- Keyword: "agent performance" (978x mentions)
- Brand Insight: IQS framework
- Intent: How-to / Performance optimization

**Generate Spoke 2:**
- Keyword: "sentiment analysis" (786x)
- Brand Insight: 100% coverage vs 1-2% manual sampling
- Intent: Educational / Feature deep-dive

**Generate Spoke 3:**
- Keyword: "quality assurance" (734x)
- Brand Insight: Automated QA → immediate coaching
- Intent: Comparison / Tools evaluation

**CHECKPOINT 1:** Validate unique keywords, data usage, brand context integration

### Batch 2: Spokes 4-6

**RE-READ all files, review Batch 1, find unused insights**

- Spoke 4: "actionable insights" (604x) + Insight-to-action gap
- Spoke 5: "customer experience" (653x) + CX as feedback engine
- Spoke 6: "natural language processing" (311x) + AI-native platform

**CHECKPOINT 2:** Cross-batch validation, no repetition

### Batch 3: Spokes 7-9

**Full refresh, complete inventory of used keywords/insights**

- Spoke 7: "conversation intelligence" (732x) + SCORE methodology
- Spoke 8: "customer service teams" (281x) + Crypto.com case study
- Spoke 9: "contact centers" (466x) + Remote monitoring

**CHECKPOINT 3:** Full cluster anti-cannibalization

### Spoke 10: Strategic Capstone

**Review entire cluster (Hub + 1-9), tie it together**

- Spoke 10: "customer satisfaction" (529x) + Qual vs Quant KPIs

**FINAL VALIDATION:** Complete 11-article cluster check

---

### Phase 1: Generate Each Spoke

**For each spoke:**

1. **Read Required Files** (see above - MANDATORY!)
2. **Filter Data:** Extract spoke-specific keywords from Step 1
3. **Unique Angle:** Different from Hub and all other spokes
4. **Generate:** 1,500-2,000 words, 5-7 H2 sections
5. **Apply Writing Rules:** brand-context/rule_writing.ts
6. **Validate:** Unique keyword, different intent, no repetition
7. **Save:** `step10_spoke##_[title].md` (NO links yet)

### Phase 2: Add Internal Links (After ALL 10 Complete)

**Step 1: Update Hub Article**
Add 1 contextual link to EACH spoke (10 total):
```markdown
For agent coaching specifically, see our [Agent Performance Improvement guide](spoke04_url).
...
When choosing a platform, check our [selection framework](spoke01_url).
```

**Distribute throughout Hub** - not clustered in one section

**Step 2: Update Each Spoke**
For each spoke, add:
- Link to Hub (always, near intro)
- Link to 1-2 related spokes:
  - Spoke 1 → Spoke 2, Spoke 3 (same category)
  - Spoke 4 → Spoke 5, Spoke 6 (same category)
  - Spoke 8 → Spoke 9 (same category)

**Step 3: Update Infrastructure**
- Add all 10 spokes to `internal_linking_map.json`
- Add all 10 URLs to sitemap
- Create cross-reference matrix

---

## 🔒 Anti-Cannibalization System

### How We Prevent Keyword Conflict:

**1. Unique Primary Keywords**
- Hub: "conversation analytics platform"
- Spoke 1: "choose conversation analytics platform"
- Spoke 4: "improve agent performance analytics"
- **No overlap = No cannibalization**

**2. Different Search Intents**
- Hub: Informational (what is it?)
- Spoke 1: Comparative (which one?)
- Spoke 2: Educational (how to implement?)
- Spoke 3: Acquisition (what's the ROI?)

**3. Distinct Angles**
- Hub: Comprehensive overview
- Spokes: Deep dive on specific subtopic

**4. Quality Validation**
Pipeline checks for >3 shared content words between titles:
```python
shared_words = set(title1.split()) & set(title2.split())
if len(shared_words - common_words) > 3:
    ⚠️ Warning: Potential overlap
```

---

## 📊 Data Sufficiency

### Do We Have Enough for 10 Spokes?

**YES!** ✅

**Evidence:**
- 696 call-center QA responses analyzed
- 50 keyword combinations (30 bigrams + 20 trigrams)
- 10 competitor articles scraped
- Multiple search intents identified

**Math:**
- Need: 10 unique topics
- Have: 50 keyword combinations
- **Ratio: 5x more data than needed**

**Confidence:** 90%+

---

## 🔧 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Not detected as Hub | Synthesis didn't say "Cluster (Hub)" | Re-check Step 4 synthesis format |
| <10 spoke topics suggested | Synthesis incomplete | Uses data-driven fallback |
| Spokes sound repetitive | Same angle used | Review anti-cannibalization checklist |
| Keyword overlap | Similar titles | Use cannibalization validator |

---

## 📈 Internal Linking Architecture

```
Hub: Conversation Analytics Platform
├── Links OUT to all 10 spokes (distributed)
│
├── Spoke 1: How to Choose
│   ├── Links TO: Hub, Spoke 2, Spoke 3
│   └── Linked FROM: Hub
│
├── Spoke 4: Agent Performance
│   ├── Links TO: Hub, Spoke 5, Spoke 6
│   └── Linked FROM: Hub
│
└── ... (8 more spokes)

Result: 11 articles, ~50 internal links total
```

**Link Distribution:**
- Hub → 10 outbound links (to spokes)
- Each Spoke → 3-4 links (Hub + 1-2 spokes)
- **No clustering** - spread naturally through content

---

## 💡 How to Improve

### Enhancement 1: Dynamic Spoke Selection
Use keyword research API to prioritize:
```python
# Query search volume for each potential spoke
# Prioritize: High volume + low competition + high intent
```

### Enhancement 2: Automated Linking
After generating all spokes, automatically add links:
```python
for spoke in spokes:
    add_link_to_hub(spoke, hub_file)
    add_link_from_hub_to_spoke(hub_file, spoke)
```

### Enhancement 3: Content Similarity Check
Use embeddings to detect too-similar content:
```python
from sentence_transformers import SentenceTransformer
similarity = cosine_similarity(hub_embedding, spoke_embedding)
if similarity > 0.85:
    ⚠️ Warning: Spoke too similar to Hub
```

### Enhancement 4: Performance Tracking
After publishing, monitor:
- Which spokes rank fastest
- Which get most traffic
- Which convert best
- Optimize future spoke selection

---

## 🎯 Success Criteria

### Complete When:
- ✅ All 10 spoke articles generated (1,500-2,000 words each)
- ✅ Each spoke has unique primary keyword
- ✅ No keyword cannibalization detected
- ✅ Hub links to all 10 spokes
- ✅ Each spoke links to Hub + 1-2 related spokes
- ✅ Internal linking map updated with all 10
- ✅ Sitemap updated with all 10 URLs
- ✅ Cross-reference matrix created

### Quality Validation:
- ✅ Average uniqueness score: 95%+
- ✅ Cannibalization risk: <5%
- ✅ Total cluster word count: ~22,000 words
- ✅ All articles pass Step 5 quality gates

---

## 📋 Deliverables Checklist

**10 Spoke Articles:**
- [ ] `step10_spoke01_how_to_choose_a_conversation_analy.md`
- [ ] `step10_spoke02_conversation_analytics_implementat.md`
- [ ] `step10_spoke03_conversation_analytics_roi_calcul.md`
- [ ] `step10_spoke04_agent_performance_improvement_wit.md`
- [ ] `step10_spoke05_sentiment_analysis_for_call_cente.md`
- [ ] `step10_spoke06_call_center_quality_assurance_aut.md`
- [ ] `step10_spoke07_csat_improvement_strategies_using.md`
- [ ] `step10_spoke08_conversation_intelligence_vs_conv.md`
- [ ] `step10_spoke09_speech_analytics_vs_conversation_.md`
- [ ] `step10_spoke10_ai-powered_vs_traditional_call_ce.md`

**Infrastructure:**
- [ ] `step10_SPOKE_CLUSTER_COMPLETE.md` (summary)
- [ ] `step10_UPDATED_internal_linking_map.json`
- [ ] `step10_UPDATED_sitemap.xml`

**With Internal Links Added (Phase 2):**
- [ ] Hub updated with 10 spoke links
- [ ] Each spoke updated with Hub + 1-2 spoke links

---

## 🔗 Related Steps

- **Requires:** Step 4 synthesis identifying article as "Cluster (Hub)"
- **Uses:** Steps 1-3 data (reused for each spoke)
- **Triggers:** Only if Hub detected
- **Impact:** 11x SEO footprint instead of 1x

---

## 🚀 Expected Results

**Input:** 1 Hub article  
**Output:** 11 total articles (Hub + 10 Spokes)  
**Word Count:** ~22,000 words of exceptional content  
**SERP Positions:** 11 instead of 1  
**Topical Authority:** Established  

**Solidroad dominates the entire "conversation analytics" keyword cluster!** 🔥

---

**Next Step:** [STEP_15_final_summary.md](STEP_15_final_summary.md) (if creating)


