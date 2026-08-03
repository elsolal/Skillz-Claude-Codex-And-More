#!/usr/bin/env python3
"""Shared, dependency-light helpers for the SEO/GEO V3 deterministic scripts."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import tempfile
import unicodedata
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


SCHEMA_VERSION = "3.0"
TEXT_DELIVERY_SUFFIXES = {".md", ".txt", ".yaml", ".yml", ".json", ".jsonl", ".csv", ".tsv", ".html"}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_datetime(value: str) -> dt.datetime:
    if not isinstance(value, str):
        raise ValueError("Une date-time ISO 8601 textuelle est attendue.")
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Le fuseau horaire est obligatoire (utiliser Z ou un décalage explicite).")
    return parsed


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()
    return value or "client"


def find_kit_root(explicit: str | Path | None = None) -> Path:
    candidates: list[Path] = [Path.cwd().resolve()]
    if os.environ.get("SEO_GEO_V3_ROOT"):
        candidates.append(Path(os.environ["SEO_GEO_V3_ROOT"]).expanduser().resolve())
    here = Path(__file__).resolve()
    candidates.extend(here.parents)
    candidates.extend(Path.cwd().resolve().parents)
    if explicit:
        candidates.insert(0, Path(explicit).expanduser().resolve())
    for candidate in candidates:
        for resource_root in (candidate, candidate / "assets" / "kit", candidate / "resources" / "kit"):
            if (resource_root / "schemas").is_dir() and (resource_root / "templates" / "project").is_dir():
                return resource_root
    raise FileNotFoundError("Racine du kit introuvable. Utilisez --kit-root ou SEO_GEO_V3_ROOT.")


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: JSON invalide: {exc.msg}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number}: chaque ligne doit être un objet JSON")
        records.append(value)
    return records


def delivery_payload_errors(path: str | Path) -> list[str]:
    """Return deterministic blockers for empty or syntactically corrupt deliverables."""

    target = Path(path)
    try:
        payload = target.read_bytes()
    except OSError as exc:
        return [f"Livrable illisible: {exc}."]
    if not payload:
        return ["Livrable vide (0 octet)."]
    suffix = target.suffix.lower()
    if suffix not in TEXT_DELIVERY_SUFFIXES:
        return []
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return ["Livrable textuel non décodable en UTF-8."]
    if not text.strip():
        return ["Livrable textuel vide ou composé uniquement d’espaces."]
    if suffix == ".json":
        try:
            json.loads(text)
        except json.JSONDecodeError as exc:
            return [f"Livrable JSON invalide: ligne {exc.lineno}, colonne {exc.colno}."]
    elif suffix == ".jsonl":
        for line_number, raw in enumerate(text.splitlines(), 1):
            if not raw.strip():
                continue
            try:
                json.loads(raw)
            except json.JSONDecodeError as exc:
                return [f"Livrable JSONL invalide à la ligne {line_number}: {exc.msg}."]
    return []


def write_json(path: str | Path, data: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    _atomic_write(target, payload)


def write_text(path: str | Path, text: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(target, text)


def append_jsonl(path: str | Path, records: Iterable[dict[str, Any]]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def _atomic_write(target: Path, payload: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=str(target.parent), text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(payload)
        os.replace(temp_name, target)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def load_simple_yaml(path: str | Path) -> dict[str, Any]:
    """Load the conservative mapping/flow-list YAML subset used by client.yaml.

    PyYAML is used when present. The fallback intentionally rejects block lists,
    anchors and tags so an audit does not silently reinterpret complex input.
    """
    try:
        import yaml  # type: ignore

        value = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("client.yaml doit contenir un mapping à la racine")
        return value
    except ImportError:
        pass

    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for number, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise ValueError(f"{path}:{number}: indentation par tabulation non acceptée")
        indent = len(raw) - len(raw.lstrip(" "))
        text = raw.strip()
        if text.startswith("-"):
            raise ValueError(f"{path}:{number}: utilisez une liste YAML en notation [\"a\", \"b\"]")
        if ":" not in text:
            raise ValueError(f"{path}:{number}: clé YAML attendue")
        key, raw_value = text.split(":", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", key):
            raise ValueError(f"{path}:{number}: clé non prise en charge: {key}")
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise ValueError(f"{path}:{number}: indentation incohérente")
        parent = stack[-1][1]
        raw_value = raw_value.strip()
        if not raw_value:
            value: Any = {}
            parent[key] = value
            stack.append((indent, value))
        else:
            parent[key] = _yaml_scalar(raw_value)
    return root


def _yaml_scalar(value: str) -> Any:
    if value.startswith(("[", "{", '"')):
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Valeur YAML/JSON non prise en charge: {value}") from exc
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    lower = value.lower()
    if lower in {"true", "false"}:
        return lower == "true"
    if lower in {"null", "~"}:
        return None
    if re.fullmatch(r"-?[0-9]+", value):
        return int(value)
    if re.fullmatch(r"-?[0-9]+\.[0-9]+", value):
        return float(value)
    return value


def validate_schema(instance: Any, schema: dict[str, Any]) -> list[str]:
    """Validate with jsonschema when available; otherwise use a strict local subset."""
    try:
        import jsonschema  # type: ignore

        validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
        errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.absolute_path))
        return [f"{_format_path(error.absolute_path)}: {error.message}" for error in errors]
    except ImportError:
        errors: list[str] = []
        _validate_subset(instance, schema, "$", errors)
        return errors


def _format_path(path: Iterable[Any]) -> str:
    result = "$"
    for part in path:
        result += f"[{part}]" if isinstance(part, int) else f".{part}"
    return result


def _validate_subset(value: Any, schema: dict[str, Any], path: str, errors: list[str]) -> None:
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: doit être {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: valeur {value!r} hors enum")
    allowed_types = schema.get("type")
    if allowed_types:
        names = [allowed_types] if isinstance(allowed_types, str) else allowed_types
        if not any(_matches_type(value, name) for name in names):
            errors.append(f"{path}: type attendu {names}, reçu {type(value).__name__}")
            return
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: propriété requise absente: {key}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{path}.{key}: propriété non autorisée")
        for key, child in properties.items():
            if key in value:
                _validate_subset(value[key], child, f"{path}.{key}", errors)
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{path}: au moins {schema['minItems']} élément(s) requis")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path}: au plus {schema['maxItems']} élément(s)")
        if schema.get("uniqueItems"):
            normalized = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in value]
            if len(normalized) != len(set(normalized)):
                errors.append(f"{path}: éléments dupliqués")
        if isinstance(schema.get("items"), dict):
            for index, item in enumerate(value):
                _validate_subset(item, schema["items"], f"{path}[{index}]", errors)
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path}: chaîne trop courte")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(f"{path}: chaîne trop longue")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: format non conforme à {schema['pattern']}")
        if schema.get("format") == "date-time":
            try:
                parse_datetime(value)
            except ValueError:
                errors.append(f"{path}: date-time invalide")
        elif schema.get("format") == "date":
            try:
                dt.date.fromisoformat(value)
            except ValueError:
                errors.append(f"{path}: date invalide")
        elif schema.get("format") == "uri":
            parsed = urlparse(value)
            if not parsed.scheme or not parsed.netloc:
                errors.append(f"{path}: URI absolue invalide")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: inférieur au minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: supérieur au maximum {schema['maximum']}")
    if "anyOf" in schema:
        branch_valid = False
        for branch in schema["anyOf"]:
            branch_errors: list[str] = []
            _validate_subset(value, branch, path, branch_errors)
            if not branch_errors:
                branch_valid = True
                break
        if not branch_valid:
            errors.append(f"{path}: aucune alternative anyOf ne correspond")


def _matches_type(value: Any, name: str) -> bool:
    return {
        "object": isinstance(value, dict), "array": isinstance(value, list), "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool), "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool), "null": value is None,
    }.get(name, True)


def pct(numerator: float, denominator: float) -> float | None:
    return round(100.0 * numerator / denominator, 1) if denominator else None
