---
title: ATHENA API MODE
order: 2
---

# Step 0: Brand Gap Analysis - Athena API Mode

**Function:** `fetch_athena_responses()` + `step0_brand_gap_analysis()`  
**Type:** Automated  
**Output:** DataFrame with responses (from API, not CSV)

---

## 🤔 Why This Step Exists

**The Problem:**
You want to generate content based on Athena data. But first you need to export responses to CSV, download the file, save it to `datasets/`, make sure filename matches, update paths. Every time. That's 5 manual steps before the pipeline even runs.

**The Reality:**
Athena is your source of truth. The data lives there. Why are you manually exporting, downloading, and managing CSV files? That's workflow friction that kills momentum.

**The Solution:**
Connect directly to Athena API. Pipeline fetches responses automatically. No exports. No downloads. No file management. Just specify the prompt name, pipeline does the rest.

**Without Athena API mode:**
- Manual CSV exports (tedious)
- File version confusion (which CSV is latest?)
- Workflow friction (5 steps before pipeline starts)
- Stale data risk (forgot to re-export)

**With Athena API mode:**
- Zero manual exports (automated)
- Always fresh data (real-time fetch)
- 1-command workflow (just run pipeline)
- No file management (Athena is source of truth)

**This step exists because manual CSV exports are bullshit. If the data lives in Athena, the pipeline should fetch it from Athena. This eliminates the entire export workflow.**

---

## 📝 Overview

**NEW:** Fetch response data directly from Athena API instead of CSV files.

**Two data modes:**
1. **Athena API** (if enabled) - Fetches from `/prompts/{id}/responses` ✅ RECOMMENDED
2. **CSV** (fallback) - Loads from `datasets/conversation-analytics-platform.csv`

---

## 🎯 Why It Matters

**Eliminates manual CSV exports:**
- No downloading data from Athena
- No saving to datasets folder
- No file management
- Always fresh, real-time data

**User-friendly prompt selection:**
- Shows zero-mention prompts automatically
- Or specify exact keyword
- Pipeline handles ID lookup

---

## ⚙️ How It Works

### **1. Check If Athena Enabled**

```python
athena_config = CONFIG.get('athena_integration', {})

if athena_config.get('enabled') and athena_config.get('website_id'):
    # ATHENA API MODE
    df = fetch_athena_responses(...)
else:
    # CSV MODE (fallback)
    df = pd.read_csv(CSV_FILE)
```

### **2. Fetch Athena Responses**

**If target_prompt specified:**
```python
target_prompt = "conversation analytics platform"

# Step A: Find prompt by name
GET /api/webhooks/prompts/list
prompt_obj = find_by_name(prompts, target_prompt)

# Step B: Get prompt ID
prompt_id = prompt_obj['id']

# Step C: Fetch all responses
GET /api/webhooks/prompts/{prompt_id}/responses?page=1&limit=100
# Paginate through all pages
```

**If target_prompt empty:**
```python
# Show zero-mention prompts
GET /api/webhooks/prompts/list

zero_mentions = [p for p in prompts if p['metrics']['totalResponses'] == 0]

# Display to user, ask them to set target_prompt in config
```

### **3. Convert to DataFrame**

**Athena API Response:**
```json
{
  "responses": [
    {
      "text": "Here are the top platforms...",
      "targetMentioned": true,
      "targetRank": 2,
      "competitorsMentioned": [
        {"name": "Observe.AI", "rank": 1}
      ]
    }
  ]
}
```

**Converted to:**
```python
pd.DataFrame([
  {
    'response': "Here are the top platforms...",
    'target_mentioned': True,
    'target_rank': 2,
    'competitors': "Observe.AI"
  }
])
```

**Same format as CSV!** 

**CRITICAL: Saves to CSV for Steps 1-2:**
```python
# After fetching from Athena, save to CSV
df.to_csv('datasets/conversation-analytics-platform.csv')

# Why? Steps 1-2 reload from CSV (not passed as parameter)
# This makes Athena mode transparent to rest of pipeline
```

Rest of pipeline works identically! ✅

---

## 📊 Inputs & Outputs

### Inputs:
- **Athena website_id** (from config)
- **API URL** (default: localhost:3000)
- **target_prompt** (keyword or empty)

### Outputs:
- **DataFrame:** Same format as CSV mode
- **Metadata:** Prompt info, response count

---

## 🚨 Quality Considerations

### Prompt Not Found:
```
❌ Prompt not found: 'your keyword'
   Add this prompt in Athena first
```

**Solution:** Create prompt in Athena, collect responses, re-run

### Zero Responses:
```
⚠️  This prompt has 0 responses!
   Collect data in Athena first
```

**Solution:** Run data collection in Athena, re-run pipeline

### API Unavailable:
```
❌ Could not fetch from Athena: Connection refused
```

**Solution:** 
- Check if Athena running (`localhost:3000`)
- Or set `enabled: false` and use CSV mode

---

## 🔧 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Prompt not found | Wrong prompt text | Check exact spelling in Athena |
| 0 responses | No data collected yet | Run data collection first |
| Timeout | Large dataset | Increase timeout, check pagination |
| 401 Unauthorized | Wrong website_id | Verify ID in Athena settings |

---

## 💡 How to Improve

### Enhancement 1: Prompt Search
```python
# Fuzzy search if exact match not found
from difflib import get_close_matches

close = get_close_matches(target_prompt, [p['prompt'] for p in prompts])
if close:
    log(f"💡 Did you mean: '{close[0]}'?")
```

### Enhancement 2: Batch Prompts
```python
# Support multiple target_prompts
"target_prompts": [
  "conversation analytics platform",
  "ai quality assurance"
]

# Fetch responses for all, combine dataset
```

### Enhancement 3: Cache Responses
```python
# Save fetched responses to cache
cache_file = f"cache/responses_{prompt_id}.json"

# Re-use on subsequent runs (faster!)
```

---

## 🎓 Strategic Rationale

**Why Athena API mode:**
- Athena is source of truth for response data
- Manual CSV exports are tedious
- Real-time data ensures freshness
- Easier team collaboration (no file sharing)

**When to use CSV mode:**
- Non-Athena users
- Offline development
- Custom datasets
- Legacy workflows

---

## 🔗 Data Flow

```
Config: target_prompt = "conversation analytics platform"
  ↓
GET /prompts/list
  ↓
Find prompt by name → Get ID
  ↓
GET /prompts/{id}/responses (paginated)
  ↓
Convert to DataFrame
  ↓
Same format as CSV → Rest of pipeline unchanged!
```

---

**This eliminates CSV dependency for Athena users!** 🚀

**Next:** [STEP_01_content_analysis.md](STEP_01_content_analysis.md)

