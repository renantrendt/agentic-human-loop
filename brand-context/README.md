# 🎨 Brand Context Configuration

**Purpose:** Brand-specific rules, voice, and configuration for content generation

---

## 📁 **FILES IN THIS FOLDER**

### **Configuration:**
- **`config.json`** - Brand settings (name, URL, author, Google Sheets, etc.)
- **`config.json.example`** - Template for other companies

### **Brand Voice & Rules:**
- **`solidroad`** - Brand voice, positioning, unique insights
- **`rule_draft.ts`** - Draft generation rules
- **`rule_writing.ts`** - 21 writing rules for brand alignment (updated Dec 2025)

### **Content Strategy:**
- **`internal_linking_map.json`** - Content hub structure
- **`sitemap`** - Site URLs for internal linking
- **`rule_citations.md`** - Citation guidelines
- **`rule_content-hub.md`** - Hub vs Spoke strategy

---

## 🔧 **USING THIS PIPELINE FOR YOUR COMPANY**

### **Step 1: Configure Brand Settings**

```bash
# Copy example config
cp brand-context/config.json.example brand-context/config.json

# Edit with your details
nano brand-context/config.json
```

**Required fields:**
- `brand.name` → "Your Company"
- `brand.url` → "https://yourcompany.com"
- `brand.author_name` → "Your Name"
- `publishing.google_sheets.spreadsheet_id` → Your sheet ID
- `publishing.google_sheets.sheet_name` → Your sheet tab name

**Optional fields:**
- `brand.default_product_links` → Only if you don't use sitemap file
- `brand.tagline` → Company tagline
- `brand.industry` → Your industry
- `brand.keywords` → Auto-generated from brand.name if not provided

### **Step 2: Add Your Brand Voice File**

Create `brand-context/yourcompany` with:
- Founding story
- Unique frameworks/methodologies
- Case studies
- Contrarian viewpoints
- Differentiators

**Format:** Plain text (like `solidroad` file)

### **Step 3: Update Internal Links (Recommended)**

**Option A: Use Sitemap File (Recommended)** ✅

Edit `brand-context/sitemap` with your actual URLs:
- Product pages
- Blog URLs
- Customer stories
- Resources

**Format:** `URL|Title|Type|Keywords`

**Example:**
```
https://yourcompany.com/contact|Contact Us|product|contact, demo, get started
https://yourcompany.com/pricing|Pricing|product|pricing, plans, cost
https://yourcompany.com/blog/article-1|Article Title|blog|topic, keyword
```

**Option B: Use Config product_links (Alternative)**

Add to `config.json`:
```json
{
  "brand": {
    "default_product_links": [
      {"url": "https://yourcompany.com/contact", "title": "Contact", ...}
    ]
  }
}
```

**Option C: Neither (Minimal)**

Pipeline will only link to your homepage (safe fallback).

**Priority Order:**
1. Sitemap (if exists) ← BEST
2. Config product_links (if provided)
3. Homepage only (always safe)

### **Step 4: Run Pipeline**

```bash
python3 agentic-human-loop/content_pipeline_with_ai_agent.py
```

**Pipeline automatically uses your config!** ✅

---

## 🎯 **WHAT'S CONFIGURABLE**

### **Brand Identity:**
- Company name (appears in all articles)
- Company URL (first mention links here)
- Author name (appears in published articles)
- Brand tagline
- Industry/category

### **Publishing:**
- Google Sheets ID (where to publish)
- Sheet tab name
- OAuth credentials (team-specific)

### **Content Standards:**
- Hub word count targets (min/ideal/max)
- Spoke word count targets
- Default category
- Default tags

### **SEO:**
- Meta description length (150-160 chars default)

---

## 📋 **FOR AGENCIES/CONSULTANTS**

**Managing multiple clients:**

```bash
# Client 1: Solidroad
brand-context/config.json          (Solidroad settings)
brand-context/solidroad            (brand voice)

# Client 2: Another Company
brand-context/config-client2.json  (their settings)
brand-context/client2-voice        (their brand)

# Switch clients:
cp brand-context/config-client2.json brand-context/config.json
```

**Run pipeline** → Generates content for Client 2 automatically!

---

## ✅ **UNIVERSAL PIPELINE**

**Same codebase works for:**
- ✅ Any B2B SaaS company
- ✅ Any industry vertical
- ✅ Any language/region
- ✅ Any content strategy

**Just update config.json!**

---

**See:** Main README.md for complete setup guide

