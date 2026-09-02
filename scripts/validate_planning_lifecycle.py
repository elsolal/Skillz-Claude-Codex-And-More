#!/usr/bin/env python3
"""Validate lifecycle links and uniqueness for planning documents."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import sys
from typing import Any, Iterable


LIFECYCLES = {"current", "superseded", "archived"}
DEFAULT_DIRECTORIES = ("plans", "specs", "prd", "architecture")
REQUIRED_FIELDS = {
    "document_id",
    "version",
    "lifecycle",
    "superseded_by",
    "amended_by",
    "amends",
}


class LifecycleError(RuntimeError):
    pass


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"null", "~"}:
        return None
    if value == "[]":
        return []
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        try:
            parsed = json.loads(value.replace("'", '"'))
        except json.JSONDecodeError:
            parsed = [
                item.strip().strip('"\'')
                for item in inner.split(",")
                if item.strip()
            ]
        if not isinstance(parsed, list):
            raise LifecycleError(f"expected inline list: {value}")
        return parsed
    if len(value) >= 2 and value[0] in {'"', "'"} and value[-1] == value[0]:
        return value[1:-1]
    return value


def parse_frontmatter(path: Path) -> dict[str, Any]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        raise LifecycleError(f"cannot read {path}: {error}") from error
    if not lines or lines[0] != "---":
        raise LifecycleError(f"missing top-level frontmatter: {path}")
    fields: dict[str, Any] = {}
    for line in lines[1:]:
        if line == "---":
            return fields
        if not line or line.startswith((" ", "\t")) or ":" not in line:
            continue
        key, raw = line.split(":", 1)
        key = key.strip()
        if key in fields:
            raise LifecycleError(f"duplicate frontmatter field {key}: {path}")
        fields[key] = _parse_scalar(raw)
    raise LifecycleError(f"unterminated frontmatter: {path}")


def _safe_link(root: Path, source: Path, value: str) -> Path:
    relative = PurePosixPath(value)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise LifecycleError(f"unsafe lifecycle link in {source}: {value}")
    candidate = source.parent.joinpath(*relative.parts)
    if not candidate.exists():
        candidate = root.joinpath(*relative.parts)
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError as error:
        raise LifecycleError(f"lifecycle link escapes repository in {source}: {value}") from error
    return candidate


def validate(root: Path, paths: Iterable[Path]) -> dict[str, Any]:
    root = root.resolve()
    documents: dict[Path, dict[str, Any]] = {}
    errors: list[str] = []
    for path in sorted({Path(item).resolve() for item in paths}):
        try:
            fields = parse_frontmatter(path)
            missing = sorted(REQUIRED_FIELDS - set(fields))
            if missing:
                raise LifecycleError(f"missing lifecycle fields {missing}: {path}")
            if not isinstance(fields["document_id"], str) or not fields["document_id"]:
                raise LifecycleError(f"invalid document_id: {path}")
            if not isinstance(fields["version"], str) or not fields["version"]:
                raise LifecycleError(f"invalid version: {path}")
            if fields["lifecycle"] not in LIFECYCLES:
                raise LifecycleError(f"invalid lifecycle {fields['lifecycle']}: {path}")
            for field in ("amended_by", "amends"):
                if not isinstance(fields[field], list) or not all(
                    isinstance(item, str) and item for item in fields[field]
                ):
                    raise LifecycleError(f"invalid {field}: {path}")
            documents[path] = fields
        except LifecycleError as error:
            errors.append(str(error))

    current_keys: dict[tuple[str, str], Path] = {}
    for path, fields in documents.items():
        if fields["lifecycle"] == "current":
            key = (fields["document_id"], fields["version"])
            if key in current_keys:
                errors.append(
                    f"duplicate current document {key}: {current_keys[key]} and {path}"
                )
            else:
                current_keys[key] = path
        superseded_by = fields["superseded_by"]
        if fields["lifecycle"] == "superseded":
            if not isinstance(superseded_by, str) or not superseded_by:
                errors.append(f"superseded document has no superseded_by target: {path}")
            else:
                try:
                    target = _safe_link(root, path, superseded_by)
                    if not target.is_file():
                        errors.append(f"superseded_by target does not exist: {path} -> {superseded_by}")
                except LifecycleError as error:
                    errors.append(str(error))
        elif superseded_by is not None:
            errors.append(f"non-superseded document has superseded_by target: {path}")

        for field, inverse in (("amended_by", "amends"), ("amends", "amended_by")):
            for value in fields[field]:
                try:
                    target = _safe_link(root, path, value)
                except LifecycleError as error:
                    errors.append(str(error))
                    continue
                target_fields = documents.get(target.resolve())
                if target_fields is None:
                    errors.append(f"{field} target is outside the validated set: {path} -> {value}")
                    continue
                reverse_candidates = {
                    path.relative_to(target.parent).as_posix()
                    if path.is_relative_to(target.parent)
                    else path.relative_to(root).as_posix(),
                    path.relative_to(root).as_posix(),
                    path.name,
                }
                if not reverse_candidates.intersection(target_fields[inverse]):
                    errors.append(
                        f"incomplete amendment link: {path} {field} {value}; "
                        f"target must declare {inverse}"
                    )

    return {
        "schema_version": 1,
        "status": "valid" if not errors else "invalid",
        "documents": len(documents),
        "current": sum(item["lifecycle"] == "current" for item in documents.values()),
        "superseded": sum(item["lifecycle"] == "superseded" for item in documents.values()),
        "archived": sum(item["lifecycle"] == "archived" for item in documents.values()),
        "errors": errors,
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    paths = [
        path
        for directory in DEFAULT_DIRECTORIES
        for path in (args.root / "docs" / "planning" / directory).glob("*.md")
    ]
    report = validate(args.root, paths)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    elif report["errors"]:
        print("\n".join(report["errors"]), file=sys.stderr)
    else:
        print(
            f"planning lifecycle valid: {report['documents']} documents "
            f"({report['current']} current, {report['superseded']} superseded, "
            f"{report['archived']} archived)"
        )
    return 0 if report["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
