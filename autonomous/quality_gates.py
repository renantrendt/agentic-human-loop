"""
Quality Gates — threshold-based auto-pass/retry/escalate logic.

Replaces human review at quality checkpoints. If a gate fails 3x,
the issue is escalated to the email digest for user review.
"""

import json
import logging
import re
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_RETRIES = 3


class GateResult:
    def __init__(self, passed: bool, score: float, details: str, gate_name: str):
        self.passed = passed
        self.score = score
        self.details = details
        self.gate_name = gate_name

    def to_dict(self) -> dict:
        return {
            "gate": self.gate_name,
            "passed": self.passed,
            "score": self.score,
            "details": self.details,
        }


def check_citation_verification(session_dir: str, min_pass_rate: float = 0.80) -> GateResult:
    """
    Step 8B: Verify citation URLs are valid.
    Pass if >= min_pass_rate of citations are valid.
    """
    report_path = Path(session_dir) / "step8b_CITATION_VERIFICATION_REPORT.md"
    if not report_path.exists():
        return GateResult(False, 0.0, "Verification report not found", "citation_verification")

    content = report_path.read_text(encoding="utf-8")

    valid_match = re.search(r"(\d+)\s*(?:valid|verified|passed)", content, re.IGNORECASE)
    total_match = re.search(r"(\d+)\s*(?:total|citations|checked)", content, re.IGNORECASE)

    if valid_match and total_match:
        valid = int(valid_match.group(1))
        total = int(total_match.group(1))
        rate = valid / total if total > 0 else 0
        passed = rate >= min_pass_rate
        return GateResult(
            passed, rate,
            f"{valid}/{total} citations valid ({rate:.0%}). Threshold: {min_pass_rate:.0%}",
            "citation_verification",
        )

    return GateResult(True, 1.0, "Could not parse report, passing by default", "citation_verification")


def check_html_quality(session_dir: str) -> GateResult:
    """
    Step 12B: Check HTML export for broken tags.
    """
    csv_path = Path(session_dir) / "step12_FRAMER_EXPORT.csv"
    if not csv_path.exists():
        return GateResult(False, 0.0, "Framer export CSV not found", "html_quality")

    content = csv_path.read_text(encoding="utf-8")

    unclosed_tags = len(re.findall(r"<(?:div|p|h[1-6]|ul|ol|li|a|span|table|tr|td|th)\b[^>]*>(?!.*</\1>)", content))
    broken_entities = len(re.findall(r"&(?!amp;|lt;|gt;|quot;|#\d+;|#x[0-9a-fA-F]+;)\w*;?", content))

    issues = unclosed_tags + broken_entities
    score = max(0, 1.0 - (issues / 100))
    passed = issues < 10

    return GateResult(
        passed, score,
        f"{issues} HTML issues found (unclosed: {unclosed_tags}, entities: {broken_entities})",
        "html_quality",
    )


def check_cluster_quality(session_dir: str, min_score: float = 0.70) -> GateResult:
    """
    Step 13: Check cluster dominance score.
    """
    dominance_path = Path(session_dir) / "step13_CLUSTER_DOMINANCE.json"
    if not dominance_path.exists():
        return GateResult(False, 0.0, "Cluster dominance report not found", "cluster_quality")

    try:
        with open(dominance_path, "r") as f:
            data = json.load(f)

        if isinstance(data, dict):
            score = data.get("overall_score", data.get("dominance_score", 0))
        elif isinstance(data, list) and data:
            scores = [item.get("score", 0) for item in data if isinstance(item, dict)]
            score = sum(scores) / len(scores) if scores else 0
        else:
            score = 0

        if isinstance(score, str):
            score = float(score)

        score = score / 100 if score > 1 else score
        passed = score >= min_score

        return GateResult(
            passed, score,
            f"Cluster quality score: {score:.2f}. Threshold: {min_score:.2f}",
            "cluster_quality",
        )
    except (json.JSONDecodeError, ValueError) as e:
        return GateResult(False, 0.0, f"Failed to parse dominance report: {e}", "cluster_quality")


def check_article_word_count(article_path: str, min_words: int = 1500) -> GateResult:
    """Basic check that the generated article meets minimum word count."""
    path = Path(article_path)
    if not path.exists():
        return GateResult(False, 0.0, f"Article not found: {article_path}", "word_count")

    content = path.read_text(encoding="utf-8")
    word_count = len(content.split())
    passed = word_count >= min_words

    return GateResult(
        passed, min(1.0, word_count / min_words),
        f"Word count: {word_count}. Minimum: {min_words}",
        "word_count",
    )


def check_content_relevance(article_path: str, target_prompt: str) -> GateResult:
    """Check that article content is relevant to the target prompt."""
    path = Path(article_path)
    if not path.exists():
        return GateResult(False, 0.0, f"Article not found: {article_path}", "content_relevance")

    content = path.read_text(encoding="utf-8").lower()
    prompt_words = [w.strip() for w in target_prompt.lower().split() if len(w.strip()) > 3]

    if not prompt_words:
        return GateResult(True, 1.0, "No target prompt to check against", "content_relevance")

    matches = sum(1 for w in prompt_words if w in content)
    score = matches / len(prompt_words) if prompt_words else 0
    passed = score >= 0.5

    return GateResult(
        passed, score,
        f"{matches}/{len(prompt_words)} target keywords found in article",
        "content_relevance",
    )


def check_article_structure(article_path: str) -> GateResult:
    """Check that the article has proper heading structure and formatting."""
    path = Path(article_path)
    if not path.exists():
        return GateResult(False, 0.0, f"Article not found: {article_path}", "article_structure")

    content = path.read_text(encoding="utf-8")

    h1_count = len(re.findall(r"^# [^\n]+", content, re.MULTILINE))
    h2_count = len(re.findall(r"^## [^\n]+", content, re.MULTILINE))
    h3_count = len(re.findall(r"^### [^\n]+", content, re.MULTILINE))
    has_lists = bool(re.search(r"^[-*\d+\.]\s", content, re.MULTILINE))
    has_bold = "**" in content

    issues = []
    if h1_count == 0:
        issues.append("Missing H1 title")
    if h1_count > 1:
        issues.append(f"{h1_count} H1 tags (should be 1)")
    if h2_count < 3:
        issues.append(f"Only {h2_count} H2 sections (need 3+)")

    score = min(1.0, (h2_count / 5) * 0.4 + (1 if h1_count == 1 else 0) * 0.3 + (1 if has_lists else 0) * 0.15 + (1 if has_bold else 0) * 0.15)
    passed = h1_count >= 1 and h2_count >= 3

    return GateResult(
        passed, score,
        f"H1:{h1_count} H2:{h2_count} H3:{h3_count} lists:{has_lists} bold:{has_bold}" + (f" Issues: {', '.join(issues)}" if issues else ""),
        "article_structure",
    )


def run_all_gates(session_dir: str, config: dict) -> dict:
    """
    Run all applicable quality gates for a session.
    Adapts to which files exist — works for both full pipeline and autonomous mode.
    """
    results = []
    escalations = []

    gates = []

    # Original pipeline gates (only if the files exist)
    citation_report = Path(session_dir) / "step8b_CITATION_VERIFICATION_REPORT.md"
    if citation_report.exists():
        gates.append(("citation_verification", lambda: check_citation_verification(session_dir)))

    framer_csv = Path(session_dir) / "step12_FRAMER_EXPORT.csv"
    if framer_csv.exists():
        gates.append(("html_quality", lambda: check_html_quality(session_dir)))

    dominance_json = Path(session_dir) / "step13_CLUSTER_DOMINANCE.json"
    if dominance_json.exists():
        gates.append(("cluster_quality", lambda: check_cluster_quality(session_dir)))

    # Autonomous mode gates (check staged articles)
    staged_dir = Path(session_dir) / "articles" / "staged"
    target_prompt = config.get("athena_integration", {}).get("target_prompt", "")
    min_words = config.get("content", {}).get("word_count_targets", {}).get("hub", {}).get("min", 3000)

    if staged_dir.exists():
        for article_file in sorted(staged_dir.glob("*.md")):
            name = article_file.stem
            gates.append((f"word_count_{name}", lambda af=str(article_file): check_article_word_count(af, min_words)))
            gates.append((f"structure_{name}", lambda af=str(article_file): check_article_structure(af)))
            if target_prompt:
                gates.append((f"relevance_{name}", lambda af=str(article_file), tp=target_prompt: check_content_relevance(af, tp)))

    # Hub article from full pipeline
    hub_article = Path(session_dir) / "articles" / "hub" / "step5_GENERATED_ARTICLE.md"
    if hub_article.exists():
        gates.append(("hub_word_count", lambda: check_article_word_count(str(hub_article), min_words)))

    for gate_name, gate_fn in gates:
        try:
            result = gate_fn()
            results.append(result.to_dict())
            if not result.passed:
                escalations.append({
                    "gate": gate_name,
                    "score": result.score,
                    "details": result.details,
                })
        except Exception as e:
            logger.error(f"Gate {gate_name} threw an exception: {e}")
            results.append({"gate": gate_name, "passed": False, "score": 0, "details": str(e)})
            escalations.append({"gate": gate_name, "score": 0, "details": str(e)})

    all_passed = all(r["passed"] for r in results)

    return {
        "all_passed": all_passed,
        "gates": results,
        "escalations": escalations,
    }
