#!/usr/bin/env python3
"""Shared standard-library helpers for the optional advanced V3 scripts."""

from __future__ import annotations

import datetime as dt
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "3.0"
CLAIM_STATUSES = ("accurate", "inaccurate", "outdated", "unverifiable")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_text(path: str | Path, content: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", dir=str(target.parent), text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
            stream.write(content)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_json(path: str | Path, value: Any) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def pct(numerator: int | float, denominator: int | float) -> float | None:
    return round(100.0 * numerator / denominator, 1) if denominator else None


def geo_run_files(inputs: Iterable[str | Path]) -> list[Path]:
    """Resolve project, geo_runs directory and JSON run inputs without recursion."""
    files: list[Path] = []
    for raw in inputs:
        path = Path(raw).expanduser().resolve()
        if path.is_file():
            files.append(path)
            continue
        if not path.is_dir():
            raise FileNotFoundError(path)
        candidate = path / "geo_runs"
        directory = candidate if candidate.is_dir() else path
        files.extend(sorted(directory.glob("*.json")))
    unique: dict[str, Path] = {}
    for path in files:
        unique[str(path)] = path
    return list(unique.values())


def load_geo_runs(inputs: Iterable[str | Path]) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    for path in geo_run_files(inputs):
        value = read_json(path)
        if not isinstance(value, dict) or not isinstance(value.get("observations"), list):
            raise ValueError(f"{path}: fichier de run GEO invalide")
        copy = dict(value)
        copy["_source_path"] = str(path)
        runs.append(copy)
    return runs


def project_dirs(inputs: Iterable[str | Path], recursive: bool = False) -> list[Path]:
    """Discover project directories identified by audit_manifest.json."""
    found: dict[str, Path] = {}
    for raw in inputs:
        path = Path(raw).expanduser().resolve()
        if (path / "audit_manifest.json").is_file():
            found[str(path)] = path
            continue
        if not path.is_dir():
            raise FileNotFoundError(path)
        pattern = "**/audit_manifest.json" if recursive else "*/audit_manifest.json"
        for manifest in sorted(path.glob(pattern)):
            found[str(manifest.parent)] = manifest.parent
    return list(found.values())


def load_optional_json(path: Path, default: Any) -> Any:
    return read_json(path) if path.is_file() else default


def compact_join(values: Iterable[Any], separator: str = " | ") -> str:
    return separator.join(str(item) for item in values if item not in (None, ""))


def csv_safe(value: Any) -> Any:
    """Neutralize spreadsheet formulas in text fields written to CSV."""
    if not isinstance(value, str):
        return value
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value
