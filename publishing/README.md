# 📰 Publishing Workflow

**Purpose:** Export generated articles to Framer (via Google Sheets) + Sync to Athena  
**Last Updated:** November 22, 2025

---

## 📋 **PUBLISHING PROCESS**

### **Step 1: Generate Content (Main Pipeline)**

Run the complete content pipeline:

```bash
cd /Users/renanserrano/script-nata
python3 agentic-human-loop/content_pipeline_with_ai_agent.py --resume
```

**Generates:**
- 1 Hub article (4,000-6,000 words)
- 10 Spoke articles (1,500-2,000 words each)
- Step 12A: Converts to HTML + fixes links + generates structure metadata
- Step 12B: AI agent writes SEO descriptions (using bigrams/trigrams)
- Output: `results/local_pipeline/session_XXXXXX/step12_FRAMER_EXPORT.csv`

---

### **Step 2: Append to Google Sheets**

After content is validated and ready to publish:

```bash
python3 agentic-human-loop/publishing/append_to_google_sheets.py
```

**What it does:**
- Reads CSV from latest session
- Authenticates with Google Sheets API
- **APPENDS** new articles (preserves existing rows!)
- Updates Framer import sheet

**Sheet URL:**  
https://docs.google.com/spreadsheets/d/1P4TkNRHwj6wHPrU_hpgXUXIOBJdQdDjBjgVQ4WUGiu0

---

## 🔐 **SETUP REQUIREMENTS**

### **OAuth2 Setup (One-Time, Team-Friendly)** ✅ RECOMMENDED

**Already done!** ✅ `oauth_credentials.json` is in the repo

**For new team members:**

1. **Install Dependencies:**
   ```bash
   pip3 install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
   ```

2. **Run the script:**
   ```bash
   python3 agentic-human-loop/publishing/append_to_google_sheets.py
   ```

3. **First run only:** Browser opens automatically
   - Sign in with your Google account
   - Click "Allow" when prompted
   - Return to terminal

4. **Done!** Token saved locally (`token.pickle`)

**Future runs:** No browser popup (uses saved token)

**Why OAuth2:**
- ✅ Easy team onboarding (clone → run → allow)
- ✅ Each person uses their own Google account
- ✅ No sharing service account JSON
- ✅ OAuth credentials safe to commit to git

---

### **Alternative: Service Account (Single User)**

**If you prefer service account:** Use `append_to_google_sheets_service.py`

**Setup:** See previous version of this README or follow Google Cloud Console guide

**When to use:** Single user, want fully automated (no browser ever)

---

## ✅ **VERIFICATION**

After publishing, verify:

1. **Google Sheet Updated:**
   - New rows appended (old rows preserved)
   - Title, Date, Author, Content columns populated
   - HTML formatted correctly

2. **Framer Sync:**
   - Framer imports from Google Sheets
   - New articles appear in Framer CMS
   - Internal links work correctly

3. **URL Slugs Match:**
   - Article titles → URL slugs auto-generated
   - Example: "AI Quality Assurance..." → `/blog/ai-quality-assurance-for-contact-centers-the-insight-to-action-gap-is-holding-back-performance-is-holding-back-performance`

---

## 🔗 **INTERNAL LINK MAPPING**

Step 14A automatically converts:

| Markdown Link | HTML Output |
|---------------|-------------|
| `[Hub](step8_ARTICLE.md)` | `<a href="/blog/top-conversation-analytics-platforms-2025">Hub</a>` |
| `[Spoke 1](step10_spoke01_*.md)` | `<a href="/blog/ai-quality-assurance-insight-to-action-gap">Spoke 1</a>` |
| `[Spoke 2](step10_spoke02_*.md)` | `<a href="/blog/how-to-choose-conversation-analytics-platform">Spoke 2</a>` |

**Slug generation:**
```python
title = "AI Quality Assurance for Contact Centers: The Insight-to-Action Gap"
slug = "ai-quality-assurance-for-contact-centers-the-insight-to-action-gap-is-holding-back-performance"
```

Matches Framer's auto-slug generation! ✅

---

## 📊 **SPREADSHEET FORMAT (Visual Content Map)**

**Columns (11 total):**

| Column | Purpose | Example |
|--------|---------|---------|
| **Title** | Article title | "Top 10 Conversation Analytics Platforms..." |
| **Date** | Publication date | "11/21/2025" |
| **Author** | Content author | "Renan Serrano" |
| **Prompt** | Target SEO keyword | "conversation analytics platform" |
| **Article_Type** | Hub or Spoke | "HUB" or "SPOKE" |
| **Hub_Title** | Parent hub (if spoke) | "Top 10 Platforms..." (for spokes) |
| **Related_Spokes** | Connected articles | "Spoke 01, Spoke 02, Spoke 03" |
| **Final_URL** | Full published URL | "https://solidroad.com/blog/top-platforms" |
| **Description** | Meta description | "Compare top conversation analytics platforms..." |
| **Content_Part1** | HTML content (part 1) | "<h2>TL;DR</h2><p>..." |
| **Content_Part2** | HTML overflow (if >50k) | "...<h2>Conclusion</h2>" (Hub only) |

**Visual Structure:**
- Filter by `Article_Type = HUB` → See pillar content
- Filter by `Hub_Title = "..."` → See all spokes in cluster
- See relationships at a glance!

**Example Hub Row:**
```csv
"Top 10 Platforms",11/21/25,Renan,"conversation analytics platform",HUB,"","Spoke 01-10","https://solidroad.com/blog/top-platforms","Compare top platforms...","<HTML part 1>","<HTML part 2>"
```

**Example Spoke Row:**
```csv
"AI Quality Assurance",11/21/25,Renan,"ai quality assurance",SPOKE,"Top 10 Platforms","Spoke 02","https://solidroad.com/blog/ai-qa","Learn how AI QA...","<HTML>",""
```

---

## 🚨 **TROUBLESHOOTING**

| Issue | Solution |
|-------|----------|
| "Service account not found" | Save `google-service-account.json` in correct location |
| "Permission denied" | Share Google Sheet with service account email |
| "API not enabled" | Enable Google Sheets API in Cloud Console |
| "Internal links broken" | Check slug generation in Step 14A |
| "Old rows deleted" | Script uses `INSERT_ROWS` mode - shouldn't happen! |

---

## 🎯 **EXPECTED RESULTS**

**After running publisher:**
- ✅ 11 new rows added to Google Sheets
- ✅ Previous articles preserved
- ✅ Framer imports and publishes
- ✅ All 11 articles live on solidroad.com/blog/
- ✅ Internal links working (Hub ↔ Spokes)

---

## 🔗 **ATHENA SYNC (Optional)**

After publishing to Google Sheets, optionally sync to AthenaHQ:

```bash
python3 agentic-human-loop/publishing/sync_to_athena.py
```

**Requirements:**
- Athena website_id in `brand-context/config.json`
- Set `athena_integration.enabled = true`

**What it syncs:**
1. **Prompts:** All article keywords (from "Prompt" column)
2. **Content:** All article URLs (from "Final_URL" column)

**Benefits:**
- Track which keywords have data vs need collection
- Monitor brand mention rates
- See content performance in Athena
- Identify zero-mention prompts

**API handles duplicates automatically:**
- Re-running is safe
- Returns: `created` vs `skipped` counts
- No errors on duplicates

**See:** Root `ATHENA_INTEGRATION_GUIDE.md` for complete setup (if that file still exists after folder moves)

---

**Ready to publish world-class content!** 🚀

