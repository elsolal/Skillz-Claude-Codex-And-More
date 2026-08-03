#!/usr/bin/env python3
"""Crawl a public site conservatively and emit traceable V3 evidence records.

Safety defaults: HTTP(S) GET only, exact public origin, DNS checked before each
request, robots.txt honored, no cookies/authentication, bounded pages/bytes/time,
delay between requests and no JavaScript execution. Use --dry-run to inspect the
plan without network access.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import http.client
import ipaddress
import json
import os
import posixpath
import re
import shutil
import socket
import ssl
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import uuid
from collections import deque
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from _common import read_json, read_jsonl, slugify


USER_AGENT = "RosoAuditBot/3.0 (+read-only; contact required by operator)"
HARD_MAX_PAGES = 200
HARD_MAX_BYTES = 5 * 1024 * 1024
DEFAULT_MAX_PAGES = 20
DEFAULT_PORTS = {"http": 80, "https": 443}
NON_PUBLIC_HOSTS = {"localhost", "metadata", "instance-data", "metadata.google.internal"}
NON_PUBLIC_SUFFIXES = (".localhost", ".local", ".internal", ".home", ".lan", ".localdomain")
AUTHORIZATION_PLACEHOLDERS = ("à renseigner", "a renseigner", "à confirmer", "a confirmer", "todo", "tbd", "to be completed")
TRANSACTION_PREFIX = ".collect_site_txn_"
TRANSACTION_FILE = "transaction.json"
_PERSIST_THREAD_LOCK = threading.Lock()
SKIP_EXTENSIONS = {
    ".7z", ".avi", ".bin", ".css", ".csv", ".doc", ".docx", ".eot", ".exe", ".gif", ".gz", ".ico",
    ".jpeg", ".jpg", ".js", ".m4a", ".mov", ".mp3", ".mp4", ".mpeg", ".pdf", ".png", ".ppt", ".pptx",
    ".rar", ".svg", ".tar", ".tif", ".tiff", ".ttf", ".wav", ".webm", ".webp", ".woff", ".woff2", ".xls", ".xlsx", ".xml", ".zip",
}


class UnsafeURL(ValueError):
    """Raised when a URL could escape the explicitly authorized public origin."""


def _authorization_confirmed(authorization: Any) -> bool:
    if not isinstance(authorization, dict):
        return False
    authorized_by = authorization.get("authorized_by")
    if not isinstance(authorized_by, str) or not authorized_by.strip():
        return False
    normalized = authorized_by.strip().casefold()
    if normalized.startswith(AUTHORIZATION_PLACEHOLDERS):
        return False
    authorized_at = authorization.get("authorized_at")
    if not isinstance(authorized_at, str) or not authorized_at.strip():
        return False
    try:
        parsed_at = dt.datetime.fromisoformat(authorized_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed_at.tzinfo is not None


def _contains_control(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def _canonical_hostname(hostname: str) -> str:
    if not hostname or _contains_control(hostname) or "\\" in hostname or hostname.endswith("."):
        raise UnsafeURL("Hôte vide, ambigu ou invalide.")
    if "%" in hostname:
        raise UnsafeURL("Les identifiants de zone et hôtes encodés sont refusés.")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        try:
            canonical = hostname.encode("idna").decode("ascii").lower()
        except UnicodeError as exc:
            raise UnsafeURL("Nom d'hôte IDNA invalide.") from exc
        if len(canonical) > 253 or any(
            not label
            or len(label) > 63
            or not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", label)
            for label in canonical.split(".")
        ):
            raise UnsafeURL("Nom d'hôte DNS invalide.")
        if canonical in NON_PUBLIC_HOSTS or canonical.endswith(NON_PUBLIC_SUFFIXES):
            raise UnsafeURL(f"Hôte non public refusé: {canonical}")
        return canonical
    if not address.is_global:
        raise UnsafeURL(f"Adresse IP non publique refusée: {address}")
    return address.compressed.lower()


def _split_safe_url(url: str) -> tuple[urllib.parse.SplitResult, str, str, int, bool]:
    if not isinstance(url, str) or not url or _contains_control(url) or "\\" in url:
        raise UnsafeURL("URL vide, ambiguë ou contenant des caractères interdits.")
    try:
        parsed = urllib.parse.urlsplit(url)
        scheme = parsed.scheme.lower()
        if scheme not in DEFAULT_PORTS or not parsed.netloc:
            raise UnsafeURL("Seules les URL HTTP(S) absolues sont autorisées.")
        if parsed.username is not None or parsed.password is not None:
            raise UnsafeURL("Les identifiants intégrés à l'URL sont refusés.")
        if parsed.netloc.endswith(":"):
            raise UnsafeURL("Port vide ou ambigu refusé.")
        hostname = _canonical_hostname(parsed.hostname or "")
        explicit_port = parsed.port is not None
        port = parsed.port if explicit_port else DEFAULT_PORTS[scheme]
    except (UnicodeError, ValueError) as exc:
        if isinstance(exc, UnsafeURL):
            raise
        raise UnsafeURL(f"URL invalide: {url}") from exc
    if port is None or not 1 <= port <= 65535:
        raise UnsafeURL("Port réseau invalide.")
    return parsed, scheme, hostname, port, explicit_port


def _public_endpoints(hostname: str, port: int) -> tuple[tuple[int, int, int, tuple[Any, ...], str], ...]:
    """Resolve once, reject every non-public answer, and retain numeric endpoints."""

    try:
        literal = ipaddress.ip_address(hostname)
    except ValueError:
        try:
            answers = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
        except OSError as exc:
            raise UnsafeURL(f"Résolution DNS impossible pour {hostname}: {exc}") from exc
        endpoints: dict[tuple[int, int, int, tuple[Any, ...]], str] = {}
        for answer in answers:
            family, socktype, proto, _canonname, sockaddr = answer
            sockaddr = answer[4]
            if not sockaddr:
                continue
            raw_address = str(sockaddr[0]).split("%", 1)[0]
            try:
                address = ipaddress.ip_address(raw_address)
            except ValueError as exc:
                raise UnsafeURL(f"Réponse DNS invalide pour {hostname}: {raw_address}") from exc
            if not address.is_global:
                raise UnsafeURL(f"Résolution DNS non publique refusée pour {hostname}: {address}")
            numeric = address.compressed.lower()
            endpoints[(family, socktype or socket.SOCK_STREAM, proto or socket.IPPROTO_TCP, tuple(sockaddr))] = numeric
        if not endpoints:
            raise UnsafeURL(f"Aucune adresse publique résolue pour {hostname}.")
        return tuple((*key, endpoints[key]) for key in sorted(endpoints, key=lambda value: endpoints[value]))
    if not literal.is_global:
        raise UnsafeURL(f"Adresse IP non publique refusée: {literal}")
    numeric = literal.compressed.lower()
    if literal.version == 6:
        return ((socket.AF_INET6, socket.SOCK_STREAM, socket.IPPROTO_TCP, (numeric, port, 0, 0), numeric),)
    return ((socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, (numeric, port), numeric),)


def _public_addresses(hostname: str, port: int) -> tuple[str, ...]:
    """Resolve a host immediately before I/O and reject every non-public answer."""

    return tuple(endpoint[4] for endpoint in _public_endpoints(hostname, port))


def _connect_public(
    hostname: str,
    port: int,
    timeout: float | object = socket._GLOBAL_DEFAULT_TIMEOUT,
    source_address: tuple[str, int] | None = None,
) -> socket.socket:
    """Connect to a numeric endpoint from the validated DNS answer without re-resolving it."""

    endpoints = _public_endpoints(hostname, port)
    last_error: OSError | None = None
    for family, socktype, proto, sockaddr, _numeric in endpoints:
        sock: socket.socket | None = None
        try:
            sock = socket.socket(family, socktype, proto)
            if timeout is not socket._GLOBAL_DEFAULT_TIMEOUT:
                sock.settimeout(timeout)
            if source_address:
                sock.bind(source_address)
            sock.connect(sockaddr)
            return sock
        except OSError as exc:
            last_error = exc
            if sock is not None:
                sock.close()
    if last_error is not None:
        raise last_error
    raise UnsafeURL(f"Aucun endpoint public connectable pour {hostname}.")


class PinnedHTTPConnection(http.client.HTTPConnection):
    """HTTP connection pinned to the exact public IP set validated for the hostname."""

    def connect(self) -> None:
        if self._tunnel_host:
            raise UnsafeURL("Les tunnels et proxys sont refusés par le collecteur.")
        self.sock = _connect_public(self.host, self.port, self.timeout, self.source_address)


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    """Pinned TCP connection with TLS SNI and certificate checks on the original host."""

    def connect(self) -> None:
        if self._tunnel_host:
            raise UnsafeURL("Les tunnels et proxys sont refusés par le collecteur.")
        raw_socket = _connect_public(self.host, self.port, self.timeout, self.source_address)
        try:
            self.sock = self._context.wrap_socket(raw_socket, server_hostname=self.host)
        except Exception:
            raw_socket.close()
            raise


class PinnedHTTPHandler(urllib.request.HTTPHandler):
    def http_open(self, request: urllib.request.Request) -> Any:
        return self.do_open(PinnedHTTPConnection, request)


class PinnedHTTPSHandler(urllib.request.HTTPSHandler):
    def __init__(self, context: ssl.SSLContext | None = None) -> None:
        super().__init__(context=context)

    def https_open(self, request: urllib.request.Request) -> Any:
        return self.do_open(
            PinnedHTTPSConnection,
            request,
            context=self._context,
        )


class URLPolicy:
    """Exact-origin and public-network policy shared by all crawler requests."""

    def __init__(self, root_url: str):
        parsed, self.scheme, self.hostname, self.port, explicit_port = _split_safe_url(root_url)
        self.origin = (self.scheme, self.hostname, self.port)
        host_for_netloc = f"[{self.hostname}]" if ":" in self.hostname else self.hostname
        self.netloc = host_for_netloc
        if explicit_port or self.port != DEFAULT_PORTS[self.scheme]:
            self.netloc += f":{self.port}"
        self.root_url = self.canonicalize(root_url, keep_query=True)

    def canonicalize(self, url: str, keep_query: bool = False) -> str:
        parsed, scheme, hostname, port, _ = _split_safe_url(url)
        if (scheme, hostname, port) != self.origin:
            raise UnsafeURL("URL hors origine autorisée (schéma, hôte ou port différent).")
        path = re.sub(r"/{2,}", "/", parsed.path or "/")
        query = parsed.query if keep_query else ""
        return urllib.parse.urlunsplit((self.scheme, self.netloc, path, query, ""))

    def validate_request(self, url: str) -> str:
        canonical = self.canonicalize(url, keep_query=True)
        _public_addresses(self.hostname, self.port)
        return canonical


def _fully_unquote(value: str) -> str:
    current = value
    for _ in range(16):
        decoded = urllib.parse.unquote(current, errors="replace")
        if decoded == current:
            return decoded
        current = decoded
    raise UnsafeURL("Encodage URL excessivement imbriqué refusé.")


def _scope_path(url: str) -> str:
    path = _fully_unquote(urllib.parse.urlsplit(url).path or "/").replace("\\", "/")
    if _contains_control(path):
        raise UnsafeURL("Chemin URL contenant des caractères de contrôle refusé.")
    trailing_slash = path.endswith("/")
    path = re.sub(r"/{2,}", "/", path)
    normalized = posixpath.normpath(path)
    if not normalized.startswith("/"):
        normalized = "/" + normalized
    if trailing_slash and normalized != "/":
        normalized += "/"
    return normalized


def _path_is_within(path: str, prefix: str) -> bool:
    if prefix == "/":
        return True
    base = prefix.rstrip("/")
    return path == base or path.startswith(base + "/")


class URLScope:
    """Manifest-provided page allowlist and deny patterns."""

    def __init__(
        self,
        policy: URLPolicy,
        include_urls: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        keep_query: bool = False,
    ):
        self.policy = policy
        self.keep_query = keep_query
        raw_includes = [policy.root_url] if include_urls is None else include_urls
        if not isinstance(raw_includes, list) or any(not isinstance(item, str) for item in raw_includes):
            raise ValueError("scope.include_urls doit être une liste d'URL.")
        raw_excludes = [] if exclude_patterns is None else exclude_patterns
        if not isinstance(raw_excludes, list) or any(not isinstance(item, str) or not item for item in raw_excludes):
            raise ValueError("scope.exclude_patterns doit être une liste de motifs non vides.")
        self.seeds: list[str] = []
        self.include_paths: list[str] = []
        for include in raw_includes:
            normalized = normalize_url(policy.root_url, include, policy, keep_query)
            if not normalized:
                raise UnsafeURL(f"URL incluse invalide ou hors origine: {include}")
            if normalized not in self.seeds:
                self.seeds.append(normalized)
                self.include_paths.append(_scope_path(normalized))
        try:
            self.exclude_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in raw_excludes]
        except re.error as exc:
            raise ValueError(f"Motif d'exclusion invalide: {exc}") from exc
        self.raw_exclude_patterns = list(raw_excludes)

    def allows(self, url: str) -> bool:
        try:
            # Always inspect the query for exclusions, including a query added
            # by a redirect when discovery itself is configured to drop queries.
            canonical = self.policy.canonicalize(url, keep_query=True)
            path = _scope_path(canonical)
            decoded_url = _fully_unquote(canonical)
        except (ValueError, UnicodeError):
            return False
        if not any(_path_is_within(path, prefix) for prefix in self.include_paths):
            return False
        candidates = (canonical, decoded_url, path)
        return not any(pattern.search(candidate) for pattern in self.exclude_patterns for candidate in candidates)


class SameHostRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, policy: URLPolicy | str, scope: URLScope | None = None):
        self.policy = policy if isinstance(policy, URLPolicy) else URLPolicy(policy)
        self.scope = scope

    def redirect_request(self, req: urllib.request.Request, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> urllib.request.Request | None:
        try:
            self.policy.validate_request(newurl)
        except UnsafeURL as exc:
            raise urllib.error.URLError(f"Redirection hors origine publique refusée: {newurl} ({exc})") from exc
        if self.scope is not None and not self.scope.allows(newurl):
            raise urllib.error.URLError(f"Redirection hors périmètre du manifeste refusée: {newurl}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.title_parts: list[str] = []
        self.in_title = False
        self.canonical: str | None = None
        self.meta_robots: str | None = None
        self.html_lang: str | None = None
        self.jsonld_blocks = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): (value or "") for key, value in attrs}
        tag = tag.lower()
        if tag == "html" and values.get("lang"):
            self.html_lang = values["lang"]
        elif tag == "title":
            self.in_title = True
        elif tag == "a" and values.get("href"):
            rel = {item.lower() for item in values.get("rel", "").split()}
            if "nofollow" not in rel:
                self.links.append(values["href"])
        elif tag == "link" and "canonical" in values.get("rel", "").lower().split() and values.get("href"):
            self.canonical = values["href"]
        elif tag == "meta" and values.get("name", "").lower() in {"robots", "googlebot"}:
            self.meta_robots = values.get("content", "")
        elif tag == "script" and values.get("type", "").lower() == "application/ld+json":
            self.jsonld_blocks += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)

    @property
    def title(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self.title_parts)).strip()[:500]

    @property
    def follow_allowed(self) -> bool:
        directives = {item.strip().lower() for item in (self.meta_robots or "").split(",")}
        return "nofollow" not in directives and "none" not in directives


def same_host(url: str, root_url: str | URLPolicy, resolve: bool = False) -> bool:
    """Return whether *url* is a safe member of the root's exact origin.

    The historical name is retained for callers, but the comparison includes
    scheme and effective port as well as host. Literal non-public destinations
    are always rejected; DNS answers are checked when ``resolve`` is true.
    """

    try:
        policy = root_url if isinstance(root_url, URLPolicy) else URLPolicy(root_url)
        if resolve:
            policy.validate_request(url)
        else:
            policy.canonicalize(url, keep_query=True)
    except (ValueError, UnicodeError):
        return False
    return True


def _normalization_policy(root_url: str | URLPolicy, base: str) -> URLPolicy:
    if isinstance(root_url, URLPolicy):
        return root_url
    if "://" in root_url:
        return URLPolicy(root_url)
    # Backwards-compatible host-only callers remain safe because scheme and
    # port are derived from the absolute base URL rather than from the link.
    policy = URLPolicy(base)
    if _canonical_hostname(root_url) != policy.hostname:
        raise UnsafeURL("L'hôte racine ne correspond pas à l'URL de base.")
    return policy


def normalize_url(base: str, href: str, root_url: str | URLPolicy, keep_query: bool = False) -> str | None:
    if not isinstance(href, str):
        return None
    href = href.strip()
    if not href or href.lower().startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return None
    try:
        policy = _normalization_policy(root_url, base)
        absolute = urllib.parse.urljoin(base, href)
        normalized = policy.canonicalize(absolute, keep_query=keep_query)
        parsed = urllib.parse.urlsplit(normalized)
        suffix = Path(_fully_unquote(parsed.path).lower()).suffix
    except (ValueError, UnicodeError):
        return None
    if suffix in SKIP_EXTENSIONS:
        return None
    return normalized


def _fetch(
    opener: urllib.request.OpenerDirector,
    url: str,
    timeout: float,
    max_bytes: int,
    policy: URLPolicy | None = None,
) -> tuple[int, dict[str, str], bytes, str]:
    policy = policy or URLPolicy(url)
    request_url = policy.validate_request(url)
    request = urllib.request.Request(request_url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1"}, method="GET")
    with opener.open(request, timeout=timeout) as response:
        status = int(getattr(response, "status", 200))
        headers = {key.lower(): value for key, value in response.headers.items()}
        final_url = policy.canonicalize(response.geturl(), keep_query=True)
        declared = response.headers.get("Content-Length")
        if declared:
            try:
                declared_size = int(declared)
            except ValueError as exc:
                raise ValueError("Content-Length invalide.") from exc
            if declared_size < 0 or declared_size > max_bytes:
                raise ValueError(f"Réponse trop volumineuse ({declared} octets)")
        body = response.read(max_bytes + 1)
        if len(body) > max_bytes:
            raise ValueError(f"Réponse supérieure à {max_bytes} octets")
        return status, headers, body, final_url


def _load_robots(
    opener: urllib.request.OpenerDirector,
    root_url: str,
    timeout: float,
    max_bytes: int,
    fail_open: bool,
    policy: URLPolicy | None = None,
) -> tuple[urllib.robotparser.RobotFileParser, dict[str, Any]]:
    policy = policy or URLPolicy(root_url)
    robots_url = urllib.parse.urljoin(root_url, "/robots.txt")
    parser = urllib.robotparser.RobotFileParser()
    parser.set_url(robots_url)
    record: dict[str, Any] = {"url": robots_url, "status": None, "body": b"", "note": ""}
    try:
        status, headers, body, final_url = _fetch(opener, robots_url, timeout, min(max_bytes, 1024 * 1024), policy)
        text = body.decode("utf-8", errors="replace")
        parser.parse(text.splitlines())
        record.update({"url": final_url, "status": status, "body": body})
    except UnsafeURL as exc:
        raise RuntimeError(f"robots.txt refusé par la politique réseau; crawl arrêté: {exc}") from exc
    except urllib.error.HTTPError as exc:
        record["status"] = exc.code
        if exc.code == 404:
            parser.parse([])
            record["note"] = "robots.txt absent (404)."
        else:
            raise RuntimeError(f"robots.txt inaccessible (HTTP {exc.code}); crawl arrêté.") from exc
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        if not fail_open:
            raise RuntimeError(f"robots.txt non vérifiable; crawl arrêté: {exc}") from exc
        parser.parse([])
        record["note"] = f"Mode fail-open explicitement demandé: {exc}"
    return parser, record


def crawl(
    root_url: str,
    max_pages: int,
    delay: float,
    timeout: float,
    max_bytes: int,
    keep_query: bool = False,
    fail_open_robots: bool = False,
    include_urls: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    policy = URLPolicy(root_url)
    scope = URLScope(policy, include_urls, exclude_patterns, keep_query)
    max_pages = min(max(1, max_pages), HARD_MAX_PAGES)
    max_bytes = min(max(1024, max_bytes), HARD_MAX_BYTES)
    # Environment proxy settings could resolve the target differently from the
    # DNS answers just validated locally, so the crawler deliberately ignores
    # them and uses a direct read-only connection.
    robots_opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}), SameHostRedirectHandler(policy),
        PinnedHTTPHandler(), PinnedHTTPSHandler(),
    )
    robots, robots_record = _load_robots(robots_opener, policy.root_url, timeout, max_bytes, fail_open_robots, policy)
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}), SameHostRedirectHandler(policy, scope),
        PinnedHTTPHandler(), PinnedHTTPSHandler(),
    )
    starts = [seed for seed in scope.seeds if scope.allows(seed)]
    queue: deque[str] = deque(starts)
    queued = set(starts)
    visited: set[str] = set()
    pages: list[dict[str, Any]] = []
    last_request_at = 0.0
    while queue and len(pages) < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)
        if not robots.can_fetch(USER_AGENT, url):
            pages.append({"url": url, "status": None, "error": "Bloqué par robots.txt", "body": b"", "headers": {}, "parser": None, "elapsed_ms": 0})
            continue
        wait = delay - (time.monotonic() - last_request_at)
        if wait > 0:
            time.sleep(wait)
        started = time.monotonic()
        try:
            status, headers, body, final_url = _fetch(opener, url, timeout, max_bytes, policy)
            last_request_at = time.monotonic()
            if not scope.allows(final_url):
                raise RuntimeError("Réponse finale hors périmètre du manifeste refusée.")
            content_type = headers.get("content-type", "").lower()
            page_parser: PageParser | None = None
            if "html" in content_type:
                charset = "utf-8"
                match = re.search(r"charset=([^;\s]+)", content_type)
                if match:
                    charset = match.group(1).strip('"\'')
                html = body.decode(charset, errors="replace")
                page_parser = PageParser()
                page_parser.feed(html)
                if page_parser.follow_allowed:
                    for href in page_parser.links:
                        candidate = normalize_url(final_url, href, policy, keep_query)
                        if candidate and scope.allows(candidate) and candidate not in queued and candidate not in visited:
                            queued.add(candidate)
                            queue.append(candidate)
            pages.append({"url": final_url, "requested_url": url, "status": status, "error": None, "body": body, "headers": headers, "parser": page_parser, "elapsed_ms": round((time.monotonic() - started) * 1000)})
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError, RuntimeError) as exc:
            last_request_at = time.monotonic()
            status = exc.code if isinstance(exc, urllib.error.HTTPError) else None
            pages.append({"url": url, "status": status, "error": str(exc), "body": b"", "headers": {}, "parser": None, "elapsed_ms": round((time.monotonic() - started) * 1000)})
    return pages, robots_record


def _utc_now_microseconds() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def utc_now() -> str:
    """Compatibility hook, now retaining microseconds for persistence IDs."""

    return _utc_now_microseconds()


def _new_run_identity() -> tuple[str, str]:
    timestamp = utc_now()
    moment = dt.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    run_id = f"collect_{moment.strftime('%Y%m%d_%H%M%S_%f')}_{uuid.uuid4().hex}"
    return timestamp, run_id


def _bytes_hash(value: Any, label: str) -> str:
    if not isinstance(value, (bytes, bytearray)):
        raise TypeError(f"{label} doit être une séquence d'octets.")
    return hashlib.sha256(bytes(value)).hexdigest()


def _parser_fingerprint(parser: Any) -> dict[str, Any] | None:
    if parser is None:
        return None
    if not isinstance(parser, PageParser):
        raise TypeError("page.parser doit être un PageParser ou null.")
    return {
        "title": parser.title,
        "canonical": parser.canonical,
        "html_lang": parser.html_lang,
        "meta_robots": parser.meta_robots,
        "jsonld_blocks": parser.jsonld_blocks,
        "links": list(parser.links),
    }


def _crawl_input_fingerprint(pages: list[dict[str, Any]], robots: dict[str, Any]) -> str:
    payload = {
        "robots": {
            "url": robots.get("url"),
            "status": robots.get("status"),
            "note": robots.get("note"),
            "body_sha256": _bytes_hash(robots.get("body", b""), "robots.body"),
        },
        "pages": [
            {
                "url": page.get("url"),
                "requested_url": page.get("requested_url"),
                "status": page.get("status"),
                "error": page.get("error"),
                "headers": page.get("headers", {}),
                "elapsed_ms": page.get("elapsed_ms"),
                "body_sha256": _bytes_hash(page.get("body", b""), "page.body"),
                "parser": _parser_fingerprint(page.get("parser")),
            }
            for page in pages
        ],
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _fsync_directory(path: Path) -> None:
    try:
        descriptor = os.open(str(path), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


def _atomic_write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent), text=True)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
        _fsync_directory(path.parent)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _atomic_write_json(path: Path, value: Any) -> None:
    _atomic_write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n")


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
        _fsync_directory(path.parent)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


@contextlib.contextmanager
def _persist_lock(project: Path):
    if not project.is_dir():
        raise FileNotFoundError(f"Projet introuvable: {project}")
    lock_path = project / ".collect_site.lock"
    with _PERSIST_THREAD_LOCK:
        descriptor = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            yield
        finally:
            with contextlib.suppress(OSError):
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)


def _upsert_jsonl(path: Path, records: list[dict[str, Any]], identifier_key: str) -> None:
    existing = read_jsonl(path) if path.is_file() else []
    by_identifier: dict[str, dict[str, Any]] = {}
    for record in existing:
        identifier = record.get(identifier_key)
        if not isinstance(identifier, str) or not identifier:
            raise ValueError(f"{path}: {identifier_key} absent ou invalide.")
        if identifier in by_identifier:
            raise ValueError(f"{path}: {identifier_key} dupliqué: {identifier}")
        by_identifier[identifier] = record
    changed = False
    for record in records:
        identifier = record.get(identifier_key)
        if not isinstance(identifier, str) or not identifier:
            raise ValueError(f"Nouvel enregistrement sans {identifier_key} valide.")
        previous = by_identifier.get(identifier)
        if previous is not None:
            if previous != record:
                raise RuntimeError(f"Collision non idempotente sur {identifier_key}={identifier}.")
            continue
        existing.append(record)
        by_identifier[identifier] = record
        changed = True
    if changed:
        serialized = "".join(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n" for record in existing)
        _atomic_write_text(path, serialized)


def _timestamp_max(current: Any, candidate: str) -> str:
    if not isinstance(current, str):
        return candidate
    try:
        current_value = dt.datetime.fromisoformat(current.replace("Z", "+00:00"))
        candidate_value = dt.datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError:
        return candidate
    return current if current_value >= candidate_value else candidate


def _install_raw_directory(project: Path, transaction_dir: Path, transaction: dict[str, Any]) -> None:
    run_id = transaction["run_id"]
    stage = transaction_dir / "raw"
    destination = project / "raw" / run_id
    expected = transaction.get("raw_files", {})
    if not isinstance(expected, dict) or any(
        not isinstance(name, str)
        or not re.fullmatch(r"[a-zA-Z0-9_.-]+", name)
        or not isinstance(digest, str)
        or not re.fullmatch(r"[a-f0-9]{64}", digest)
        for name, digest in expected.items()
    ):
        raise ValueError("Journal de transaction: raw_files invalide.")
    if not destination.exists():
        if stage.is_symlink() or not stage.is_dir():
            raise RuntimeError(f"Répertoire brut préparé introuvable pour {run_id}.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        os.replace(stage, destination)
        _fsync_directory(destination.parent)
    if destination.is_symlink() or not destination.is_dir():
        raise RuntimeError(f"Collision de chemin brut pour {run_id}.")
    children = list(destination.iterdir())
    if any(path.is_symlink() or not path.is_file() for path in children):
        raise RuntimeError(f"Contenu brut inattendu pour {run_id}.")
    actual_files = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in children}
    if actual_files != expected:
        raise RuntimeError(f"Le répertoire brut existant ne correspond pas à la transaction {run_id}.")


def _update_manifest_for_transaction(project: Path, transaction: dict[str, Any]) -> None:
    manifest_path = project / "audit_manifest.json"
    manifest = read_json(manifest_path)
    if manifest.get("audit_id") != transaction.get("audit_id"):
        raise RuntimeError("Le manifeste ne correspond plus à l'audit de la transaction.")
    run_ids = manifest.setdefault("run_ids", {})
    if not isinstance(run_ids, dict):
        raise ValueError("audit_manifest.run_ids doit être un objet.")
    collector_ids = run_ids.setdefault("collector", [])
    if not isinstance(collector_ids, list):
        raise ValueError("audit_manifest.run_ids.collector doit être une liste.")
    if transaction["run_id"] not in collector_ids:
        collector_ids.append(transaction["run_id"])
    manifest["updated_at"] = _timestamp_max(manifest.get("updated_at"), transaction["timestamp"])
    if manifest.get("status") == "planned":
        manifest["status"] = "collecting"
    _atomic_write_json(manifest_path, manifest)


def _load_transaction(transaction_dir: Path) -> dict[str, Any]:
    if transaction_dir.is_symlink():
        raise RuntimeError(f"Transaction symbolique refusée: {transaction_dir}")
    transaction = read_json(transaction_dir / TRANSACTION_FILE)
    expected_run_id = transaction_dir.name[len(TRANSACTION_PREFIX):]
    if not isinstance(transaction, dict) or transaction.get("version") != 1:
        raise ValueError(f"Journal de transaction invalide: {transaction_dir}")
    run_id = transaction.get("run_id")
    if run_id != expected_run_id or not isinstance(run_id, str) or not re.fullmatch(r"collect_[a-z0-9_-]+", run_id):
        raise ValueError(f"run_id de transaction invalide: {run_id}")
    if (
        not isinstance(transaction.get("audit_id"), str)
        or not isinstance(transaction.get("timestamp"), str)
        or not isinstance(transaction.get("input_fingerprint"), str)
        or not isinstance(transaction.get("evidence_records"), list)
        or not isinstance(transaction.get("event"), dict)
        or not isinstance(transaction.get("result"), dict)
    ):
        raise ValueError(f"Contenu de transaction incomplet: {transaction_dir}")
    return transaction


def _commit_transaction(project: Path, transaction_dir: Path, transaction: dict[str, Any]) -> dict[str, Any]:
    run_id = transaction["run_id"]
    audit_id = transaction["audit_id"]
    current_manifest = read_json(project / "audit_manifest.json")
    if current_manifest.get("audit_id") != audit_id:
        raise RuntimeError("La transaction appartient à un autre audit.")
    result = transaction.get("result")
    if not isinstance(result, dict) or result.get("run_id") != run_id:
        raise ValueError("Résultat de transaction invalide.")
    evidence_records = transaction.get("evidence_records")
    event = transaction.get("event")
    if not isinstance(evidence_records, list) or any(
        not isinstance(record, dict)
        or record.get("audit_id") != audit_id
        or record.get("metadata", {}).get("run_id") != run_id
        for record in evidence_records
    ):
        raise ValueError("Preuves de transaction invalides.")
    if not isinstance(event, dict) or event.get("audit_id") != audit_id or event.get("run_id") != run_id:
        raise ValueError("Événement de transaction invalide.")
    _install_raw_directory(project, transaction_dir, transaction)
    _upsert_jsonl(project / "evidence.jsonl", evidence_records, "evidence_id")
    _upsert_jsonl(project / "events.jsonl", [event], "event_id")
    _update_manifest_for_transaction(project, transaction)
    shutil.rmtree(transaction_dir)
    _fsync_directory(project)
    return result


def _pending_transactions(project: Path) -> list[tuple[Path, dict[str, Any]]]:
    pending: list[tuple[Path, dict[str, Any]]] = []
    for transaction_dir in sorted(project.glob(f"{TRANSACTION_PREFIX}*")):
        marker = transaction_dir / TRANSACTION_FILE
        if marker.is_file():
            pending.append((transaction_dir, _load_transaction(transaction_dir)))
    return pending


def _prepare_transaction(
    project: Path,
    manifest: dict[str, Any],
    pages: list[dict[str, Any]],
    robots: dict[str, Any],
    input_fingerprint: str,
) -> tuple[Path, dict[str, Any]]:
    audit_id = manifest["audit_id"]
    collector_ids = manifest.get("run_ids", {}).get("collector", []) if isinstance(manifest.get("run_ids", {}), dict) else []
    transaction_dir: Path | None = None
    timestamp = ""
    run_id = ""
    for _ in range(32):
        timestamp, run_id = _new_run_identity()
        candidate = project / f"{TRANSACTION_PREFIX}{run_id}"
        if run_id in collector_ids or (project / "raw" / run_id).exists():
            continue
        try:
            candidate.mkdir(mode=0o700)
        except FileExistsError:
            continue
        transaction_dir = candidate
        break
    if transaction_dir is None:
        raise RuntimeError("Impossible d'allouer un run_id de collecte unique après 32 tentatives.")
    records: list[dict[str, Any]] = []
    raw_files: dict[str, str] = {}
    raw_dir_relative = Path("raw") / run_id
    try:
        stage_raw = transaction_dir / "raw"
        stage_raw.mkdir()
        robots_body = bytes(robots.get("body", b""))
        robots_digest = _bytes_hash(robots_body, "robots.body")
        robots_raw_path = None
        if robots_body:
            raw_name = "robots.txt"
            _atomic_write_bytes(stage_raw / raw_name, robots_body)
            raw_files[raw_name] = robots_digest
            robots_raw_path = str(raw_dir_relative / raw_name)
        records.append({
            "schema_version": "3.0", "evidence_id": f"ev_{slugify(run_id)}_robots", "audit_id": audit_id, "check_id": "robots.fetch",
            "collected_at": timestamp, "expires_at": None, "source_type": "robots", "method": "http_get", "url": robots["url"],
            "scope": {"device": "desktop", "account_state": "clean", "user_agent": USER_AGENT}, "http_status": robots.get("status"),
            "content_type": "text/plain", "observation": robots.get("note") or "robots.txt collecté avant exploration.",
            "raw_hash": f"sha256:{robots_digest}" if robots_body else None, "raw_path": robots_raw_path, "status": "observed",
            "confidence": "confirmed", "collector": "collect_site.py", "authorization_permission": "public_web", "metadata": {"run_id": run_id},
        })
        for index, page in enumerate(pages, 1):
            body = bytes(page.get("body", b""))
            content_hash = _bytes_hash(body, "page.body")
            raw_path = None
            parsed: PageParser | None = page.get("parser")
            if parsed is not None and not isinstance(parsed, PageParser):
                raise TypeError("page.parser doit être un PageParser ou null.")
            if body:
                suffix = ".html" if parsed else ".bin"
                raw_name = f"page_{index:04d}_{content_hash[:12]}{suffix}"
                _atomic_write_bytes(stage_raw / raw_name, body)
                raw_files[raw_name] = content_hash
                raw_path = str(raw_dir_relative / raw_name)
            observation = page.get("error") or f"HTTP {page.get('status')} collecté en lecture seule."
            metadata = {"run_id": run_id, "requested_url": page.get("requested_url", page["url"]), "elapsed_ms": page.get("elapsed_ms")}
            if parsed:
                metadata.update({"canonical": parsed.canonical, "html_lang": parsed.html_lang, "meta_robots": parsed.meta_robots, "jsonld_blocks": parsed.jsonld_blocks, "links_discovered": len(parsed.links)})
            records.append({
                "schema_version": "3.0", "evidence_id": f"ev_{slugify(run_id)}_page_{index:04d}", "audit_id": audit_id, "check_id": "crawl.url",
                "collected_at": timestamp, "expires_at": None, "source_type": "web_page", "method": "http_get", "url": page["url"],
                "scope": {"device": "desktop", "account_state": "clean", "user_agent": USER_AGENT}, "http_status": page.get("status"),
                "content_type": page.get("headers", {}).get("content-type", ""), "title": parsed.title if parsed else "", "observation": observation,
                "raw_hash": f"sha256:{content_hash}" if body else None, "raw_path": raw_path,
                "status": "observed" if page.get("status") else "unknown", "confidence": "confirmed" if page.get("status") else "strong",
                "collector": "collect_site.py", "authorization_permission": "public_web", "metadata": metadata,
            })
        target_status = "collecting" if manifest.get("status") == "planned" else manifest.get("status")
        event = {
            "schema_version": "3.0", "event_id": f"event_{slugify(run_id)}", "audit_id": audit_id, "at": timestamp, "run_id": run_id,
            "actor": "collect_site.py", "actor_type": "script", "event_type": "collected", "object_type": "audit", "object_id": audit_id,
            "from_status": None, "to_status": target_status, "message": f"Crawl public terminé: {len(pages)} URL(s) traitée(s).",
            "artifacts": [str(raw_dir_relative)], "metadata": {"run_id": run_id, "input_fingerprint": input_fingerprint},
        }
        result = {"run_id": run_id, "pages": len(pages), "evidence_records": len(records), "raw_dir": str(project / raw_dir_relative)}
        transaction = {
            "version": 1,
            "run_id": run_id,
            "audit_id": audit_id,
            "timestamp": timestamp,
            "input_fingerprint": input_fingerprint,
            "raw_files": raw_files,
            "evidence_records": records,
            "event": event,
            "result": result,
        }
        _atomic_write_json(transaction_dir / TRANSACTION_FILE, transaction)
        # Make the prepared journal durable before any project artifact is
        # replaced, so a crash always leaves either no transaction or one that
        # can be replayed idempotently.
        _fsync_directory(project)
        return transaction_dir, transaction
    except Exception:
        shutil.rmtree(transaction_dir, ignore_errors=True)
        raise


def persist(project: Path, pages: list[dict[str, Any]], robots: dict[str, Any]) -> dict[str, Any]:
    project = Path(project)
    input_fingerprint = _crawl_input_fingerprint(pages, robots)
    with _persist_lock(project):
        recovered_result: dict[str, Any] | None = None
        for transaction_dir, transaction in _pending_transactions(project):
            recovered_result = _commit_transaction(project, transaction_dir, transaction)
        if recovered_result is not None:
            return recovered_result

        manifest = read_json(project / "audit_manifest.json")
        authorization = manifest.get("authorization", {})
        permissions = authorization.get("permissions", []) if isinstance(authorization, dict) else []
        if not isinstance(permissions, list) or "public_web" not in permissions:
            raise PermissionError("Le manifeste n'accorde pas la permission public_web.")
        transaction_dir, transaction = _prepare_transaction(project, manifest, pages, robots, input_fingerprint)
        return _commit_transaction(project, transaction_dir, transaction)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root_url", nargs="?", help="URL HTTP(S), ignorée si --project fournit le manifeste")
    parser.add_argument("--project", type=Path, help="Projet V3 dans lequel stocker preuves et captures")
    parser.add_argument("--max-pages", type=int, help="Réduire le plafond du manifeste (20 par défaut sans projet)")
    parser.add_argument("--delay", type=float, default=1.0, help="Délai minimal entre requêtes (secondes)")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--max-bytes", type=int, default=2 * 1024 * 1024)
    parser.add_argument("--keep-query", action="store_true", help="Conserver les query strings; peut augmenter fortement le crawl")
    parser.add_argument("--fail-open-robots", action="store_true", help="Continuer si robots.txt est inaccessible; à utiliser uniquement avec autorisation explicite")
    parser.add_argument("--dry-run", action="store_true", help="Afficher le plan sans aucune requête réseau")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.max_pages is not None and (args.max_pages < 1 or args.max_pages > HARD_MAX_PAGES):
        print(f"ERREUR: --max-pages doit être compris entre 1 et {HARD_MAX_PAGES}.", file=sys.stderr)
        return 2
    if args.delay < 0.25:
        print("ERREUR: --delay doit être au moins 0,25 seconde.", file=sys.stderr)
        return 2
    if args.timeout <= 0:
        print("ERREUR: --timeout doit être strictement positif.", file=sys.stderr)
        return 2
    project = args.project.resolve() if args.project else None
    manifest_max_pages: int | None = None
    authorization_confirmed: bool | None = None
    if project:
        manifest = read_json(project / "audit_manifest.json")
        authorization = manifest.get("authorization", {})
        permissions = authorization.get("permissions", []) if isinstance(authorization, dict) else []
        if not isinstance(permissions, list) or "public_web" not in permissions:
            print("ERREUR: permission public_web absente du manifeste.", file=sys.stderr)
            return 2
        authorization_confirmed = _authorization_confirmed(authorization)
        scope_config = manifest.get("scope", {})
        if not isinstance(scope_config, dict):
            print("ERREUR: scope du manifeste invalide.", file=sys.stderr)
            return 2
        root_url = scope_config.get("root_url")
        manifest_max_pages = scope_config.get("max_pages")
        if (
            isinstance(manifest_max_pages, bool)
            or not isinstance(manifest_max_pages, int)
            or manifest_max_pages < 1
            or manifest_max_pages > HARD_MAX_PAGES
        ):
            print(f"ERREUR: scope.max_pages doit être compris entre 1 et {HARD_MAX_PAGES}.", file=sys.stderr)
            return 2
        include_urls = scope_config.get("include_urls")
        exclude_patterns = scope_config.get("exclude_patterns")
        effective_max_pages = min(manifest_max_pages, args.max_pages or manifest_max_pages)
    else:
        root_url = args.root_url
        include_urls = None
        exclude_patterns = None
        effective_max_pages = args.max_pages or DEFAULT_MAX_PAGES
    if not root_url:
        print("ERREUR: fournir root_url ou --project.", file=sys.stderr)
        return 2
    try:
        policy = URLPolicy(root_url)
        url_scope = URLScope(policy, include_urls, exclude_patterns, args.keep_query)
        if args.root_url and project:
            supplied_root = policy.canonicalize(args.root_url, keep_query=True)
            if supplied_root != policy.root_url:
                raise ValueError("l'URL fournie ne correspond pas exactement au manifeste.")
    except (ValueError, UnicodeError) as exc:
        print(f"ERREUR: configuration du crawl refusée: {exc}", file=sys.stderr)
        return 2
    effective_max_bytes = min(max(1024, args.max_bytes), HARD_MAX_BYTES)
    plan = {
        "root_url": policy.root_url,
        "same_host_only": True,
        "same_origin_only": True,
        "public_addresses_only": True,
        "dns_revalidated_before_request": True,
        "robots_honored": True,
        "max_pages": effective_max_pages,
        "manifest_max_pages": manifest_max_pages,
        "hard_max_pages": HARD_MAX_PAGES,
        "include_urls": url_scope.seeds,
        "exclude_patterns": url_scope.raw_exclude_patterns,
        "authorization_confirmed": authorization_confirmed,
        "delay_seconds": args.delay,
        "timeout_seconds": args.timeout,
        "max_bytes": effective_max_bytes,
        "user_agent": USER_AGENT,
        "network_performed": not args.dry_run,
    }
    if args.dry_run:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0
    if project and not authorization_confirmed:
        print("ERREUR: authorization.authorized_by doit identifier un approbateur avant toute requête réseau.", file=sys.stderr)
        return 2
    try:
        pages, robots = crawl(
            policy.root_url,
            effective_max_pages,
            args.delay,
            args.timeout,
            effective_max_bytes,
            args.keep_query,
            args.fail_open_robots,
            include_urls,
            exclude_patterns,
        )
        result = persist(project, pages, robots) if project else {"pages": len(pages), "records": [{"url": page["url"], "status": page["status"], "error": page["error"]} for page in pages]}
    except (ValueError, RuntimeError, PermissionError, urllib.error.URLError) as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
