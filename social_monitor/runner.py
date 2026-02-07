"""
Social Monitor Runner — orchestrates Reddit + YouTube collectors.

Can be run standalone or imported by the autonomous orchestrator.

Usage:
    python -m social_monitor.runner [--config path/to/config.json] [--session-dir path/to/session]
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from social_monitor import reddit_collector, youtube_collector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = "brand-context/config.json"


def run(config: dict, session_dir: str) -> dict:
    """
    Run all enabled social collectors and merge results.

    Returns a summary dict with results from each collector
    and path to the merged social_signals.json.
    """
    logger.info("*" * 60)
    logger.info("SOCIAL MONITOR — STARTING")
    logger.info("*" * 60)

    results = {}

    reddit_result = reddit_collector.collect(config, session_dir)
    results["reddit"] = reddit_result
    logger.info(f"Reddit: {reddit_result.get('status')} — {reddit_result.get('posts_found', 0)} posts")

    youtube_result = youtube_collector.collect(config, session_dir)
    results["youtube"] = youtube_result
    logger.info(f"YouTube: {youtube_result.get('status')} — {youtube_result.get('comments_found', 0)} comments")

    merged = _merge_signals(session_dir, reddit_result, youtube_result)
    results["merged"] = merged

    logger.info("*" * 60)
    logger.info("SOCIAL MONITOR — COMPLETE")
    logger.info(f"Total signals: {merged.get('total_entries', 0)}")
    logger.info("*" * 60)

    return results


def _merge_signals(session_dir: str, reddit_result: dict, youtube_result: dict) -> dict:
    """
    Merge Reddit posts and YouTube comments into a unified social_signals.json
    with a common schema for the gap detector to consume.
    """
    entries = []

    reddit_path = Path(session_dir) / "reddit_signals.json"
    if reddit_path.exists():
        with open(reddit_path, "r", encoding="utf-8") as f:
            reddit_data = json.load(f)
        for post in reddit_data.get("posts", []):
            entries.append({
                "source": "reddit",
                "text": f"{post.get('post_title', '')} {post.get('content_snippet', '')}".strip(),
                "url": post.get("post_link", ""),
                "category": post.get("category_name", ""),
                "published_at": post.get("published_at"),
                "metadata": {
                    "subreddit": post.get("post_subreddit", ""),
                    "post_id": post.get("post_id", ""),
                },
            })

    youtube_path = Path(session_dir) / "youtube_signals.json"
    if youtube_path.exists():
        with open(youtube_path, "r", encoding="utf-8") as f:
            youtube_data = json.load(f)
        for record in youtube_data.get("records", []):
            entries.append({
                "source": "youtube",
                "text": record.get("comment_content", ""),
                "url": record.get("video_url", ""),
                "category": record.get("category_name", ""),
                "published_at": record.get("comment_published_at"),
                "metadata": {
                    "video_title": record.get("video_title", ""),
                    "video_id": record.get("video_id", ""),
                    "channel": record.get("chanel_title", ""),
                    "comment_likes": record.get("comment_likes", "0"),
                    "view_count": record.get("view_count", "0"),
                },
            })

    merged_path = Path(session_dir) / "social_signals.json"
    merged_data = {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "total_entries": len(entries),
        "reddit_count": sum(1 for e in entries if e["source"] == "reddit"),
        "youtube_count": sum(1 for e in entries if e["source"] == "youtube"),
        "entries": entries,
    }

    with open(merged_path, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Merged {len(entries)} entries to {merged_path}")

    return {
        "total_entries": len(entries),
        "reddit_entries": merged_data["reddit_count"],
        "youtube_entries": merged_data["youtube_count"],
        "output_file": str(merged_path),
    }


def main():
    parser = argparse.ArgumentParser(description="Social Monitor — Reddit + YouTube signal collector")
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="Path to config.json")
    parser.add_argument("--session-dir", default=None, help="Session directory for output")
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

    results = run(config, session_dir)

    summary_path = Path(session_dir) / "social_monitor_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Summary written to {summary_path}")


if __name__ == "__main__":
    main()
