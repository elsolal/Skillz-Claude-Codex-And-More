#!/usr/bin/env python3
"""Plan or explicitly run integrity checks against allowlisted official rule URLs.

Network access is disabled by default. A GET request is made only when the
operator passes --network; this is required to compute a content hash.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterable

from _advanced_common import read_json, utc_now, write_json

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from collect_site import (  # noqa: E402
    PinnedHTTPSHandler,
    UnsafeURL,
    _public_endpoints,
    _split_safe_url,
)


DEFAULT_ALLOWED_DOMAINS = {
    "developers.google.com", "support.google.com", "openai.com", "help.openai.com",
    "support.claude.com", "docs.perplexity.ai", "blogs.bing.com", "schema.org",
    "w3.org", "www.w3.org", "ietf.org", "www.ietf.org", "ucp.dev",
    "developer.chrome.com", "indexnow.org", "www.indexnow.org", "llmstxt.org",
}
HARD_MAX_BYTES = 10 * 1024 * 1024
URL_PATTERN = re.compile(r"https://[^\s<>\]\[\"']+")


def _domain_allowed(host: str, allowed: set[str]) -> bool:
    host = host.lower().rstrip(".")
    return any(host == item or host.endswith("." + item) for item in allowed)


def _validate_url(url: str, allowed: set[str]) -> str:
    cleaned = url.rstrip(".,;:!?)}`")
    parsed = urllib.parse.urlsplit(cleaned)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError(f"URL HTTPS officielle attendue: {url}")
    if not _domain_allowed(parsed.hostname, allowed):
        raise ValueError(f"Domaine non allowlisté: {parsed.hostname}")
    try:
        _split_safe_url(cleaned)
    except UnsafeURL as exc:
        raise ValueError(str(exc)) from exc
    return cleaned


def _validate_network_destination(url: str) -> None:
    """Resolve the HTTPS destination and reject every non-public endpoint."""

    try:
        _parsed, scheme, hostname, port, _explicit_port = _split_safe_url(url)
        if scheme != "https":
            raise UnsafeURL("Seules les URL HTTPS sont autorisées pour les sources de règles.")
        _public_endpoints(hostname, port)
    except UnsafeURL as exc:
        raise ValueError(str(exc)) from exc


def extract_urls(path: Path) -> list[str]:
    if path.suffix.lower() == ".json":
        value = read_json(path)
        if isinstance(value, list):
            candidates = [item.get("url") if isinstance(item, dict) else item for item in value]
        elif isinstance(value, dict):
            source_items = value.get("sources") or value.get("results") or []
            candidates = [item.get("url") if isinstance(item, dict) else item for item in source_items]
        else:
            raise ValueError(f"{path}: liste JSON ou objet avec sources/results attendu")
        return [str(item) for item in candidates if item]
    return URL_PATTERN.findall(path.read_text(encoding="utf-8"))


def collect_urls(inputs: Iterable[Path], explicit: Iterable[str], allowed: set[str]) -> list[str]:
    candidates = list(explicit)
    for path in inputs:
        candidates.extend(extract_urls(path))
    unique: dict[str, None] = {}
    for url in candidates:
        unique[_validate_url(str(url), allowed)] = None
    return list(unique)


class AllowlistedRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, allowed: set[str]):
        self.allowed = allowed

    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> Any:
        _validate_url(newurl, self.allowed)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _fetch(url: str, allowed: set[str], timeout: float, max_bytes: int) -> dict[str, Any]:
    _validate_network_destination(url)
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        PinnedHTTPSHandler(),
        AllowlistedRedirectHandler(allowed),
    )
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "RosoRuleSourceCheck/3.0 (+operator-initiated)", "Accept-Encoding": "identity"},
        method="GET",
    )
    try:
        response = opener.open(request, timeout=timeout)
    except urllib.error.HTTPError as exc:
        response = exc
    try:
        status = int(getattr(response, "status", getattr(response, "code", 0)))
        final_url = str(response.geturl())
        _validate_url(final_url, allowed)
        declared = response.headers.get("Content-Length")
        if declared and int(declared) > max_bytes:
            raise ValueError(f"Content-Length {declared} > limite {max_bytes}")
        body = response.read(max_bytes + 1)
        if len(body) > max_bytes:
            raise ValueError(f"Réponse > limite {max_bytes} octets")
        return {
            "url": url, "final_url": final_url, "check_status": "checked", "http_status": status,
            "content_sha256": f"sha256:{hashlib.sha256(body).hexdigest()}", "bytes": len(body),
            "last_modified": response.headers.get("Last-Modified"), "etag": response.headers.get("ETag"),
            "content_type": response.headers.get("Content-Type"), "checked_at": utc_now(), "error": None,
        }
    finally:
        response.close()


def _baseline_index(path: Path | None) -> dict[str, dict[str, Any]]:
    if not path:
        return {}
    value = read_json(path)
    return {str(item.get("url")): item for item in value.get("results", []) if item.get("url")}


def check_sources(
    urls: list[str],
    network: bool = False,
    allowed_domains: set[str] | None = None,
    timeout: float = 15.0,
    max_bytes: int = 2 * 1024 * 1024,
    delay: float = 0.5,
    baseline: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    allowed = allowed_domains or set(DEFAULT_ALLOWED_DOMAINS)
    baseline = baseline or {}
    results: list[dict[str, Any]] = []
    for index, url in enumerate(urls):
        if not network:
            item = {
                "url": url, "final_url": None, "check_status": "not_checked", "http_status": None,
                "content_sha256": None, "bytes": None, "last_modified": None, "etag": None,
                "content_type": None, "checked_at": None, "error": "Réseau désactivé; utiliser --network pour lancer le GET.",
            }
        else:
            if index and delay:
                time.sleep(delay)
            try:
                item = _fetch(url, allowed, timeout, min(max(1024, max_bytes), HARD_MAX_BYTES))
            except (OSError, ValueError, urllib.error.URLError, TimeoutError) as exc:
                item = {
                    "url": url, "final_url": None, "check_status": "error", "http_status": None,
                    "content_sha256": None, "bytes": None, "last_modified": None, "etag": None,
                    "content_type": None, "checked_at": utc_now(), "error": str(exc),
                }
        previous = baseline.get(url)
        item["change"] = {
            "baseline_available": bool(previous),
            "http_status_changed": bool(previous and previous.get("http_status") is not None and item["http_status"] is not None and previous.get("http_status") != item["http_status"]),
            "content_hash_changed": bool(previous and previous.get("content_sha256") and item["content_sha256"] and previous.get("content_sha256") != item["content_sha256"]),
            "last_modified_changed": bool(previous and previous.get("last_modified") and item["last_modified"] and previous.get("last_modified") != item["last_modified"]),
        }
        results.append(item)
    changed = sum(any(value for key, value in item["change"].items() if key != "baseline_available") for item in results)
    errors = sum(item["check_status"] == "error" or (item["http_status"] is not None and not 200 <= item["http_status"] < 400) for item in results)
    return {
        "schema_version": "3.0", "generated_at": utc_now(), "network_requested": network,
        "method": "Operator-triggered HTTPS GET with allowlisted domains; SHA-256 covers the received response bytes.",
        "allowed_domains": sorted(allowed), "source_count": len(urls), "changed_count": changed, "error_count": errors,
        "results": results,
        "limitations": [
            "Un changement de hash signale une variation des octets reçus, pas nécessairement une modification de règle.",
            "Last-Modified et ETag sont déclaratifs et peuvent être absents; examiner humainement toute source modifiée.",
            "Les pages dynamiques, variantes locales ou protections réseau peuvent produire des différences sans changement éditorial.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    default_registry = Path(__file__).resolve().parents[2] / "references" / "product" / "rules_registry.md"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", type=Path, help=f"Markdown/JSON de sources; défaut: {default_registry}")
    parser.add_argument("--url", action="append", default=[])
    parser.add_argument("--network", action="store_true", help="Autoriser explicitement les requêtes HTTPS GET")
    parser.add_argument("--allow-domain", action="append", default=[], help="Ajouter un domaine officiel à l'allowlist")
    parser.add_argument("--baseline", type=Path, help="Rapport JSON antérieur à comparer")
    parser.add_argument("--output", type=Path, help="Rapport JSON; stdout si omis")
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--max-bytes", type=int, default=2 * 1024 * 1024)
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--fail-on-change", action="store_true")
    parser.set_defaults(default_registry=default_registry)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        allowed = set(DEFAULT_ALLOWED_DOMAINS) | {item.lower().rstrip(".") for item in args.allow_domain}
        inputs = args.input or [args.default_registry]
        urls = collect_urls(inputs, args.url, allowed)
        if not urls:
            raise ValueError("Aucune URL officielle trouvée.")
        report = check_sources(
            urls, args.network, allowed, args.timeout, args.max_bytes, args.delay, _baseline_index(args.baseline),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        return 2
    if args.output:
        write_json(args.output, report)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["error_count"]:
        return 1
    if args.fail_on_change and report["changed_count"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
