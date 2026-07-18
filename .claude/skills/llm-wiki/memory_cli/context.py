"""Project-first lexical retrieval for the portable memory CLI."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import RetrievalHit, RetrievalMode, TaskCategory
from .manifest import discover_manifest, load_manifest
from .projection import load_projection
from .qmd_adapter import (
    DEFAULT_SEARCH_TIMEOUT_SECONDS,
    QmdInvocationError,
    QmdOutputError,
    QmdSearchStatus,
    QmdTimeoutError,
    Runner,
    search_qmd,
)


MODE_SEARCH_CONFIG: dict[RetrievalMode, tuple[int, float]] = {
    RetrievalMode.MINIMAL: (3, 0.70),
    RetrievalMode.PROJECT: (8, 0.55),
    RetrievalMode.HISTORICAL: (15, 0.45),
}
QMD_INSTALL_COMMAND = "bun install -g @tobilu/qmd"


@dataclass(frozen=True, slots=True)
class ContextOutcome:
    status: str
    exit_code: int
    project_id: str
    mode: RetrievalMode
    task_category: TaskCategory
    route: tuple[str, ...]
    retrieval_status: QmdSearchStatus
    duration_ms: int | None
    hits: tuple[RetrievalHit, ...]
    warnings: tuple[dict[str, Any], ...] = ()
    errors: tuple[dict[str, Any], ...] = ()

    def data(self) -> dict[str, Any]:
        retrieval: dict[str, Any] = {
            "status": self.retrieval_status.value,
            "hits": [
                {
                    "docid": hit.docid,
                    "collection": hit.collection,
                    "path": hit.relative_path.as_posix(),
                    "title": hit.title,
                    "score": hit.score,
                    "snippet_line": hit.snippet_line,
                }
                for hit in self.hits
            ],
        }
        if self.duration_ms is not None:
            retrieval["duration_ms"] = self.duration_ms
        return {
            "mode": self.mode.value,
            "task_category": self.task_category.value,
            "route": list(self.route),
            "retrieval": retrieval,
        }


def _qmd_executable() -> str | None:
    override = os.environ.get("SKILLZ_MEMORY_QMD")
    if override is None:
        return shutil.which("qmd")
    candidate = Path(override)
    if not candidate.is_file() or not os.access(candidate, os.X_OK):
        return None
    return override


def _blocked(
    *,
    project_id: str,
    mode: RetrievalMode,
    task_category: TaskCategory,
    route: tuple[str, ...],
    retrieval_status: QmdSearchStatus,
    code: str,
    message: str,
    correction: str,
    exit_code: int,
) -> ContextOutcome:
    return ContextOutcome(
        status="blocked",
        exit_code=exit_code,
        project_id=project_id,
        mode=mode,
        task_category=task_category,
        route=route,
        retrieval_status=retrieval_status,
        duration_ms=None,
        hits=(),
        errors=(
            {
                "code": code,
                "message": message,
                "correction": correction,
            },
        ),
    )


def run_context(
    *,
    mode: RetrievalMode,
    task_category: TaskCategory,
    query: str,
    runner: Runner = subprocess.run,
    timeout_seconds: float = DEFAULT_SEARCH_TIMEOUT_SECONDS,
) -> ContextOutcome:
    """Execute only the first project route; sufficiency and fallback land later."""

    manifest_path = discover_manifest()
    manifest = load_manifest(manifest_path)
    load_projection(manifest_path)
    route = (manifest.stores.project.collection,)
    executable = _qmd_executable()
    if executable is None:
        return _blocked(
            project_id=manifest.project.id,
            mode=mode,
            task_category=task_category,
            route=route,
            retrieval_status=QmdSearchStatus.ERROR,
            code="qmd_missing",
            message="QMD is required for project retrieval but is unavailable.",
            correction=QMD_INSTALL_COMMAND,
            exit_code=31,
        )

    limit, min_score = MODE_SEARCH_CONFIG[mode]
    try:
        retrieval = search_qmd(
            executable,
            query=query,
            collection=route[0],
            limit=limit,
            min_score=min_score,
            runner=runner,
            timeout_seconds=timeout_seconds,
        )
    except QmdTimeoutError:
        return _blocked(
            project_id=manifest.project.id,
            mode=mode,
            task_category=task_category,
            route=route,
            retrieval_status=QmdSearchStatus.TIMEOUT,
            code="qmd_timeout",
            message="The project QMD search exceeded its bounded timeout.",
            correction="Retry memory context or run memory doctor.",
            exit_code=40,
        )
    except QmdOutputError:
        return _blocked(
            project_id=manifest.project.id,
            mode=mode,
            task_category=task_category,
            route=route,
            retrieval_status=QmdSearchStatus.INVALID,
            code="qmd_invalid_output",
            message="The project QMD search returned an unsupported result.",
            correction="Repair or update QMD 0.9.x, then run memory doctor.",
            exit_code=40,
        )
    except QmdInvocationError:
        return _blocked(
            project_id=manifest.project.id,
            mode=mode,
            task_category=task_category,
            route=route,
            retrieval_status=QmdSearchStatus.ERROR,
            code="qmd_search_failed",
            message="The project QMD search failed.",
            correction="Run memory doctor, then retry the context command.",
            exit_code=40,
        )

    if retrieval.status is QmdSearchStatus.EMPTY:
        return ContextOutcome(
            status="insufficient",
            exit_code=20,
            project_id=manifest.project.id,
            mode=mode,
            task_category=task_category,
            route=route,
            retrieval_status=retrieval.status,
            duration_ms=retrieval.duration_ms,
            hits=(),
            warnings=(
                {
                    "code": "no_result",
                    "message": "The project QMD search returned no result.",
                    "correction": "Refine the query or inspect project entry pages.",
                },
            ),
        )
    return ContextOutcome(
        status="ready",
        exit_code=0,
        project_id=manifest.project.id,
        mode=mode,
        task_category=task_category,
        route=route,
        retrieval_status=retrieval.status,
        duration_ms=retrieval.duration_ms,
        hits=retrieval.hits,
    )
