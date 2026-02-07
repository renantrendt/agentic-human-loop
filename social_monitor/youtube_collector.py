"""
YouTube signal collector — searches YouTube Data API v3 for videos and top comments.

Adapted from AY-AY-AY-AY/new-prompt-planner back-end/activities/youtube_search.py
Temporal + Supabase dependencies removed. Outputs JSON to session folder.

Usage:
    from social_monitor.youtube_collector import collect
    results = collect(config, session_dir)
"""

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
import tenacity

from autonomous.secrets import get_secret

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
REQUEST_TIMEOUT = 30
MAX_VIDEOS_PER_CATEGORY = 10
MAX_COMMENTS_PER_VIDEO = 20
REQUEST_DELAY = 1

YOUTUBE_CATEGORY_CACHE: dict[str, str] = {}

YOUTUBE_CATEGORY_FALLBACK: dict[str, str] = {
    "1": "Film & Animation", "2": "Autos & Vehicles", "10": "Music",
    "15": "Pets & Animals", "17": "Sports", "19": "Travel & Events",
    "20": "Gaming", "22": "People & Blogs", "23": "Comedy",
    "24": "Entertainment", "25": "News & Politics", "26": "Howto & Style",
    "27": "Education", "28": "Science & Technology",
}


def get_youtube_category_name(category_id: str, api_key: str, region_code: str = "US") -> str:
    if not category_id:
        return "Unknown"
    if category_id in YOUTUBE_CATEGORY_CACHE:
        return YOUTUBE_CATEGORY_CACHE[category_id]

    if not YOUTUBE_CATEGORY_CACHE:
        try:
            url = f"{YOUTUBE_API_BASE}/videoCategories"
            params = {"part": "snippet", "regionCode": region_code, "key": api_key}
            with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            for item in data.get("items", []):
                cat_id = item.get("id", "")
                cat_name = item.get("snippet", {}).get("title", "")
                if cat_id and cat_name:
                    YOUTUBE_CATEGORY_CACHE[cat_id] = cat_name
            if category_id in YOUTUBE_CATEGORY_CACHE:
                return YOUTUBE_CATEGORY_CACHE[category_id]
        except Exception as e:
            logger.warning(f"Failed to fetch YouTube categories from API: {e}")

    return YOUTUBE_CATEGORY_FALLBACK.get(category_id, f"Category {category_id}")


@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
    retry=tenacity.retry_if_exception_type(
        (httpx.HTTPStatusError, httpx.ConnectError, httpx.ReadTimeout)
    ),
)
def search_videos(
    keyword: str,
    api_key: str,
    max_results: int = MAX_VIDEOS_PER_CATEGORY,
    relevance_language: str = "en",
    region_code: str = "US",
) -> list[dict]:
    url = f"{YOUTUBE_API_BASE}/search"
    params = {
        "part": "snippet",
        "q": keyword,
        "type": "video",
        "maxResults": min(max_results, 50),
        "order": "relevance",
        "relevanceLanguage": relevance_language,
        "regionCode": region_code,
        "key": api_key,
    }
    with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    return data.get("items", [])


@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
    retry=tenacity.retry_if_exception_type(
        (httpx.HTTPStatusError, httpx.ConnectError, httpx.ReadTimeout)
    ),
)
def get_video_details(video_ids: list[str], api_key: str) -> list[dict]:
    if not video_ids:
        return []
    url = f"{YOUTUBE_API_BASE}/videos"
    params = {
        "part": "snippet,statistics",
        "id": ",".join(video_ids),
        "key": api_key,
    }
    with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    return data.get("items", [])


@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
    retry=tenacity.retry_if_exception_type(
        (httpx.HTTPStatusError, httpx.ConnectError, httpx.ReadTimeout)
    ),
)
def fetch_comments_page(video_id: str, api_key: str, page_token: str = "") -> dict:
    url = f"{YOUTUBE_API_BASE}/commentThreads"
    params = {
        "part": "snippet",
        "videoId": video_id,
        "maxResults": 100,
        "order": "relevance",
        "textFormat": "plainText",
        "key": api_key,
    }
    if page_token:
        params["pageToken"] = page_token
    with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        return response.json()


def get_top_comments(video_id: str, api_key: str, max_comments: int = MAX_COMMENTS_PER_VIDEO) -> list[dict]:
    all_comments = []
    try:
        data = fetch_comments_page(video_id, api_key)
        items = data.get("items", [])
        for item in items:
            snippet = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
            like_count = snippet.get("likeCount", 0)
            reply_count = item.get("snippet", {}).get("totalReplyCount", 0)
            all_comments.append({
                "comment_content": snippet.get("textDisplay", ""),
                "comment_published_at": snippet.get("publishedAt"),
                "comment_likes": str(like_count),
                "comment_reply_count": str(reply_count),
            })
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 403:
            logger.warning(f"Comments disabled for video {video_id}")
            return []
        raise

    all_comments.sort(key=lambda c: int(c["comment_likes"] or "0"), reverse=True)
    return all_comments[:max_comments]


def parse_video_metadata(video_resource: dict, api_key: str, region_code: str = "US") -> dict:
    snippet = video_resource.get("snippet", {})
    stats = video_resource.get("statistics", {})
    category_id = snippet.get("categoryId", "")
    video_id = video_resource.get("id", "")

    return {
        "video_id": video_id,
        "video_title": snippet.get("title", ""),
        "chanel_title": snippet.get("channelTitle", ""),
        "published_at": snippet.get("publishedAt"),
        "view_count": stats.get("viewCount", "0"),
        "like_count": stats.get("likeCount", "0"),
        "comment_count": stats.get("commentCount", "0"),
        "video_url": f"https://www.youtube.com/watch?v={video_id}",
        "video_category": get_youtube_category_name(category_id, api_key, region_code),
    }


def collect(config: dict, session_dir: str) -> dict:
    """
    Main entry point. Reads social_monitor.youtube config, searches YouTube,
    writes results to session_dir/youtube_signals.json.

    Returns summary dict with status, counts.
    """
    yt_config = config.get("social_monitor", {}).get("youtube", {})
    if not yt_config.get("enabled", False):
        logger.info("YouTube collector disabled in config")
        return {"status": "disabled", "videos_found": 0, "comments_found": 0}

    api_key_env = yt_config.get("api_key_env", "YOUTUBE_API_KEY")
    api_key = get_secret(api_key_env)
    if not api_key:
        return {"status": "failed", "error": f"{api_key_env} not set in environment"}

    categories = config.get("social_monitor", {}).get("categories", [])
    if not categories:
        categories = _derive_categories_from_config(config)

    if not categories:
        return {"status": "no_categories", "videos_found": 0, "comments_found": 0}

    max_videos = yt_config.get("max_videos_per_category", MAX_VIDEOS_PER_CATEGORY)
    max_comments = yt_config.get("max_comments_per_video", MAX_COMMENTS_PER_VIDEO)

    language = config.get("content", {}).get("language", "English")
    relevance_language = _language_to_code(language)
    region_code = yt_config.get("region_code", "US")

    logger.info("=" * 60)
    logger.info("YOUTUBE SIGNAL COLLECTOR")
    logger.info(f"Categories: {len(categories)}")
    logger.info(f"Language: {relevance_language}, Region: {region_code}")
    logger.info("=" * 60)

    all_records: list[dict] = []
    total_videos = 0
    seen_video_ids: set[str] = set()

    for cat_idx, category in enumerate(categories):
        if not category:
            continue

        logger.info(f"  [{cat_idx + 1}/{len(categories)}] Searching YouTube for: '{category}'")

        try:
            search_results = search_videos(
                category, api_key, max_videos,
                relevance_language=relevance_language,
                region_code=region_code,
            )
            if not search_results:
                logger.info("    No videos found")
                continue

            video_ids = []
            for item in search_results:
                vid_id = item.get("id", {}).get("videoId", "")
                if vid_id and vid_id not in seen_video_ids:
                    video_ids.append(vid_id)
                    seen_video_ids.add(vid_id)

            if not video_ids:
                logger.info("    All videos already processed from other categories")
                continue

            logger.info(f"    Found {len(video_ids)} new videos")

            time.sleep(REQUEST_DELAY)
            video_resources = get_video_details(video_ids, api_key)

            for video_resource in video_resources:
                video_meta = parse_video_metadata(video_resource, api_key, region_code)
                vid_id = video_meta["video_id"]
                total_videos += 1

                logger.info(
                    f"    Video: '{video_meta['video_title'][:60]}...' "
                    f"({video_meta['view_count']} views)"
                )

                time.sleep(REQUEST_DELAY)
                top_comments = get_top_comments(vid_id, api_key, max_comments)
                logger.info(f"      Top {len(top_comments)} comments collected")

                for comment in top_comments:
                    record = {
                        "category_name": category,
                        **video_meta,
                        **comment,
                    }
                    all_records.append(record)

        except Exception as e:
            logger.warning(f"    Failed to process category '{category}': {e}")

    output_path = Path(session_dir) / "youtube_signals.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "categories_searched": len(categories),
            "total_videos": total_videos,
            "total_comments": len(all_records),
            "records": all_records,
        }, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(all_records)} comment records ({total_videos} videos) to {output_path}")

    return {
        "status": "success",
        "categories_searched": len(categories),
        "videos_found": total_videos,
        "comments_found": len(all_records),
        "output_file": str(output_path),
    }


def _derive_categories_from_config(config: dict) -> list[str]:
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
        "english": "en", "portuguese": "pt", "spanish": "es",
        "french": "fr", "german": "de", "italian": "it",
    }
    return mapping.get(language.lower(), "en")
