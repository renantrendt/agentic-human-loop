---
title: CONTENT ANALYSIS
order: 3
---

# Step 1: Content Analysis

**Function:** `step1_content_analysis()`  
**Type:** Automated  
**Output:** `step1_FOR_AGENT_ANALYSIS.md`, `step1_content_patterns.json`

---

## 🤔 Why This Step Exists

**The Problem:**
You're about to write a 2,000-word article. What should it be about? What keywords should it target? You're guessing based on intuition or worse—copying competitors.

**The Reality:**
AI models have already revealed the market's language through 696 responses. They mention "agent performance" 978 times, "sentiment analysis" 786 times. That's not random—that's demand signal.

**The Solution:**
Extract what people actually talk about. Count the exact phrases. "Conversation analytics" appears 2,990 times? That's your primary keyword. "Quality assurance" appears 734 times? That's a spoke topic.

**Without this step:**
- Keyword guessing (hope you picked the right ones)
- Generic content angles (what competitors already cover)
- No data-backed strategy

**With this step:**
- 50 keyword combinations with exact frequencies
- Content patterns validated by 696 responses
- Proof of what the market cares about

**This step exists because great content starts with great data. Frequency = demand. If the market talks about it 978 times, you write about it.**

---

## 📝 Overview

Extracts keyword patterns from call-center QA responses using n-gram analysis to identify the most frequent topics, phrases, and content structures.

**This is the data foundation** for all content strategy.

---

## 🎯 Why It Matters

**What it reveals:**
- Top 30 bigrams (e.g., "agent performance" mentioned 978x)
- Top 20 trigrams (e.g., "conversation analytics platform" 707x)
- Content patterns AI models use
- Topic clustering opportunities

**Strategic value:**
- **Keyword targeting:** High-frequency phrases = high search demand
- **Content angles:** What topics resonate with audiences
- **Language patterns:** How to phrase your content
- **Topic validation:** Confirms target keyword is relevant

---

## ⚙️ How It Works

### 1. Categorize Responses by Source Domain
```python
df['source_category'] = df.apply(categorize_by_sources, axis=1)
```

**Categories:**
- `call_center_qa` - Our target domain (observe.ai, maestroqa, etc.)
- `software_qa` - Wrong domain (selenium, cypress, etc.)
- `mixed` - Both domains cited
- `no_sources` - No citations
- `other` - Different domains

### 2. Filter to Target Domain
```python
target_domain_df = df[df['source_category'].isin(['call_center_qa', 'mixed'])]
```

**Why:** We only want call-center QA responses, not software testing

### 3. Extract N-grams
```python
all_bigrams = extract_ngrams(text, n=2)    # "agent performance"
all_trigrams = extract_ngrams(text, n=3)   # "natural language processing"
```

**Cleaning:**
- Lowercase normalization
- Remove punctuation
- Filter out generic words (http, www, click)
- Minimum 3 characters

### 4. Count Frequencies
```python
bigram_counts = Counter(all_bigrams)
top_bigrams = bigram_counts.most_common(50)
```

### 5. Generate Analysis Report
- Top 30 bigrams with frequencies
- Top 20 trigrams with frequencies
- Sample responses (first 5)
- Questions for AI agent to analyze

---

## 📊 Inputs & Outputs

### Inputs:
- **CSV File:** `conversation-analytics-platform.csv`
- **Required Columns:** `Response`, `Sources`, `Prompt Variation`

### Outputs:
**`step1_content_patterns.json`:**
```json
{
  "total_responses": 820,
  "call_center_qa_responses": 696,
  "percentage": 84.9,
  "top_bigrams": [
    ["conversation analytics", 2990],
    ["agent performance", 978],
    ...
  ],
  "category_distribution": {...}
}
```

**`step1_FOR_AGENT_ANALYSIS.md`:**
- Data overview
- Top 30 bigrams (with counts)
- Top 20 trigrams (with counts)
- 5 sample responses
- Analysis questions for AI agent

---

## 🚨 Quality Gates & Rescue Tasks

### Quality Gate 1: CSV Exists
```python
if not os.path.exists(CSV_FILE):
    → RESCUE_STEP1_CSV_MISSING.md
```

### Quality Gate 2: Minimum Responses
```python
if len(target_domain_df) < 100:
    → RESCUE_STEP1_INSUFFICIENT_DATA.md
```

**Why 100 minimum:**
- Statistical significance requires sample size
- Need diverse keyword patterns
- Ensure broad topic coverage

**Rescue Mission:**
- Expand Athena query date range
- Check categorization logic (some might be miscategorized)
- Add supplemental CSV file

### Soft Warning: Unique Bigrams
```python
if len(top_bigrams) < 30:
    ⚠️ Warning: Limited patterns
```

---

## 🔧 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Low QA responses | Wrong dataset or categorization | Check CALL_CENTER_QA_DOMAINS list |
| Generic bigrams | Low-quality responses | Filter out filler words |
| Few unique patterns | Repetitive data | Augment with diverse prompts |
| Miscategorization | Domain list incomplete | Add domains to categorize_by_sources() |

---

## 📈 Example Output

```markdown
## 🎯 TOP PATTERNS IN CALL CENTER QA RESPONSES

### Top 30 Bigrams:

1. `conversation analytics` - 2,990x
2. `agent performance` - 978x
3. `customer service` - 952x
4. `sentiment analysis` - 786x
5. `quality assurance` - 734x
...

### Top 20 Trigrams:

1. `conversation analytics platform` - 707x
2. `natural language processing` - 311x
3. `customer service teams` - 281x
...
```

---

## 💡 How to Improve

### Enhancement 1: Co-occurrence Analysis
Track which bigrams appear together:
```python
# If "agent performance" and "coaching" co-occur → spoke opportunity
```

### Enhancement 2: Negative Keyword Filtering
Exclude noise bigrams:
```python
noise_words = ['such as', 'the platform', 'if you', ...]
filtered_bigrams = [bg for bg in bigrams if bg[0] not in noise_words]
```

### Enhancement 3: Semantic Clustering
Group related bigrams:
```python
clusters = {
    'Performance': ['agent performance', 'call quality', 'qa scores'],
    'Analytics': ['conversation analytics', 'speech analytics', ...],
    'Outcomes': ['customer satisfaction', 'csat improvement', ...]
}
```

### Enhancement 4: Competitor-Specific Patterns
Extract patterns from responses citing specific competitors:
```python
observe_ai_patterns = extract_patterns(df[df['Sources'].str.contains('observe.ai')])
maestroqa_patterns = extract_patterns(df[df['Sources'].str.contains('maestroqa')])
```

---

## 🎓 Strategic Insights

### High-Frequency Bigrams (>500 mentions):
**Use these as primary/secondary keywords**
- conversation analytics (2,990x)
- agent performance (978x)
- customer service (952x)

### Medium-Frequency (200-500):
**Use as long-tail opportunities**
- customer satisfaction (529x)
- speech analytics (397x)

### Low-Frequency (<200):
**Use for niche spokes**
- ai-powered conversation analytics (180x)

---

## 🔗 Data Flow

```
CSV File
  ↓
Categorize by domain (call-center QA vs software QA)
  ↓
Filter to target domain (696 responses)
  ↓
Extract bigrams & trigrams
  ↓
Count frequencies
  ↓
Save top 50 bigrams, top 30 trigrams
  ↓
Step 4 (AI Synthesis) uses these for keyword strategy
  ↓
Step 5 (Article) integrates these keywords naturally
```

---

## 🔗 Related Steps

- **Requires:** CSV file with Response column
- **Feeds:** Step 4 (keyword strategy), Step 10 (spoke topics)
- **Parallel:** Step 0 (brand gap uses same CSV)

---

## 📋 Quality Checklist

Before proceeding to Step 2:
- [ ] ✅ 100+ call-center QA responses analyzed
- [ ] ✅ 30+ unique bigrams extracted
- [ ] ✅ No generic-only patterns
- [ ] ✅ Top bigrams are domain-relevant (not "such as", "the platform")

---

**Next Step:** [STEP_02_url_analysis.md](STEP_02_url_analysis.md)


