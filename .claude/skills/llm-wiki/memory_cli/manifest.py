"""Discovery, strict parsing, and semantic validation for manifest V1."""

from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath
from typing import Any, NoReturn
from urllib.parse import urlsplit

from .contracts import (
    MANIFEST_SCHEMA_VERSION,
    BudgetConfig,
    FallbackConfig,
    GoldenPaths,
    MemoryManifest,
    PolicyConfig,
    PrincipalRole,
    ProjectConfig,
    RetrievalMode,
    SemanticRetrieval,
    StoreConfig,
    StoresConfig,
    TaskCategory,
)


ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")
WINDOWS_ABSOLUTE_PATTERN = re.compile(r"^[A-Za-z]:[/\\]")
INTERPOLATION_MARKERS = ("${", "$(", "`")
SCP_REMOTE_PATTERN = re.compile(r"^git@[A-Za-z0-9.-]+:[A-Za-z0-9._/-]+(?:\.git)?$")


class ManifestError(Exception):
    """A stable, user-correctable manifest failure."""

    exit_code = 30

    def __init__(self, *, code: str, field: str, message: str, correction: str) -> None:
        super().__init__(message)
        self.code = code
        self.field = field
        self.message = message
        self.correction = correction

    def as_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "field": self.field,
            "message": self.message,
            "correction": self.correction,
        }


def _error(*, code: str, field: str, message: str, correction: str) -> NoReturn:
    raise ManifestError(code=code, field=field, message=message, correction=correction)


def _git_root(start: Path) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    _error(
        code="git_root_not_found",
        field="cwd",
        message="The current directory is not inside a Git repository.",
        correction="Run the command from a Git repository containing .agents/memory.yaml.",
    )


def discover_manifest(start: Path | str | None = None) -> Path:
    """Find the nearest manifest while remaining inside the current Git root."""

    current = Path.cwd() if start is None else Path(start)
    current = current.resolve()
    if current.is_file():
        current = current.parent
    git_root = _git_root(current)

    candidate = current
    while True:
        manifest_path = candidate / ".agents" / "memory.yaml"
        if manifest_path.is_file():
            return manifest_path
        if candidate == git_root:
            break
        candidate = candidate.parent

    _error(
        code="manifest_not_found",
        field=".agents/memory.yaml",
        message="No memory manifest was found inside Git root.",
        correction='Create ".agents/memory.yaml" inside the current Git repository.',
    )


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _error(
                code="duplicate_key",
                field=key,
                message=f'Manifest key "{key}" is declared more than once.',
                correction=f'Keep exactly one "{key}" key.',
            )
        result[key] = value
    return result


def _reject_json_constant(value: str) -> NoReturn:
    _error(
        code="invalid_json_constant",
        field="manifest",
        message=f'Non-standard JSON constant "{value}" is not allowed in manifest V1.',
        correction="Replace NaN and Infinity with a finite JSON number or a documented null value.",
    )


def _parse_json(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        _error(
            code="manifest_unreadable",
            field=".agents/memory.yaml",
            message="The manifest cannot be read safely.",
            correction="Check that the manifest exists and is readable by the current user.",
        )
    try:
        payload = json.loads(
            raw,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
    except ManifestError:
        raise
    except (UnicodeError, json.JSONDecodeError) as exc:
        location = ""
        if isinstance(exc, json.JSONDecodeError):
            location = f" at line {exc.lineno}, column {exc.colno}"
        _error(
            code="manifest_not_json_compatible",
            field="manifest",
            message=f"Manifest V1 is not valid JSON-compatible YAML{location}.",
            correction="Rewrite the file as JSON-compatible YAML: quote keys and strings, and remove tags, comments, includes, and YAML-only syntax.",
        )
    if not isinstance(payload, dict):
        _error(
            code="invalid_type",
            field="manifest",
            message="Manifest V1 must be a JSON object.",
            correction="Wrap the manifest fields in a single JSON object: { ... }.",
        )
    return payload


def _object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _error(
            code="invalid_type",
            field=field,
            message=f'Field "{field}" must be an object.',
            correction=f'Set "{field}" to a JSON object: {{ ... }}.',
        )
    return value


def _exact_keys(
    value: dict[str, Any],
    field: str,
    *,
    required: set[str],
    optional: set[str] | None = None,
) -> None:
    optional = optional or set()
    allowed = required | optional
    unknown = sorted(set(value) - allowed)
    if unknown:
        unknown_field = f"{field}.{unknown[0]}" if field else unknown[0]
        _error(
            code="unknown_key",
            field=unknown_field,
            message=f'Field "{unknown_field}" is not allowed in manifest V1.',
            correction=f'Remove the unknown key. Allowed keys: {", ".join(sorted(allowed))}.',
        )
    missing = sorted(required - set(value))
    if missing:
        missing_field = f"{field}.{missing[0]}" if field else missing[0]
        _error(
            code="missing_key",
            field=missing_field,
            message=f'Required field "{missing_field}" is missing.',
            correction=f'Add the required "{missing[0]}" field.',
        )


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _error(
            code="invalid_type",
            field=field,
            message=f'Field "{field}" must be a non-empty string.',
            correction=f'Set "{field}" to a non-empty quoted string.',
        )
    if any(marker in value for marker in INTERPOLATION_MARKERS):
        _error(
            code="interpolation_forbidden",
            field=field,
            message=f'Field "{field}" contains shell interpolation syntax.',
            correction="Replace interpolation with a literal portable value; ${...}, $(...), and backticks are forbidden.",
        )
    return value


def _start_question(value: Any) -> str:
    question = _string(value, "golden.start_question")
    if len(question) > 500 or any(ord(character) < 32 for character in question):
        _error(
            code="invalid_start_question",
            field="golden.start_question",
            message=(
                'Field "golden.start_question" must be a single-line question '
                "of at most 500 characters."
            ),
            correction=(
                "Use one concise, single-line golden start question without "
                "control characters."
            ),
        )
    return question


def _identifier(value: Any, field: str) -> str:
    identifier = _string(value, field)
    if not ID_PATTERN.fullmatch(identifier):
        _error(
            code="invalid_id",
            field=field,
            message=f'Field "{field}" is not a valid portable identifier.',
            correction=f'Set "{field}" to lowercase kebab-case matching ^[a-z0-9][a-z0-9-]{{1,62}}$.',
        )
    return identifier


def _relative_path(value: Any, field: str) -> PurePosixPath:
    raw_path = _string(value, field)
    path = PurePosixPath(raw_path)
    if path.is_absolute() or WINDOWS_ABSOLUTE_PATTERN.match(raw_path) or raw_path.startswith("~"):
        _error(
            code="absolute_path_forbidden",
            field=field,
            message=f'Field "{field}" contains an absolute or machine-local path.',
            correction=f'Set "{field}" to a relative path such as "wiki/entities/project.md".',
        )
    if "\\" in raw_path:
        _error(
            code="non_portable_path",
            field=field,
            message=f'Field "{field}" uses a platform-specific path separator.',
            correction=f'Set "{field}" to a portable relative path using "/" separators.',
        )
    if "://" in raw_path or any(ord(character) < 32 for character in raw_path):
        _error(
            code="non_portable_path",
            field=field,
            message=f'Field "{field}" is not a portable filesystem path.',
            correction=f'Set "{field}" to a relative repository or vault path, not a URL or control sequence.',
        )
    if ".." in path.parts:
        _error(
            code="path_traversal",
            field=field,
            message=f'Field "{field}" contains parent traversal.',
            correction=f'Remove traversal from "{field}" and keep the path inside its declared store.',
        )
    return path


def _path_list(value: Any, field: str, *, allow_empty: bool = False) -> tuple[PurePosixPath, ...]:
    if not isinstance(value, list) or (not value and not allow_empty):
        _error(
            code="invalid_type",
            field=field,
            message=f'Field "{field}" must be a non-empty array of relative paths.',
            correction=f'Set "{field}" to an array such as ["wiki/entities/project.md"].',
        )
    return tuple(_relative_path(item, f"{field}.{index}") for index, item in enumerate(value))


def _enum_list(value: Any, field: str, enum_type: type[Any]) -> tuple[Any, ...]:
    if not isinstance(value, list) or not value:
        _error(
            code="invalid_type",
            field=field,
            message=f'Field "{field}" must be a non-empty array.',
            correction=f'Set "{field}" to a non-empty array of allowed values.',
        )
    allowed = [member.value for member in enum_type]
    result = []
    for index, item in enumerate(value):
        if item not in allowed:
            _error(
                code="invalid_enum",
                field=f"{field}.{index}",
                message=f'Value "{item}" is not allowed for "{field}".',
                correction=f'Use one of: {", ".join(allowed)}.',
            )
        result.append(enum_type(item))
    return tuple(result)


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        _error(
            code="invalid_integer",
            field=field,
            message=f'Field "{field}" must be a positive integer.',
            correction=f'Set "{field}" to a positive integer without quotes.',
        )
    return value


def _store(value: Any, field: str) -> StoreConfig:
    data = _object(value, field)
    _exact_keys(data, field, required={"remote", "collection", "entry_pages"})
    remote = _string(data["remote"], f"{field}.remote")
    parsed_remote = urlsplit(remote)
    no_unsafe_characters = not any(
        character.isspace() or ord(character) < 32 for character in remote
    )
    valid_url_remote = bool(parsed_remote.hostname) and no_unsafe_characters and (
        (
            parsed_remote.scheme == "https"
            and parsed_remote.username is None
            and parsed_remote.password is None
        )
        or (parsed_remote.scheme == "ssh" and parsed_remote.password is None)
    )
    if not valid_url_remote and not SCP_REMOTE_PATTERN.fullmatch(remote):
        _error(
            code="invalid_remote",
            field=f"{field}.remote",
            message="The memory remote must use an explicit Git transport.",
            correction=f'Set "{field}.remote" to an https://, ssh://, or git@ Git remote without credentials or whitespace.',
        )
    return StoreConfig(
        remote=remote,
        collection=_identifier(data["collection"], f"{field}.collection"),
        entry_pages=_path_list(data["entry_pages"], f"{field}.entry_pages"),
    )


def _fallback(value: Any, index: int) -> FallbackConfig:
    field = f"fallbacks.{index}"
    data = _object(value, field)
    _exact_keys(
        data,
        field,
        required={"id", "collection", "allowed_roles", "task_categories"},
        optional={"entry_pages"},
    )
    return FallbackConfig(
        id=_identifier(data["id"], f"{field}.id"),
        collection=_identifier(data["collection"], f"{field}.collection"),
        allowed_roles=_enum_list(data["allowed_roles"], f"{field}.allowed_roles", PrincipalRole),
        task_categories=_enum_list(data["task_categories"], f"{field}.task_categories", TaskCategory),
        entry_pages=_path_list(data.get("entry_pages", []), f"{field}.entry_pages", allow_empty=True),
    )


def _budget(value: Any, field: str) -> BudgetConfig:
    data = _object(value, field)
    _exact_keys(data, field, required={"target_tokens", "hard_tokens"})
    target = _positive_int(data["target_tokens"], f"{field}.target_tokens")
    hard = _positive_int(data["hard_tokens"], f"{field}.hard_tokens")
    if target > hard:
        _error(
            code="invalid_budget",
            field=field,
            message=f'Budget "{field}" has target_tokens above hard_tokens.',
            correction=f'Set "{field}.target_tokens" to a value less than or equal to "{field}.hard_tokens".',
        )
    return BudgetConfig(target_tokens=target, hard_tokens=hard)


def _build_manifest(payload: dict[str, Any]) -> MemoryManifest:
    if "schema_version" not in payload:
        _error(
            code="missing_key",
            field="schema_version",
            message='Required field "schema_version" is missing.',
            correction='Add "schema_version": 1 as the first manifest field.',
        )
    version = payload["schema_version"]
    if isinstance(version, bool) or not isinstance(version, int) or version != MANIFEST_SCHEMA_VERSION:
        _error(
            code="unsupported_schema_version",
            field="schema_version",
            message=f'Manifest schema version "{version}" is not supported.',
            correction='Set "schema_version" to 1 and migrate incompatible fields before retrying.',
        )

    _exact_keys(
        payload,
        "",
        required={"schema_version", "project", "stores", "fallbacks", "budgets", "policy", "golden"},
    )

    project_data = _object(payload["project"], "project")
    _exact_keys(project_data, "project", required={"id", "name", "owner"})
    project = ProjectConfig(
        id=_identifier(project_data["id"], "project.id"),
        name=_string(project_data["name"], "project.name"),
        owner=_string(project_data["owner"], "project.owner"),
    )

    stores_data = _object(payload["stores"], "stores")
    _exact_keys(stores_data, "stores", required={"project"})
    stores = StoresConfig(project=_store(stores_data["project"], "stores.project"))

    fallbacks_data = payload["fallbacks"]
    if not isinstance(fallbacks_data, list):
        _error(
            code="invalid_type",
            field="fallbacks",
            message='Field "fallbacks" must be an array.',
            correction='Set "fallbacks" to [] or an array of fallback objects.',
        )
    fallbacks = tuple(_fallback(value, index) for index, value in enumerate(fallbacks_data))
    fallback_ids = [fallback.id for fallback in fallbacks]
    if len(set(fallback_ids)) != len(fallback_ids):
        _error(
            code="duplicate_id",
            field="fallbacks",
            message="Fallback IDs must be unique.",
            correction="Rename duplicate fallback IDs so each fallback has a unique lowercase kebab-case ID.",
        )

    budgets_data = _object(payload["budgets"], "budgets")
    mode_names = {mode.value for mode in RetrievalMode}
    _exact_keys(budgets_data, "budgets", required=mode_names)
    budgets = {
        mode: _budget(budgets_data[mode.value], f"budgets.{mode.value}")
        for mode in RetrievalMode
    }

    policy_data = _object(payload["policy"], "policy")
    _exact_keys(
        policy_data,
        "policy",
        required={"semantic_retrieval", "full_index_fallback", "retention_days"},
    )
    semantic_value = _string(policy_data["semantic_retrieval"], "policy.semantic_retrieval")
    if semantic_value not in {member.value for member in SemanticRetrieval}:
        _error(
            code="invalid_enum",
            field="policy.semantic_retrieval",
            message=f'Semantic retrieval mode "{semantic_value}" is not supported in V1.',
            correction='Set "policy.semantic_retrieval" to "explicit".',
        )
    full_index_fallback = policy_data["full_index_fallback"]
    if not isinstance(full_index_fallback, bool):
        _error(
            code="invalid_type",
            field="policy.full_index_fallback",
            message='Field "policy.full_index_fallback" must be a boolean.',
            correction='Set "policy.full_index_fallback" to true or false without quotes.',
        )
    retention_days = _positive_int(policy_data["retention_days"], "policy.retention_days")
    policy = PolicyConfig(
        semantic_retrieval=SemanticRetrieval(semantic_value),
        full_index_fallback=full_index_fallback,
        retention_days=retention_days,
    )

    golden_data = _object(payload["golden"], "golden")
    _exact_keys(
        golden_data,
        "golden",
        required={"visible_path", "quality_rubric"},
        optional={"start_question"},
    )
    golden = GoldenPaths(
        visible_path=_relative_path(golden_data["visible_path"], "golden.visible_path"),
        quality_rubric=_relative_path(golden_data["quality_rubric"], "golden.quality_rubric"),
        start_question=(
            _start_question(golden_data["start_question"])
            if "start_question" in golden_data
            else None
        ),
    )

    return MemoryManifest.create(
        schema_version=version,
        project=project,
        stores=stores,
        fallbacks=fallbacks,
        budgets=budgets,
        policy=policy,
        golden=golden,
    )


def load_manifest(path: Path | str) -> MemoryManifest:
    """Load a manifest file into the immutable V1 contract."""

    return _build_manifest(_parse_json(Path(path)))


def load_nearest_manifest(start: Path | str | None = None) -> MemoryManifest:
    return load_manifest(discover_manifest(start))


def initial_route(
    manifest: MemoryManifest,
    *,
    role: str | PrincipalRole,
    task_category: str | TaskCategory,
) -> tuple[str, ...]:
    """Return the deterministic eligible route; sufficiency is handled later."""

    try:
        principal_role = role if isinstance(role, PrincipalRole) else PrincipalRole(role)
        category = task_category if isinstance(task_category, TaskCategory) else TaskCategory(task_category)
    except ValueError as exc:
        raise ValueError(f"Unsupported route input: {exc}") from exc

    route = [manifest.stores.project.collection]
    route.extend(
        fallback.collection
        for fallback in manifest.fallbacks
        if principal_role in fallback.allowed_roles and category in fallback.task_categories
    )
    return tuple(route)
