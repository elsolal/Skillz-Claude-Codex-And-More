"""Immutable public contracts for portable memory manifests."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Mapping


PUBLIC_SCHEMA_VERSION = 1
MANIFEST_SCHEMA_VERSION = 1
DEFAULT_SUFFICIENCY_THRESHOLDS_VERSION = "qmd-0.9-v1"


class RetrievalMode(str, Enum):
    MINIMAL = "minimal"
    PROJECT = "project"
    HISTORICAL = "historical"


class SemanticRetrieval(str, Enum):
    EXPLICIT = "explicit"


class PrincipalRole(str, Enum):
    OWNER = "owner"
    COLLABORATOR = "collaborator"


class TaskCategory(str, Enum):
    BUG = "bug"
    ARCHITECTURE = "architecture"
    PRODUCT = "product"
    OPERATIONS = "operations"
    SECURITY = "security"
    DATA = "data"
    HISTORICAL = "historical"
    ONBOARDING = "onboarding"
    GENERAL = "general"


class FreshnessStatus(str, Enum):
    FRESH = "fresh"
    STALE = "stale"
    UNKNOWN = "unknown"


class ProvenanceKind(str, Enum):
    PAGE = "page"
    SOURCE = "source"
    SYNTHESIS = "synthesis"
    UNKNOWN = "unknown"


class SufficiencyStatus(str, Enum):
    SUFFICIENT = "sufficient"
    INSUFFICIENT = "insufficient"
    AMBIGUOUS = "ambiguous"
    BLOCKED = "blocked"


class SufficiencyReason(str, Enum):
    NO_RESULT = "no_result"
    BELOW_SCORE = "below_score"
    INSUFFICIENT_COVERAGE = "insufficient_coverage"
    STALE = "stale"
    MISSING_PROVENANCE = "missing_provenance"
    TASK_REQUIRES_TRANSVERSE = "task_requires_transverse"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True, slots=True)
class ProjectConfig:
    id: str
    name: str
    owner: str


@dataclass(frozen=True, slots=True)
class StoreConfig:
    remote: str
    collection: str
    entry_pages: tuple[PurePosixPath, ...]


@dataclass(frozen=True, slots=True)
class StoresConfig:
    project: StoreConfig


@dataclass(frozen=True, slots=True)
class FallbackConfig:
    id: str
    collection: str
    allowed_roles: tuple[PrincipalRole, ...]
    task_categories: tuple[TaskCategory, ...]
    entry_pages: tuple[PurePosixPath, ...]


@dataclass(frozen=True, slots=True)
class BudgetConfig:
    target_tokens: int
    hard_tokens: int


@dataclass(frozen=True, slots=True)
class PolicyConfig:
    semantic_retrieval: SemanticRetrieval
    full_index_fallback: bool
    retention_days: int
    sufficiency_thresholds_version: str


@dataclass(frozen=True, slots=True)
class GoldenPaths:
    visible_path: PurePosixPath
    quality_rubric: PurePosixPath
    start_question: str | None = None


@dataclass(frozen=True, slots=True)
class MemoryManifest:
    schema_version: int
    project: ProjectConfig
    stores: StoresConfig
    fallbacks: tuple[FallbackConfig, ...]
    budgets: Mapping[RetrievalMode, BudgetConfig]
    policy: PolicyConfig
    golden: GoldenPaths

    @classmethod
    def create(
        cls,
        *,
        schema_version: int,
        project: ProjectConfig,
        stores: StoresConfig,
        fallbacks: tuple[FallbackConfig, ...],
        budgets: dict[RetrievalMode, BudgetConfig],
        policy: PolicyConfig,
        golden: GoldenPaths,
    ) -> "MemoryManifest":
        return cls(
            schema_version=schema_version,
            project=project,
            stores=stores,
            fallbacks=fallbacks,
            budgets=MappingProxyType(dict(budgets)),
            policy=policy,
            golden=golden,
        )


@dataclass(frozen=True, slots=True)
class LocalStoreConfig:
    root: Path


@dataclass(frozen=True, slots=True)
class MemoryProjection:
    schema_version: int
    principal_role: PrincipalRole
    stores: Mapping[str, LocalStoreConfig]

    @classmethod
    def create(
        cls,
        *,
        principal_role: PrincipalRole,
        stores: dict[str, LocalStoreConfig],
    ) -> "MemoryProjection":
        return cls(
            schema_version=PUBLIC_SCHEMA_VERSION,
            principal_role=principal_role,
            stores=MappingProxyType(dict(stores)),
        )


@dataclass(frozen=True, slots=True)
class RetrievalHit:
    """Normalized QMD result kept independent from the external JSON shape."""

    docid: str
    collection: str
    relative_path: PurePosixPath
    title: str
    score: float
    snippet_line: int
    snippet: str


@dataclass(frozen=True, slots=True)
class SufficiencyHit:
    """Minimal normalized evidence consumed by the pure sufficiency gate."""

    docid: str
    score: float
    provenance: ProvenanceKind


@dataclass(frozen=True, slots=True)
class SufficiencyEvidence:
    mode: RetrievalMode
    task_category: TaskCategory
    hits: tuple[SufficiencyHit, ...]
    freshness: FreshnessStatus
    thresholds_version: str = DEFAULT_SUFFICIENCY_THRESHOLDS_VERSION


@dataclass(frozen=True, slots=True)
class SufficiencyDecision:
    status: SufficiencyStatus
    reason_codes: tuple[SufficiencyReason, ...]
    thresholds_version: str
    evidence: SufficiencyEvidence
