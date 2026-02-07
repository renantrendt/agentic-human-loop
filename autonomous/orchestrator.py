"""
Autonomous Orchestrator — runs the full content pipeline end-to-end.

Coordinates: social monitoring → gap detection → content generation → staging.
Content is NEVER auto-published. All articles are staged for user approval
via the email digest.

Usage:
    python -m autonomous.orchestrator [--config brand-context/config.json]
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = "brand-context/config.json"


def run_pipeline(config: dict, session_dir: str) -> dict:
    """
    Run the full autonomous pipeline for a single session.

    Steps:
        1. Social signal collection (Reddit + YouTube)
        2. Gap detection (clustering + coverage comparison)
        3. Content generation for each gap (via agent_executor)
        4. Quality gates
        5. Stage articles (NOT publish — awaits user approval)

    Returns a session summary dict.
    """
    from social_monitor.runner import run as run_social_monitor
    from social_monitor.gap_detector import detect_gaps
    from autonomous.agent_executor import execute_task, get_client
    from autonomous.quality_gates import run_all_gates

    summary = {
        "session_dir": session_dir,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "steps": {},
        "articles_staged": [],
        "escalations": [],
        "package_requests": [],
    }

    # --- Step 1: Social Signal Collection ---
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 1: SOCIAL SIGNAL COLLECTION")
    logger.info("=" * 80)

    try:
        social_results = run_social_monitor(config, session_dir)
        summary["steps"]["social_monitor"] = {
            "status": "success",
            "reddit_posts": social_results.get("reddit", {}).get("posts_found", 0),
            "youtube_comments": social_results.get("youtube", {}).get("comments_found", 0),
            "total_signals": social_results.get("merged", {}).get("total_entries", 0),
        }
    except Exception as e:
        logger.error(f"Social monitoring failed: {e}")
        summary["steps"]["social_monitor"] = {"status": "failed", "error": str(e)}
        summary["escalations"].append({
            "type": "step_failure",
            "step": "social_monitor",
            "error": str(e),
        })
        return summary

    # --- Step 2: Gap Detection ---
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 2: BRAND GAP DETECTION")
    logger.info("=" * 80)

    try:
        gap_results = detect_gaps(config, session_dir)
        gaps = gap_results.get("gaps", [])
        summary["steps"]["gap_detection"] = {
            "status": gap_results.get("status", "unknown"),
            "candidates_generated": gap_results.get("candidates_generated", 0),
            "gaps_found": len(gaps),
            "analysis_summary": gap_results.get("analysis_summary", ""),
        }
    except Exception as e:
        logger.error(f"Gap detection failed: {e}")
        summary["steps"]["gap_detection"] = {"status": "failed", "error": str(e)}
        summary["escalations"].append({
            "type": "step_failure",
            "step": "gap_detection",
            "error": str(e),
        })
        return summary

    if not gaps:
        logger.info("No content gaps found — brand already covers all detected topics")
        summary["steps"]["gap_detection"]["message"] = "No gaps — brand content is comprehensive"
        summary["completed_at"] = datetime.now(timezone.utc).isoformat()
        _save_summary(session_dir, summary)
        return summary

    # --- Step 3: Content Generation ---
    logger.info("\n" + "=" * 80)
    logger.info(f"PHASE 3: CONTENT GENERATION ({len(gaps)} gaps to address)")
    logger.info("=" * 80)

    max_articles = config.get("autonomous", {}).get("max_articles_per_run", 3)
    gaps_to_process = gaps[:max_articles]
    logger.info(f"Processing top {len(gaps_to_process)} gaps (max per run: {max_articles})")

    articles_generated = []
    for i, gap in enumerate(gaps_to_process):
        prompt_text = gap.get("prompt", "")
        logger.info(f"\n--- Article {i + 1}/{len(gaps_to_process)}: '{prompt_text}' ---")

        try:
            article_result = _generate_article_for_gap(
                gap=gap,
                config=config,
                session_dir=session_dir,
                article_index=i,
            )
            articles_generated.append(article_result)

            if article_result.get("status") == "success":
                summary["articles_staged"].append({
                    "prompt": prompt_text,
                    "article_file": article_result.get("article_file", ""),
                    "word_count": article_result.get("word_count", 0),
                    "priority": gap.get("priority", "medium"),
                    "coverage_score": gap.get("coverage_score", 0),
                    "approved": False,
                })
        except Exception as e:
            logger.error(f"Article generation failed for '{prompt_text}': {e}")
            summary["escalations"].append({
                "type": "article_failure",
                "prompt": prompt_text,
                "error": str(e),
            })

    summary["steps"]["content_generation"] = {
        "status": "success",
        "gaps_processed": len(gaps_to_process),
        "articles_generated": len([a for a in articles_generated if a.get("status") == "success"]),
    }

    # --- Step 4: Quality Gates ---
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 4: QUALITY GATES")
    logger.info("=" * 80)

    gate_results = run_all_gates(session_dir, config)
    summary["steps"]["quality_gates"] = gate_results

    if gate_results.get("escalations"):
        summary["escalations"].extend([
            {"type": "quality_gate", **esc} for esc in gate_results["escalations"]
        ])

    # --- Finalize ---
    summary["completed_at"] = datetime.now(timezone.utc).isoformat()
    summary["status"] = "completed"

    logger.info("\n" + "*" * 80)
    logger.info("PIPELINE COMPLETE")
    logger.info(f"Articles staged: {len(summary['articles_staged'])}")
    logger.info(f"Escalations: {len(summary['escalations'])}")
    logger.info(f"All content awaits user approval via email digest")
    logger.info("*" * 80)

    _save_summary(session_dir, summary)
    return summary


def _generate_article_for_gap(gap: dict, config: dict, session_dir: str, article_index: int) -> dict:
    """Generate a complete article for a content gap using the agent executor."""
    from autonomous.agent_executor import execute_task, get_client, call_claude, SYSTEM_PROMPT

    prompt_text = gap.get("prompt", "")
    rationale = gap.get("rationale", "")
    keyword_type = gap.get("keyword_type", "")
    search_intent = gap.get("search_intent", "")

    client, model, max_tokens = get_client(config)

    # Build the article generation prompt
    brand_context = ""
    brand_file = Path("brand-context/solidroad")
    if brand_file.exists():
        brand_context = brand_file.read_text(encoding="utf-8")[:5000]

    target_audience = config.get("content", {}).get("target_audience", "")
    language = config.get("content", {}).get("language", "English")
    tone = config.get("content", {}).get("tone", "")
    word_targets = config.get("content", {}).get("word_count_targets", {}).get("hub", {})
    min_words = word_targets.get("min", 3000)
    ideal_words = word_targets.get("ideal", 4000)

    article_prompt = f"""Write a comprehensive, SEO-optimized article for the following topic.

## Topic
**Search Query**: {prompt_text}
**Keyword Type**: {keyword_type}
**Search Intent**: {search_intent}
**Why This Matters**: {rationale}

## Requirements
- Language: {language}
- Target audience: {target_audience}
- Tone: {tone}
- Word count: {ideal_words} words (minimum {min_words})
- Format: Markdown with proper heading hierarchy (H1, H2, H3)
- Include an engaging introduction that hooks the reader
- Include actionable takeaways and practical advice
- Include a compelling conclusion
- Use data and examples where possible
- Write for humans first, search engines second

## Brand Context
{brand_context}

Output ONLY the article in Markdown format. Start with the H1 title."""

    try:
        article_content = call_claude(client, model, max_tokens, SYSTEM_PROMPT, article_prompt)
        word_count = len(article_content.split())

        article_dir = Path(session_dir) / "articles" / "staged"
        article_dir.mkdir(parents=True, exist_ok=True)

        slug = prompt_text.lower().strip()[:60]
        slug = slug.replace(" ", "-").replace("?", "").replace("'", "")
        slug = "-".join(slug.split("-")[:8])

        article_file = article_dir / f"article_{article_index:02d}_{slug}.md"
        article_file.write_text(article_content, encoding="utf-8")

        logger.info(f"  Generated: {article_file.name} ({word_count} words)")

        return {
            "status": "success",
            "article_file": str(article_file),
            "word_count": word_count,
            "prompt": prompt_text,
        }
    except Exception as e:
        return {"status": "failed", "error": str(e), "prompt": prompt_text}


def _save_summary(session_dir: str, summary: dict):
    summary_path = Path(session_dir) / "pipeline_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(f"Summary saved to {summary_path}")


def main():
    parser = argparse.ArgumentParser(description="Autonomous Content Agent Pipeline")
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="Path to config.json")
    parser.add_argument("--session-dir", default=None, help="Session directory (auto-generated if not set)")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Config not found: {config_path}")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    if args.session_dir:
        session_dir = args.session_dir
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = f"results/local_pipeline/session_{timestamp}"

    Path(session_dir).mkdir(parents=True, exist_ok=True)

    summary = run_pipeline(config, session_dir)

    print(f"\n{'=' * 80}")
    print(f"SESSION COMPLETE: {session_dir}")
    print(f"Articles staged: {len(summary.get('articles_staged', []))}")
    print(f"Escalations: {len(summary.get('escalations', []))}")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
