#!/usr/bin/env python3
"""
Push secrets from .env to GCP Secret Manager.

Reads the .env file, filters for sensitive keys (defined in autonomous/secrets.py),
and creates/updates each one in GCP Secret Manager.

Prerequisites:
    - gcloud CLI authenticated
    - Secret Manager API enabled on project athena-hq
    - pip install google-cloud-secret-manager

Usage:
    python3 scripts/setup_secrets.py                     # from agentic-human-loop/.env
    python3 scripts/setup_secrets.py --env /path/to/.env # custom .env path
    python3 scripts/setup_secrets.py --dry-run            # preview without writing
"""

import argparse
import logging
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from autonomous.secrets import GCP_PROJECT, SENSITIVE_KEYS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [SECRETS] %(message)s")
logger = logging.getLogger(__name__)


def parse_env_file(env_path: Path) -> dict[str, str]:
    """Parse a .env file into a dict, handling quotes and multiline values."""
    secrets = {}
    if not env_path.exists():
        logger.error(f".env not found at {env_path}")
        sys.exit(1)

    content = env_path.read_text()
    for line in content.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue

        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key in SENSITIVE_KEYS and value:
            secrets[key] = value

    return secrets


def enable_secret_manager_api():
    """Enable the Secret Manager API if not already enabled."""
    logger.info("Enabling Secret Manager API...")
    subprocess.run(
        ["gcloud", "services", "enable", "secretmanager.googleapis.com",
         "--project", GCP_PROJECT],
        capture_output=True, text=True,
    )


def push_secret(name: str, value: str, dry_run: bool = False) -> bool:
    """Create or update a secret in GCP Secret Manager using gcloud CLI."""
    if dry_run:
        preview = value[:12] + "..." if len(value) > 15 else value[:4] + "***"
        logger.info(f"  [DRY RUN] Would push: {name} = {preview} ({len(value)} chars)")
        return True

    try:
        # Create the secret (ignore if already exists)
        create_result = subprocess.run(
            ["gcloud", "secrets", "create", name,
             "--replication-policy", "automatic",
             "--project", GCP_PROJECT],
            capture_output=True, text=True,
        )
        if create_result.returncode == 0:
            logger.info(f"  Created secret: {name}")
        elif "already exists" not in create_result.stderr.lower():
            logger.error(f"  Failed to create {name}: {create_result.stderr}")
            return False

        # Add a new version with the value (pipe via stdin)
        version_result = subprocess.run(
            ["gcloud", "secrets", "versions", "add", name,
             "--data-file=-",
             "--project", GCP_PROJECT],
            input=value, capture_output=True, text=True,
        )
        if version_result.returncode == 0:
            logger.info(f"  Updated: {name} ({len(value)} chars)")
            return True
        else:
            logger.error(f"  Failed to set {name}: {version_result.stderr}")
            return False

    except Exception as e:
        logger.error(f"  Failed to push {name}: {e}")
        return False


def grant_access(service_account: str):
    """Grant the VM's service account access to all secrets."""
    logger.info(f"\nGranting secretAccessor to {service_account}...")
    for key in SENSITIVE_KEYS:
        subprocess.run([
            "gcloud", "secrets", "add-iam-policy-binding", key,
            "--member", f"serviceAccount:{service_account}",
            "--role", "roles/secretmanager.secretAccessor",
            "--project", GCP_PROJECT,
        ], capture_output=True, text=True)
    logger.info("Done. Service account can now access all secrets.")


def main():
    parser = argparse.ArgumentParser(description="Push .env secrets to GCP Secret Manager")
    parser.add_argument("--env", default=None, help="Path to .env file")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument(
        "--grant-access",
        default=None,
        metavar="SA_EMAIL",
        help="Grant a service account access to all secrets (e.g. vertexairunner@athenahq.iam.gserviceaccount.com)",
    )
    args = parser.parse_args()

    if args.env:
        env_path = Path(args.env)
    else:
        candidates = [
            Path(__file__).parent.parent / ".env",
            Path(__file__).parent.parent.parent / ".env",
            Path.home() / ".env",
        ]
        env_path = next((p for p in candidates if p.exists()), candidates[0])

    logger.info(f"Reading secrets from: {env_path}")
    secrets = parse_env_file(env_path)

    if not secrets:
        logger.warning("No sensitive keys found in .env")
        return

    logger.info(f"Found {len(secrets)} sensitive keys to push:\n")
    for key in sorted(secrets.keys()):
        logger.info(f"  • {key}")

    if not args.dry_run:
        enable_secret_manager_api()

    print()
    success = 0
    for key, value in sorted(secrets.items()):
        if push_secret(key, value, dry_run=args.dry_run):
            success += 1

    logger.info(f"\n{'[DRY RUN] ' if args.dry_run else ''}Pushed {success}/{len(secrets)} secrets to {GCP_PROJECT}")

    if args.grant_access:
        grant_access(args.grant_access)

    if not args.dry_run and success == len(secrets):
        logger.info("\nSecrets are now in GCP Secret Manager.")
        logger.info("You can safely delete the .env file from this machine.")
        logger.info("Scripts will automatically fall back to Secret Manager.")


if __name__ == "__main__":
    main()
