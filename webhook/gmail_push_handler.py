"""
Gmail Pub/Sub Push Webhook — receives push notifications from Google Pub/Sub
when a new email arrives in Gmail. Processes feedback replies to Content Agent digests.

Deploy on Brev (port 8082) or any server with a public URL.
Pub/Sub sends POST to this endpoint with the notification.

Usage:
    python3 webhook/gmail_push_handler.py
"""

import base64
import json
import logging
import os
import subprocess
import sys
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

AGENT_DIR = Path(__file__).parent.parent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [WEBHOOK] %(message)s")
logger = logging.getLogger(__name__)

PORT = int(os.getenv("WEBHOOK_PORT", "8082"))

_processing_lock = threading.Lock()
_approved_sessions = set()
_last_history_id = None
APPROVED_SESSIONS_FILE = AGENT_DIR / "approved_sessions.json"
HISTORY_ID_FILE = AGENT_DIR / "last_history_id.txt"


class GmailPushHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

        try:
            data = json.loads(body)
            message = data.get("message", {})
            pubsub_data = message.get("data", "")

            if pubsub_data:
                decoded = base64.b64decode(pubsub_data).decode("utf-8")
                notification = json.loads(decoded)
                email = notification.get("emailAddress", "")
                history_id = notification.get("historyId", "")
                logger.info(f"Gmail notification: email={email} historyId={history_id}")

                if _processing_lock.locked():
                    logger.info("  Already processing — will catch up next time")
                    return

                threading.Thread(
                    target=_process_feedback,
                    args=(history_id,),
                    daemon=True,
                ).start()
            else:
                logger.info("Pub/Sub verification ping (no data)")

        except Exception as e:
            logger.error(f"Error handling push: {e}")

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        status = {"status": "running", "service": "gmail-push-webhook", "port": PORT}
        self.wfile.write(json.dumps(status).encode())

    def log_message(self, format, *args):
        pass


def _process_feedback(history_id: str):
    """Process feedback using Gmail history API (no search, no delay)."""
    global _last_history_id
    with _processing_lock:
        logger.info(f"Processing feedback (historyId={history_id})...")
        try:
            import pickle, re as _re
            from pathlib import Path as _Path

            token_path = AGENT_DIR / "gmail_token.pickle"
            if not token_path.exists():
                logger.error("No Gmail token")
                return

            with open(token_path, "rb") as f:
                creds = pickle.load(f)

            from googleapiclient.discovery import build
            service = build("gmail", "v1", credentials=creds)

            processed_file = AGENT_DIR / "processed_emails.json"
            processed_ids = set(json.loads(processed_file.read_text())) if processed_file.exists() else set()

            start_id = _last_history_id or str(int(history_id) - 100)
            history = service.users().history().list(
                userId="me", startHistoryId=start_id,
                historyTypes=["messageAdded"], labelId="Label_23",
            ).execute()
            _last_history_id = history.get("historyId", history_id)
            HISTORY_ID_FILE.write_text(_last_history_id)

            msg_ids = []
            for record in history.get("history", []):
                for added in record.get("messagesAdded", []):
                    mid = added["message"]["id"]
                    if mid not in processed_ids:
                        msg_ids.append(mid)

            if not msg_ids:
                logger.info("  No new messages in history")
                return

            sys.path.insert(0, str(AGENT_DIR))
            from autonomous.gmail_poller import _extract_body, _extract_reply_text, _extract_session_id, mark_as_processed, _load_processed_ids, _save_processed_ids
            from autonomous.feedback_processor import process_feedback as do_process
            from publishing.email_digest import send_confirmation

            config = json.load(open(AGENT_DIR / "brand-context" / "config.json"))

            for mid in msg_ids:
                msg = service.users().messages().get(userId="me", id=mid, format="full").execute()
                headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
                subject = headers.get("subject", "")

                if "Content Agent" not in subject:
                    continue

                all_headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
                is_from_resend = "amazonses" in all_headers.get("received", "") or "x-ses-outgoing" in all_headers

                if is_from_resend:
                    logger.info(f"  Skipping Resend/SES email: {mid}")
                    pids = _load_processed_ids(); pids.add(mid); _save_processed_ids(pids)
                    continue

                body = _extract_body(msg)
                reply_text = _extract_reply_text(body)
                session_dir = _extract_session_id(subject)

                if not reply_text.strip() or not session_dir:
                    pids = _load_processed_ids(); pids.add(mid); _save_processed_ids(pids)
                    continue

                if session_dir in _approved_sessions:
                    logger.info(f"  Session already approved: {session_dir}")
                    pids = _load_processed_ids(); pids.add(mid); _save_processed_ids(pids)
                    continue

                logger.info(f"  Processing reply for {session_dir}: {reply_text[:60]}")
                result = do_process(config, session_dir, reply_text)
                pids = _load_processed_ids(); pids.add(mid); _save_processed_ids(pids)
                mark_as_processed(service, mid)

                if result.get("approved"):
                    _approved_sessions.add(session_dir)
                    APPROVED_SESSIONS_FILE.write_text(json.dumps(list(_approved_sessions)))
                    logger.info(f"  Session approved: {session_dir}")

                    summary_path = _Path(session_dir) / "pipeline_summary.json"
                    if summary_path.exists():
                        summary = json.load(open(summary_path))
                        approved_articles = [
                            a for i, a in enumerate(summary.get("articles_staged", []))
                            if (i + 1) in result["approved"]
                        ]
                        send_confirmation(config, session_dir, approved_articles)
                        logger.info(f"  Confirmation sent")

                if result.get("revised_articles"):
                    from publishing.email_digest import send_digest
                    summary_path = _Path(session_dir) / "pipeline_summary.json"
                    if summary_path.exists():
                        summary = json.load(open(summary_path))
                        send_digest(config, session_dir, summary)
                        logger.info(f"  Revision email sent")

        except Exception as e:
            logger.error(f"Feedback error: {e}")
            import traceback
            logger.error(traceback.format_exc())


def _load_approved_sessions():
    """Load sessions that have already been approved — stop processing replies for these."""
    global _approved_sessions
    try:
        if APPROVED_SESSIONS_FILE.exists():
            _approved_sessions = set(json.loads(APPROVED_SESSIONS_FILE.read_text()))
            logger.info(f"Loaded {len(_approved_sessions)} approved sessions")
    except (json.JSONDecodeError, OSError):
        pass


def _check_and_mark_approved(poller_output: str):
    """If the poller approved articles, mark that session as done."""
    try:
        output = json.loads(poller_output.strip().split("\n")[-1]) if "\n" in poller_output else json.loads(poller_output)
        for r in output.get("results", []):
            result = r.get("result", {})
            if result.get("approved"):
                session = r.get("session", "")
                if session:
                    _approved_sessions.add(session)
                    APPROVED_SESSIONS_FILE.write_text(json.dumps(list(_approved_sessions)))
                    logger.info(f"Session marked as approved (no further processing): {session}")
    except (json.JSONDecodeError, KeyError, IndexError):
        pass


def _seed_processed_emails():
    """On startup, ensure processed_emails.json exists and has content.
    If empty/missing, scan Gmail for all existing reply IDs so we don't
    reprocess old messages."""
    processed_file = AGENT_DIR / "processed_emails.json"
    try:
        existing = json.loads(processed_file.read_text()) if processed_file.exists() else []
        if existing:
            logger.info(f"Loaded {len(existing)} previously processed email IDs")
            return
    except (json.JSONDecodeError, OSError):
        existing = []

    logger.info("No processed emails found — seeding from Gmail to avoid reprocessing old replies...")
    try:
        import pickle
        from googleapiclient.discovery import build
        token_path = AGENT_DIR / "gmail_token.pickle"
        if not token_path.exists():
            logger.warning("No Gmail token — can't seed. Old replies may get reprocessed on first notification.")
            return
        with open(token_path, "rb") as f:
            creds = pickle.load(f)
        service = build("gmail", "v1", credentials=creds)
        result = service.users().messages().list(
            userId="me",
            q='subject:"Re:" subject:"Content Agent" from:me newer_than:7d',
            maxResults=50,
        ).execute()
        msg_ids = [m["id"] for m in result.get("messages", [])]
        processed_file.write_text(json.dumps(msg_ids))
        logger.info(f"Seeded {len(msg_ids)} existing reply IDs — these will be skipped")
    except Exception as e:
        logger.error(f"Seeding failed: {e}")


def main():
    global _last_history_id
    _load_approved_sessions()
    _seed_processed_emails()
    if HISTORY_ID_FILE.exists():
        _last_history_id = HISTORY_ID_FILE.read_text().strip()
        logger.info(f"Resuming from historyId: {_last_history_id}")
    server = HTTPServer(("0.0.0.0", PORT), GmailPushHandler)
    logger.info(f"Gmail push webhook listening on port {PORT}")
    logger.info(f"Endpoint: POST http://0.0.0.0:{PORT}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down")
        server.server_close()


if __name__ == "__main__":
    main()
