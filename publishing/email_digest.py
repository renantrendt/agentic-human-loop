"""
Email Digest — sends a weekly summary via Resend with rich HTML article rendering,
approve/reject buttons linked to GitHub Actions workflows, quality scores,
and package install requests.

Usage:
    from publishing.email_digest import send_digest
    send_digest(config, session_dir, pipeline_summary)
"""

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import resend

from autonomous.secrets import get_secret

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GITHUB_REPO = "renantrendt/script-nata"
GITHUB_BRANCH = "Autonomous-content-agent"


def send_confirmation(config: dict, session_dir: str, approved_articles: list, published_url: str = None) -> dict:
    """Send a lightweight confirmation email when articles are approved (no full digest)."""
    notif_config = config.get("notifications", {}).get("resend", {})
    api_key = get_secret(notif_config.get("api_key_env", "RESEND_API_KEY"))
    if not api_key:
        return {"status": "failed", "error": "RESEND_API_KEY not set"}

    from_email = notif_config.get("from_email", "")
    to_email = notif_config.get("to_email", "")
    resend.api_key = api_key

    titles = [a.get("prompt", f"Article {i+1}") for i, a in enumerate(approved_articles)]
    titles_html = "".join(f"<li>{_escape(t)}</li>" for t in titles)

    published_section = ""
    if published_url:
        published_section = f'<p style="margin:16px 0 0;"><a href="{published_url}" style="color:#16a34a;font-weight:600;">View on Framer →</a></p>'

    html = f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:500px;margin:0 auto;padding:24px;">
      <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:20px;">
        <h2 style="margin:0 0 12px;color:#16a34a;font-size:18px;">✓ Content Approved</h2>
        <ul style="margin:0;padding:0 0 0 20px;color:#333;line-height:1.8;">{titles_html}</ul>
        {published_section}
      </div>
      <p style="color:#999;font-size:12px;margin-top:16px;">Content Agent — {datetime.now(timezone.utc).strftime('%b %d, %Y %H:%M UTC')}</p>
    </div>
    """

    import re as _re
    session_tag = ""
    session_match = _re.search(r"session_\d{8}_\d{6}", session_dir)
    if session_match:
        session_tag = f" [{session_match.group(0)}]"
    date = datetime.now(timezone.utc).strftime("%b %d, %Y")
    subject = f"Re: Content Agent — {len(approved_articles)} articles ready for review — {date}{session_tag}"

    headers = {}
    thread_file = Path(session_dir) / "email_thread.json"
    if thread_file.exists():
        try:
            thread_data = json.load(open(thread_file))
            original_id = thread_data.get("message_id", "")
            if original_id:
                headers = {
                    "In-Reply-To": f"<{original_id}@resend.dev>",
                    "References": f"<{original_id}@resend.dev>",
                }
        except (json.JSONDecodeError, KeyError):
            pass

    email_payload = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "html": html,
    }
    if headers:
        email_payload["headers"] = headers

    try:
        result = resend.Emails.send(email_payload)
        email_id = result.get("id", "")
        logger.info(f"Confirmation sent to {to_email} (id: {email_id})")
        return {"status": "success", "email_id": email_id, "to": to_email}
    except Exception as e:
        logger.error(f"Confirmation email failed: {e}")
        return {"status": "failed", "error": str(e)}


def send_digest(config: dict, session_dir: str, summary: dict) -> dict:
    notif_config = config.get("notifications", {}).get("resend", {})

    api_key_env = notif_config.get("api_key_env", "RESEND_API_KEY")
    api_key = get_secret(api_key_env)
    if not api_key:
        return {"status": "failed", "error": f"{api_key_env} not set"}

    from_email = notif_config.get("from_email", "")
    to_email = notif_config.get("to_email", "")
    if not from_email or not to_email:
        return {"status": "failed", "error": "from_email or to_email not configured"}

    resend.api_key = api_key

    html = _build_html(config, session_dir, summary)
    subject = _build_subject(summary)

    email_payload = {
        "from": from_email,
        "to": [to_email],
        "reply_to": [to_email],
        "subject": subject,
        "html": html,
    }

    # Thread emails together: use stored message_id from first email
    thread_file = Path(session_dir) / "email_thread.json"
    if thread_file.exists():
        try:
            thread_data = json.load(open(thread_file))
            original_id = thread_data.get("message_id", "")
            if original_id:
                email_payload["headers"] = {
                    "In-Reply-To": f"<{original_id}@resend.dev>",
                    "References": f"<{original_id}@resend.dev>",
                }
                # Keep original subject for Gmail threading
                original_subject = thread_data.get("subject", "")
                if original_subject and not subject.startswith("Re:"):
                    email_payload["subject"] = f"Re: {original_subject}"
        except (json.JSONDecodeError, KeyError):
            pass

    try:
        result = resend.Emails.send(email_payload)
        email_id = result.get("id", "")
        logger.info(f"Email digest sent to {to_email} (id: {email_id})")

        # Save thread info on first email, preserve original on follow-ups
        if not thread_file.exists():
            thread_data = {
                "message_id": email_id,
                "subject": subject,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        else:
            thread_data = json.load(open(thread_file))
            thread_data["last_reply_id"] = email_id
            thread_data["last_reply_at"] = datetime.now(timezone.utc).isoformat()
            thread_data["reply_count"] = thread_data.get("reply_count", 0) + 1

        with open(thread_file, "w") as f:
            json.dump(thread_data, f, indent=2)

        return {"status": "success", "email_id": email_id, "to": to_email}
    except Exception as e:
        logger.error(f"Failed to send digest: {e}")
        return {"status": "failed", "error": str(e)}


def _build_subject(summary: dict) -> str:
    articles = len(summary.get("articles_staged", []))
    escalations = len(summary.get("escalations", []))
    date = datetime.now(timezone.utc).strftime("%b %d, %Y")

    session_dir = summary.get("session_dir", "")
    session_tag = ""
    import re as _re
    session_match = _re.search(r"session_\d{8}_\d{6}", session_dir)
    if session_match:
        session_tag = f" [{session_match.group(0)}]"

    if escalations > 0:
        return f"[Action Required] Content Agent — {articles} articles, {escalations} issues — {date}{session_tag}"
    elif articles > 0:
        return f"Content Agent — {articles} articles ready for review — {date}{session_tag}"
    else:
        return f"Content Agent — No new content — {date}{session_tag}"


def _markdown_to_html(md: str) -> str:
    """Convert markdown to styled HTML for email rendering."""
    lines = md.split("\n")
    result = []
    in_list = False
    list_type = None
    in_table = False
    table_rows = []

    def _close_list():
        nonlocal in_list, list_type
        if in_list:
            result.append(f"</{list_type}>")
            in_list = False
            list_type = None

    def _close_table():
        nonlocal in_table, table_rows
        if in_table and table_rows:
            table_html = '<table style="width:100%;border-collapse:collapse;margin:16px 0;font-size:14px;">'
            for row_idx, row in enumerate(table_rows):
                cells = [c.strip() for c in row.split("|")]
                cells = [c for c in cells if c != ""]
                tag = "th" if row_idx == 0 else "td"
                bg = "background:#f8f9fa;" if row_idx == 0 else ("background:#fafafa;" if row_idx % 2 == 0 else "")
                cell_style = f"padding:8px 12px;border:1px solid #e0e0e0;text-align:left;{bg}"
                header_extra = "font-weight:600;font-size:13px;text-transform:uppercase;color:#555;" if row_idx == 0 else ""
                row_html = "".join(f'<{tag} style="{cell_style}{header_extra}">{_inline(c)}</{tag}>' for c in cells)
                table_html += f"<tr>{row_html}</tr>"
            table_html += "</table>"
            result.append(table_html)
        in_table = False
        table_rows = []

    for line in lines:
        stripped = line.strip()

        # Table rows (detect | col | col | pattern)
        if re.match(r"^\|.*\|.*\|", stripped):
            _close_list()
            if not in_table:
                in_table = True
                table_rows = []
            if re.match(r"^\|[-:\s|]+\|$", stripped):
                continue
            table_rows.append(stripped)
            continue
        elif in_table:
            _close_table()

        # Unordered list
        if re.match(r"^[-*]\s", stripped):
            if in_table:
                _close_table()
            if not in_list or list_type != "ul":
                _close_list()
                result.append('<ul style="margin:8px 0;padding-left:24px;">')
                in_list = True
                list_type = "ul"
            item = re.sub(r"^[-*]\s", "", stripped)
            result.append(f'<li style="margin:4px 0;line-height:1.6;">{_inline(item)}</li>')
            continue

        # Ordered list
        if re.match(r"^\d+\.\s", stripped):
            if in_table:
                _close_table()
            if not in_list or list_type != "ol":
                _close_list()
                result.append('<ol style="margin:8px 0;padding-left:24px;">')
                in_list = True
                list_type = "ol"
            item = re.sub(r"^\d+\.\s", "", stripped)
            result.append(f'<li style="margin:4px 0;line-height:1.6;">{_inline(item)}</li>')
            continue

        _close_list()

        # Headings
        if stripped.startswith("### "):
            result.append(f'<h3 style="color:#444;font-size:16px;margin:20px 0 8px;border-bottom:1px solid #eee;padding-bottom:4px;">{_inline(stripped[4:])}</h3>')
        elif stripped.startswith("## "):
            result.append(f'<h2 style="color:#333;font-size:20px;margin:28px 0 12px;border-bottom:2px solid #e0e0e0;padding-bottom:6px;">{_inline(stripped[3:])}</h2>')
        elif stripped.startswith("# "):
            result.append(f'<h1 style="color:#1a1a2e;font-size:26px;margin:0 0 16px;">{_inline(stripped[2:])}</h1>')
        elif stripped == "---":
            result.append('<hr style="border:none;border-top:1px solid #e0e0e0;margin:20px 0;">')
        elif stripped == "":
            if result and not result[-1].endswith("<br>"):
                result.append("<br>")
        else:
            result.append(f'<p style="margin:6px 0;line-height:1.7;color:#333;">{_inline(stripped)}</p>')

    _close_list()
    _close_table()

    return "\n".join(result)


def _inline(text: str) -> str:
    """Process inline markdown: bold, italic, code, links."""
    t = _escape(text)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)
    t = re.sub(r"`([^`]+)`", r'<code style="background:#f0f0f0;padding:1px 4px;border-radius:3px;font-size:13px;">\1</code>', t)
    t = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r'<a href="\2" style="color:#2563eb;text-decoration:underline;">\1</a>',
        t,
    )
    return t


def _build_html(config: dict, session_dir: str, summary: dict) -> str:
    articles = summary.get("articles_staged", [])
    escalations = summary.get("escalations", [])
    package_requests = summary.get("package_requests", [])
    steps = summary.get("steps", {})

    social = steps.get("social_monitor", {})
    gaps = steps.get("gap_detection", {})
    gates = steps.get("quality_gates", {})

    sections = []

    # --- Header ---
    sections.append(f"""
    <div style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);padding:36px 32px;border-radius:16px;margin-bottom:28px;">
      <h1 style="color:#f0f0f0;margin:0;font-size:30px;font-weight:700;letter-spacing:-0.5px;">Content Agent</h1>
      <p style="color:#7f8c9b;margin:10px 0 0;font-size:15px;">Weekly Digest — {datetime.now(timezone.utc).strftime('%B %d, %Y')}</p>
      <div style="margin-top:16px;display:flex;gap:20px;">
        <div style="background:rgba(255,255,255,0.08);padding:12px 18px;border-radius:8px;">
          <div style="color:#7f8c9b;font-size:11px;text-transform:uppercase;letter-spacing:1px;">Articles</div>
          <div style="color:#f0f0f0;font-size:24px;font-weight:700;">{len(articles)}</div>
        </div>
        <div style="background:rgba(255,255,255,0.08);padding:12px 18px;border-radius:8px;">
          <div style="color:#7f8c9b;font-size:11px;text-transform:uppercase;letter-spacing:1px;">Signals</div>
          <div style="color:#f0f0f0;font-size:24px;font-weight:700;">{social.get('total_signals', 0)}</div>
        </div>
        <div style="background:rgba(255,255,255,0.08);padding:12px 18px;border-radius:8px;">
          <div style="color:#7f8c9b;font-size:11px;text-transform:uppercase;letter-spacing:1px;">Gaps Found</div>
          <div style="color:#f0f0f0;font-size:24px;font-weight:700;">{gaps.get('gaps_found', 0)}</div>
        </div>
      </div>
    </div>
    """)

    # --- Gap Detection Summary ---
    if gaps and gaps.get("analysis_summary"):
        sections.append(f"""
        <div style="background:#f0f7ff;padding:20px;border-radius:10px;margin-bottom:24px;border-left:4px solid #2563eb;">
          <h2 style="margin:0 0 8px;color:#1e40af;font-size:16px;">AI Analysis</h2>
          <p style="color:#555;margin:0;line-height:1.5;">{_escape(gaps['analysis_summary'])}</p>
        </div>
        """)

    # --- Articles for Review ---
    if articles:
        sections.append('<h2 style="color:#1a1a2e;margin:32px 0 20px;font-size:22px;">Articles for Review</h2>')

        # Reply instructions — adapt copy based on article count
        if len(articles) == 1:
            sections.append("""
        <div style="background:#f0f7ff;padding:18px 20px;border-radius:10px;margin-bottom:24px;border:1px solid #bfdbfe;">
          <h3 style="margin:0 0 10px;color:#1e40af;font-size:15px;">How to respond</h3>
          <p style="margin:0 0 8px;color:#555;font-size:14px;line-height:1.6;">
            Reply to this email with your decision:
          </p>
          <div style="background:white;padding:14px 16px;border-radius:6px;font-family:monospace;font-size:13px;color:#333;line-height:1.8;">
            <strong>Approve</strong> — publish to Framer as-is<br>
            <strong>Changes:</strong> fix the intro, add a pricing section, make it shorter<br>
            <strong>Reject:</strong> we already cover this topic
          </div>
          <p style="margin:10px 0 0;color:#888;font-size:12px;">
            The agent will apply your changes and send you a revised version. Approved articles get published to Framer.
          </p>
        </div>
        """)
        else:
            sections.append(f"""
        <div style="background:#f0f7ff;padding:18px 20px;border-radius:10px;margin-bottom:24px;border:1px solid #bfdbfe;">
          <h3 style="margin:0 0 10px;color:#1e40af;font-size:15px;">How to respond</h3>
          <p style="margin:0 0 8px;color:#555;font-size:14px;line-height:1.6;">
            Reply to this email with your decisions. You can handle all {len(articles)} articles in one reply:
          </p>
          <div style="background:white;padding:14px 16px;border-radius:6px;font-family:monospace;font-size:13px;color:#333;line-height:1.8;">
            <strong>Approve 1</strong><br>
            <strong>Article 2:</strong> fix the intro to be more engaging, add a section about pricing<br>
            <strong>Reject 3:</strong> we already cover this topic on the blog
          </div>
          <p style="margin:10px 0 0;color:#888;font-size:12px;">
            The agent will apply your changes and send you an updated email. Approved articles get published to Framer.
          </p>
        </div>
        """)

        # Load feedback history for revision details
        feedback_history = []
        history_path = Path(session_dir) / "feedback_history.json"
        if history_path.exists():
            try:
                feedback_history = json.load(open(history_path)).get("iterations", [])
            except (json.JSONDecodeError, KeyError):
                pass

        for i, article in enumerate(articles):
            article_content = ""
            article_file = article.get("article_file", "")
            if article_file:
                candidates = [
                    Path(session_dir) / article_file,
                    Path(article_file),
                    Path(session_dir) / ".." / article_file,
                ]
                for candidate in candidates:
                    if candidate.exists():
                        article_content = candidate.read_text(encoding="utf-8")
                        break

            priority_colors = {"high": ("#dc2626", "#fef2f2"), "medium": ("#d97706", "#fffbeb"), "low": ("#16a34a", "#f0fdf4")}
            p_color, p_bg = priority_colors.get(article.get("priority", "medium"), ("#d97706", "#fffbeb"))

            rich_html = _markdown_to_html(article_content)

            # Determine article status
            is_approved = article.get("approved", False)
            is_rejected = article.get("rejected", False)
            revision_count = article.get("revision_count", 0)

            if is_approved:
                status_badge = '<span style="background:#dcfce7;color:#16a34a;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600;text-transform:uppercase;">Approved</span>'
            elif is_rejected:
                status_badge = '<span style="background:#fef2f2;color:#dc2626;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600;text-transform:uppercase;">Rejected</span>'
            elif revision_count > 0:
                status_badge = f'<span style="background:#eff6ff;color:#2563eb;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600;text-transform:uppercase;">Revised (v{revision_count + 1})</span>'
            else:
                status_badge = '<span style="background:#f5f5f5;color:#888;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600;text-transform:uppercase;">New — v1</span>'

            # Build revision history for this article
            revision_html = ""
            if revision_count > 0 or is_approved or is_rejected:
                history_items = []

                history_items.append(
                    '<div style="padding:6px 0;color:#666;font-size:13px;">'
                    '<span style="color:#999;">v1</span> &mdash; Original draft generated by agent'
                    '</div>'
                )

                article_num = i + 1
                for iteration in feedback_history:
                    revised_in = iteration.get("revised", [])
                    approved_in = iteration.get("approved", [])
                    rejected_in = iteration.get("rejected", [])
                    timestamp = iteration.get("timestamp", "")
                    feedback = iteration.get("feedback", "")

                    if article_num in revised_in:
                        change_lines = [l.strip() for l in feedback.split("\n") if l.strip().lower().startswith(f"article {article_num}") or l.strip().lower().startswith(f"{article_num}:")]
                        change_desc = change_lines[0] if change_lines else "Changes requested"
                        change_desc = re.sub(r"^(?:article\s+)?\d+\s*[,:.\-—]\s*", "", change_desc, flags=re.IGNORECASE)
                        ts_short = timestamp[:16].replace("T", " ") if timestamp else ""
                        history_items.append(
                            f'<div style="padding:6px 0;color:#666;font-size:13px;border-top:1px solid #f0f0f0;">'
                            f'<span style="color:#2563eb;">v{len(history_items) + 1}</span> &mdash; '
                            f'<em>{_escape(change_desc)}</em>'
                            f'<span style="color:#bbb;margin-left:8px;font-size:11px;">{ts_short}</span>'
                            f'</div>'
                        )

                    if article_num in approved_in:
                        ts_short = timestamp[:16].replace("T", " ") if timestamp else ""
                        history_items.append(
                            f'<div style="padding:6px 0;color:#16a34a;font-size:13px;border-top:1px solid #f0f0f0;">'
                            f'&#10004; Approved'
                            f'<span style="color:#bbb;margin-left:8px;font-size:11px;">{ts_short}</span>'
                            f'</div>'
                        )

                    if article_num in rejected_in:
                        reason = article.get("rejection_reason", "")
                        ts_short = timestamp[:16].replace("T", " ") if timestamp else ""
                        history_items.append(
                            f'<div style="padding:6px 0;color:#dc2626;font-size:13px;border-top:1px solid #f0f0f0;">'
                            f'&#10008; Rejected: {_escape(reason)}'
                            f'<span style="color:#bbb;margin-left:8px;font-size:11px;">{ts_short}</span>'
                            f'</div>'
                        )

                revision_html = f"""
                <div style="padding:12px 24px;background:#fafbfc;border-bottom:1px solid #f0f0f0;">
                  <div style="font-size:12px;font-weight:600;color:#888;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Version History</div>
                  {''.join(history_items)}
                </div>
                """

            # Skip showing content for rejected articles
            if is_rejected:
                sections.append(f"""
                <div style="border:1px solid #fecaca;border-radius:14px;margin-bottom:32px;overflow:hidden;opacity:0.7;">
                  <div style="padding:20px 24px;background:#fef2f2;">
                    <h3 style="margin:0 0 8px;color:#1a1a2e;font-size:18px;">
                      Article {i + 1}: {_escape(article.get('prompt', 'Untitled'))}
                    </h3>
                    <div>{status_badge}</div>
                  </div>
                  {revision_html}
                </div>
                """)
                continue

            sections.append(f"""
            <div style="border:1px solid {'#bbf7d0' if is_approved else '#e0e0e0'};border-radius:14px;margin-bottom:32px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.04);">

              <!-- Article Header -->
              <div style="padding:20px 24px;border-bottom:1px solid #f0f0f0;background:{'#f0fdf4' if is_approved else '#fafafa'};">
                <h3 style="margin:0 0 8px;color:#1a1a2e;font-size:18px;">
                  Article {i + 1}: {_escape(article.get('prompt', 'Untitled'))}
                </h3>
                <div>
                  {status_badge}
                  <span style="background:{p_bg};color:{p_color};padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600;text-transform:uppercase;margin-left:6px;">
                    {article.get('priority', 'medium')} priority
                  </span>
                  <span style="color:#888;margin-left:14px;font-size:13px;">{article.get('word_count', 0):,} words</span>
                  <span style="color:#888;margin-left:14px;font-size:13px;">Gap score: {(1 - article.get('coverage_score', 0)):.0%}</span>
                </div>
              </div>

              <!-- Version History -->
              {revision_html}

              <!-- Article Content (Rich HTML, scrollable container) -->
              <div style="padding:24px 28px;max-height:500px;overflow-y:auto;background:white;font-family:Georgia,'Times New Roman',serif;font-size:15px;line-height:1.8;color:#333;border-top:1px solid #f0f0f0;border-bottom:1px solid #f0f0f0;">
                {rich_html}
              </div>

              <!-- Article action footer -->
              <div style="padding:14px 24px;background:#f8f9fa;border-top:1px solid #f0f0f0;">
                <p style="margin:0;color:#888;font-size:13px;text-align:center;">
                  {'&#10004; This article has been approved and will be published.' if is_approved else f'Article <strong>{i + 1}</strong> — Reply to this email with your decision'}
                </p>
              </div>
            </div>
            """)
    else:
        sections.append("""
        <div style="background:#f8f9fa;padding:24px;border-radius:10px;margin-bottom:24px;">
          <h2 style="margin:0 0 8px;color:#333;">No New Articles</h2>
          <p style="color:#666;">The brand already covers all topics detected in social signals. Nice.</p>
        </div>
        """)

    # --- Quality Gates ---
    if gates and gates.get("gates"):
        sections.append('<h2 style="color:#1a1a2e;margin:28px 0 16px;font-size:18px;">Quality Gates</h2>')
        for gate in gates["gates"]:
            passed = gate["passed"]
            icon = "&#10004;" if passed else "&#10008;"
            color = "#16a34a" if passed else "#dc2626"
            bg = "#f0fdf4" if passed else "#fef2f2"
            gate_name = gate["gate"].replace("_", " ").title()
            sections.append(f"""
            <div style="padding:12px 16px;background:{bg};border-left:4px solid {color};margin-bottom:6px;border-radius:0 6px 6px 0;">
              <span style="color:{color};font-weight:bold;font-size:16px;">{icon}</span>
              <strong style="margin-left:4px;">{_escape(gate_name)}</strong>
              <span style="color:#666;margin-left:8px;font-size:13px;">{_escape(gate.get('details', ''))}</span>
              <span style="float:right;color:#888;font-size:13px;">{gate.get('score', 0):.0%}</span>
            </div>
            """)

    # --- Escalations ---
    if escalations:
        real_escalations = [e for e in escalations if e.get("type") != "quality_gate"]
        if real_escalations:
            esc_items = "".join(
                f'<p style="margin:4px 0;color:#666;font-size:14px;">&bull; <strong>{_escape(e.get("type", ""))}</strong>: {_escape(e.get("details", e.get("error", "")))}</p>'
                for e in real_escalations
            )
            sections.append(f"""
            <div style="background:#fef2f2;padding:20px;border-radius:10px;margin:24px 0;border:1px solid #fecaca;">
              <h2 style="margin:0 0 12px;color:#dc2626;font-size:16px;">Escalations ({len(real_escalations)})</h2>
              {esc_items}
            </div>
            """)

    # --- Package Requests ---
    if package_requests:
        pkg_items = "".join(
            f'<p style="margin:6px 0;"><code style="background:#fff;padding:2px 6px;border-radius:3px;">{_escape(p.get("package", ""))}</code> &mdash; {_escape(p.get("reason", ""))}</p>'
            for p in package_requests
        )
        sections.append(f"""
        <div style="background:#fffbe6;padding:20px;border-radius:10px;margin:24px 0;border:1px solid #ffe58f;">
          <h2 style="margin:0 0 12px;color:#8b6914;font-size:16px;">Package Install Requests</h2>
          <p style="color:#666;font-size:13px;">The agent needs these packages. Reply with "APPROVE PACKAGE [name]" to allow installation on next run.</p>
          {pkg_items}
        </div>
        """)

    # --- Footer ---
    sections.append(f"""
    <div style="margin-top:36px;padding-top:20px;border-top:1px solid #e0e0e0;color:#999;font-size:12px;">
      <p style="margin:4px 0;">Session: <code>{_escape(session_dir)}</code></p>
      <p style="margin:4px 0;">Model: Claude Opus 4.6</p>
      <p style="margin:4px 0;">Generated by Autonomous Content Agent</p>
    </div>
    """)

    body = "\n".join(sections)

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,sans-serif;max-width:720px;margin:0 auto;padding:24px;color:#333;background:#ffffff;">
{body}
</body>
</html>"""


def _escape(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
