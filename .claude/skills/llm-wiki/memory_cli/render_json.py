"""Stable JSON renderer for context outcomes."""

from __future__ import annotations

import json
from typing import Any, TextIO

from .contracts import PUBLIC_SCHEMA_VERSION
from .receipts import ContextOutcome


def context_envelope(outcome: ContextOutcome) -> dict[str, Any]:
    return {
        "schema_version": PUBLIC_SCHEMA_VERSION,
        "command": "context",
        "status": outcome.status,
        "project_id": outcome.project_id,
        "event_id": outcome.event_id,
        "data": outcome.data(),
        "warnings": list(outcome.warnings),
        "errors": list(outcome.errors),
    }


def render_context_json(outcome: ContextOutcome, *, stream: TextIO) -> None:
    print(
        json.dumps(
            context_envelope(outcome),
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        file=stream,
    )
