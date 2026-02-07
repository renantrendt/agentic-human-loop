"""
Content Agent Claw — persistent, event-driven orchestrator running inside OpenShell.

Each step runs in its own OpenShell sandbox with scoped permissions.
The claw runs on the Brev host, orchestrating sandboxes via:
  - openshell sandbox upload: push code/data into sandboxes
  - openshell sandbox connect: run scripts via SSH pipe
  - openshell sandbox download: pull results out

Usage:
    python3 openshell/claw.py --once    # single cycle
    python3 openshell/claw.py           # continuous loop
"""

import argparse
import json
import logging
import os
import selectors
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [CLAW] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_INTERVAL = 7200
SIGNAL_THRESHOLD = 5
MAX_ARTICLES_PER_CYCLE = 1
FEEDBACK_POLL_INTERVAL = 300

REPO_DIR = Path.home() / "script-nata"
AGENT_DIR = REPO_DIR / "agentic-human-loop"
OPENSHELL = os.getenv("OPENSHELL_BIN", str(Path.home() / ".local/bin/openshell"))


def ssh_run(sandbox_name: str, script: str, timeout: int = 600) -> dict:
    """Run a script inside a sandbox via SSH, streaming output to logs."""
    logger.info(f"  [{sandbox_name}] executing script (timeout={timeout}s)...")

    env_exports = ""
    for key in ["ANTHROPIC_API_KEY", "YOUTUBE_API_KEY", "RESEND_API_KEY", "FRAMER_API_KEY"]:
        val = os.environ.get(key, "")
        if val:
            env_exports += f'export {key}="{val}"\n'

    script_content = "#!/bin/bash\nset -e\n" + env_exports + script
    local_script = tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False)
    local_script.write(script_content)
    local_script.close()

    t0 = time.time()
    try:
        ssh_cfg = _get_ssh_config(sandbox_name)
        ssh_host = f"openshell-{sandbox_name}"

        proc = subprocess.Popen(
            ["ssh", "-F", ssh_cfg, ssh_host, "bash -s"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        proc.stdin.write(script_content)
        proc.stdin.close()

        stdout_lines = []
        stderr_lines = []

        sel = selectors.DefaultSelector()
        sel.register(proc.stdout, selectors.EVENT_READ)
        sel.register(proc.stderr, selectors.EVENT_READ)

        open_streams = 2
        while open_streams > 0:
            for key, _ in sel.select(timeout=timeout):
                line = key.fileobj.readline()
                if not line:
                    sel.unregister(key.fileobj)
                    open_streams -= 1
                    continue
                line = line.rstrip("\n")
                if key.fileobj is proc.stdout:
                    stdout_lines.append(line)
                    if not line.startswith("RESULT_JSON:"):
                        logger.info(f"  [{sandbox_name}] {line}")
                        sys.stdout.flush()
                else:
                    stderr_lines.append(line)

        proc.wait(timeout=10)
        elapsed = time.time() - t0
        status = "success" if proc.returncode == 0 else "failed"

        if stderr_lines:
            for line in stderr_lines[-3:]:
                logger.warning(f"  [{sandbox_name}] stderr: {line}")

        logger.info(f"  [{sandbox_name}] finished in {elapsed:.1f}s — {status} (exit={proc.returncode})")

        return {
            "status": status,
            "exit_code": proc.returncode,
            "stdout": "\n".join(stdout_lines),
            "stderr": "\n".join(stderr_lines),
        }
    except subprocess.TimeoutExpired:
        proc.kill()
        logger.error(f"  [{sandbox_name}] TIMEOUT after {timeout}s")
        return {"status": "timeout", "stdout": "", "stderr": "Timeout"}
    except Exception as e:
        logger.error(f"  [{sandbox_name}] ERROR: {e}")
        return {"status": "error", "stdout": "", "stderr": str(e)}
    finally:
        os.unlink(local_script.name)


def _get_ssh_config(sandbox_name: str) -> str:
    """Get SSH config file path for a sandbox. Caches per sandbox."""
    config_path = f"/tmp/openshell_ssh_{sandbox_name}.cfg"
    result = subprocess.run(
        [OPENSHELL, "sandbox", "ssh-config", sandbox_name],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ssh-config for {sandbox_name} failed: {result.stderr}")
    Path(config_path).write_text(result.stdout)
    return config_path


def upload_to_sandbox(sandbox_name: str, local_path: str, remote_path: str) -> bool:
    """Upload files from host to sandbox via SCP."""
    try:
        p = Path(local_path)
        is_dir = p.is_dir()
        size = sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) if is_dir else p.stat().st_size
        logger.info(f"  [{sandbox_name}] ↑ upload: {p.name} ({size/1024:.1f}KB) → {remote_path}")

        ssh_cfg = _get_ssh_config(sandbox_name)
        ssh_host = f"openshell-{sandbox_name}"
        cmd = ["scp", "-F", ssh_cfg]
        if is_dir:
            cmd.append("-r")
        cmd += [local_path, f"{ssh_host}:{remote_path}"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            logger.error(f"  [{sandbox_name}] ↑ UPLOAD FAILED: {result.stderr[:200]}")
        else:
            logger.info(f"  [{sandbox_name}] ↑ upload OK")
        return result.returncode == 0
    except Exception as e:
        logger.error(f"  [{sandbox_name}] ↑ upload error: {e}")
        return False


def download_from_sandbox(sandbox_name: str, remote_path: str, local_path: str) -> bool:
    """Download files from sandbox to host via SCP."""
    try:
        logger.info(f"  [{sandbox_name}] ↓ download: {remote_path} → {local_path}")
        ssh_cfg = _get_ssh_config(sandbox_name)
        ssh_host = f"openshell-{sandbox_name}"
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        cmd = ["scp", "-r", "-F", ssh_cfg, f"{ssh_host}:{remote_path}", local_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            logger.error(f"  [{sandbox_name}] ↓ DOWNLOAD FAILED: {result.stderr[:200]}")
        else:
            dl = Path(local_path)
            size = dl.stat().st_size if dl.is_file() else sum(f.stat().st_size for f in dl.rglob("*") if f.is_file())
            logger.info(f"  [{sandbox_name}] ↓ download OK ({size/1024:.1f}KB)")
        return result.returncode == 0
    except Exception as e:
        logger.error(f"  [{sandbox_name}] ↓ download error: {e}")
        return False


def setup_sandbox_code(sandbox_name: str):
    """Upload the pipeline code and config into a sandbox."""
    logger.info(f"  [{sandbox_name}] setting up sandbox code...")
    ssh_run(sandbox_name, "mkdir -p /sandbox/results /sandbox/results/articles/staged", timeout=10)
    paths_to_upload = [
        (str(AGENT_DIR / "social_monitor"), "/sandbox/social_monitor"),
        (str(AGENT_DIR / "autonomous"), "/sandbox/autonomous"),
        (str(AGENT_DIR / "publishing"), "/sandbox/publishing"),
        (str(AGENT_DIR / "brand-context"), "/sandbox/brand-context"),
    ]
    for local, remote in paths_to_upload:
        if Path(local).exists():
            upload_to_sandbox(sandbox_name, local, remote)
    logger.info(f"  [{sandbox_name}] sandbox code ready")


def phase_monitor(config: dict, session_dir: str) -> dict:
    """Run social signal collection in monitor-agent sandbox."""
    logger.info("=" * 60)
    logger.info("PHASE: MONITOR")
    logger.info("=" * 60)

    setup_sandbox_code("monitor-agent")

    script = """
cd /sandbox
export PATH="/sandbox/.venv/bin:$PATH"
python3 -c "import httpx" 2>/dev/null || { echo "[monitor] installing deps..." && pip install -q httpx tenacity 2>&1 | tail -1; }
echo "[monitor] collecting signals..."
mkdir -p results
python3 -c "
import json, sys
sys.path.insert(0, '.')
print('[monitor] running reddit collector...')
from social_monitor.runner import run
config = json.load(open('brand-context/config.json'))
result = run(config, 'results')
total = result.get('merged', {}).get('total_entries', 0)
print(f'[monitor] collected {total} signals')
print('RESULT_JSON:' + json.dumps(result))
" 2>&1
"""

    result = ssh_run("monitor-agent", script, timeout=300)

    if result["status"] == "success":
        for line in result["stdout"].split("\n"):
            if line.startswith("RESULT_JSON:"):
                data = json.loads(line[len("RESULT_JSON:"):])
                download_from_sandbox("monitor-agent", "/sandbox/results/social_signals.json",
                                     str(Path(session_dir) / "social_signals.json"))
                download_from_sandbox("monitor-agent", "/sandbox/results/reddit_signals.json",
                                     str(Path(session_dir) / "reddit_signals.json"))
                download_from_sandbox("monitor-agent", "/sandbox/results/youtube_signals.json",
                                     str(Path(session_dir) / "youtube_signals.json"))
                return data

    logger.error(f"Monitor failed: {result.get('stderr', '')[:200]} | stdout: {result.get('stdout', '')[:200]}")
    return {"status": "failed"}


def phase_analyst(config: dict, session_dir: str) -> dict:
    """Run gap detection in analyst-agent sandbox."""
    logger.info("=" * 60)
    logger.info("PHASE: ANALYST")
    logger.info("=" * 60)

    setup_sandbox_code("analyst-agent")

    signals_file = Path(session_dir) / "social_signals.json"
    if signals_file.exists():
        upload_to_sandbox("analyst-agent", str(signals_file), "/sandbox/results/social_signals.json")

    script = """
cd /sandbox
export PATH="/sandbox/.venv/bin:$PATH"
python3 -c "import anthropic" 2>/dev/null || { echo "[analyst] installing deps..." && pip install -q httpx tenacity anthropic 2>&1 | tail -1; }
echo "[analyst] deps ready"
echo "[analyst] loading social signals..."
mkdir -p results
python3 -c "
import json, sys, os
sys.path.insert(0, '.')
signals = json.load(open('results/social_signals.json'))
te = signals.get('total_entries', 0)
print(f'[analyst] loaded {te} signals')
print('[analyst] running clustering + gap detection with Claude...')
from social_monitor.gap_detector import detect_gaps
config = json.load(open('brand-context/config.json'))
result = detect_gaps(config, 'results')
gaps = result.get('gaps', [])
print(f'[analyst] found {len(gaps)} content gaps')
for i, g in enumerate(gaps[:5]):
    label = g.get('prompt', g.get('topic', '?'))[:80]
    print(f'[analyst]   gap[{i}]: {label}')
print('RESULT_JSON:' + json.dumps(result))
" 2>&1
"""

    result = ssh_run("analyst-agent", script, timeout=600)

    if result["status"] in ("success", "failed"):
        stdout = result.get("stdout", "")
        for line in stdout.split("\n"):
            if line.startswith("RESULT_JSON:"):
                data = json.loads(line[len("RESULT_JSON:"):])
                download_from_sandbox("analyst-agent", "/sandbox/results/content_gaps.json",
                                     str(Path(session_dir) / "content_gaps.json"))
                return data

    logger.error(f"Analyst failed: {result.get('stderr', '')[:300]} | stdout: {result.get('stdout', '')[:300]}")
    return {"status": "failed", "gaps": []}


def phase_writer(config: dict, session_dir: str, gaps: list) -> list:
    """Generate articles in writer-agent sandbox."""
    logger.info("=" * 60)
    logger.info(f"PHASE: WRITER ({min(len(gaps), MAX_ARTICLES_PER_CYCLE)} articles)")
    logger.info("=" * 60)

    setup_sandbox_code("writer-agent")

    articles = []
    for i, gap in enumerate(gaps[:MAX_ARTICLES_PER_CYCLE]):
        prompt = gap.get("prompt", "")
        logger.info(f"  Article {i+1}: {prompt[:60]}")

        gap_file = Path(session_dir) / f"gap_{i}.json"
        gap_file.write_text(json.dumps(gap))
        upload_to_sandbox("writer-agent", str(gap_file), f"/sandbox/gap_{i}.json")

        script = f"""
cd /sandbox
export PATH="/sandbox/.venv/bin:$PATH"
python3 -c "import anthropic" 2>/dev/null || {{ echo "[writer] installing deps..." && pip install -q anthropic 2>&1 | tail -1; }}
echo "[writer] generating article {i+1}: {prompt[:60]}..."
mkdir -p results/articles/staged
python3 -c "
import json, sys, os
sys.path.insert(0, '.')
print('[writer] calling Claude Opus 4.6...')
from autonomous.orchestrator import _generate_article_for_gap
config = json.load(open('brand-context/config.json'))
gap = json.load(open('gap_{i}.json'))
result = _generate_article_for_gap(gap, config, 'results', {i})
wc = result.get('word_count', 0)
print('[writer] article generated: ' + str(wc) + ' words')
print('RESULT_JSON:' + json.dumps(result))
" 2>&1
"""

        result = ssh_run("writer-agent", script, timeout=600)

        if result["status"] in ("success", "failed"):
            for line in result.get("stdout", "").split("\n"):
                if line.startswith("RESULT_JSON:"):
                    article_data = json.loads(line[len("RESULT_JSON:"):])
                    articles.append(article_data)
                    staged_dir = Path(session_dir) / "articles" / "staged"
                    staged_dir.mkdir(parents=True, exist_ok=True)
                    download_from_sandbox("writer-agent", "/sandbox/results/articles/staged/",
                                         str(staged_dir) + "/")

    return articles


def phase_reviewer(config: dict, session_dir: str, summary: dict) -> dict:
    """Send email digest in reviewer-agent sandbox."""
    logger.info("=" * 60)
    logger.info("PHASE: REVIEWER")
    logger.info("=" * 60)

    setup_sandbox_code("reviewer-agent")

    summary_path = Path(session_dir) / "pipeline_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    upload_to_sandbox("reviewer-agent", str(summary_path), "/sandbox/results/pipeline_summary.json")

    staged_dir = Path(session_dir) / "articles" / "staged"
    if staged_dir.exists():
        ssh_run("reviewer-agent", "mkdir -p /sandbox/results/articles/staged", timeout=10)
        upload_to_sandbox("reviewer-agent", str(staged_dir) + "/", "/sandbox/results/articles/staged/")

    script = """
cd /sandbox
export PATH="/sandbox/.venv/bin:$PATH"
python3 -c "import resend" 2>/dev/null || { echo "[reviewer] installing deps..." && pip install -q resend anthropic 2>&1 | tail -1; }
echo "[reviewer] preparing email digest..."
python3 -c "
import json, sys
sys.path.insert(0, '.')
summary = json.load(open('results/pipeline_summary.json'))
n = len(summary.get('articles_staged', []))
print('[reviewer] sending digest with ' + str(n) + ' articles...')
from publishing.email_digest import send_digest
config = json.load(open('brand-context/config.json'))
result = send_digest(config, 'results', summary)
status = result.get('status', 'unknown')
print('[reviewer] email sent: ' + str(status))
print('RESULT_JSON:' + json.dumps(result))
" 2>&1
"""

    result = ssh_run("reviewer-agent", script, timeout=120)
    return {"status": result["status"]}


def phase_publisher(config: dict, session_dir: str, article_file: str) -> dict:
    """Publish approved article in publisher-agent sandbox."""
    logger.info(f"  Publishing: {Path(article_file).name}")

    setup_sandbox_code("publisher-agent")
    upload_to_sandbox("publisher-agent", article_file, "/sandbox/article.md")

    script = """
cd /sandbox
npm install -q framer-api 2>/dev/null
node --input-type=module -e "
import { connect } from 'framer-api';
import fs from 'fs';

const config = JSON.parse(fs.readFileSync('brand-context/config.json', 'utf-8'));
const fc = config.publishing?.framer || {};
const projectUrl = 'https://' + fc.project_url;
const apiKey = process.env.FRAMER_API_KEY;
const collectionId = fc.collection_id;

const content = fs.readFileSync('/sandbox/article.md', 'utf-8');
const title = content.match(/^# (.+)$/m)?.[1] || 'Untitled';
const slug = title.toLowerCase().replace(/[^a-z0-9 ]/g, '').replace(/ +/g, '-').slice(0, 60);

const framer = await connect(projectUrl, apiKey);
const collection = await framer.getCollection(collectionId);
const fields = await collection.getFields();
const titleField = fields.find(f => f.name === 'Title');
const contentField = fields.find(f => f.name === 'Content');
const fieldData = {};
fieldData[titleField.id] = { type: 'string', value: title };
fieldData[contentField.id] = { type: 'formattedText', value: content, contentType: 'markdown' };
await collection.addItems([{ slug, draft: false, fieldData }]);
await framer.publish();
await framer.disconnect();
console.log('RESULT_JSON:' + JSON.stringify({ published: true, slug }));
"
"""

    return ssh_run("publisher-agent", script, timeout=60)


def run_cycle(config: dict, reuse_session: str = None) -> dict:
    """Run one full claw cycle. If reuse_session is given, skip monitor and use that session's data."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if reuse_session:
        source_dir = Path(reuse_session) if Path(reuse_session).is_absolute() else (
            AGENT_DIR / "results" / "local_pipeline" / reuse_session
        )
        if not source_dir.exists():
            candidates = sorted(AGENT_DIR.glob(f"results/local_pipeline/session_*{reuse_session}*"))
            source_dir = candidates[-1] if candidates else source_dir
        session_dir = str(AGENT_DIR / "results" / "local_pipeline" / f"session_{timestamp}")
        Path(session_dir).mkdir(parents=True, exist_ok=True)
        import shutil
        for f in source_dir.glob("*.json"):
            shutil.copy2(f, Path(session_dir) / f.name)
        logger.info(f"Reusing monitor data from: {source_dir.name}")
    else:
        session_dir = str(AGENT_DIR / "results" / "local_pipeline" / f"session_{timestamp}")
        Path(session_dir).mkdir(parents=True, exist_ok=True)

    logger.info("*" * 60)
    logger.info(f"CLAW CYCLE — {timestamp}")
    logger.info("*" * 60)

    summary = {
        "session_dir": session_dir,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "steps": {},
        "articles_staged": [],
        "escalations": [],
    }

    cycle_start = time.time()

    # 1. Monitor (skip if reusing session)
    if reuse_session:
        signals_file = Path(session_dir) / "social_signals.json"
        if signals_file.exists():
            data = json.loads(signals_file.read_text())
            total_signals = data.get("total_entries", 0)
            reddit_posts = data.get("reddit_count", 0)
            yt_comments = data.get("youtube_count", 0)
            logger.info(f"  → Reusing existing data: {total_signals} signals (reddit={reddit_posts}, youtube={yt_comments})")
        else:
            logger.error(f"  No social_signals.json found in {source_dir}")
            return {"status": "failed"}
    else:
        monitor_result = phase_monitor(config, session_dir)
        reddit_posts = monitor_result.get("reddit", {}).get("posts_found", 0)
        yt_comments = monitor_result.get("youtube", {}).get("comments_found", 0)
        total_signals = monitor_result.get("merged", {}).get("total_entries", 0)
    summary["steps"]["social_monitor"] = {
        "total_signals": total_signals,
        "reddit_posts": reddit_posts,
        "youtube_comments": yt_comments,
    }
    logger.info(f"  → Monitor result: {total_signals} signals (reddit={reddit_posts}, youtube={yt_comments})")

    if total_signals < SIGNAL_THRESHOLD:
        logger.info(f"  Only {total_signals} signals (need {SIGNAL_THRESHOLD}) — skipping cycle")
        summary["status"] = "insufficient_signals"
        return summary

    # 2. Analyze
    analyst_result = phase_analyst(config, session_dir)
    gaps = analyst_result.get("gaps", [])
    summary["steps"]["gap_detection"] = {
        "gaps_found": len(gaps),
        "analysis_summary": analyst_result.get("analysis_summary", ""),
    }
    logger.info(f"  → Analyst result: {len(gaps)} content gaps detected")
    for i, gap in enumerate(gaps[:5]):
        logger.info(f"    gap[{i}]: {gap.get('prompt', gap.get('topic', 'unknown'))[:80]}")

    if not gaps:
        logger.info("  No content gaps — brand already covers these topics")
        summary["status"] = "no_gaps"
        return summary

    # 3. Write
    articles = phase_writer(config, session_dir, gaps)
    for article in articles:
        if article.get("status") == "success":
            summary["articles_staged"].append({
                "prompt": article.get("prompt", ""),
                "article_file": article.get("article_file", ""),
                "word_count": article.get("word_count", 0),
                "approved": False,
            })
            logger.info(f"  → Article staged: {article.get('prompt', '')[:60]} ({article.get('word_count', 0)} words)")

    # 4. Review (send email)
    summary["completed_at"] = datetime.now(timezone.utc).isoformat()
    summary["status"] = "completed"
    phase_reviewer(config, session_dir, summary)

    elapsed = time.time() - cycle_start
    logger.info("*" * 60)
    logger.info(f"CYCLE COMPLETE in {elapsed:.0f}s — {len(summary['articles_staged'])} articles staged")
    logger.info(f"  Session: {session_dir}")
    logger.info("*" * 60)

    return summary


def feedback_loop(config: dict):
    """Poll for feedback via reviewer-agent."""
    script = """
cd /sandbox
export PATH="/sandbox/.venv/bin:$PATH"
pip install -q resend anthropic google-auth google-auth-oauthlib google-api-python-client 2>&1 | tail -1
python3 -c "
import json, sys
sys.path.insert(0, '.')
from autonomous.gmail_poller import poll_and_process
config = json.load(open('brand-context/config.json'))
result = poll_and_process(config)
print('RESULT_JSON:' + json.dumps(result))
" 2>&1
"""

    result = ssh_run("reviewer-agent", script, timeout=120)
    if result["status"] == "success":
        for line in result["stdout"].split("\n"):
            if line.startswith("RESULT_JSON:"):
                data = json.loads(line[len("RESULT_JSON:"):])
                if data.get("processed", 0) > 0:
                    logger.info(f"Processed {data['processed']} feedback replies")


def _load_env():
    """Load .env file into os.environ if it exists."""
    env_file = AGENT_DIR / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key.strip(), value)


def main():
    parser = argparse.ArgumentParser(description="Content Agent Claw")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL)
    parser.add_argument("--config", default=str(AGENT_DIR / "brand-context" / "config.json"))
    parser.add_argument("--once", action="store_true", help="Run one cycle and exit")
    parser.add_argument("--session", type=str, help="Reuse monitor data from an existing session (skip monitor phase)")
    parser.add_argument("--max-articles", type=int, default=MAX_ARTICLES_PER_CYCLE, help="Max articles to generate per cycle (default 1)")
    args = parser.parse_args()

    _load_env()
    config = json.load(open(args.config))

    if args.max_articles:
        global MAX_ARTICLES_PER_CYCLE
        MAX_ARTICLES_PER_CYCLE = args.max_articles

    if args.once or args.session:
        run_cycle(config, reuse_session=args.session)
        return

    logger.info("CONTENT AGENT CLAW — STARTING")
    logger.info(f"Monitor every {args.interval}s, feedback every {FEEDBACK_POLL_INTERVAL}s")

    last_monitor = 0
    while True:
        now = time.time()
        if now - last_monitor >= args.interval:
            try:
                run_cycle(config)
            except Exception as e:
                logger.error(f"Cycle failed: {e}")
            last_monitor = now

        try:
            feedback_loop(config)
        except Exception as e:
            logger.error(f"Feedback failed: {e}")

        time.sleep(FEEDBACK_POLL_INTERVAL)


if __name__ == "__main__":
    main()
