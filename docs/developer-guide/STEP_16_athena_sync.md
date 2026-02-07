---
title: ATHENA SYNC
order: 24
---

# Step 16: Sync to AthenaHQ (Optional)

**Script:** `publishing/sync_to_athena.py`  
**Type:** Optional (manual execution)  
**Output:** Prompts + Content registered in Athena

---

## 🤔 Why This Step Exists

**The Problem:**
You just published 11 articles. Now what? How do you know if they're working? Is brand visibility improving? Which keywords are performing? You're flying blind without tracking.

**The Reality:**
Content without tracking is hope-based marketing. You need to monitor: Did brand mention rate improve from 2% → 20%? Are AI models citing you more? Which keywords drove the best results?

**The Solution:**
Sync all published keywords and URLs to Athena. Register prompts for tracking. Monitor performance over time. Close the loop: generate → publish → measure → improve.

**Without this step:**
- No performance tracking (did it work?)
- Can't prove content ROI (no before/after data)
- Blind iteration (which keywords to focus next?)

**With this step:**
- All keywords tracked in Athena
- Brand visibility monitored (2% → X%)
- Performance data for next iteration

**This step exists because content creation isn't the end—it's the beginning. You need to track if it's working. Athena sync closes the loop from analysis → creation → measurement.**

---

## 📝 Overview

After publishing content, optionally sync keywords and article URLs to AthenaHQ for tracking and monitoring.

**Closes the loop: Generate content → Publish → Track performance**

---

## 🎯 Why It Matters

**Content Tracking:**
- Register all published keywords in Athena
- Monitor brand mention rates over time
- See which keywords drive performance

**Data Collection Priority:**
- Identify which keywords have data vs need collection
- Prioritize data collection for published content
- Know where to focus efforts

**Performance Monitoring:**
- Track how content impacts brand mentions
- See ranking improvements
- Measure content ROI

---

## ⚙️ How It Works

### 1. Load Published Articles

```python
# Read CSV from latest session
csv_file = 'results/local_pipeline/session_XXXXXX/step12_FRAMER_EXPORT.csv'

articles = read_csv(csv_file)
# → 11 articles with Prompt, Title, Final_URL columns
```

### 2. Fetch Athena Settings

```python
GET /api/webhooks/settings

{
  "defaultLanguage": "English",
  "personas": [...],
  "baseLocation": "United States"
}
```

**Used for prompts webhook metadata**

### 3. Send Prompts Webhook

```python
POST /api/webhooks/prompts

{
  "prompts": [
    {
      "prompt": "conversation analytics platform",  // From CSV "Prompt" column
      "topic": "Conversation Analytics",            // From config
      "language": "English",                        // From Athena settings
      "personas": "VP Customer Support,...",        // From Athena settings
      "country": "United States"                    // From Athena settings
    },
    ... (10 more)
  ]
}
```

**Response:**
```json
{
  "success": true,
  "created": 11,
  "skipped": 0,
  "details": {
    "newTopics": 1,
    "newPersonas": 0
  }
}
```

### 4. Send Content Webhook

```python
POST /api/webhooks/content

{
  "content": [
    {
      "title": "Top 10 Conversation Analytics Platforms...",
      "url": "solidroad.com/blog/top-platforms"  // Strips https://
    },
    ... (10 more)
  ]
}
```

**Response:**
```json
{
  "success": true,
  "created": 11,
  "updated": 0,
  "skipped": 0
}
```

### 5. Verify Status (Optional)

```python
GET /api/webhooks/prompts/list

# Check which synced prompts have data vs need collection

zero_mentions = filter(totalResponses == 0)
with_data = filter(totalResponses > 0)

# Report to user
```

---

## 📊 Inputs & Outputs

### Inputs:
- **CSV file:** `step12_FRAMER_EXPORT.csv` (from Step 12)
- **Config:** `athena_integration.website_id`
- **Athena API:** Running at configured URL

### Outputs:
**In Athena:**
- 11 prompts registered (or skipped if exist)
- 11 content URLs registered (or skipped)
- Ready for tracking

**Console Output:**
```
✅ Prompts synced: created 11, skipped 0
✅ Content synced: created 11, skipped 0
⚠️  11 prompts need data collection (0 responses)
```

---

## 🚨 Quality Considerations

### Not a Hard Blocker:

This step is **completely optional**:
- Athena integration is opt-in
- Content works without Athena
- Just adds monitoring capability

### When to Run:

**After publishing:**
```bash
# 1. Generate content
python3 content_pipeline_with_ai_agent.py

# 2. Publish to Sheets
python3 publishing/append_to_google_sheets.py

# 3. Sync to Athena (optional)
python3 publishing/sync_to_athena.py
```

### Duplicate Handling:

**API automatically handles duplicates:**
- Re-running is safe (idempotent)
- Existing prompts/content skipped
- Returns clear counts: created vs skipped

---

## 🔧 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| website_id not configured | Missing in config | Add athena_integration.website_id |
| 401 Unauthorized | Invalid website_id | Verify ID in Athena settings |
| Connection refused | Athena not running | Start Athena or check api_url |
| All skipped | Already synced | Normal! Re-running is safe |

---

## 💡 Monitoring Workflow

### After Syncing:

**Check prompt status:**
```python
GET /api/webhooks/prompts/list

# For each synced keyword:
- totalResponses: 0 → Need to collect data
- totalResponses: 820 → Has data, ready for updates
- brandMentions: 3 → Low, need content optimization
- mentionRate: 75% → High, content working!
```

**Prioritize data collection:**
- Published keywords with 0 responses = priority
- Collect data for these first
- Re-generate content when data available

**Track improvements:**
- Baseline: 0.4% mention rate before content
- After publishing: Monitor if rate improves
- Measure content impact!

---

## 🔗 Data Flow

```
Step 12: CSV with 11 articles
  ↓
sync_to_athena.py
  ↓
Fetch /settings (get personas, language)
  ↓
POST /prompts (11 keywords)
  ↓
POST /content (11 URLs)
  ↓
GET /prompts/list (verify status)
  ↓
Report: which need data collection
```

---

## 🎯 Complete Integration

**Athena integration provides:**

1. **Input:** Fetch response data (`/prompts/{id}/responses`)
2. **Config:** Auto-fill brand settings (`/settings`)
3. **Output:** Sync published content (Step 15)
4. **Monitoring:** Track performance over time

**Complete closed loop!** ✅

---

**Athena users get full API integration with no manual steps!** 🚀

**Next:** Monitor published content performance in Athena dashboard

