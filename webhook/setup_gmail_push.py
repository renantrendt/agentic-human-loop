"""
Set up Gmail Pub/Sub push notifications.

1. Creates a Pub/Sub topic (if needed)
2. Grants Gmail permission to publish to it
3. Creates a push subscription pointing to the webhook URL
4. Calls gmail.users.watch() to start notifications

Prerequisites:
    - gcloud CLI authenticated
    - Gmail API + Pub/Sub API enabled
    - OAuth credentials with gmail.modify scope

Usage:
    python3 webhook/setup_gmail_push.py --webhook-url https://YOUR_URL/
"""

import argparse
import json
import logging
import os
import pickle
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [SETUP] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ID = "athena-hq"
TOPIC_NAME = "content-agent-gmail"
SUBSCRIPTION_NAME = "content-agent-gmail-push"
FULL_TOPIC = f"projects/{PROJECT_ID}/topics/{TOPIC_NAME}"


def run_gcloud(args: list[str], check=True) -> str:
    cmd = ["gcloud"] + args + ["--project", PROJECT_ID, "--format", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        if "already exists" in result.stderr.lower() or "ALREADY_EXISTS" in result.stderr:
            return result.stderr
        raise RuntimeError(f"gcloud {' '.join(args)} failed: {result.stderr}")
    return result.stdout


def setup_pubsub(webhook_url: str):
    logger.info("Step 1: Enabling APIs...")
    run_gcloud(["services", "enable", "pubsub.googleapis.com"], check=False)
    run_gcloud(["services", "enable", "gmail.googleapis.com"], check=False)

    logger.info(f"Step 2: Creating Pub/Sub topic '{TOPIC_NAME}'...")
    try:
        run_gcloud(["pubsub", "topics", "create", TOPIC_NAME])
        logger.info("  Topic created")
    except RuntimeError as e:
        if "already exists" in str(e).lower():
            logger.info("  Topic already exists")
        else:
            raise

    logger.info("Step 3: Granting Gmail publish permission...")
    run_gcloud([
        "pubsub", "topics", "add-iam-policy-binding", TOPIC_NAME,
        "--member", "serviceAccount:gmail-api-push@system.gserviceaccount.com",
        "--role", "roles/pubsub.publisher",
    ])
    logger.info("  Permission granted")

    logger.info(f"Step 4: Creating push subscription → {webhook_url}")
    try:
        run_gcloud([
            "pubsub", "subscriptions", "create", SUBSCRIPTION_NAME,
            "--topic", TOPIC_NAME,
            "--push-endpoint", webhook_url,
            "--ack-deadline", "30",
        ])
        logger.info("  Subscription created")
    except RuntimeError as e:
        if "already exists" in str(e).lower():
            logger.info("  Subscription already exists, updating endpoint...")
            run_gcloud([
                "pubsub", "subscriptions", "update", SUBSCRIPTION_NAME,
                "--push-endpoint", webhook_url,
            ])
        else:
            raise

    logger.info("Step 5: Registering Gmail watch...")
    setup_gmail_watch()

    logger.info("\nDone. Gmail will push notifications to your webhook when emails arrive.")
    logger.info(f"  Topic: {FULL_TOPIC}")
    logger.info(f"  Webhook: {webhook_url}")


def setup_gmail_watch():
    """Call gmail.users.watch() to start push notifications."""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    from autonomous.secrets import get_secret

    token_path = Path(__file__).parent.parent / "gmail_token.pickle"
    if not token_path.exists():
        token_b64 = get_secret("GMAIL_TOKEN")
        if token_b64:
            import base64
            token_path.write_bytes(base64.b64decode(token_b64))
        else:
            raise FileNotFoundError(f"No Gmail token at {token_path} and GMAIL_TOKEN env not set")

    with open(token_path, "rb") as f:
        creds = pickle.load(f)

    service = build("gmail", "v1", credentials=creds)

    watch_request = {
        "topicName": FULL_TOPIC,
        "labelIds": ["INBOX"],
    }

    result = service.users().watch(userId="me", body=watch_request).execute()
    logger.info(f"  Gmail watch registered: historyId={result.get('historyId')}, expiration={result.get('expiration')}")
    logger.info("  Watch expires in ~7 days — renew with: python3 webhook/setup_gmail_push.py --renew")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--webhook-url", required=True, help="Public URL for Pub/Sub push")
    parser.add_argument("--renew", action="store_true", help="Just renew the Gmail watch")
    args = parser.parse_args()

    if args.renew:
        setup_gmail_watch()
    else:
        setup_pubsub(args.webhook_url)


if __name__ == "__main__":
    main()
