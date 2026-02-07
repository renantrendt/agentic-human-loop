"""
Resend Inbound Webhook → GitHub Actions trigger.

Receives email replies from Resend's inbound email feature,
extracts the reply text and session ID, and triggers the
process-feedback GitHub Actions workflow via repository_dispatch.

Deploy to Vercel: `cd webhook && vercel`

Required env vars (set in Vercel dashboard):
  GITHUB_PAT        — GitHub Personal Access Token (repo scope)
  RESEND_SIGNING_SECRET — Resend webhook signing secret (optional, for verification)
"""

import hashlib
import hmac
import json
import os
import re
from http.server import BaseHTTPRequestHandler
import urllib.request

GITHUB_REPO = "renantrendt/script-nata"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}/dispatches"


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        # Verify Resend webhook signature (if configured)
        signing_secret = os.environ.get("RESEND_SIGNING_SECRET", "")
        if signing_secret:
            signature = self.headers.get("svix-signature", "")
            if not _verify_signature(body, signature, signing_secret):
                self._respond(401, {"error": "Invalid signature"})
                return

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self._respond(400, {"error": "Invalid JSON"})
            return

        # Resend inbound email payload structure
        # https://resend.com/docs/dashboard/webhooks/event-types#emailreceived
        event_type = payload.get("type", "")

        if event_type == "email.received":
            data = payload.get("data", {})
            from_email = data.get("from", "")
            subject = data.get("subject", "")
            text_body = data.get("text", "") or data.get("html", "")

            # Extract the reply text (strip quoted original email)
            reply_text = _extract_reply(text_body)

            # Try to find session ID from subject or body
            session_id = _extract_session_id(subject + " " + text_body)

            if not reply_text.strip():
                self._respond(200, {"status": "skipped", "reason": "Empty reply"})
                return

            # Trigger GitHub Actions workflow
            github_pat = os.environ.get("GITHUB_PAT", "")
            if not github_pat:
                self._respond(500, {"error": "GITHUB_PAT not configured"})
                return

            dispatch_payload = {
                "event_type": "email-feedback",
                "client_payload": {
                    "feedback": reply_text,
                    "session_dir": session_id,
                    "from_email": from_email,
                    "subject": subject,
                },
            }

            success = _trigger_github_dispatch(github_pat, dispatch_payload)

            if success:
                self._respond(200, {
                    "status": "triggered",
                    "session_dir": session_id,
                    "feedback_length": len(reply_text),
                })
            else:
                self._respond(500, {"error": "Failed to trigger GitHub Actions"})
        else:
            self._respond(200, {"status": "ignored", "event_type": event_type})

    def do_GET(self):
        self._respond(200, {"status": "ok", "service": "content-agent-webhook"})

    def _respond(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


def _extract_reply(text: str) -> str:
    """Extract only the new reply, stripping quoted original email."""
    # Common reply separators
    separators = [
        r"On .+ wrote:",
        r"---+\s*Original Message",
        r"From:\s*content-agent",
        r"_{3,}",
        r"-{3,}\s*$",
        r"^>",
    ]

    lines = text.split("\n")
    reply_lines = []

    for line in lines:
        is_separator = any(re.search(sep, line, re.IGNORECASE) for sep in separators)
        if is_separator:
            break
        if line.strip().startswith(">"):
            continue
        reply_lines.append(line)

    return "\n".join(reply_lines).strip()


def _extract_session_id(text: str) -> str:
    """Try to find a session directory reference in the email."""
    match = re.search(r"session_\d{8}_\d{6}", text)
    if match:
        return f"results/local_pipeline/{match.group(0)}"

    # Fallback: find the most recent session
    return ""


def _trigger_github_dispatch(pat: str, payload: dict) -> bool:
    """Trigger a GitHub Actions repository_dispatch event."""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        GITHUB_API,
        data=data,
        headers={
            "Authorization": f"Bearer {pat}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status == 204
    except Exception as e:
        print(f"GitHub dispatch failed: {e}")
        return False


def _verify_signature(body: bytes, signature: str, secret: str) -> bool:
    """Verify Resend webhook signature (Svix)."""
    if not signature:
        return False
    try:
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected)
    except Exception:
        return False
