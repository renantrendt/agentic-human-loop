"""
Brand Gap Detector — clusters social signals, filters by relevance,
and compares against existing brand content to find uncovered topics.

Adapted from AY-AY-AY-AY/new-prompt-planner back-end/activities/prompt_planner_social.py
Temporal + Supabase removed. Uses local files + sitemap + optional Athena API.

Usage:
    from social_monitor.gap_detector import detect_gaps
    gaps = detect_gaps(config, session_dir)
"""

import json
import logging
import os
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import anthropic
import tenacity
from anthropic.types import TextBlock

from autonomous.secrets import get_secret

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MIN_CLUSTER_SIZE = 3
MAX_ENTRIES_PER_CLUSTER_FOR_AI = 15
MAX_SOCIAL_ENTRIES = 200
MAX_CONCURRENT_REQUESTS = 10


def _get_claude_client(config: dict):
    model = config.get("autonomous", {}).get("model", "claude-opus-4-6")
    max_tokens = config.get("autonomous", {}).get("max_tokens", 16000)
    api_key = get_secret("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    client = anthropic.Anthropic(api_key=api_key)
    return client, model, max_tokens


# ---------------------------------------------------------------------------
# Claude helpers
# ---------------------------------------------------------------------------

@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
    retry=tenacity.retry_if_exception_type(Exception),
)
def _call_claude(client, model: str, max_tokens: int, prompt: str) -> str:
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}],
    )
    if response.content:
        for block in response.content:
            if isinstance(block, TextBlock):
                return block.text
    raise ValueError(f"Unexpected response format: {response}")


def _extract_json(text: str, expect_array: bool = True):
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if json_match:
        json_str = json_match.group(1).strip()
    else:
        open_fence = re.search(r"```(?:json)?\s*", text)
        if open_fence:
            json_str = text[open_fence.end():].strip()
        else:
            json_str = text.strip()
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        json_str = _repair_json(json_str)
        return json.loads(json_str)


def _repair_json(text: str) -> str:
    repaired = re.sub(r',\s*"[^"]*$', "", text)
    repaired = re.sub(r':\s*"[^"]*$', ': ""', repaired)
    open_braces = repaired.count("{") - repaired.count("}")
    open_brackets = repaired.count("[") - repaired.count("]")
    repaired += "}" * max(0, open_braces)
    repaired += "]" * max(0, open_brackets)
    return repaired


# ---------------------------------------------------------------------------
# Clustering via Claude (no local ML models needed)
# ---------------------------------------------------------------------------

CLUSTERING_PROMPT = """You are an expert in social listening and thematic analysis.

Below are {count} social media posts/comments collected from Reddit and YouTube.
Group them into thematic clusters based on the topics and questions people are discussing.

{entries_text}

## Instructions
- Group posts that discuss the same topic/question/theme together
- Ignore noise, spam, or off-topic posts (mark them as outliers)
- Each cluster should have at least {min_size} entries
- For each cluster, identify the core theme and representative entries

Return ONLY this JSON:
```json
{{
    "clusters": [
        {{
            "cluster_id": 0,
            "theme": "short descriptive theme",
            "entry_indices": [0, 3, 7],
            "total_entries": 3
        }}
    ],
    "outlier_count": 5
}}
```"""


def cluster_social_entries(entries: list[dict], client=None, model: str = "", max_tokens: int = 16000) -> list[dict]:
    """Clusters social entries using Claude instead of local ML models."""
    if len(entries) > MAX_SOCIAL_ENTRIES:
        entries = entries[:MAX_SOCIAL_ENTRIES]
        logger.warning(f"  Capped to {MAX_SOCIAL_ENTRIES} entries for performance")

    logger.info(f"  Clustering {len(entries)} social entries with Claude...")

    entries_lines = []
    for i, e in enumerate(entries):
        src = e.get("source", "unknown").upper()
        text = e["text"][:200].replace("\n", " ")
        entries_lines.append(f"[{i}] [{src}] {text}")

    prompt = CLUSTERING_PROMPT.format(
        count=len(entries),
        entries_text="\n".join(entries_lines),
        min_size=MIN_CLUSTER_SIZE,
    )

    response = _call_claude(client, model, max_tokens, prompt)
    result = _extract_json(response, expect_array=False)

    clusters = []
    for c in result.get("clusters", []):
        indices = c.get("entry_indices", [])
        cluster_entries = [entries[i] for i in indices if i < len(entries)]

        reddit_count = sum(1 for e in cluster_entries if e.get("source") == "reddit")
        youtube_count = sum(1 for e in cluster_entries if e.get("source") == "youtube")
        categories = list(set(e.get("category", "") for e in cluster_entries if e.get("category")))

        clusters.append({
            "cluster_id": c.get("cluster_id", len(clusters)),
            "theme": c.get("theme", "Unknown"),
            "entries": cluster_entries[:MAX_ENTRIES_PER_CLUSTER_FOR_AI],
            "total_entries": len(cluster_entries),
            "reddit_count": reddit_count,
            "youtube_count": youtube_count,
            "categories": categories[:5],
        })

    clusters.sort(key=lambda x: x["total_entries"], reverse=True)
    outliers = result.get("outlier_count", 0)
    logger.info(f"  Found {len(clusters)} clusters (excluded {outliers} outliers)")
    return clusters


def _format_clusters_for_ai(clusters: list[dict]) -> str:
    lines = []
    for cluster in clusters:
        lines.append(f"### Cluster {cluster['cluster_id']}")
        lines.append(
            f"- Total entries: {cluster['total_entries']} "
            f"(Reddit: {cluster['reddit_count']}, YouTube: {cluster['youtube_count']})"
        )
        lines.append(
            f"- Product categories: {', '.join(cluster['categories']) if cluster['categories'] else 'Various'}"
        )
        lines.append("- Sample conversations:")
        for entry in cluster["entries"][:8]:
            source_label = f"[{entry['source'].upper()}]"
            text_preview = entry["text"][:200].replace("\n", " ")
            lines.append(f"  {source_label} \"{text_preview}\"")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Brand content comparison
# ---------------------------------------------------------------------------

def load_existing_content(config: dict) -> list[str]:
    """
    Load existing brand content from sitemap URLs.
    Extracts page slugs/titles as text for semantic comparison.
    """
    sitemap_path = Path("brand-context/sitemap")
    existing_content = []

    if sitemap_path.exists():
        try:
            content = sitemap_path.read_text(encoding="utf-8")
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            # Strip the first line if it's not XML
            if not content.strip().startswith("<?xml") and not content.strip().startswith("<urlset"):
                lines = content.split("\n")
                content = "\n".join(lines[1:]) if len(lines) > 1 else content

            root = ET.fromstring(content)
            for url_el in root.findall("sm:url", ns):
                loc = url_el.find("sm:loc", ns)
                if loc is not None and loc.text:
                    slug = loc.text.rstrip("/").split("/")[-1]
                    title = slug.replace("-", " ").replace("_", " ")
                    if title and title not in ("404", ""):
                        existing_content.append(title)
        except ET.ParseError as e:
            logger.warning(f"Failed to parse sitemap: {e}")
            # Fallback: regex extraction
            urls = re.findall(r"<loc>([^<]+)</loc>", sitemap_path.read_text(encoding="utf-8"))
            for url in urls:
                slug = url.rstrip("/").split("/")[-1]
                title = slug.replace("-", " ").replace("_", " ")
                if title and title not in ("404", ""):
                    existing_content.append(title)

    logger.info(f"  Loaded {len(existing_content)} existing content pages from sitemap")
    return existing_content


COVERAGE_PROMPT = """You are an SEO content strategist.

## Candidate Topics
{candidates}

## Existing Brand Content (page titles/slugs)
{existing}

For each candidate, determine if the brand already covers this topic.
A topic is "covered" if an existing page substantially addresses it (not just tangentially).

Return ONLY this JSON array:
```json
[
    {{"prompt": "the candidate", "is_covered": false, "best_match": null, "coverage_score": 0.0}},
    {{"prompt": "another", "is_covered": true, "best_match": "existing page title", "coverage_score": 0.9}}
]
```"""


def check_coverage(
    candidate_prompts: list[str],
    existing_content: list[str],
    client=None,
    model: str = "",
    max_tokens: int = 16000,
) -> list[dict]:
    """Compares candidate prompts against existing content using Claude."""
    if not existing_content or not candidate_prompts:
        return [{"prompt": p, "coverage_score": 0.0, "is_covered": False} for p in candidate_prompts]

    logger.info(f"  Checking coverage of {len(candidate_prompts)} candidates against {len(existing_content)} pages...")

    candidates_text = "\n".join(f"- {p}" for p in candidate_prompts)
    existing_text = "\n".join(f"- {c}" for c in existing_content[:100])

    prompt = COVERAGE_PROMPT.format(candidates=candidates_text, existing=existing_text)
    response = _call_claude(client, model, max_tokens, prompt)
    results = _extract_json(response, expect_array=True)

    prompt_map = {r.get("prompt", "").strip().lower(): r for r in results}
    final = []
    for p in candidate_prompts:
        match = prompt_map.get(p.strip().lower(), {"prompt": p, "coverage_score": 0.0, "is_covered": False})
        final.append(match)

    covered = sum(1 for r in final if r.get("is_covered"))
    logger.info(f"  Coverage check: {covered}/{len(final)} prompts already covered")
    return final


# ---------------------------------------------------------------------------
# Rejection memory
# ---------------------------------------------------------------------------

def load_past_rejections(session_dir: str) -> list[dict]:
    """Scan all past sessions for rejections.json and aggregate them."""
    results_root = Path(session_dir).parent
    all_rejections = []
    if not results_root.exists():
        return all_rejections

    for session_path in sorted(results_root.glob("session_*")):
        rej_file = session_path / "rejections.json"
        if rej_file.exists():
            try:
                data = json.load(open(rej_file))
                for r in data.get("rejections", []):
                    all_rejections.append(r)
            except (json.JSONDecodeError, KeyError):
                continue

    if all_rejections:
        logger.info(f"  Loaded {len(all_rejections)} past rejections for agent learning")
    return all_rejections


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

CLUSTER_ANALYSIS_PROMPT = """You are an expert in social listening, consumer insights, and SEO strategy.

## Company Context

**Target Prompt**: {target_prompt}
**Target Audience**: {target_audience}
**Language**: {language}

## Social Media Discussion Clusters

Below are {cluster_count} thematic clusters identified from Reddit posts and YouTube comments.

{clusters_data}

## Your Task

Analyze these clusters. For each cluster, determine:
1. Is it relevant to the brand's target topic ("{target_prompt}")?
2. What user need does it represent?
3. How many search prompts (2-8) should address this cluster?
4. What angles should the prompts cover?

ONLY mark clusters as relevant if they directly relate to the brand's topic.

## Output Format

```json
{{
    "analysis_summary": "Brief summary of social data insights",
    "clusters": [
        {{
            "cluster_id": 0,
            "theme": "descriptive theme",
            "is_relevant": true,
            "relevance_reason": "Why relevant or not",
            "user_need": "What people are asking",
            "prompt_count": 5,
            "prompt_angles": ["angle 1", "angle 2"],
            "priority": "high|medium|low"
        }}
    ],
    "total_prompts_recommended": 30
}}
```

Return ONLY the JSON object."""


PROMPT_GENERATION_PROMPT = """You are an expert in SEO and social listening.

## Context
**Target Topic**: {target_prompt}
**Target Audience**: {target_audience}

## Social Signal Summary
{analysis_summary}

## Cluster to Address
**Theme**: {cluster_theme}
**User Need**: {user_need}

### Real conversations:
{cluster_samples}

### Angles to cover: {prompt_angles}

Generate {prompt_count} search prompts that address what people are discussing.
{rejected_section}
Requirements:
1. Realistic search queries people would actually type
2. Address the UNDERLYING NEED from the discussions
3. Vary keyword types (head, mid-tail, long-tail)
4. Vary search intent (informational, commercial, transactional)
5. No brand names, no duplicates
6. Do NOT generate prompts similar to previously rejected topics

```json
[
    {{
        "prompt": "the search query",
        "keyword_type": "head|mid_tail|long_tail",
        "search_intent": "informational|commercial|transactional",
        "funnel_stage": "TOFU|MOFU|BOFU",
        "rationale": "What user need this addresses"
    }}
]
```

Return ONLY the JSON array."""


def detect_gaps(config: dict, session_dir: str) -> dict:
    """
    Main entry point. Reads social_signals.json, clusters, analyzes relevance,
    generates candidate prompts, compares against existing content, outputs gaps.
    """
    signals_path = Path(session_dir) / "social_signals.json"
    if not signals_path.exists():
        return {"status": "no_signals", "error": "social_signals.json not found. Run social monitor first."}

    with open(signals_path, "r", encoding="utf-8") as f:
        signals = json.load(f)

    entries = signals.get("entries", [])
    if len(entries) < MIN_CLUSTER_SIZE:
        return {
            "status": "insufficient_data",
            "entries_count": len(entries),
            "error": f"Not enough social data ({len(entries)} entries). Need at least {MIN_CLUSTER_SIZE}.",
        }

    client, model, max_tokens = _get_claude_client(config)

    target_prompt = config.get("athena_integration", {}).get("target_prompt", "")
    target_audience = config.get("content", {}).get("target_audience", "")
    language = config.get("content", {}).get("language", "English")

    logger.info("=" * 60)
    logger.info("BRAND GAP DETECTOR")
    logger.info(f"Social entries: {len(entries)}")
    logger.info("=" * 60)

    # Step 1: Cluster (using Claude)
    logger.info("\nStep 1: Clustering social entries with Claude...")
    clusters = cluster_social_entries(entries, client=client, model=model, max_tokens=max_tokens)
    if not clusters:
        return {"status": "no_clusters", "entries_count": len(entries)}

    # Step 2: Analyze relevance with Claude
    logger.info("\nStep 2: Analyzing cluster relevance with AI...")
    clusters_data = _format_clusters_for_ai(clusters)

    analysis_prompt = CLUSTER_ANALYSIS_PROMPT.format(
        target_prompt=target_prompt,
        target_audience=target_audience,
        language=language,
        cluster_count=len(clusters),
        clusters_data=clusters_data,
    )

    analysis_response = _call_claude(client, model, max_tokens, analysis_prompt)
    analysis = _extract_json(analysis_response, expect_array=False)

    analysis_summary = analysis.get("analysis_summary", "")
    relevant_clusters = [c for c in analysis.get("clusters", []) if c.get("is_relevant")]
    logger.info(f"  Relevant clusters: {len(relevant_clusters)}/{len(clusters)}")

    if not relevant_clusters:
        result = {
            "status": "no_relevant_clusters",
            "entries_count": len(entries),
            "clusters_count": len(clusters),
            "analysis_summary": analysis_summary,
            "gaps": [],
        }
        _save_results(session_dir, result)
        return result

    # Load past rejections for agent learning
    past_rejections = load_past_rejections(session_dir)
    rejected_section = ""
    if past_rejections:
        rej_lines = [f"- \"{r['prompt']}\" (reason: {r.get('reason', 'no reason')})" for r in past_rejections[:20]]
        rejected_section = "\n## Previously Rejected Topics (DO NOT generate similar prompts)\n" + "\n".join(rej_lines) + "\n"

    # Step 3: Generate candidate prompts (parallel)
    logger.info("\nStep 3: Generating candidate prompts...")
    all_prompts = []

    def _generate_for_cluster(cluster_info, original_cluster):
        cluster_id = cluster_info.get("cluster_id")
        prompt_count = cluster_info.get("prompt_count", 5)
        prompt_angles = cluster_info.get("prompt_angles", [])
        user_need = cluster_info.get("user_need", "")

        samples = []
        for entry in original_cluster.get("entries", [])[:8]:
            src = entry["source"].upper()
            txt = entry["text"][:300].replace("\n", " ")
            samples.append(f'[{src}] "{txt}"')

        gen_prompt = PROMPT_GENERATION_PROMPT.format(
            target_prompt=target_prompt,
            target_audience=target_audience,
            analysis_summary=analysis_summary,
            cluster_theme=cluster_info.get("theme", ""),
            user_need=user_need,
            cluster_samples="\n".join(samples),
            prompt_angles=", ".join(prompt_angles) if prompt_angles else "Various",
            prompt_count=prompt_count,
            rejected_section=rejected_section,
        )

        try:
            response = _call_claude(client, model, max_tokens, gen_prompt)
            prompts = _extract_json(response, expect_array=True)
            for p in prompts:
                p["cluster_id"] = cluster_id
                p["cluster_theme"] = cluster_info.get("theme", "")
                p["priority"] = cluster_info.get("priority", "medium")
            return prompts
        except Exception as e:
            logger.error(f"  Cluster {cluster_id} failed: {e}")
            return []

    cluster_tasks = []
    for cluster_info in relevant_clusters:
        cid = cluster_info.get("cluster_id")
        original = next((c for c in clusters if c["cluster_id"] == cid), None)
        if original:
            cluster_tasks.append((cluster_info, original))

    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
        futures = {
            executor.submit(_generate_for_cluster, ci, oc): ci.get("cluster_id")
            for ci, oc in cluster_tasks
        }
        for future in as_completed(futures):
            prompts = future.result()
            all_prompts.extend(prompts)

    # Deduplicate
    seen = set()
    unique_prompts = []
    for p in all_prompts:
        text = p.get("prompt", "").strip().lower()
        if text and text not in seen:
            seen.add(text)
            unique_prompts.append(p)

    logger.info(f"  Generated {len(unique_prompts)} unique candidate prompts")

    # Step 4: Compare against existing content
    logger.info("\nStep 4: Checking coverage against existing brand content...")
    existing_content = load_existing_content(config)
    candidate_texts = [p["prompt"] for p in unique_prompts]
    coverage_results = check_coverage(candidate_texts, existing_content, client=client, model=model, max_tokens=max_tokens)

    # Build gaps list (uncovered prompts, excluding previously rejected topics)
    rejected_prompts = {r["prompt"].strip().lower() for r in past_rejections}
    gaps = []
    for prompt_data, coverage in zip(unique_prompts, coverage_results):
        if not coverage["is_covered"]:
            if prompt_data.get("prompt", "").strip().lower() in rejected_prompts:
                logger.info(f"  Skipping previously rejected: {prompt_data['prompt'][:60]}")
                continue
            gaps.append({
                **prompt_data,
                "coverage_score": coverage["coverage_score"],
                "closest_existing": coverage["best_match"],
            })

    # Sort by priority then by coverage score (lowest first = biggest gap)
    priority_order = {"high": 0, "medium": 1, "low": 2}
    gaps.sort(key=lambda g: (priority_order.get(g.get("priority", "medium"), 1), g["coverage_score"]))

    logger.info(f"\n  GAPS FOUND: {len(gaps)} uncovered topics out of {len(unique_prompts)} candidates")

    result = {
        "status": "success",
        "entries_count": len(entries),
        "clusters_count": len(clusters),
        "relevant_clusters": len(relevant_clusters),
        "analysis_summary": analysis_summary,
        "candidates_generated": len(unique_prompts),
        "candidates_covered": len(unique_prompts) - len(gaps),
        "gaps_found": len(gaps),
        "gaps": gaps,
    }

    _save_results(session_dir, result)
    return result


def _save_results(session_dir: str, result: dict):
    output_path = Path(session_dir) / "content_gaps.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "detected_at": datetime.now(timezone.utc).isoformat(),
            **result,
        }, f, indent=2, ensure_ascii=False)
    logger.info(f"  Results saved to {output_path}")
