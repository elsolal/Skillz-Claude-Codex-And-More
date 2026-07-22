"""Safe Markdown section materialization under visible context budgets."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Mapping, NoReturn

from .contracts import (
    AssemblyStatus,
    BudgetConfig,
    ContextAssembly,
    ContextSection,
    FreshnessStatus,
    ProvenanceKind,
    RetrievalHit,
    RetrievalMode,
    RiskReason,
    SufficiencyDecision,
    SufficiencyEvidence,
    SufficiencyHit,
    SufficiencyStatus,
    TaskCategory,
)
from .sufficiency import evaluate_sufficiency, provenance_for_path
from .tokens import ESTIMATOR_VERSION, estimate_tokens


SECTION_LIMITS: dict[RetrievalMode, int] = {
    RetrievalMode.MINIMAL: 1,
    RetrievalMode.PROJECT: 3,
    RetrievalMode.HISTORICAL: 6,
}
USEFUL_FRONTMATTER = {"title", "category", "summary", "tags", "sources", "updated"}
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


class DocumentAccessError(Exception):
    """A local document could not be mapped and opened inside its allowed root."""

    exit_code = 32

    def __init__(self, *, code: str, message: str, correction: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.correction = correction


def _access_error(*, code: str, message: str, correction: str) -> NoReturn:
    raise DocumentAccessError(code=code, message=message, correction=correction)


def section_limit_for(mode: RetrievalMode) -> int:
    return SECTION_LIMITS[mode]


def resolve_document(root: Path, relative_path: PurePosixPath) -> Path:
    """Resolve a QMD-relative path without allowing traversal or symlink escape."""

    raw_path = relative_path.as_posix()
    if (
        relative_path.is_absolute()
        or not relative_path.parts
        or "\\" in raw_path
        or any(part in {"", ".", ".."} for part in relative_path.parts)
    ):
        _access_error(
            code="document_outside_root",
            message="A retrieved document path falls outside its projected local root.",
            correction="Re-index the authorized collection and retry memory context.",
        )
    try:
        resolved_root = root.resolve(strict=True)
    except (OSError, RuntimeError):
        _access_error(
            code="document_root_unavailable",
            message="A projected collection root is unavailable.",
            correction="Restore the local vault or run memory configure again.",
        )
    if not resolved_root.is_dir() or not os.access(resolved_root, os.R_OK | os.X_OK):
        _access_error(
            code="document_root_unavailable",
            message="A projected collection root cannot be traversed safely.",
            correction="Restore read and traversal access to the local vault.",
        )

    candidates = (
        resolved_root.joinpath(*relative_path.parts),
        resolved_root.joinpath("wiki", *relative_path.parts),
    )
    for candidate in candidates:
        try:
            resolved = candidate.resolve(strict=True)
        except (OSError, RuntimeError):
            continue
        try:
            resolved.relative_to(resolved_root)
        except ValueError:
            _access_error(
                code="document_outside_root",
                message="A retrieved document resolves outside its projected local root.",
                correction="Remove the escaping symlink, update QMD, and retry.",
            )
        if not resolved.is_file() or not os.access(resolved, os.R_OK):
            _access_error(
                code="document_unavailable",
                message="A retrieved document is not a readable regular file.",
                correction="Restore the indexed page or update the QMD collection.",
            )
        return resolved

    _access_error(
        code="document_unavailable",
        message="A retrieved document is absent from its projected local root.",
        correction="Update the QMD collection or restore the missing page.",
    )


def _provenance(hit: RetrievalHit) -> ProvenanceKind:
    return provenance_for_path(hit.relative_path)


def _ranked_unique(hits: tuple[RetrievalHit, ...]) -> tuple[RetrievalHit, ...]:
    best_by_path: dict[tuple[str, PurePosixPath], tuple[int, RetrievalHit]] = {}
    for rank, hit in enumerate(hits):
        key = (hit.collection, hit.relative_path)
        current = best_by_path.get(key)
        if current is None or hit.score > current[1].score:
            best_by_path[key] = (rank, hit)
    confidence = {
        ProvenanceKind.SOURCE: 0,
        ProvenanceKind.SYNTHESIS: 1,
        ProvenanceKind.PAGE: 2,
        ProvenanceKind.UNKNOWN: 3,
    }
    return tuple(
        item[1]
        for item in sorted(
            best_by_path.values(),
            key=lambda item: (
                confidence[_provenance(item[1])],
                -item[1].score,
                item[0],
            ),
        )
    )


def _frontmatter(lines: list[str]) -> tuple[dict[str, str], int]:
    if not lines or lines[0].strip() != "---":
        return {}, 0
    try:
        closing = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        return {}, 0
    values: dict[str, str] = {}
    for line in lines[1:closing]:
        key, separator, value = line.partition(":")
        normalized_key = key.strip()
        if separator and normalized_key in USEFUL_FRONTMATTER:
            values[normalized_key] = value.strip().strip("\"'")
    return values, closing + 1


@dataclass(frozen=True, slots=True)
class _Paragraph:
    content: str
    line_start: int
    line_end: int


@dataclass(frozen=True, slots=True)
class _ExtractedSection:
    title: str
    provenance: ProvenanceKind
    frontmatter: dict[str, str]
    paragraphs: tuple[_Paragraph, ...]
    essential_index: int


def _section_bounds(lines: list[str], *, snippet_line: int, body_start: int) -> tuple[int, int]:
    if snippet_line < 1 or snippet_line > len(lines):
        _access_error(
            code="document_line_unavailable",
            message="A retrieved snippet line is outside the current local document.",
            correction="Update the QMD collection and retry memory context.",
        )
    snippet_index = snippet_line - 1
    heading_index: int | None = None
    heading_level: int | None = None
    for index in range(snippet_index, body_start - 1, -1):
        match = HEADING_PATTERN.match(lines[index])
        if match is not None:
            heading_index = index
            heading_level = len(match.group(1))
            break
    start = heading_index if heading_index is not None else body_start
    end = len(lines)
    if heading_level is not None:
        for index in range(start + 1, len(lines)):
            match = HEADING_PATTERN.match(lines[index])
            if match is not None and len(match.group(1)) <= heading_level:
                end = index
                break
    return start, end


def _paragraphs(lines: list[str], *, offset: int) -> tuple[_Paragraph, ...]:
    result: list[_Paragraph] = []
    start: int | None = None
    content: list[str] = []
    for local_index, line in enumerate(lines):
        if line.strip():
            if start is None:
                start = local_index
            content.append(line)
            continue
        if start is not None:
            result.append(
                _Paragraph(
                    content="\n".join(content),
                    line_start=offset + start + 1,
                    line_end=offset + local_index,
                )
            )
            start = None
            content = []
    if start is not None:
        result.append(
            _Paragraph(
                content="\n".join(content),
                line_start=offset + start + 1,
                line_end=offset + len(lines),
            )
        )
    return tuple(result)


def _extract_section(hit: RetrievalHit, path: Path) -> _ExtractedSection:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        _access_error(
            code="document_unavailable",
            message="A retrieved document could not be read as UTF-8 Markdown.",
            correction="Repair the indexed page encoding and update QMD.",
        )
    lines = text.splitlines()
    frontmatter, body_start = _frontmatter(lines)
    start, end = _section_bounds(
        lines,
        snippet_line=hit.snippet_line,
        body_start=body_start,
    )
    paragraphs = _paragraphs(lines[start:end], offset=start)
    if not paragraphs:
        _access_error(
            code="document_section_empty",
            message="A retrieved document has no readable Markdown section at the hit.",
            correction="Update the page content and re-index the QMD collection.",
        )
    essential_index = min(
        range(len(paragraphs)),
        key=lambda index: (
            0
            if paragraphs[index].line_start <= hit.snippet_line <= paragraphs[index].line_end
            else min(
                abs(paragraphs[index].line_start - hit.snippet_line),
                abs(paragraphs[index].line_end - hit.snippet_line),
            )
        ),
    )
    return _ExtractedSection(
        title=frontmatter.get("title", hit.title),
        provenance=_provenance(hit),
        frontmatter=frontmatter,
        paragraphs=paragraphs,
        essential_index=essential_index,
    )


def _render_paragraphs(paragraphs: tuple[_Paragraph, ...], indices: set[int]) -> str:
    return "\n\n".join(
        paragraph.content
        for index, paragraph in enumerate(paragraphs)
        if index in indices
    ).strip() + "\n"


def _fit_section(
    extracted: _ExtractedSection,
    *,
    current_tokens: int,
    budget: BudgetConfig,
    risk_reason: RiskReason | None,
) -> tuple[str, int, int, bool, bool] | None:
    mandatory = {extracted.essential_index}
    if HEADING_PATTERN.match(extracted.paragraphs[0].content):
        mandatory.add(0)
    content = _render_paragraphs(extracted.paragraphs, mandatory)
    tokens = estimate_tokens(content)
    if current_tokens + tokens > budget.hard_tokens and risk_reason is None:
        return None

    selected = set(mandatory)
    if current_tokens + tokens <= budget.target_tokens:
        for index in range(len(extracted.paragraphs)):
            if index in selected:
                continue
            candidate_indices = selected | {index}
            candidate = _render_paragraphs(extracted.paragraphs, candidate_indices)
            candidate_tokens = estimate_tokens(candidate)
            if current_tokens + candidate_tokens <= budget.target_tokens:
                selected = candidate_indices
                content = candidate
                tokens = candidate_tokens
    selected_paragraphs = [extracted.paragraphs[index] for index in sorted(selected)]
    return (
        content,
        min(paragraph.line_start for paragraph in selected_paragraphs),
        max(paragraph.line_end for paragraph in selected_paragraphs),
        len(selected) < len(extracted.paragraphs),
        current_tokens + tokens > budget.hard_tokens,
    )


def _decision(
    hits: tuple[RetrievalHit, ...],
    *,
    mode: RetrievalMode,
    task_category: TaskCategory,
    freshness: FreshnessStatus,
    thresholds_version: str,
) -> SufficiencyDecision:
    return evaluate_sufficiency(
        SufficiencyEvidence(
            mode=mode,
            task_category=task_category,
            hits=tuple(
                SufficiencyHit(
                    docid=hit.docid,
                    score=hit.score,
                    provenance=_provenance(hit),
                )
                for hit in hits
            ),
            freshness=freshness,
            thresholds_version=thresholds_version,
        )
    )


def assemble_context(
    hits: tuple[RetrievalHit, ...],
    *,
    mode: RetrievalMode,
    task_category: TaskCategory,
    freshness: FreshnessStatus,
    thresholds_version: str,
    budget: BudgetConfig,
    collection_roots: Mapping[str, Path],
    risk_reason: RiskReason | None = None,
) -> ContextAssembly:
    """Materialize only the sections required to make selected evidence sufficient."""

    retrieved = _ranked_unique(hits)
    selected_hits: list[RetrievalHit] = []
    sections: list[ContextSection] = []
    estimated_tokens = 0
    hard_cap_exceeded = False
    decision = _decision(
        (),
        mode=mode,
        task_category=task_category,
        freshness=freshness,
        thresholds_version=thresholds_version,
    )
    reason_codes: tuple[str, ...] = ()

    for hit in retrieved:
        if decision.status is SufficiencyStatus.SUFFICIENT:
            break
        if len(sections) >= section_limit_for(mode):
            reason_codes = ("section_limit_reached",)
            break
        root = collection_roots.get(hit.collection)
        if root is None:
            _access_error(
                code="document_root_unmapped",
                message="A retrieved collection has no authorized local root projection.",
                correction="Run memory configure with the manifest fallback store, then retry.",
            )
        path = resolve_document(root, hit.relative_path)
        extracted = _extract_section(hit, path)
        fitted = _fit_section(
            extracted,
            current_tokens=estimated_tokens,
            budget=budget,
            risk_reason=risk_reason,
        )
        if fitted is None:
            reason_codes = ("hard_cap_reached",)
            break
        content, line_start, line_end, truncated, exceeded = fitted
        section_tokens = estimate_tokens(content)
        sections.append(
            ContextSection.create(
                docid=hit.docid,
                collection=hit.collection,
                relative_path=hit.relative_path,
                title=extracted.title,
                provenance=extracted.provenance,
                line_start=line_start,
                line_end=line_end,
                frontmatter=extracted.frontmatter,
                content=content,
                estimated_tokens=section_tokens,
                truncated=truncated,
            )
        )
        selected_hits.append(hit)
        estimated_tokens += section_tokens
        hard_cap_exceeded = hard_cap_exceeded or exceeded
        decision = _decision(
            tuple(selected_hits),
            mode=mode,
            task_category=task_category,
            freshness=freshness,
            thresholds_version=thresholds_version,
        )

    if decision.status is SufficiencyStatus.SUFFICIENT:
        status = AssemblyStatus.READY
    elif sections:
        status = AssemblyStatus.PARTIAL
        if not reason_codes:
            reason_codes = tuple(reason.value for reason in decision.reason_codes)
    else:
        status = AssemblyStatus.PARTIAL if reason_codes else AssemblyStatus.INSUFFICIENT
        if not reason_codes:
            reason_codes = tuple(reason.value for reason in decision.reason_codes)

    return ContextAssembly(
        status=status,
        decision=decision,
        retrieved=retrieved,
        sections=tuple(sections),
        estimator_version=ESTIMATOR_VERSION,
        target_tokens=budget.target_tokens,
        hard_tokens=budget.hard_tokens,
        estimated_tokens=estimated_tokens,
        hard_cap_exceeded=hard_cap_exceeded,
        risk_reason=risk_reason if hard_cap_exceeded else None,
        reason_codes=reason_codes,
    )
