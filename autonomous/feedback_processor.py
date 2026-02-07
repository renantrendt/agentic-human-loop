"""
Feedback Processor — parses user email replies and iterates on articles.

Handles three actions:
  - Approve N       → mark article as approved, trigger Framer publish
  - Article N: ...  → apply requested changes with Claude, update staged file
  - Reject N: ...   → mark as rejected, save reason for agent learning

Usage:
    from autonomous.feedback_processor import process_feedback
    result = process_feedback(config, session_dir, feedback_text)
"""

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import subprocess

import anthropic
import tenacity
from anthropic.types import TextBlock

from autonomous.secrets import get_secret

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _resolve_article_path(session_dir: str, article_file: str) -> str | None:
    """Find the actual article file path."""
    candidates = [
        Path(session_dir) / article_file,
        Path(article_file),
        Path(session_dir) / ".." / article_file,
    ]
    for c in candidates:
        if c.exists():
            return str(c.resolve())
    return None


def _publish_to_framer(config: dict, article_path: str) -> bool:
    """Publish an approved article to Framer CMS via framer-api SDK (requires Node 22)."""
    api_key = get_secret("FRAMER_API_KEY")
    if not api_key:
        logger.warning("FRAMER_API_KEY not set — skipping publish")
        return False

    publish_script = Path(__file__).parent.parent / "publishing" / "publish_to_framer.js"
    config_path = Path(__file__).parent.parent / "brand-context" / "config.json"

    if not publish_script.exists():
        logger.error(f"publish_to_framer.js not found")
        return False

    nvm_dir = os.path.expanduser("~/.nvm")
    cmd = (
        f'export NVM_DIR="{nvm_dir}" && . "$NVM_DIR/nvm.sh" && nvm use 22 --silent && '
        f'node {publish_script} --config {config_path} --article {article_path}'
    )

    try:
        result = subprocess.run(
            ["bash", "-c", cmd],
            capture_output=True, text=True, timeout=60,
            cwd=str(publish_script.parent),
            env={**os.environ, "FRAMER_API_KEY": api_key},
        )
        if result.returncode == 0:
            logger.info(f"Framer publish: {result.stdout.strip()}")
            return True
        else:
            logger.error(f"Framer publish failed: {result.stderr[-200:]} | {result.stdout[-200:]}")
            return False
    except Exception as e:
        logger.error(f"Framer publish error: {e}")
        return False


def process_feedback(config: dict, session_dir: str, feedback_text: str) -> dict:
    """
    Parse user feedback and process each instruction.

    Returns summary of actions taken.
    """
    summary_path = Path(session_dir) / "pipeline_summary.json"
    if not summary_path.exists():
        return {"status": "error", "error": f"pipeline_summary.json not found in {session_dir}"}

    with open(summary_path, "r") as f:
        summary = json.load(f)

    articles = summary.get("articles_staged", [])
    if not articles:
        return {"status": "error", "error": "No staged articles found"}

    instructions = _parse_feedback(feedback_text, config=config, article_count=len(articles))
    if not instructions:
        return {"status": "error", "error": "Could not parse any instructions from feedback"}

    logger.info(f"Parsed {len(instructions)} instructions from feedback")

    results = {
        "approved": [],
        "revised_articles": [],
        "rejected": [],
        "errors": [],
    }

    for instr in instructions:
        article_num = instr["article_num"]
        idx = article_num - 1

        if idx < 0 or idx >= len(articles):
            results["errors"].append({"article": article_num, "error": f"Article {article_num} does not exist (have {len(articles)})"})
            continue

        article = articles[idx]
        article_file = article.get("article_file", "")

        if instr["action"] == "approve":
            article["approved"] = True
            article["approved_at"] = datetime.now(timezone.utc).isoformat()
            results["approved"].append(article_num)
            logger.info(f"Article {article_num} approved")

            full_path = _resolve_article_path(session_dir, article_file)
            if full_path:
                published = _publish_to_framer(config, full_path)
                if published:
                    article["published"] = True
                    article["published_at"] = datetime.now(timezone.utc).isoformat()
                    logger.info(f"Article {article_num} published to Framer")
                else:
                    article["ready_to_publish"] = True
                    logger.info(f"Article {article_num} approved — ready for manual Framer import")

        elif instr["action"] == "revise":
            full_path = _resolve_article_path(session_dir, article_file)
            if not full_path:
                results["errors"].append({"article": article_num, "error": "Article file not found"})
                continue
            article_file = full_path

            logger.info(f"Article {article_num}: applying changes — {instr['details'][:80]}...")
            revised = _revise_article(config, article_file, instr["details"])

            if revised:
                Path(article_file).write_text(revised, encoding="utf-8")
                article["word_count"] = len(revised.split())
                article["last_revised"] = datetime.now(timezone.utc).isoformat()
                article["revision_count"] = article.get("revision_count", 0) + 1
                results["revised_articles"].append({
                    "article": article_num,
                    "changes_requested": instr["details"],
                    "new_word_count": article["word_count"],
                })
                logger.info(f"Article {article_num} revised ({article['word_count']} words)")
            else:
                results["errors"].append({"article": article_num, "error": "Revision failed"})

        elif instr["action"] == "reject":
            article["rejected"] = True
            article["rejection_reason"] = instr["details"]
            article["rejected_at"] = datetime.now(timezone.utc).isoformat()
            results["rejected"].append({"article": article_num, "reason": instr["details"]})
            logger.info(f"Article {article_num} rejected: {instr['details'][:60]}")

            _save_rejection(session_dir, article, instr["details"])

    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # Log iteration history
    _save_feedback_history(session_dir, feedback_text, results)

    return {
        "status": "success",
        **results,
    }


PARSE_FEEDBACK_PROMPT = """You are parsing a user's email reply about content articles they received for review.
The email contains {article_count} article(s). Article numbers start at 1.

The user's reply may be casual, formal, or anything in between. Your job is to figure out what they want for each article.

Three possible actions:
- **approve**: they want to publish it (e.g. "looks good", "ship it", "approve", "love it", "perfect", "yes", "lgtm", "go ahead")
- **revise**: they want changes before publishing (e.g. "make the intro shorter", "add examples", "fix the tone", "needs work on...")
- **reject**: they don't want it at all (e.g. "we already have this", "not relevant", "skip this one", "trash it", "no")

If there's only 1 article and the user doesn't mention a number, assume they're talking about article 1.

User's reply:
---
{feedback_text}
---

Return ONLY this JSON array:
```json
[
    {{"action": "approve", "article_num": 1, "details": ""}},
    {{"action": "revise", "article_num": 2, "details": "make the intro shorter and add pricing"}},
    {{"action": "reject", "article_num": 3, "details": "we already cover this topic"}}
]
```"""


def _parse_feedback(text: str, config: dict = None, article_count: int = 1) -> list[dict]:
    """Parse freeform feedback using Claude to understand natural language."""
    api_key = get_secret("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("No ANTHROPIC_API_KEY — falling back to regex parsing")
        return _parse_feedback_regex(text)

    model = (config or {}).get("autonomous", {}).get("model", "claude-opus-4-6")
    client = anthropic.Anthropic(api_key=api_key)

    prompt = PARSE_FEEDBACK_PROMPT.format(
        article_count=article_count,
        feedback_text=text,
    )

    try:
        response = client.messages.create(
            model=model,
            max_tokens=1000,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = response.content[0].text

        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response_text)
        json_str = json_match.group(1).strip() if json_match else response_text.strip()
        instructions = json.loads(json_str)

        logger.info(f"Claude parsed {len(instructions)} instructions from feedback")
        for instr in instructions:
            logger.info(f"  → {instr['action']} article {instr['article_num']}: {instr.get('details', '')[:60]}")
        return instructions

    except Exception as e:
        logger.error(f"Claude parsing failed ({e}), falling back to regex")
        return _parse_feedback_regex(text)


def _parse_feedback_regex(text: str) -> list[dict]:
    """Fallback regex parser if Claude is unavailable."""
    instructions = []
    lines = text.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        approve_match = re.match(r"(?:approve|approved|ok|lgtm|ship)\s+([\d,\s]+)", line, re.IGNORECASE)
        if approve_match:
            nums = re.findall(r"\d+", approve_match.group(1))
            for n in nums:
                instructions.append({"action": "approve", "article_num": int(n), "details": ""})
            continue

        reject_match = re.match(r"(?:reject|rejected|no|skip|drop)\s+(\d+)\s*[,:.\-—]\s*(.*)", line, re.IGNORECASE)
        if reject_match:
            instructions.append({
                "action": "reject",
                "article_num": int(reject_match.group(1)),
                "details": reject_match.group(2).strip(),
            })
            continue

        revise_match = re.match(r"(?:article\s+)?(\d+)\s*[,:.\-—]\s*(.+)", line, re.IGNORECASE)
        if revise_match:
            instructions.append({
                "action": "revise",
                "article_num": int(revise_match.group(1)),
                "details": revise_match.group(2).strip(),
            })
            continue

    return instructions


def _revise_article(config: dict, article_file: str, changes: str) -> str | None:
    """Send the article + requested changes to Claude, get revised version."""
    model = config.get("autonomous", {}).get("model", "claude-opus-4-6")
    max_tokens = config.get("autonomous", {}).get("max_tokens", 16000)
    api_key = get_secret("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not set")
        return None

    original = Path(article_file).read_text(encoding="utf-8")
    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""You are revising an article based on editorial feedback. Apply the requested changes while keeping the overall structure, quality, and length intact.

## Requested Changes
{changes}

## Original Article
{original}

## Instructions
- Apply ONLY the changes requested above
- Keep everything else the same (don't rewrite sections that weren't mentioned)
- Maintain the same markdown formatting
- If asked to add a section, integrate it naturally into the article flow
- If asked to change tone, adjust throughout consistently
- Output the complete revised article in markdown format

Output ONLY the revised article, no commentary."""

    try:
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
    except Exception as e:
        logger.error(f"Claude revision failed: {e}")

    return None


def _save_rejection(session_dir: str, article: dict, reason: str):
    """Save rejection to rejections.json for agent learning."""
    rejections_path = Path(session_dir) / "rejections.json"
    try:
        data = json.load(open(rejections_path))
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"rejections": []}

    data["rejections"].append({
        "prompt": article.get("prompt", ""),
        "reason": reason,
        "rejected_at": datetime.now(timezone.utc).isoformat(),
    })

    with open(rejections_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _save_feedback_history(session_dir: str, feedback_text: str, results: dict):
    """Save feedback iteration history."""
    history_path = Path(session_dir) / "feedback_history.json"
    try:
        history = json.load(open(history_path))
    except (FileNotFoundError, json.JSONDecodeError):
        history = {"iterations": []}

    history["iterations"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "feedback": feedback_text,
        "approved": results.get("approved", []),
        "revised": [r["article"] for r in results.get("revised_articles", [])],
        "rejected": [r["article"] for r in results.get("rejected", [])],
    })

    with open(history_path, "w") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
