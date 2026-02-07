"""
Reddit signal collector — fetches posts from Reddit's public RSS search feed.

Adapted from AY-AY-AY-AY/new-prompt-planner back-end/activities/reddit_search.py
Temporal + Supabase dependencies removed. Outputs JSON to session folder.

Usage:
    from social_monitor.reddit_collector import collect
    results = collect(config, session_dir)
"""

import json
import logging
import os
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus

import httpx
import tenacity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REDDIT_RSS_BASE_URL = "https://www.reddit.com/search.rss"
REQUEST_TIMEOUT = 30
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)
ATOM_NS = "{http://www.w3.org/2005/Atom}"
REQUEST_DELAY = 3
POST_ID_PREFIX = "t3_"


@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
    retry=tenacity.retry_if_exception_type(
        (httpx.HTTPStatusError, httpx.ConnectError, httpx.ReadTimeout)
    ),
)
def fetch_reddit_rss(query: str, sort: str = "relevance", language: str = "en") -> str:
    encoded_query = quote_plus(query)
    url = f"{REDDIT_RSS_BASE_URL}?q={encoded_query}&sort={sort}&t=year"

    base_lang = language.split("-")[0] if "-" in language else language
    accept_language = f"{language},{base_lang};q=0.9,en;q=0.5"

    with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
        response = client.get(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/atom+xml, application/xml, text/xml, */*",
                "Accept-Language": accept_language,
            },
            follow_redirects=True,
        )
        response.raise_for_status()
        return response.text


def parse_reddit_feed(xml_content: str) -> list[dict]:
    root = ET.fromstring(xml_content)
    entries = root.findall(f"{ATOM_NS}entry")
    posts = []

    for entry in entries:
        post_id = _get_text(entry, f"{ATOM_NS}id")
        if not post_id.startswith(POST_ID_PREFIX):
            continue

        title = _get_text(entry, f"{ATOM_NS}title")
        updated = _get_text(entry, f"{ATOM_NS}updated")
        published = _get_text(entry, f"{ATOM_NS}published")

        link_el = entry.find(f"{ATOM_NS}link")
        link = link_el.get("href", "") if link_el is not None else ""

        category_el = entry.find(f"{ATOM_NS}category")
        subreddit = category_el.get("term", "") if category_el is not None else ""

        content_el = entry.find(f"{ATOM_NS}content")
        content_snippet = ""
        if content_el is not None and content_el.text:
            content_snippet = _strip_html(content_el.text)[:500]

        posts.append({
            "post_id": post_id,
            "post_title": title,
            "post_subreddit": subreddit,
            "post_link": link,
            "published_at": _parse_timestamp(published),
            "updated_at": _parse_timestamp(updated),
            "content_snippet": content_snippet,
        })

    return posts


def search_categories_on_reddit(
    categories: list[str],
    language: str = "en",
    max_posts_per_category: int = 25,
) -> list[dict]:
    all_posts: list[dict] = []
    seen_post_ids: set[str] = set()
    total = len(categories)

    for i, category in enumerate(categories):
        if not category:
            continue

        logger.info(f"  [{i + 1}/{total}] Searching Reddit for: '{category}'")

        try:
            xml_content = fetch_reddit_rss(category, language=language)
            posts = parse_reddit_feed(xml_content)

            new_posts = 0
            for post in posts:
                if post["post_id"] not in seen_post_ids and new_posts < max_posts_per_category:
                    seen_post_ids.add(post["post_id"])
                    post["category_name"] = category
                    all_posts.append(post)
                    new_posts += 1

            logger.info(f"    Found {len(posts)} posts, {new_posts} new (after dedup)")
        except Exception as e:
            logger.warning(f"    Failed to search '{category}': {e}")

        if i < total - 1:
            time.sleep(REQUEST_DELAY)

    return all_posts


def collect(config: dict, session_dir: str) -> dict:
    """
    Main entry point. Reads social_monitor.reddit config, searches Reddit,
    writes results to session_dir/reddit_signals.json.

    Returns summary dict with status, counts.
    """
    reddit_config = config.get("social_monitor", {}).get("reddit", {})
    if not reddit_config.get("enabled", False):
        logger.info("Reddit collector disabled in config")
        return {"status": "disabled", "posts_found": 0}

    categories = reddit_config.get("categories", [])
    if not categories:
        categories = _derive_categories_from_config(config)

    if not categories:
        return {"status": "no_categories", "posts_found": 0, "error": "No categories configured"}

    language = config.get("content", {}).get("language", "English")
    lang_code = _language_to_code(language)
    max_posts = reddit_config.get("max_posts_per_category", 25)

    logger.info("=" * 60)
    logger.info("REDDIT SIGNAL COLLECTOR")
    logger.info(f"Categories: {len(categories)}")
    logger.info(f"Language: {lang_code}")
    logger.info("=" * 60)

    posts = search_categories_on_reddit(
        categories=categories,
        language=lang_code,
        max_posts_per_category=max_posts,
    )

    output_path = Path(session_dir) / "reddit_signals.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "categories_searched": len(categories),
            "total_posts": len(posts),
            "posts": posts,
        }, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(posts)} posts to {output_path}")

    return {
        "status": "success",
        "categories_searched": len(categories),
        "posts_found": len(posts),
        "output_file": str(output_path),
    }


def _derive_categories_from_config(config: dict) -> list[str]:
    """Fallback: derive search categories from existing config fields."""
    categories = []
    target_prompt = config.get("athena_integration", {}).get("target_prompt", "")
    if target_prompt:
        categories.append(target_prompt)
    domain_name = config.get("data_source", {}).get("domain_name", "")
    if domain_name and domain_name != target_prompt:
        categories.append(domain_name)
    target_audience = config.get("content", {}).get("target_audience", "")
    if target_audience:
        for segment in target_audience.split(","):
            segment = segment.strip()
            if segment and target_prompt:
                categories.append(f"{target_prompt} {segment}")
    return categories


def _language_to_code(language: str) -> str:
    mapping = {
        "english": "en", "portuguese": "pt-BR", "spanish": "es",
        "french": "fr", "german": "de", "italian": "it",
    }
    return mapping.get(language.lower(), "en")


def _get_text(element: ET.Element, tag: str) -> str:
    child = element.find(tag)
    return child.text if child is not None and child.text else ""


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'").replace("&#32;", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _parse_timestamp(ts: str) -> str | None:
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.isoformat()
    except (ValueError, TypeError):
        return None
