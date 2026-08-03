#!/usr/bin/env python3
"""Create an isolated, schema-ready RosoAI V3 client project."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import uuid
from pathlib import Path
from urllib.parse import urlparse

from _common import find_kit_root, read_json, slugify, utc_now, write_json, write_text


def normalize_root_url(value: str) -> str:
    candidate = value.strip()
    if "://" not in candidate:
        candidate = "https://" + candidate
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Le domaine doit être une URL HTTP(S) ou un nom de domaine valide.")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("Le domaine ne doit contenir aucun identifiant ni mot de passe.")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Port invalide dans le domaine.") from exc
    hostname = parsed.hostname.lower().rstrip(".")
    rendered_host = f"[{hostname}]" if ":" in hostname else hostname
    default_port = 443 if parsed.scheme == "https" else 80
    authority = rendered_host if port in {None, default_port} else f"{rendered_host}:{port}"
    return f"{parsed.scheme}://{authority}/"


def yaml_scalar(value: str) -> str:
    """Serialize a scalar as a JSON string, which is also valid YAML."""
    return json.dumps(str(value), ensure_ascii=False)


def create_project(
    destination: Path,
    client_name: str,
    domain: str,
    locale: str = "fr-FR",
    market: str = "France",
    vertical: str = "other",
    kit_root: Path | None = None,
) -> Path:
    client_name = client_name.strip()
    if not client_name or len(client_name) > 200:
        raise ValueError("Le nom client doit contenir entre 1 et 200 caractères.")
    kit_root = find_kit_root(kit_root)
    template = kit_root / "templates" / "project"
    if not template.is_dir():
        raise FileNotFoundError(f"Template projet absent: {template}")
    version_path = kit_root / "VERSION.json"
    if not version_path.is_file():
        raise FileNotFoundError(f"Métadonnées de version absentes: {version_path}")
    version = read_json(version_path)
    if not isinstance(version, dict) or not version.get("version") or not version.get("rules_verified_on"):
        raise ValueError("VERSION.json doit déclarer version et rules_verified_on.")
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(f"Destination non vide: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copytree(template, destination, dirs_exist_ok=True)

    now = utc_now()
    date_token = now[:10].replace("-", "")
    slug = slugify(client_name)
    client_id = f"client_{slug}"[:71].rstrip("_")
    nonce = uuid.uuid4().hex[:12]
    audit_suffix = f"_{date_token}_{nonce}"
    audit_slug_budget = 70 - len("audit_") - len(audit_suffix)
    audit_slug = slug[:audit_slug_budget].rstrip("_") or "client"
    audit_id = f"audit_{audit_slug}{audit_suffix}"
    root_url = normalize_root_url(domain)
    hostname = urlparse(root_url).hostname or domain
    country_code = locale.rsplit("-", 1)[-1] if "-" in locale else market

    client_yaml = (
        'schema_version: "3.0"\n'
        f"client_id: {yaml_scalar(client_id)}\n"
        "identity:\n"
        f"  name: {yaml_scalar(client_name)}\n"
        f"  legal_name: {yaml_scalar(client_name)}\n"
        f"  domain: {yaml_scalar(hostname)}\n"
        "  aliases: []\n"
        "business:\n"
        f"  vertical: {yaml_scalar(vertical)}\n"
        f"  description: {yaml_scalar('À compléter et faire approuver par le client.')}\n"
        "  offers: []\n"
        "markets:\n"
        f"  primary: {yaml_scalar(market)}\n"
        f"  countries: {json.dumps([country_code], ensure_ascii=False)}\n"
        f"  locales: {json.dumps([locale], ensure_ascii=False)}\n"
        "audiences:\n"
        f"  primary: {yaml_scalar('À compléter.')}\n"
        "competitors:\n"
        "  domains: []\n"
        "brand_governance:\n"
        "  approved_claims: []\n"
        '  forbidden_claims: ["Résultats garantis", "Numéro 1 sans preuve"]\n'
        f"  tone: {yaml_scalar('À valider.')}\n"
        "contacts:\n"
        f"  data_owner: {yaml_scalar('À renseigner')}\n"
        f"  approval_owner: {yaml_scalar('À renseigner')}\n"
    )
    write_text(destination / "client.yaml", client_yaml)

    manifest = read_json(destination / "audit_manifest.json")
    manifest.update({"audit_id": audit_id, "client_id": client_id, "created_at": now, "updated_at": now, "status": "planned"})
    manifest["scope"].update({
        "root_url": root_url, "locales": [locale], "markets": [market], "vertical": vertical,
        "include_urls": [root_url], "exclude_patterns": ["/compte/", "/login/", "/panier/", "/checkout/"],
    })
    manifest["authorization"] = {
        "authorized_by": "À renseigner avant collecte",
        "authorized_at": None,
        "permissions": ["public_web"],
        "write_actions_require_approval": True,
        "notes": "Autorisation à confirmer; aucune écriture externe n'est permise par défaut.",
    }
    manifest["data_policy"]["deletion_contact"] = "À renseigner"
    manifest["methodology"].update({
        "kit_version": version["version"],
        "schema_version": version.get("schema_version", "3.0"),
        "rules_snapshot_date": version["rules_verified_on"],
    })
    manifest["run_ids"] = {"collector": [], "geo": []}
    manifest["blind_spots"] = ["Les accès first-party et les limites de collecte restent à documenter."]
    write_json(destination / "audit_manifest.json", manifest)

    for filename, collection in (("facts.json", "facts"), ("findings.json", "findings"), ("actions.json", "actions")):
        data = read_json(destination / filename)
        data["audit_id"] = audit_id
        data["generated_at"] = now
        data[collection] = []
        write_json(destination / filename, data)
    write_text(destination / "evidence.jsonl", "")
    write_text(destination / "events.jsonl", "")
    for path in (destination / "geo_runs").glob("*.json"):
        path.unlink()
    event = {
        "schema_version": "3.0", "event_id": f"event_{audit_id.removeprefix('audit_')}_created", "audit_id": audit_id, "at": now,
        "actor": "create_project.py", "actor_type": "script", "event_type": "created", "object_type": "audit",
        "object_id": audit_id, "from_status": None, "to_status": "planned", "message": "Projet d'audit créé.",
        "metadata": {"kit_version": manifest["methodology"]["kit_version"]},
    }
    write_text(destination / "events.jsonl", __import__("json").dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")
    raw_dir = destination / "raw"
    if raw_dir.exists():
        shutil.rmtree(raw_dir)
    for directory in ("raw", "reports", "exports", "logs"):
        (destination / directory).mkdir(exist_ok=True)
    return destination


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="Dossier isolé du projet client")
    parser.add_argument("--client-name", required=True)
    parser.add_argument("--domain", required=True)
    parser.add_argument("--locale", default="fr-FR")
    parser.add_argument("--market", default="France")
    parser.add_argument("--vertical", choices=["local", "b2b", "saas", "ecommerce", "publisher", "ymyl", "personal_brand", "other"], default="other")
    parser.add_argument("--kit-root", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        created = create_project(args.destination.resolve(), args.client_name, args.domain, args.locale, args.market, args.vertical, args.kit_root)
    except (ValueError, FileNotFoundError, FileExistsError) as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        return 2
    print(created)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
