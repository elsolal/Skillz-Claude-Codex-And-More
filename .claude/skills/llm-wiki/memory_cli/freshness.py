"""Shared freshness policy for QMD collection status."""

from __future__ import annotations

from .contracts import FreshnessStatus
from .qmd_adapter import QmdCollectionStatus


QMD_FRESHNESS_WARNING_SECONDS = 24 * 60 * 60


def collection_freshness(collection: QmdCollectionStatus | None) -> FreshnessStatus:
    """Classify collection freshness with the same threshold used by doctor."""

    if collection is None:
        return FreshnessStatus.UNKNOWN
    if collection.age_seconds <= QMD_FRESHNESS_WARNING_SECONDS:
        return FreshnessStatus.FRESH
    return FreshnessStatus.STALE
