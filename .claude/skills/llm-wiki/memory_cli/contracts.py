"""Immutable public contracts for portable memory manifests."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Mapping


PUBLIC_SCHEMA_VERSION = 1
MANIFEST_SCHEMA_VERSION = 1


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


@dataclass(frozen=True, slots=True)
class GoldenPaths:
    visible_path: PurePosixPath
    quality_rubric: PurePosixPath


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
