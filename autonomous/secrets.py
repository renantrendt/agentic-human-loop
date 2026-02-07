"""
Centralized secret access — env var first (local dev), GCP Secret Manager (production).

Local dev:
    Secrets loaded from .env via load_dotenv as before.
    get_secret() finds them in os.environ and returns immediately.

Production (server / GitHub Actions):
    No .env file on disk. get_secret() falls through to GCP Secret Manager.
    VM authenticates via its service account — no extra credentials needed.

Setup:
    python3 scripts/setup_secrets.py  (pushes .env keys to Secret Manager)
"""

import logging
import os

logger = logging.getLogger(__name__)

_cache: dict[str, str] = {}
_sm_client = None
_sm_unavailable = False

GCP_PROJECT = "athena-hq"

SENSITIVE_KEYS = {
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "PERPLEXITY_API_KEY",
    "RESEND_API_KEY",
    "FRAMER_API_KEY",
    "YOUTUBE_API_KEY",
    "GMAIL_TOKEN",
    "GITHUB_PAT",
    "VERTEX_AI_API_KEY",
    "VERTEX_PRIVATE_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
    "SUPABASE_ANON_KEY",
    "SUPABASE_DATABASE_URL",
    "CLICKHOUSE_PASSWORD",
    "DATABASE_URL",
    "PUREMD_API_KEY",
    "EXA_API_KEY",
    "RESEND_SIGNING_SECRET",
}


def get_secret(name: str, default: str = "") -> str:
    """
    Fetch a secret: env var first (local dev), then GCP Secret Manager (production).
    Results are cached for the process lifetime.
    """
    val = os.environ.get(name)
    if val:
        return val

    if name in _cache:
        return _cache[name]

    global _sm_unavailable
    if _sm_unavailable:
        return default

    try:
        client = _get_sm_client()
        resource = f"projects/{GCP_PROJECT}/secrets/{name}/versions/latest"
        response = client.access_secret_version(request={"name": resource})
        secret_val = response.payload.data.decode("UTF-8")
        _cache[name] = secret_val
        return secret_val
    except ImportError:
        _sm_unavailable = True
        logger.debug("google-cloud-secret-manager not installed, using env vars only")
        return default
    except Exception as e:
        logger.debug(f"Secret '{name}' not in Secret Manager: {e}")
        return default


def _get_sm_client():
    global _sm_client
    if _sm_client is None:
        from google.cloud import secretmanager
        _sm_client = secretmanager.SecretManagerServiceClient()
    return _sm_client
