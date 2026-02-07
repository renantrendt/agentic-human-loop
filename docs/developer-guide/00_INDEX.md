---
title: README
order: 0
---

# Pipeline Documentation Index

**Last Updated:** 2025-12-10  
**Purpose:** Per-step documentation for the Content Pipeline with AI Agent

---

## 📖 How to Use This Documentation

Each step of the pipeline has its own documentation file explaining:
- What the step does
- Why it matters
- What data it produces
- What can go wrong (and rescue tasks)
- How to improve it

---

## 📋 Documentation Structure

### **Core Documentation**
- [`../README.md`](../README.md) - Quick overview & getting started
- [`../user-guide/QUICK_START.md`](../user-guide/QUICK_START.md) - Operational guide
- [`../user-guide/HUB_SPOKE_STRATEGY_ANALYSIS.md`](../user-guide/HUB_SPOKE_STRATEGY_ANALYSIS.md) - Hub & Spoke strategy (foundational)
- [`../user-guide/ZERO_COMPROMISE_MODE.md`](../user-guide/ZERO_COMPROMISE_MODE.md) - Philosophy & rescue system
- [`../user-guide/AI_AGENT_EXECUTION_PROMPTS.md`](../user-guide/AI_AGENT_EXECUTION_PROMPTS.md) - Ready-to-use prompts
- [`../../CONFIGURATION_GUIDE.md`](../../CONFIGURATION_GUIDE.md) - Configuration modes
- [`../../ATHENA_INTEGRATION_GUIDE.md`](../../ATHENA_INTEGRATION_GUIDE.md) - Athena integration

### **Step-by-Step Guides (This Folder)**

#### **Phase 1: Data Analysis (Automated)**
- [`STEP_00_brand_gap_analysis.md`](STEP_00_brand_gap_analysis.md) ✅ - Brand visibility analysis
- [`STEP_01_content_analysis.md`](STEP_01_content_analysis.md) ✅ - Keyword pattern extraction
- [`STEP_02_url_analysis.md`](STEP_02_url_analysis.md) ✅ - Citation domain analysis
- [`STEP_02C_url_semantic_analysis.md`](STEP_02C_url_semantic_analysis.md) ✅ - Search intent classification

#### **Phase 2: AI Agent Tasks - Data Collection**
- [`STEP_02B_competitor_scraping.md`](STEP_02B_competitor_scraping.md) ⭐ AI AGENT - Browser scraping task
- [`STEP_03_scraping_analysis.md`](STEP_03_scraping_analysis.md) ✅ - Competitor content review (waits for Step 2B)
- [`STEP_03B_source_library.md`](STEP_03B_source_library.md) 🆕 AUTOMATED - Perplexity Sonar source discovery (builds verified citation library)

#### **Phase 3: AI Agent Tasks - Content Creation**
- [`STEP_04_ai_synthesis.md`](STEP_04_ai_synthesis.md) ⭐ AI AGENT - Strategic synthesis
- [`STEP_05_article_generation.md`](STEP_05_article_generation.md) ⭐ AI AGENT - Article creation
- [`STEP_05B_hub_faq_generation.md`](STEP_05B_hub_faq_generation.md) ⭐ AI AGENT - Hub FAQ generation (3-5 broad FAQs)
- [`STEP_06_writing_rules.md`](STEP_06_writing_rules.md) ⭐ AI AGENT - Brand voice application

#### **Phase 4: Optimization (Automated/Hybrid)**
- [`STEP_07_internal_links.md`](STEP_07_internal_links.md) ✅ - Internal linking
- [`STEP_08_citations.md`](STEP_08_citations.md) ✅ - External citation (manual fallback)
- [`STEP_08_citation_workflow_redesign.md`](STEP_08_citation_workflow_redesign.md) 📋 DESIGN DOC - Perplexity Sonar architecture
- [`STEP_08B_citation_verification.md`](STEP_08B_citation_verification.md) 🆕 AUTOMATED - URL verification (quality gate)
- [`STEP_08C_citation_review.md`](STEP_08C_citation_review.md) 🆕 AI AGENT - Fix broken links/unverified claims (only if 8B fails)
- [`STEP_09_infrastructure.md`](STEP_09_infrastructure.md) ⭐ AI AGENT (if Spoke) - Linking map & sitemap updates

#### **Phase 5: Cluster Expansion (AI Agent, Hub Only)**
- [`STEP_10_spoke_cluster.md`](STEP_10_spoke_cluster.md) ⭐ AI AGENT - Hub + 10 spokes generation (only if Hub detected)
- [`STEP_10A_utility_articles.md`](STEP_10A_utility_articles.md) ⭐ AI AGENT - Generate 3-5 utility articles (gap-aware, task-based with Dead-End strategy)
- [`STEP_10B_spoke_citations.md`](STEP_10B_spoke_citations.md) ⭐ AI AGENT - Add citations to each spoke (10 sequential tasks)
- [`STEP_10C_citation_verification.md`](STEP_10C_citation_verification.md) ✅ AUTOMATED - Verify all spokes have citations (quality gate with smart loop)
- [`STEP_11_cluster_crosslinking.md`](STEP_11_cluster_crosslinking.md) ⭐ AI AGENT - Add internal links (Split: 11A Hub↔Spokes, 11B Utilities integration)
- [`STEP_11C_keyword_review.md`](STEP_11C_keyword_review.md) ⭐ AI AGENT - Keyword optimization (long-tail, priority, brand filter)
- [`STEP_11D_spoke_faq_generation.md`](STEP_11D_spoke_faq_generation.md) ⭐ AI AGENT - Spoke FAQ generation (2-3 specific FAQs per spoke)
- [`STEP_11E_faq_cannibalization.md`](STEP_11E_faq_cannibalization.md) ⭐ AI AGENT - FAQ overlap review & deduplication

#### **Phase 6: Publishing**
- [`STEP_12_publishing.md`](STEP_12_publishing.md) ✅ - HTML conversion + metadata generation (automated + AI agent)
- [`STEP_12B_html_editor.md`](STEP_12B_html_editor.md) ⭐ AI AGENT - HTML quality review & fixes
- [`STEP_12.5_content_qa_polish.md`](STEP_12.5_content_qa_polish.md) ✅ AUTOMATED - Editorial polish & brand voice consistency (NEW!)
- [`STEP_12C_content_gaps.md`](STEP_12C_content_gaps.md) ✅ AUTOMATED - Content gap analysis
- [`STEP_12D_link_verification.md`](STEP_12D_link_verification.md) ⭐ AI AGENT - Link & citation verification

#### **Phase 7: Quality Validation (MANDATORY)**
- [`STEP_13_model_calibration.md`](STEP_13_model_calibration.md) 🔬 - AI model validation (runs before Step 14)
- [`STEP_14_evaluation.md`](STEP_14_evaluation.md) ✅ MANDATORY - Cluster dominance test validates #1 rankings

#### **Phase 8: Completion**
- [`STEP_15_final_summary.md`](STEP_15_final_summary.md) ✅ - Session summary & handoff

#### **Phase 9: Integration (Optional)**
- [`STEP_16_athena_sync.md`](STEP_16_athena_sync.md) 🆕 - Sync published content to Athena (optional)
- [`../../ATHENA_INTEGRATION_GUIDE.md`](../../ATHENA_INTEGRATION_GUIDE.md) 🆕 - Complete Athena integration guide
- [`../../ATHENA_API_MODE.md`](../../ATHENA_API_MODE.md) 🆕 - API mode workflow (no CSV!)
- [`../../CONFIGURATION_GUIDE.md`](../../CONFIGURATION_GUIDE.md) 🆕 - Configuration reference

#### **Strategic Guides**
- [`../user-guide/HUB_SPOKE_STRATEGY_ANALYSIS.md`](../user-guide/HUB_SPOKE_STRATEGY_ANALYSIS.md) ✅ - Data sufficiency & anti-cannibalization (moved to Writer Guide)

---

## 🎯 Quick Navigation

**Want to understand a specific step?** → Open its `STEP_XX_*.md` file

**Want to improve a step?** → Each doc includes "How to Improve" section

**Troubleshooting?** → Check step's "Common Issues" section

**Adding features?** → Review "Future Enhancements" in relevant step

---

## 🔥 Documentation Philosophy

Each step doc follows this structure:
1. **Why This Step Exists** - The foundational "why" (problem/reality/solution)
2. **Overview** - What it does in 1 sentence
3. **Why It Matters** - Impact on final content quality
4. **How It Works** - Technical implementation
5. **Inputs/Outputs** - Data flow
6. **Quality Gates** - What must pass to proceed
7. **Rescue Tasks** - What triggers AI agent intervention
8. **Common Issues** - Troubleshooting
9. **How to Improve** - Enhancement opportunities

---

**Navigate:** Choose a step from the list above to dive deep! 🚀

