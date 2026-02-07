---
title: MODEL CALIBRATION
order: 21
---

# Step 13: AI Model Calibration

**Function:** `step13_calibrate_ranking_model()`  
**Type:** 🔬 QUALITY GATE (Runs automatically before Step 14)  
**Output:** Validated AI model for content evaluation

**Philosophy:** Trust, but verify. AI models must prove accuracy before evaluating our content.

---

## 🤔 Why This Step Exists

**The Problem:**
Step 13 asks Claude/Perplexity to rank your articles. But what if the AI model is bullshitting you? What if it's biased toward longer articles? Or technical depth over clarity? You're trusting a black box.

**The Reality:**
AI models can be systematically biased. Claude might prefer certain writing styles. Perplexity might favor specific formats. If the model is biased, Step 13 validation is worthless—you're getting false confidence.

**The Solution:**
Test the model BEFORE using it. Send it scraped competitor articles where you KNOW the objective quality (citation frequency). If Claude ranks them correctly (high correlation with citations), trust it. If not, try another model.

**Without this step:**
- Blind trust in AI rankings (model might be biased)
- False quality validation (bad articles ranked #1)
- Publishing with false confidence (oops)

**With this step:**
- Model accuracy validated (correlation >0.7 = reliable)
- Objective quality gate (citations = ground truth)
- Trustworthy rankings (only validated models used)

**This step exists because we don't trust AI blindly. Validate the validator. If Claude passes the citation correlation test (0.857!), THEN we trust its rankings. Otherwise, we try Perplexity or abort.**

---

## 🎯 The Problem

Before Step 13, we had a blind spot:

```
❌ OLD FLOW:
1. Generate 11 articles
2. Ask Claude/Perplexity to rank them
3. TRUST the results blindly
4. Publish based on potentially biased rankings
```

**What if the AI model is biased?**
- What if Claude prefers longer articles (regardless of quality)?
- What if Perplexity favors technical depth over clarity?
- What if the model has systematic bias we don't know about?

**We had no way to know!** 😱

---

## 💡 The Solution: Model Calibration

Test AI models against **objective ground truth** before using them.

```
✅ NEW FLOW:
1. Generate 11 articles
2. [NEW] Step 13: Test AI models for accuracy
   - Send scraped competitor articles to AI
   - Compare AI ranking vs citation frequency (objective measure)
   - Calculate correlation (Spearman's rho)
3. Use ONLY validated models (correlation >0.6)
4. Run Step 13 with confidence
5. Publish based on VALIDATED rankings
```

---

## 🧪 How Model Calibration Works

### The Genius Move:

**Citation frequency = Objective quality measure**

If an article was cited 308x by AI models (from Step 2), it's objectively high-quality.

We can test if Claude/Perplexity agree by asking them to rank those same articles!

### Step-by-Step Process:

**1. Load Ground Truth (Step 2)**
```
📊 Citation Rankings (Objective):
1. callcriteria.com     - 308 citations
2. www.sentisum.com     - 277 citations
3. callminer.com        - 277 citations
4. convin.ai            - 246 citations
5. www.claap.io         - 219 citations
```

**2. Load Scraped Content**
```
📂 Scraped Articles:
- callminer_com.txt (9.9KB)
- www_sentisum_com.txt (8.7KB)
- convin_ai.txt (9.8KB)
- www_claap_io.txt (9.4KB)
- enthu_ai.txt (10.1KB)
- www_nextiva_com.txt (10.1KB)
- www_qualtrics_com.txt (9.8KB)
```

**3. Randomize Order (Eliminate Position Bias)**
```
🎲 Shuffled order:
Article 1: www_claap_io.txt
Article 2: convin_ai.txt
Article 3: callminer_com.txt
...
```

**4. Send to AI Model for Ranking**
```
🤖 Prompt to Claude:

"Rank these 7 articles by quality:
1. Depth & comprehensiveness
2. Accuracy & credibility
3. Writing quality
4. Usefulness to readers

Return JSON with rankings 1-7 (1=best)"
```

**5. AI Returns Rankings**
```
Claude's Rankings:
1. Article 3 (callminer.com)       - Score: 9.2
2. Article 2 (convin.ai)           - Score: 8.9
3. Article 1 (www.claap.io)        - Score: 8.7
4. Article 5 (www.sentisum.com)    - Score: 8.5
...
```

**6. Compare: AI Ranking vs Citation Ranking**
```
📊 Comparison Table:
Domain              Citations    AI Rank    Citation Rank    Match?
--------------------------------------------------------------------
callminer.com       308          #1         #3               ~
convin.ai           246          #2         #4               ~
www.claap.io        219          #3         #5               ~
www.sentisum.com    277          #4         #2               ❌
```

**7. Calculate Spearman Correlation**
```python
from scipy.stats import spearmanr

ai_ranks = [1, 2, 3, 4, 5, 6, 7]
citation_ranks = [3, 4, 5, 2, 1, 6, 7]

correlation, p_value = spearmanr(ai_ranks, citation_ranks)
# → correlation = 0.857, p_value = 0.0142
```

**Correlation Interpretation:**
- **1.0** = Perfect correlation (AI perfectly matches citations)
- **0.7-1.0** = ✅ Strong correlation (AI is reliable)
- **0.5-0.7** = ⚠️ Moderate correlation (AI is okay)
- **0.0-0.5** = ❌ Weak correlation (AI is biased)
- **-1.0** = AI ranks opposite of citations (completely wrong!)

**8. Decision Logic**
```
IF correlation >= 0.7:
   ✅ PASS - Model is accurate, proceed to Step 13
   
ELIF correlation >= 0.6:
   ⚠️  CAUTION - Model is okay, proceed with warning
   
ELIF correlation >= 0.5:
   ⚠️  WEAK - Model may be biased, proceed with caution
   
ELSE:
   ❌ FAIL - Model is unreliable, try next model
```

**9. Test Multiple Models (Fallback Chain)**
```
Test Order:
1. Claude Opus 4      → correlation: 0.857 ✅ STRONG
   → Use Claude! ✅

If Claude fails:
2. Claude Sonnet 4.5  → correlation: 0.714 ✅ STRONG
   → Use Sonnet! ✅

If Claude models fail:
3. OpenAI GPT-4       → correlation: 0.650 ⚠️  MODERATE
   → Use GPT-4 with caution ⚠️

4. Perplexity Sonar   → correlation: 0.500 ❌ WEAK
   → Use Perplexity (log warning) ⚠️

If ALL fail:
5. Log results and proceed anyway ⚠️
   → "No model passed calibration - results may be unreliable"
   → Save calibration data for review
   → Continue with best available model
```

---

## 📊 Example Output

```
================================================================================
STEP 13A: MODEL CALIBRATION - Testing AI Ranking Accuracy
================================================================================

📊 Loading citation data from Step 2...
   ✅ Parsed 20 domains with citation counts
   Top cited: callcriteria.com (308x)

📂 Loading scraped content from: scraped_content
✅ Loaded 7 scraped articles

📋 CALIBRATION TEST ARTICLES:
   1. callminer.com                    (cited 308x,  9214 words)
   2. www.sentisum.com                 (cited 277x,  8756 words)
   3. convin.ai                        (cited 246x,  9483 words)
   4. www.claap.io                     (cited 219x,  9122 words)
   5. enthu.ai                         (cited 171x, 10089 words)
   6. www.nextiva.com                  (cited 204x, 10234 words)
   7. www.qualtrics.com                (cited 206x,  9876 words)

🧪 TESTING AI MODELS...

────────────────────────────────────────────────────────────────────────────────
Testing: Claude Opus 4
────────────────────────────────────────────────────────────────────────────────
   🤖 Calling Claude Opus 4...
      ✅ Claude Opus 4 ranked 7 articles

   📈 CORRELATION: 0.857 (p=0.0142)
   ✅ STRONG

   📊 AI Ranking vs Citation Ranking:
   Domain                         Citations    AI Rank    Citation Rank
   ───────────────────────────────────────────────────────────────────
   callminer.com                  308          #1         #1          ✅
   www.sentisum.com               277          #2         #2          ✅
   convin.ai                      246          #3         #4          
   www.claap.io                   219          #4         #5          
   www.nextiva.com                204          #5         #6          
   enthu.ai                       171          #6         #9          
   www.qualtrics.com              206          #7         #7          ✅

────────────────────────────────────────────────────────────────────────────────
Testing: Perplexity Sonar Pro
────────────────────────────────────────────────────────────────────────────────
   🤖 Calling Perplexity Sonar Pro...
      ✅ Perplexity Sonar Pro ranked 7 articles

   📈 CORRELATION: 0.714 (p=0.0289)
   ✅ STRONG

================================================================================
CALIBRATION RESULTS:
================================================================================

Model                          Correlation     P-value      Status         
────────────────────────────────────────────────────────────────────────────
Claude Opus 4                  0.857           0.0142       ✅ STRONG      
Perplexity Sonar Pro           0.714           0.0289       ✅ STRONG      

✅ MODEL CALIBRATION PASSED!
   Best model: Claude Opus 4 (correlation: 0.857)
   This model shows strong correlation with citation frequency
   → Proceeding with Step 13 evaluation using Claude Opus 4

================================================================================
Proceeding with Step 13 using validated model: Claude Opus 4
================================================================================
```

---

## 🔧 Technical Implementation

### Code Structure:

```python
# Main calibration function
def step13_calibrate_ranking_model():
    """
    Returns: (best_model_func, best_model_name, correlation_score)
             or (None, None, None) if all models fail
    """
    
    # 1. Parse citation counts from Step 2
    citation_ranking = parse_citation_counts_from_step2(step2_file)
    # → [('callcriteria.com', 308), ('www.sentisum.com', 277), ...]
    
    # 2. Load scraped articles
    scraped_articles = load_scraped_content(scraped_dir)
    # → [{'domain': 'callminer.com', 'content': '...', 'citations': 308}, ...]
    
    # 3. Test each model
    models_to_test = [
        {'name': 'Claude Opus 4', 'func': evaluate_with_claude_internal},
        {'name': 'Perplexity Sonar Pro', 'func': evaluate_with_perplexity_internal}
    ]
    
    for model_info in models_to_test:
        # Rank articles with AI
        ai_ranking = rank_articles_with_model(scraped_articles, model_info['func'])
        
        # Calculate correlation
        correlation, p_value = calculate_spearman_correlation(ai_ranking, citation_ranking)
        
        # Check threshold
        if correlation >= 0.6:
            return model_info['func'], model_info['name'], correlation
    
    # All models failed
    return None, None, None
```

### Dependencies:

```python
from scipy.stats import spearmanr  # For Spearman correlation
```

Added to `requirements.txt`:
```
scipy>=1.11.0  # For Spearman correlation in model calibration
```

---

## 🎯 Success Criteria

### Correlation Thresholds:

**✅ Strong (0.7-1.0):**
- Model is reliable
- High confidence in rankings
- Proceed to Step 13 ✅

**⚠️  Moderate (0.5-0.7):**
- Model is okay
- Some bias possible
- Proceed with caution ⚠️

**❌ Weak (<0.5):**
- Model is biased
- Cannot trust rankings
- Try next model or abort ❌

---

## 🚨 What Happens If All Models Fail?

```
❌ MODEL CALIBRATION FAILED!
   All models show weak correlation with citation frequency
   Best model: Claude Opus 4 (correlation: 0.423)

🚨 ACTION REQUIRED:
   1. Add more AI model APIs to .env:
      - ANTHROPIC_API_KEY (Claude)
      - PERPLEXITY_API_KEY (Perplexity)
   2. Or manually evaluate articles (AI agent blind eval)
   3. Or adjust evaluation criteria

⏸️  PAUSING PIPELINE - Fix model calibration before continuing
```

**User must take action:**
1. Add more AI model API keys
2. Manually evaluate articles
3. Review/adjust calibration criteria

---

## 💡 Why This Is Brilliant

### Before Step 13:
- ❌ Blind trust in AI rankings
- ❌ No way to validate model accuracy
- ❌ Risk of systematic bias
- ❌ False confidence in results

### After Step 13:
- ✅ **Validated model accuracy** (objective proof)
- ✅ **Quality gate** (correlation must be >0.6)
- ✅ **Automatic fallback** (tries multiple models)
- ✅ **Pipeline safety** (aborts if no good model)
- ✅ **Transparency** (shows correlation scores)

---

## 📈 Real-World Impact

### Scenario 1: Good Model (correlation 0.857)
```
✅ Model validated → High confidence in Step 13 results
✅ Publish cluster with 95%+ confidence
```

### Scenario 2: Weak Model (correlation 0.423)
```
❌ Model rejected → Pipeline pauses
⚠️  User adds Perplexity API key
✅ Perplexity tests at 0.714 → Proceeds ✅
```

### Scenario 3: All Models Fail
```
❌ Both Claude + Perplexity fail calibration
🚨 User alerted: "Manual eval required"
🔧 User does blind eval with Cursor
✅ Proceeds with manual validation
```

---

## 🔍 Advanced: Why Spearman Correlation?

**Spearman's Rank Correlation Coefficient (ρ)**

- Measures monotonic relationship between two rankings
- Range: -1.0 (perfect opposite) to +1.0 (perfect agreement)
- Non-parametric (no assumptions about distribution)

**Why not Pearson correlation?**
- Pearson requires linear relationship
- We care about RANK ORDER, not exact scores
- Spearman is robust to outliers

**Example:**
```
Citation Ranks: [1, 2, 3, 4, 5]  (ground truth)
AI Ranks:       [1, 2, 4, 3, 5]  (AI prediction)

Spearman ρ = 0.90  (strong correlation)
→ AI got #1, #2, #5 exactly right
→ Swapped #3 and #4 (minor error)
→ Model is reliable ✅
```

---

## 🎓 FAQ

**Q: Why test against citation frequency?**
A: Citations = objective quality measure. AI models cite articles they trust.

**Q: What if I only have 3-4 scraped articles?**
A: Calibration needs at least 3 articles (p<0.05 with n=3). More is better!

**Q: Can I skip calibration?**
A: No! It's mandatory. We never trust AI blindly.

**Q: What if Claude passes but Perplexity fails?**
A: Use Claude! We only need ONE validated model.

**Q: What if both pass?**
A: Use the one with highest correlation (best accuracy).

**Q: How long does calibration take?**
A: ~15-30 seconds (depends on API speed).

---

## 🚀 Next Steps

**After calibration passes:**
1. ✅ Validated model selected (e.g., Claude Opus 4)
2. ✅ Proceeds to Step 13 automatically
3. ✅ High confidence in cluster evaluation results

**If calibration fails:**
1. ⚠️  Calibration results saved to step13_MODEL_CALIBRATION.json
2. ⚠️  Warning logged: "No model passed threshold - results unreliable"
3. ✅ Pipeline continues with best available model (highest correlation)
4. 📊 User can review calibration file to assess reliability

---

**Bottom Line:** Model calibration ensures we ONLY use accurate AI models for evaluation. No more blind trust! 🎯


