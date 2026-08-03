#!/usr/bin/env python3
"""Vérifie et installe le Squad RosoAI V3 complet dans un dossier choisi."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SKILL_NAME = "roso-seo-geo-squad-v3"
METHODOLOGY = ROOT / "skill" / "roso-seo-geo-v3"
REQUIRED = [
    ROOT / "VERSION.json",
    ROOT / "KIT_MANIFEST.json",
    ROOT / "SKILL.md",
    ROOT / "agents" / "openai.yaml",
    ROOT / "START_HERE.md",
    ROOT / "core" / "00_REGLES_COMMUNES_V3.md",
    ROOT / "core" / "01_MASTER_ORCHESTRATOR_V3.md",
    ROOT / "core" / "AGENTS_MANIFEST.json",
    ROOT / "docs" / "INSTALLATION.md",
    METHODOLOGY / "SKILL.md",
    METHODOLOGY / "agents" / "openai.yaml",
    METHODOLOGY / "references" / "architecture.md",
    METHODOLOGY / "references" / "data_model.md",
    METHODOLOGY / "references" / "scoring_v3.md",
    METHODOLOGY / "assets" / "kit" / "VERSION.json",
    METHODOLOGY / "assets" / "default_theme.json",
    METHODOLOGY / "assets" / "kit" / "schemas" / "audit_manifest.schema.json",
    METHODOLOGY / "assets" / "kit" / "templates" / "project" / "client.yaml",
    METHODOLOGY / "tools" / "render_html_pdf.cjs",
    METHODOLOGY / "tools" / "render_tagged_pdf.cjs",
    METHODOLOGY / "tools" / "render_markdown_pdf.py",
    METHODOLOGY / "assets" / "fonts" / "fonts.css",
    ROOT / "templates" / "Charte_PDF_RosoAI_V3.md",
    METHODOLOGY / "package.json",
    METHODOLOGY / "package-lock.json",
    METHODOLOGY / "requirements-pdf.txt",
]


def check_package() -> list[str]:
    errors: list[str] = []
    if sys.version_info < (3, 10):
        errors.append(
            f"Python 3.10+ requis; runtime détecté: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        )
    for path in REQUIRED:
        if not path.is_file():
            errors.append(f"Fichier absent : {path.relative_to(ROOT)}")
    version_path = ROOT / "VERSION.json"
    if version_path.is_file():
        try:
            payload = json.loads(version_path.read_text(encoding="utf-8"))
            if payload.get("version") != "3.1.0":
                errors.append("VERSION.json ne déclare pas la version 3.1.0")
            bundled_version = METHODOLOGY / "assets" / "kit" / "VERSION.json"
            if bundled_version.is_file() and json.loads(bundled_version.read_text(encoding="utf-8")) != payload:
                errors.append("La VERSION.json embarquée dans le Skill diffère de la version racine")
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"VERSION.json invalide : {exc}")
    skill_md = ROOT / "SKILL.md"
    if skill_md.is_file():
        text = skill_md.read_text(encoding="utf-8")
        if not text.startswith("---\nname: roso-seo-geo-squad-v3\n"):
            errors.append("Frontmatter SKILL.md invalide")
        if "[TODO" in text:
            errors.append("SKILL.md contient encore un TODO")
    agents_manifest = ROOT / "core" / "AGENTS_MANIFEST.json"
    if agents_manifest.is_file():
        try:
            agents_payload = json.loads(agents_manifest.read_text(encoding="utf-8"))
            agents = agents_payload.get("agents")
            if not isinstance(agents, list) or len(agents) != 21:
                errors.append("AGENTS_MANIFEST.json doit déclarer exactement 21 agents")
            else:
                for agent in agents:
                    relative = agent.get("file") if isinstance(agent, dict) else None
                    if not isinstance(relative, str) or not (ROOT / relative).is_file():
                        errors.append(f"Carte d’agent absente ou invalide : {relative}")
        except (OSError, json.JSONDecodeError, TypeError) as exc:
            errors.append(f"AGENTS_MANIFEST.json invalide : {exc}")
    manifest_path = ROOT / "KIT_MANIFEST.json"
    if manifest_path.is_file():
        try:
            expected = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not isinstance(expected, dict):
                raise TypeError("la racine doit être un objet")
            if expected.get("product") != "RosoAI SEO/GEO Squad V3":
                errors.append("KIT_MANIFEST.json: product invalide")
            if expected.get("version") != "3.1.0":
                errors.append("KIT_MANIFEST.json: version invalide")
            if expected.get("algorithm") != "sha256":
                errors.append("KIT_MANIFEST.json: algorithm doit valoir sha256")
            files = expected.get("files")
            if not isinstance(files, list):
                raise TypeError("files doit être une liste")
            if expected.get("file_count") != len(files):
                errors.append("KIT_MANIFEST.json: file_count incohérent")
            paths: list[str] = []
            for index, item in enumerate(files):
                if not isinstance(item, dict):
                    raise TypeError(f"files[{index}] doit être un objet")
                relative = item.get("path")
                byte_count = item.get("bytes")
                digest = item.get("sha256")
                if (
                    not isinstance(relative, str) or not relative or relative.startswith("/")
                    or ".." in Path(relative).parts or "\\" in relative
                ):
                    errors.append(f"KIT_MANIFEST.json: chemin invalide à files[{index}]")
                    continue
                if not isinstance(byte_count, int) or isinstance(byte_count, bool) or byte_count < 0:
                    errors.append(f"KIT_MANIFEST.json: taille invalide pour {relative}")
                if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
                    errors.append(f"KIT_MANIFEST.json: SHA-256 invalide pour {relative}")
                paths.append(relative)
            if len(paths) != len(set(paths)):
                errors.append("KIT_MANIFEST.json: chemins dupliqués")
            expected_by_path = {
                item["path"]: item for item in files
                if isinstance(item, dict) and isinstance(item.get("path"), str)
            }
            actual_paths = {}
            for path in ROOT.rglob("*"):
                if not path.is_file():
                    continue
                relative = path.relative_to(ROOT)
                if path.name in {"KIT_MANIFEST.json", ".DS_Store"}:
                    continue
                if {"__pycache__", ".claude", "node_modules", ".venv", "venv"} & set(relative.parts):
                    continue
                actual_paths[relative.as_posix()] = path
            for relative in sorted(set(expected_by_path) | set(actual_paths)):
                item = expected_by_path.get(relative)
                path = actual_paths.get(relative)
                if item is None:
                    errors.append(f"Intégrité: fichier non manifesté : {relative}")
                    continue
                if path is None:
                    errors.append(f"Intégrité: fichier absent : {relative}")
                    continue
                payload = path.read_bytes()
                if len(payload) != item.get("bytes") or hashlib.sha256(payload).hexdigest() != item.get("sha256"):
                    errors.append(f"Intégrité: fichier modifié : {relative}")
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            errors.append(f"KIT_MANIFEST.json invalide : {exc}")
    return errors


def install(destination: Path, replace: bool) -> Path:
    destination = destination.expanduser().resolve()
    target = destination / SKILL_NAME
    destination.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if not replace:
            raise FileExistsError(
                f"{target} existe déjà. Relancer avec --replace après vérification."
            )
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = target.with_name(f"{target.name}.backup-{stamp}")
        target.rename(backup)
        print(f"Sauvegarde créée : {backup}")
    shutil.copytree(
        ROOT,
        target,
        ignore=shutil.ignore_patterns(
            "__pycache__", "*.pyc", ".DS_Store", ".claude", "node_modules", ".venv", "venv"
        ),
    )
    return target


def pdf_engine_notice() -> str | None:
    """Avertir si aucun moteur PDF n'est disponible. Ne bloque jamais le préflight."""
    try:
        import importlib.util

        if importlib.util.find_spec("reportlab") is not None:
            return None
    except (ImportError, ValueError):
        pass
    if (METHODOLOGY / "node_modules" / "playwright").exists():
        return None
    return (
        "Aucun moteur PDF détecté. La livraison client PDF reste indisponible tant qu'un moteur "
        "n'est pas installé; les aperçus Markdown sont des contrôles internes, pas des livrables conformes.\n"
        "  Moteur balisé (recommandé) : cd skill/roso-seo-geo-v3 && npm ci && npx playwright install chromium\n"
        "  Moteur de secours isolé : python3 -m venv .venv-pdf && "
        ".venv-pdf/bin/python -m pip install -r skill/roso-seo-geo-v3/requirements-pdf.txt\n"
        "  Ne pas contourner PEP 668 ni installer ces dépendances dans le Python système."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Vérifier sans installer")
    parser.add_argument("--destination", type=Path, help="Dossier parent des Skills")
    parser.add_argument("--replace", action="store_true", help="Sauvegarder et remplacer")
    args = parser.parse_args()

    errors = check_package()
    if errors:
        print("Échec du préflight :", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Préflight réussi : Squad RosoAI SEO/GEO V3 cohérent.")
    notice = pdf_engine_notice()
    if notice:
        print(f"Avertissement : {notice}")
    if args.check:
        if args.destination is not None:
            print("Mode --check : aucune installation effectuée.")
        return 0
    if args.destination is None:
        parser.error("--destination est requis pour installer")
    try:
        target = install(args.destination, args.replace)
    except (OSError, FileExistsError) as exc:
        print(f"Installation impossible : {exc}", file=sys.stderr)
        return 2
    print(f"Squad installé : {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
