#!/usr/bin/env python3
"""Construit ou vérifie le manifeste d’intégrité SHA-256 du kit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "KIT_MANIFEST.json"
IGNORED_PARTS = {"__pycache__", ".DS_Store", ".claude", "node_modules", ".venv", "venv"}
IGNORED_PATHS = {"KIT_MANIFEST.json"}


def inventory() -> list[dict[str, object]]:
    files: list[dict[str, object]] = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        relative_path = path.relative_to(ROOT)
        relative = relative_path.as_posix()
        if relative in IGNORED_PATHS or any(part in IGNORED_PARTS for part in relative_path.parts):
            continue
        payload = path.read_bytes()
        files.append(
            {
                "path": relative,
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    return files


def build() -> None:
    files = inventory()
    payload = {
        "product": "SEO/GEO Squad V3",
        "version": "3.1.0",
        "algorithm": "sha256",
        "file_count": len(files),
        "files": files,
    }
    MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Manifeste créé : {len(files)} fichiers")


def verify() -> int:
    if not MANIFEST.is_file():
        print("KIT_MANIFEST.json absent")
        return 1
    expected = json.loads(MANIFEST.read_text(encoding="utf-8"))
    actual = inventory()
    canonical = {
        "product": "SEO/GEO Squad V3",
        "version": "3.1.0",
        "algorithm": "sha256",
        "file_count": len(actual),
        "files": actual,
    }
    if expected != canonical:
        if not isinstance(expected, dict):
            print("Différence : racine du manifeste invalide")
            return 2
        for key in ("product", "version", "algorithm", "file_count"):
            if expected.get(key) != canonical[key]:
                print(f"Différence : {key}")
        expected_files = expected.get("files", [])
        if not isinstance(expected_files, list) or any(not isinstance(item, dict) or "path" not in item for item in expected_files):
            print("Différence : files invalide")
            return 2
        expected_by_path = {item["path"]: item for item in expected_files}
        actual_by_path = {item["path"]: item for item in actual}
        for path in sorted(set(expected_by_path) | set(actual_by_path)):
            if expected_by_path.get(path) != actual_by_path.get(path):
                print(f"Différence : {path}")
        return 2
    print(f"Intégrité vérifiée : {len(actual)} fichiers")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        return verify()
    build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
