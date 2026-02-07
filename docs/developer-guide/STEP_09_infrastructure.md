---
title: INFRASTRUCTURE
order: 13
---

# Step 9: Update Linking Infrastructure

**Function:** `step9_update_linking_infrastructure()`  
**Type:** Automated  
**Output:** `step9_UPDATED_internal_linking_map.json`, `step9_UPDATED_sitemap.xml`

---

## 🤔 Why This Step Exists

**The Problem:**
You just published an article. Tomorrow you write another one. How does the new article know this one exists? How do you auto-link to it? You don't have a registry.

**The Reality:**
Without infrastructure, every new article requires manual linking. You have to remember "oh yeah, we wrote about conversation analytics 3 months ago, let me find that URL and manually add the link." That doesn't scale.

**The Solution:**
Register every article in the internal linking map. Title, URL, primary keyword, Hub/Spoke status. Now future articles can auto-link to it. Sitemap updated? Google knows it exists.

**Without this step:**
- Manual linking nightmare (doesn't scale)
- Forgotten content (old articles never get linked)
- No SEO infrastructure (Google can't discover)

**With this step:**
- Auto-linking enabled (future articles link automatically)
- Content registry maintained (nothing forgotten)
- Sitemap updated (Google crawls new content)

**This step exists because 1 article is easy. 50 articles? You need infrastructure. This is the database that makes the content machine work.**

---

## 📝 Overview

Updates the internal linking map and sitemap with the new article, preparing infrastructure for future internal linking.

**Keeps content ecosystem organized and discoverable.**

---

## 🎯 Why It Matters

**Internal Linking Map:**
- Registry of all published content
- Keyword → URL mapping
- Cluster/spoke relationships
- Future articles can auto-link to this one

**Sitemap:**
- Tells search engines about new content
- Ensures proper indexation
- Last-modified dates
- Priority signals

**Infrastructure = Scalability:**
Without map → Manual linking nightmare  
With map → Automated linking in future articles

---

## ⚙️ How It Works

### 1. Generate URL Slug
```python
article_slug = article_title.lower()
article_slug = re.sub(r'[^\w\s-]', '', article_slug)  # Remove special chars
article_slug = re.sub(r'[-\s]+', '-', article_slug)    # Spaces to hyphens

# "Best Platforms 2025" → "best-platforms-2025"
```

### 2. Construct Full URL
```python
article_url = f"/blog/{article_slug}"
full_url = f"https://www.solidroad.com{article_url}"
```

### 3. Determine Hub vs Spoke Classification

**Parse synthesis to identify article type:**
```python
is_cluster = False
if 'cluster (hub)' in synthesis_text.lower():
    is_cluster = True
    # Extract cluster name
elif 'spoke' in synthesis_text.lower():
    is_cluster = False
    # Extract parent cluster hint
```

### 4. Update Internal Linking Map

**Load existing map:**
```python
linking_map = json.load(open('brand-context/internal_linking_map.json'))
```

#### 4a. If Article is a HUB:
```python
# Find matching cluster in map
for cluster in linking_map['clusters']:
    if cluster_name.lower() in cluster['name'].lower():
        cluster['hub_url'] = article_url
        cluster['status'] = 'published'
        break
```

#### 4b. If Article is a SPOKE (NEW - 2025-11-21):

**Creates AI Agent Task:**

```python
spoke_task_file = os.path.join(SESSION_DIR, "step9_SPOKE_REGISTRATION_TASK.md")

# Task file includes:
# - Article title and URL
# - Parent cluster hint (from synthesis)
# - JSON template for spoke entry
# - Cluster selection criteria
# - Output file path

print(f"🤖 AGENT_TASK_READY: {spoke_task_file}")
print(f"📋 OUTPUT_FILE: step9_UPDATED_internal_linking_map.json")
```

**AI Agent Mission:**
1. Read current `internal_linking_map.json`
2. Analyze article topic + synthesis
3. Determine best-fit parent cluster based on:
   - Topic overlap
   - Keyword complementarity
   - Hub-spoke relationship logic
4. Add spoke entry to cluster's 'spokes' array:
   ```json
   {
     "primary_keyword": "conversation-analytics-platform",
     "url": "/blog/conversation-analytics-platform",
     "status": "published",
     "title": "Conversation Analytics Platform Guide",
     "created_date": "2025-11-21"
   }
   ```
5. Update meta.last_updated
6. Save updated map

**What you'll see:**
```
[HH:MM:SS] 📝 Article identified as Spoke (parent: auto-detect)
[HH:MM:SS] ✅ Spoke registration task created: step9_SPOKE_REGISTRATION_TASK.md

🤖 AGENT_TASK_READY: step9_SPOKE_REGISTRATION_TASK.md
📋 OUTPUT_FILE: step9_UPDATED_internal_linking_map.json
⏸️  Pipeline paused - AI Agent must register spoke in linking map...
```

**Why automated now:**  
Previously required manual JSON editing. Now AI agent reads the map, analyzes the article, and registers it automatically in the most appropriate cluster.

**Detect Hub or Spoke:**
```python
if 'cluster (hub)' in synthesis_text.lower():
    is_cluster = True
    # Update or create cluster entry
elif 'spoke' in synthesis_text.lower():
    is_cluster = False
    # Add to appropriate cluster's spokes array
```

**Update map structure:**
```json
{
  "clusters": [
    {
      "name": "Conversation Analytics",
      "hub_url": "/blog/conversation-analytics-platform",  ← Updated
      "status": "published",                                ← Set to published
      "spokes": [
        {
          "title": "Agent Performance Guide",
          "primary_keyword": "agent performance",
          "url": "/blog/improve-agent-performance",
          "status": "published"
        }
      ]
    }
  ],
  "meta": {
    "last_updated": "2025-11-21"                           ← Timestamp
  }
}
```

### 4. Update Sitemap

**Load existing sitemap:**
```python
sitemap_content = read_file('brand-context/sitemap')
```

**Add new entry:**
```xml
<url>
  <loc>https://www.solidroad.com/blog/best-conversation-analytics-platforms-2025</loc>
</url>
```

**Insert before closing `</urlset>` tag**

### 5. Save Updated Files
```python
json.dump(linking_map, 'step9_UPDATED_internal_linking_map.json')
write_file('step9_UPDATED_sitemap.xml', sitemap_content)
```

---

## 📊 Inputs & Outputs

### Inputs:
- Article title (for slug generation)
- Step 4 synthesis (Hub vs Spoke classification)
- Existing linking map & sitemap

### Outputs:
**`step9_UPDATED_internal_linking_map.json`:**
- New Hub entry (if cluster)
- New spoke entry (if spoke)
- Updated timestamp

**`step9_UPDATED_sitemap.xml`:**
- New URL entry
- Proper XML formatting

---

## 🚨 Quality Considerations

### Not a Hard Blocker:
```python
try:
    update_linking_map()
except Exception as e:
    ⚠️ Warning, continues (non-critical)
```

**Why:**
- Infrastructure updates are "nice to have"
- Can be done manually
- Doesn't affect article quality

### Best Practice:
Always keep map & sitemap updated for:
- Easier internal linking in future
- Better SEO organization
- Team collaboration

---

## 🔧 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Cluster not found in map | New topic cluster | Log warning, manual addition needed |
| Malformed JSON | Editing error | Validate JSON structure |
| Duplicate URLs | Same article run twice | Check before adding |
| Sitemap size limit | >50,000 URLs | Split into multiple sitemaps |

---

## 📈 Internal Linking Map Structure

### Cluster Entry:
```json
{
  "name": "Conversation Analytics",          ← Cluster name
  "hub_url": "/blog/conversation-analytics", ← Pillar article
  "hub_title": "Best Platforms 2025",
  "hub_keyword": "conversation analytics platform",
  "status": "published",
  "created": "2025-11-21",
  "spokes": [...]                            ← Array of spoke articles
}
```

### Spoke Entry:
```json
{
  "title": "Agent Performance Guide",
  "primary_keyword": "improve agent performance",
  "url": "/blog/improve-agent-performance-analytics",
  "status": "published",
  "created": "2025-11-21",
  "word_count": 1850,
  "links_to_hub": true,
  "links_to_spokes": ["spoke_4", "spoke_6"]
}
```

---

## 💡 How to Improve

### Enhancement 1: Automatic Cluster Detection
```python
# Instead of parsing synthesis text:
# Analyze article content structure
if word_count > 2500 and h2_count > 15:
    likely_hub = True
```

### Enhancement 2: Bi-directional Linking
```python
# When adding new spoke:
# 1. Add spoke to cluster
# 2. Update Hub article to link to new spoke
# 3. Update related spokes to link to new spoke
```

### Enhancement 3: Link Opportunity Detection
```python
# For new article, scan existing articles:
# Which articles should link to this new one?
# Auto-generate linking suggestions
```

### Enhancement 4: Sitemap Priorities
```python
# Hubs get priority 0.9
# Spokes get priority 0.7
# Other content 0.5

<url>
  <loc>https://...</loc>
  <priority>0.9</priority>
  <changefreq>monthly</changefreq>
</url>
```

---

## 🎓 Sitemap Best Practices

### XML Structure:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://www.solidroad.com/blog/article-slug</loc>
    <lastmod>2025-11-21</lastmod>
    <priority>0.8</priority>
  </url>
  ...
</urlset>
```

### Priority Guidelines:
- Homepage: 1.0
- Hub articles: 0.9
- Spoke articles: 0.7
- Blog posts: 0.5
- Utility pages: 0.3

### Change Frequency:
- Evergreen hubs: `monthly`
- Time-sensitive: `weekly`
- Static pages: `yearly`

---

## 🔗 Data Flow

```
Step 7: Article with internal links
  ↓
Step 8: Citations added
  ↓
Step 9: Update infrastructure
  ↓
Extract: Title, slug, Hub/Spoke type
  ↓
Update: internal_linking_map.json
  ↓
Update: sitemap.xml
  ↓
Save: Updated versions to session dir
  ↓
Step 10: Uses map for spoke generation
```

---

## 📋 Infrastructure Checklist

After this step:
- [ ] ✅ Article registered in linking map
- [ ] ✅ URL added to sitemap
- [ ] ✅ Hub/Spoke relationship recorded
- [ ] ✅ Timestamp updated
- [ ] ✅ Future articles can auto-link to this

---

## 🎓 Long-Term Vision

### Content Ecosystem Growth:

**After 1 article:**
- Linking map has 1 entry
- Sitemap has 1 URL

**After Hub + 10 spokes:**
- Linking map has 11 entries (1 cluster)
- Sitemap has 11 URLs
- 50+ internal links between articles

**After 5 Hubs (50 total articles):**
- Linking map has 50 entries (5 clusters)
- Sitemap has 50 URLs
- 200+ internal links
- **Topical authority DOMINANCE**

### Maintenance:

**Quarterly review:**
- Check for broken links (404s)
- Update outdated content (refresh dates)
- Add new spokes to existing hubs
- Cross-link related clusters

---

## 🔗 Related Steps

- **Requires:** Article title, Step 4 synthesis
- **Feeds:** Future Step 7 (internal linking for new articles)
- **Used by:** Step 10 (spoke cluster updates map)

---

**Infrastructure = Foundation for scale** 🏗️

**Next:** [STEP_10_spoke_cluster.md](STEP_10_spoke_cluster.md)


