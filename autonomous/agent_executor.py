"""
Agent Executor — calls Claude Opus 4.6 to complete pipeline task files.

Reads a task file (step4_SYNTHESIS_TASK.md, step5_ARTICLE_GENERATION_TASK.md, etc.),
sends its content to Claude as context, and writes the output file that the
pipeline expects to find on resume.

This replaces the human-in-the-loop: instead of printing AGENT_TASK_READY and
waiting, the pipeline calls execute_task() which returns immediately with the result.
"""

import json
import logging
import os
import re
from pathlib import Path

import anthropic
import tenacity
from anthropic.types import TextBlock

from autonomous.secrets import get_secret

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_client(config: dict) -> tuple:
    model = config.get("autonomous", {}).get("model", "claude-opus-4-6")
    max_tokens = config.get("autonomous", {}).get("max_tokens", 16000)
    api_key = get_secret("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    client = anthropic.Anthropic(api_key=api_key)
    return client, model, max_tokens


@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=2, min=5, max=30),
    retry=tenacity.retry_if_exception_type(Exception),
)
def call_claude(client, model: str, max_tokens: int, system_prompt: str, user_prompt: str) -> str:
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=0.3,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    if response.content:
        for block in response.content:
            if isinstance(block, TextBlock):
                return block.text
    raise ValueError("No text in Claude response")


# Task file → output file mapping (what the pipeline expects)
TASK_OUTPUT_MAP = {
    "step4_SYNTHESIS_TASK.md": "step4_AGENT_SYNTHESIS.md",
    "step5_ARTICLE_GENERATION_TASK.md": "articles/hub/step5_GENERATED_ARTICLE.md",
    "step5_AGENT_GENERATE_CONTENT.md": "articles/hub/step5_GENERATED_ARTICLE.md",
    "step6_WRITING_RULES_TASK.md": "articles/hub/step6_ARTICLE_RULES_APPLIED.md",
    "step7_INTERNAL_LINKS_TASK.md": "articles/hub/step7_ARTICLE_WITH_INTERNAL_LINKS.md",
    "step8_CITATIONS_TASK.md": "articles/hub/step8_ARTICLE_WITH_CITATIONS.md",
    "step9_SPOKE_REGISTRATION_TASK.md": "step9_UPDATED_internal_linking_map.json",
    "step10_SPOKE_CLUSTER_TASK.md": None,  # multi-file output (spokes)
    "step10a_UTILITY_GENERATION_TASK.md": "step10a_UTILITIES_COMPLETE.txt",
    "step11a_HUB_SPOKES_CROSSLINKING_TASK.md": "step11_CROSSLINKING_COMPLETE.txt",
    "step11b_INTEGRATE_UTILITIES_TASK.md": "step11b_UTILITIES_INTEGRATED.txt",
    "step11c_KEYWORD_REVIEW_TASK.md": "step11c_REVIEWED_KEYWORDS.csv",
    "step12b_HTML_EDITOR_TASK.md": "step12b_HTML_CLEANED.csv",
    "step12d_LINK_VERIFICATION_TASK.md": "step12d_LINK_VERIFICATION_REPORT.md",
    "step12e_FIX_LINKS_TASK.md": "step12e_LINKS_FIXED.md",
}

SYSTEM_PROMPT = """You are an expert SEO content writer and strategist working inside an automated content pipeline.

You will receive a task file that describes exactly what you need to produce. Follow the instructions precisely.

Rules:
- Output ONLY the content requested — no meta-commentary, no "here's what I'll do" preamble
- Follow the exact format specified in the task
- If the task asks for Markdown, output Markdown
- If the task asks for JSON, output valid JSON
- If the task asks for CSV, output valid CSV
- Maintain the brand voice and style described in the task context
- Include all required elements (citations, internal links, FAQs, etc.)
- Be thorough — this content will be published directly"""


def execute_task(
    task_file_path: str,
    session_dir: str,
    config: dict,
    additional_context: str = "",
) -> dict:
    """
    Execute a pipeline task file by sending it to Claude and writing the output.

    Args:
        task_file_path: Absolute path to the task file
        session_dir: Session directory for output files
        config: Pipeline config dict
        additional_context: Extra files/context to include

    Returns:
        dict with status, output_file, etc.
    """
    task_path = Path(task_file_path)
    if not task_path.exists():
        return {"status": "error", "error": f"Task file not found: {task_file_path}"}

    task_content = task_path.read_text(encoding="utf-8")
    task_filename = task_path.name

    output_filename = TASK_OUTPUT_MAP.get(task_filename)
    if output_filename is None and task_filename not in TASK_OUTPUT_MAP:
        output_filename = task_filename.replace("_TASK", "_COMPLETE").replace("TASK_", "")

    client, model, max_tokens = get_client(config)

    # Load any referenced files from the task
    referenced_files = _extract_referenced_files(task_content, session_dir)

    user_prompt = f"# Task File: {task_filename}\n\n{task_content}"

    if referenced_files:
        user_prompt += "\n\n# Referenced Files\n\n"
        for ref_name, ref_content in referenced_files.items():
            user_prompt += f"## {ref_name}\n\n{ref_content[:50000]}\n\n"

    if additional_context:
        user_prompt += f"\n\n# Additional Context\n\n{additional_context}"

    # Load brand context files
    brand_context = _load_brand_context()
    if brand_context:
        user_prompt += f"\n\n# Brand Context\n\n{brand_context}"

    logger.info(f"Executing task: {task_filename} with {model}")
    logger.info(f"  Prompt size: ~{len(user_prompt)} chars")

    try:
        result_content = call_claude(client, model, max_tokens, SYSTEM_PROMPT, user_prompt)
    except Exception as e:
        logger.error(f"Claude API failed for {task_filename}: {e}")
        return {"status": "failed", "error": str(e), "task_file": task_filename}

    if output_filename:
        output_path = Path(session_dir) / output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result_content, encoding="utf-8")
        logger.info(f"  Output written to: {output_path}")
    else:
        output_path = Path(session_dir) / task_filename.replace("_TASK.md", "_COMPLETE.md")
        output_path.write_text(result_content, encoding="utf-8")

    return {
        "status": "success",
        "task_file": task_filename,
        "output_file": str(output_path),
        "output_size": len(result_content),
        "model": model,
    }


def execute_spoke_generation(
    task_file_path: str,
    session_dir: str,
    config: dict,
    num_spokes: int = 10,
) -> dict:
    """
    Special handler for spoke cluster generation (step 10) which produces
    multiple output files (one per spoke article).
    """
    task_path = Path(task_file_path)
    if not task_path.exists():
        return {"status": "error", "error": f"Task file not found: {task_file_path}"}

    task_content = task_path.read_text(encoding="utf-8")
    client, model, max_tokens = get_client(config)

    brand_context = _load_brand_context()

    spokes_dir = Path(session_dir) / "articles" / "spokes"
    spokes_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for spoke_num in range(1, num_spokes + 1):
        spoke_prompt = (
            f"{task_content}\n\n"
            f"Generate SPOKE {spoke_num} of {num_spokes}.\n"
            f"Output the complete spoke article in Markdown format.\n"
        )
        if brand_context:
            spoke_prompt += f"\n# Brand Context\n\n{brand_context}"

        try:
            result_content = call_claude(client, model, max_tokens, SYSTEM_PROMPT, spoke_prompt)
            spoke_file = spokes_dir / f"step10_spoke{spoke_num:02d}.md"
            spoke_file.write_text(result_content, encoding="utf-8")
            results.append({"spoke": spoke_num, "status": "success", "file": str(spoke_file)})
            logger.info(f"  Spoke {spoke_num}/{num_spokes} generated")
        except Exception as e:
            results.append({"spoke": spoke_num, "status": "failed", "error": str(e)})
            logger.error(f"  Spoke {spoke_num} failed: {e}")

    successful = sum(1 for r in results if r["status"] == "success")
    return {
        "status": "success" if successful > 0 else "failed",
        "spokes_generated": successful,
        "spokes_total": num_spokes,
        "results": results,
    }


def _extract_referenced_files(task_content: str, session_dir: str) -> dict[str, str]:
    """Extract and load files referenced in the task (e.g., 'Read step1_FOR_AGENT_ANALYSIS.md')."""
    refs = {}
    patterns = [
        r"(?:Read|read|review|Review|See|see|analyze|Analyze)\s+[`*]*([^\s`*,]+\.(?:md|json|csv|txt))[`*]*",
        r"(?:File:|INPUT:)\s*[`*]*([^\s`*,]+\.(?:md|json|csv|txt))[`*]*",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, task_content)
        for match in matches:
            file_path = Path(session_dir) / match
            if not file_path.exists():
                for subdir in ["articles/hub", "articles/spokes", "articles/utilities"]:
                    alt_path = Path(session_dir) / subdir / match
                    if alt_path.exists():
                        file_path = alt_path
                        break

            if file_path.exists():
                try:
                    content = file_path.read_text(encoding="utf-8")
                    refs[match] = content
                except Exception:
                    pass

    return refs


def _load_brand_context() -> str:
    """Load brand context files (voice, rules, sitemap)."""
    context_parts = []
    brand_dir = Path("brand-context")

    for filename in ["solidroad", "rule_writing.ts", "rule_draft.ts", "rule_citations.md"]:
        filepath = brand_dir / filename
        if filepath.exists():
            content = filepath.read_text(encoding="utf-8")
            context_parts.append(f"### {filename}\n\n{content[:10000]}")

    return "\n\n".join(context_parts) if context_parts else ""
