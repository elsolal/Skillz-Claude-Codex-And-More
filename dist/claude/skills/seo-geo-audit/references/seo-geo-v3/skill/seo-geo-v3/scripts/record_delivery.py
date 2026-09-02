#!/usr/bin/env python3
"""Bind one reviewed deliverable to its bytes and current structured inputs."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any

from _common import delivery_payload_errors, read_json, utc_now
from qa_audit import pdf_page_count
from score_v3 import canonical_score_errors, input_fingerprint


def record_validation(
    project: Path,
    artifact: Path | str,
    actor: str,
    actor_type: str = "human",
    all_pages_reviewed: bool = False,
    page_count: int | None = None,
) -> dict[str, Any]:
    """Append a validation event after explicit review of an existing artifact."""

    project = project.resolve()
    actor = actor.strip()
    if not actor:
        raise ValueError("L’acteur de validation est obligatoire.")
    if actor_type not in {"human", "agent", "script", "system"}:
        raise ValueError("actor_type invalide.")
    artifact_path = Path(artifact)
    if not artifact_path.is_absolute():
        artifact_path = project / artifact_path
    artifact_path = artifact_path.resolve()
    try:
        relative = artifact_path.relative_to(project).as_posix()
    except ValueError as exc:
        raise ValueError("Le livrable doit rester dans le dossier projet.") from exc
    if not artifact_path.is_file():
        raise FileNotFoundError(f"Livrable absent: {artifact_path}")
    payload_issues = delivery_payload_errors(artifact_path)
    if payload_issues:
        raise ValueError(" ".join(payload_issues))
    if artifact_path.suffix.lower() == ".pdf":
        if not all_pages_reviewed or not isinstance(page_count, int) or page_count < 1:
            raise ValueError("Un PDF exige --all-pages-reviewed et un --page-count positif après inspection réelle.")
        actual_page_count = pdf_page_count(artifact_path)
        if actual_page_count is None:
            raise ValueError("Le nombre réel de pages du PDF est introuvable ou invalide.")
        if page_count != actual_page_count:
            raise ValueError(
                f"--page-count={page_count} ne correspond pas aux {actual_page_count} pages du PDF."
            )
    elif all_pages_reviewed or page_count is not None:
        raise ValueError("Les options de revue de pages sont réservées aux PDF.")

    manifest = read_json(project / "audit_manifest.json")
    audit_id = manifest.get("audit_id")
    if not isinstance(audit_id, str) or not audit_id.startswith("audit_"):
        raise ValueError("audit_id absent ou invalide dans le manifeste.")
    current_fingerprint = input_fingerprint(project)
    score_path = project / "reports" / "score_v3.json"
    if not score_path.is_file():
        raise FileNotFoundError("Score canonique absent: générer reports/score_v3.json avant toute validation.")
    score = read_json(score_path)
    score_issues = canonical_score_errors(project, score)
    if score_issues:
        raise ValueError(" ".join(score_issues))
    if score.get("audit_id") != audit_id:
        raise ValueError("Le score canonique appartient à un autre audit.")
    if score.get("input_fingerprint") != current_fingerprint:
        raise ValueError("Le score canonique est obsolète par rapport aux entrées structurées.")
    score_as_of = score.get("as_of")
    if not isinstance(score_as_of, str):
        raise ValueError("Le score canonique ne contient pas de date de coupure as_of.")
    score_digest = "sha256:" + hashlib.sha256(score_path.read_bytes()).hexdigest()
    digest = "sha256:" + hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    metadata: dict[str, Any] = {
        "sha256": digest,
        "input_fingerprint": current_fingerprint,
        "score_as_of": score_as_of,
        "score_sha256": score_digest,
    }
    if artifact_path.suffix.lower() == ".pdf":
        metadata.update({
            "page_count": actual_page_count,
            "rendered_page_review": "all_pages",
        })
    now = utc_now()
    event = {
        "schema_version": "3.0",
        "event_id": f"event_delivery_{uuid.uuid4().hex[:20]}",
        "audit_id": audit_id,
        "at": now,
        "actor": actor,
        "actor_type": actor_type,
        "event_type": "validated",
        "object_type": "report",
        "object_id": f"report_{hashlib.sha256(relative.encode('utf-8')).hexdigest()[:20]}",
        "from_status": None,
        "to_status": None,
        "message": f"Livrable relu et lié à ses données structurées: {relative}.",
        "artifacts": [relative],
        "metadata": metadata,
    }
    events_path = project / "events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n"
    with events_path.open("a", encoding="utf-8") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
        fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
    return event


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("artifact", type=Path, help="Chemin relatif au projet ou chemin absolu interne")
    parser.add_argument("--actor", required=True, help="Personne ou agent ayant réellement effectué la revue")
    parser.add_argument("--actor-type", choices=["human", "agent", "script", "system"], default="human")
    parser.add_argument("--all-pages-reviewed", action="store_true", help="Confirmer la revue visuelle de toutes les pages PDF")
    parser.add_argument("--page-count", type=int, help="Nombre de pages effectivement inspectées")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        event = record_validation(
            args.project,
            args.artifact,
            args.actor,
            args.actor_type,
            args.all_pages_reviewed,
            args.page_count,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(event, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
