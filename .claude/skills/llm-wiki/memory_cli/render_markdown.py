"""Shareable metadata-only Markdown rendering for weekly reports."""

from __future__ import annotations

import html
import re
from typing import NoReturn

from .receipts import WeeklyReportOutcome


_CONTENT_LABEL = re.compile(
    r"(?i)(?:^|[\s`])(?:prompt|query|response|snippet|transcript|body|content)\s*:"
)
_POSIX_ABSOLUTE = re.compile(r"(?<![:\w])/(?:[^\s`]+)")
_WINDOWS_ABSOLUTE = re.compile(r"\b[A-Za-z]:[\\/][^\s`]+")
_UNC_ABSOLUTE = re.compile(r"\\\\[^\\\s]+\\[^\\\s]+")
_SECRET = re.compile(
    r"(?:sk-(?:proj-)?[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|"
    r"AKIA[0-9A-Z]{16}|-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----|"
    r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)"
)


class ReportExportError(RuntimeError):
    exit_code = 50

    def __init__(self, *, code: str, message: str, correction: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.correction = correction

    def as_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "message": self.message,
            "correction": self.correction,
        }


def _privacy_error() -> NoReturn:
    raise ReportExportError(
        code="report_export_privacy_violation",
        message="The Markdown export contains material outside the metadata-only contract.",
        correction=(
            "Remove content-bearing fields, secrets and absolute paths before export."
        ),
    )


def scan_markdown_export(markdown: str) -> None:
    """Scan final serialized bytes, after all Markdown interpolation."""

    if any(
        pattern.search(markdown)
        for pattern in (
            _CONTENT_LABEL,
            _POSIX_ABSOLUTE,
            _WINDOWS_ABSOLUTE,
            _UNC_ABSOLUTE,
            _SECRET,
        )
    ):
        _privacy_error()


def _inline(value: object) -> str:
    printable = "".join(
        character if character.isprintable() else " " for character in str(value)
    )
    return (
        html.escape(printable, quote=False)
        .replace("`", "'")
        .replace("|", "\\|")
    )


def _code(value: object) -> str:
    return "".join(
        character if character.isprintable() else " " for character in str(value)
    ).replace("`", "'")


def _percentage(value: object) -> str:
    return "not measured" if value is None else f"{float(value):.1%}"


def render_weekly_report_markdown(outcome: WeeklyReportOutcome) -> str:
    data = outcome.data()
    efficiency = data["efficiency"]
    reliability = data["reliability"]
    funnel = data["usage_funnel"]
    quality = data["quality"]
    lines = [
        f"# Memory Weekly · {_inline(outcome.project_id)}",
        "",
        f"- Period: {_inline(outcome.period_start)} to {_inline(outcome.period_end)}",
        f"- Review budget: {data['review']['budget_minutes']} minutes",
        f"- Decisions: {data['review']['decision_count']} of {data['review']['cap']} maximum",
        "",
        "## Project aggregates",
        "",
        f"- Context events: {efficiency['context_events']}",
        (
            "- Estimated context tokens: "
            f"median {_inline(efficiency['estimated_context_tokens']['median'])}, "
            f"p95 {_inline(efficiency['estimated_context_tokens']['p95'])}"
        ),
        (
            "- Retrieval duration ms: "
            f"median {_inline(efficiency['duration_ms']['median'])}, "
            f"p95 {_inline(efficiency['duration_ms']['p95'])}"
        ),
        f"- Fallback rate: {reliability['fallback_rate']:.1%}",
        f"- Insufficiency rate: {reliability['insufficiency_rate']:.1%}",
        (
            "- Freshness: "
            f"{reliability['freshness']['fresh']} fresh, "
            f"{reliability['freshness']['stale']} stale, "
            f"{reliability['freshness']['unknown']} unknown"
        ),
        (
            "- Usage funnel: "
            f"{funnel['retrieved']} retrieved, {funnel['read']} read, "
            f"{funnel['used']} used, {funnel['cited']} cited"
        ),
    ]
    if quality is None:
        lines.append("- Quality: not measured this week")
    else:
        lines.extend(
            [
                f"- Golden retrieval: {_percentage(quality['retrieval_hit_rate'])}",
                (
                    "- Quality degradation: "
                    f"{_percentage(quality['quality_degradation'])}"
                ),
            ]
        )
    lines.extend(["", "## Decisions", ""])
    if not outcome.decisions:
        lines.append("Healthy · no human decision required this week.")
    for index, decision in enumerate(outcome.decisions, start=1):
        lines.extend(
            [
                (
                    f"### {index}. {_inline(decision['priority'])} · "
                    f"{_inline(str(decision['risk']).upper())} · "
                    f"{_inline(decision['category'])}"
                ),
                "",
                (
                    f"- Memory: {_inline(decision['memory']['docid'])} · "
                    f"{_inline(decision['memory']['path'])}"
                ),
                (
                    f"- Repository: {_inline(decision['repository']['path'])} · "
                    f"{_inline(decision['repository']['evidence_type'])}"
                ),
                f"- Observed impacts: {decision['observed_impact_count']}",
                "- Actions:",
                f"  - `{_code(decision['actions']['fix'])}`",
                f"  - `{_code(decision['actions']['ignore'])}`",
                f"  - `{_code(decision['actions']['snooze'])}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Appendix",
            "",
            f"- Additional debts: {outcome.appendix['remaining_count']}",
            f"- By risk: {_inline(outcome.appendix['by_risk'])}",
            f"- By category: {_inline(outcome.appendix['by_category'])}",
            "",
            "## Privacy",
            "",
            "- 0 prompts",
            "- 0 responses",
            "- 0 cross-project raw events",
            "",
        ]
    )
    markdown = "\n".join(lines)
    scan_markdown_export(markdown)
    return markdown
