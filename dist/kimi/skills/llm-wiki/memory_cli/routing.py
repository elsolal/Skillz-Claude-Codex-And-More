"""Pure authorization helpers for project-first fallback routing."""

from __future__ import annotations

from .contracts import FallbackConfig, MemoryManifest, PrincipalRole, TaskCategory


def authorized_fallbacks(
    manifest: MemoryManifest,
    *,
    principal_role: PrincipalRole,
    task_category: TaskCategory,
) -> tuple[FallbackConfig, ...]:
    """Return only shared-policy fallbacks allowed for the local role and task."""

    return tuple(
        fallback
        for fallback in manifest.fallbacks
        if principal_role in fallback.allowed_roles
        and task_category in fallback.task_categories
    )
