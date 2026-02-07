"""
Gmail Poller — checks for email replies to Content Agent digests
and processes them as feedback.

Uses Gmail API with OAuth2 (same credentials as Google Sheets publishing).
Requires gmail.modify scope (to read + mark as processed).

First run (local):
    python -m autonomous.gmail_poller --auth
    This opens browser for OAuth consent, saves token with Gmail scope.

Polling run:
    python -m autonomous.gmail_poller --poll
    Checks for unread replies, processes them, marks as read.
"""

import argparse
import base64
import json
import logging
import os
import pickle
import re
import sys
from datetime import datetime, timezone
from email.utils import parseaddr
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
]
TOKEN_FILE = "gmail_token.pickle"
CREDENTIALS_FILE = "../oauth_credentials.json"
PROCESSED_LABEL = "ContentAgent/Processed"
DIGEST_SUBJECT_PATTERN = r"Content Agent"


def authenticate(credentials_file: str = CREDENTIALS_FILE, token_file: str = TOKEN_FILE) -> Credentials:
    """Authenticate with Gmail API. Opens browser on first run."""
    creds = None

    if Path(token_file).exists():
        with open(token_file, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path(credentials_file).exists():
                raise FileNotFoundError(
                    f"OAuth credentials not found at {credentials_file}. "
                    f"Copy from your Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_file, "wb") as f:
            pickle.dump(creds, f)
        logger.info(f"Token saved to {token_file}")

    return creds


def get_gmail_service(creds: Credentials):
    return build("gmail", "v1", credentials=creds)


def find_reply_emails(service, max_results: int = 10) -> list[dict]:
    """
    Find unread reply emails to Content Agent digests.
    Searches for emails that are replies (have In-Reply-To header)
    and match the digest subject pattern.
    """
    query = 'subject:"Re:" subject:"Content Agent" from:me newer_than:1d'

    try:
        result = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=max_results,
        ).execute()
    except Exception as e:
        logger.error(f"Gmail search failed: {e}")
        return []

    messages = result.get("messages", [])

    if not messages:
        logger.info("No reply emails found")
        return []

    processed_ids = _load_processed_ids()

    replies = []
    for msg_ref in messages:
        if msg_ref["id"] in processed_ids:
            continue

        msg = service.users().messages().get(
            userId="me",
            id=msg_ref["id"],
            format="full",
        ).execute()

        headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
        subject = headers.get("subject", "")

        if not re.search(DIGEST_SUBJECT_PATTERN, subject, re.IGNORECASE):
            continue

        body = _extract_body(msg)

        if "Content Approved" in body or "Content Agent —" in body[:200]:
            logger.info(f"  Skipping our own outbound email: {msg_ref['id']}")
            _save_processed_id(msg_ref["id"])
            continue

        reply_text = _extract_reply_text(body)
        session_id = _extract_session_id(subject)

        if reply_text.strip():
            replies.append({
                "message_id": msg_ref["id"],
                "subject": subject,
                "from": headers.get("from", ""),
                "date": headers.get("date", ""),
                "reply_text": reply_text,
                "session_dir": session_id,
            })

    logger.info(f"Found {len(replies)} new reply emails to process")
    return replies


def mark_as_processed(service, message_id: str):
    """Track message as processed so we don't reprocess it."""
    processed_ids = _load_processed_ids()
    processed_ids.add(message_id)
    _save_processed_ids(processed_ids)
    logger.info(f"Marked message {message_id} as processed")


def _load_processed_ids() -> set:
    path = Path("processed_emails.json")
    if path.exists():
        try:
            return set(json.load(open(path)))
        except (json.JSONDecodeError, TypeError):
            pass
    return set()


def _save_processed_ids(ids: set):
    with open("processed_emails.json", "w") as f:
        json.dump(list(ids), f)


def poll_and_process(config: dict) -> dict:
    """
    Main polling loop: check Gmail for replies, process each one.
    """
    from autonomous.feedback_processor import process_feedback
    from publishing.email_digest import send_digest

    creds = authenticate()
    service = get_gmail_service(creds)

    replies = find_reply_emails(service)
    if not replies:
        return {"status": "no_replies", "processed": 0}

    results = []
    for reply in replies:
        session_dir = reply["session_dir"]
        feedback_text = reply["reply_text"]

        if not session_dir:
            logger.warning(f"Could not extract session ID from: {reply['subject']}")
            mark_as_processed(service, reply["message_id"])
            continue

        approved_file = Path(__file__).parent.parent / "approved_sessions.json"
        approved_sessions = set()
        if approved_file.exists():
            try:
                approved_sessions = set(json.loads(approved_file.read_text()))
            except (json.JSONDecodeError, OSError):
                pass
        if session_dir in approved_sessions:
            logger.info(f"Session {session_dir} already approved — skipping reply")
            mark_as_processed(service, reply["message_id"])
            continue

        logger.info(f"Processing reply for {session_dir}: {feedback_text[:80]}...")

        try:
            result = process_feedback(config, session_dir, feedback_text)
            results.append({"session": session_dir, "result": result})

            has_revisions = bool(result.get("revised_articles"))
            if has_revisions:
                summary_path = Path(session_dir) / "pipeline_summary.json"
                if summary_path.exists():
                    summary = json.load(open(summary_path))
                    send_digest(config, session_dir, summary)
                    logger.info("Updated email sent with revisions")

            if result.get("approved") and not has_revisions:
                from publishing.email_digest import send_confirmation
                summary_path = Path(session_dir) / "pipeline_summary.json"
                if summary_path.exists():
                    summary = json.load(open(summary_path))
                    approved_articles = [
                        a for i, a in enumerate(summary.get("articles_staged", []))
                        if (i + 1) in result["approved"]
                    ]
                    send_confirmation(config, session_dir, approved_articles)
                    logger.info(f"Confirmation sent for approved articles: {result['approved']}")

        except Exception as e:
            logger.error(f"Failed to process feedback: {e}")
            results.append({"session": session_dir, "error": str(e)})

        mark_as_processed(service, reply["message_id"])

    return {"status": "success", "processed": len(results), "results": results}


def _extract_body(msg: dict) -> str:
    """Extract plain text body from Gmail message."""
    payload = msg.get("payload", {})

    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data", "")
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    parts = payload.get("parts", [])
    for part in parts:
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data", "")
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        if part.get("parts"):
            for subpart in part["parts"]:
                if subpart.get("mimeType") == "text/plain":
                    data = subpart.get("body", {}).get("data", "")
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    return ""


def _extract_reply_text(body: str) -> str:
    """Strip quoted original email from reply."""
    lines = body.split("\n")
    reply_lines = []
    for line in lines:
        if re.match(r"On .+ wrote:", line):
            break
        if re.match(r"---+\s*(Original|Forwarded)", line, re.IGNORECASE):
            break
        if line.strip().startswith(">"):
            continue
        reply_lines.append(line)
    return "\n".join(reply_lines).strip()


def _extract_session_id(subject: str) -> str:
    """Extract session directory from email subject, or fall back to latest session."""
    match = re.search(r"session_\d{8}_\d{6}", subject)
    if match:
        return f"results/local_pipeline/{match.group(0)}"

    # Fallback: find the most recent session on disk
    import glob
    sessions = sorted(glob.glob("results/local_pipeline/session_*"))
    if sessions:
        return sessions[-1]
    return ""


def main():
    parser = argparse.ArgumentParser(description="Gmail Poller for Content Agent feedback")
    parser.add_argument("--auth", action="store_true", help="Run OAuth2 authentication flow")
    parser.add_argument("--poll", action="store_true", help="Poll for replies and process")
    parser.add_argument("--config", default="brand-context/config.json", help="Config file path")
    args = parser.parse_args()

    load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)

    if args.auth:
        creds = authenticate()
        print(f"Authenticated successfully. Token saved to {TOKEN_FILE}")

        token_b64 = base64.b64encode(Path(TOKEN_FILE).read_bytes()).decode()
        print(f"\nTo use in GitHub Actions, add this as a secret named GMAIL_TOKEN:")
        print(f"{token_b64[:80]}... ({len(token_b64)} chars)")
        print(f"\nFull value saved to gmail_token_b64.txt")
        Path("gmail_token_b64.txt").write_text(token_b64)
        return

    if args.poll:
        config = json.load(open(args.config))
        result = poll_and_process(config)
        print(json.dumps(result, indent=2))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
