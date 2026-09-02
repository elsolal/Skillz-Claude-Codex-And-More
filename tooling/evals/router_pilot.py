#!/usr/bin/env python3
"""Measure the figma-generate-library router pilot against its Git baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time
from typing import Any, Iterable


SCHEMA_VERSION = 1
BASELINE_COMMIT = "ffa29cae73b0ec47d5cd84bfb5eb6c1b82c66a7c"
ENTRY = ".claude/skills/figma-generate-library/SKILL.md"
BASELINE_SHA256 = "079d4427d8afe582c3202dd0fd6ff8cbb0260b2c2b37cdac2d7bc1ea4c624b0b"
BASELINE_BYTES = 12141
ROUTES = {
    "discovery": "references/discovery-phase.md",
    "foundations": "references/token-creation.md",
    "structure": "references/documentation-creation.md",
    "component": "references/component-creation.md",
    "integration": "references/code-connect-setup.md",
    "recovery": "references/error-recovery.md",
}
ASSERTIONS = (
    "figma-use",
    "search_design_system",
    "return",
    "figma.notify()",
    "setcurrentpageasync",
    "variables",
    "components",
    "all_scopes",
    "instance_swap",
    "node ids",
    "get_metadata",
    "get_screenshot",
    "no destructive cleanup",
    "state ledger",
    "code connect",
    "accessibility",
)


class PilotError(RuntimeError):
    pass


def _git(root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise PilotError(result.stderr.decode("utf-8", errors="replace").strip())
    return result.stdout


def _baseline(root: Path) -> bytes:
    content = _git(root, "show", f"{BASELINE_COMMIT}:{ENTRY}")
    if len(content) != BASELINE_BYTES:
        raise PilotError(f"baseline byte count drifted: {len(content)}")
    digest = hashlib.sha256(content).hexdigest()
    if digest != BASELINE_SHA256:
        raise PilotError(f"baseline hash drifted: {digest}")
    return content


def _frontmatter_value(content: bytes, key: str) -> str:
    text = content.decode("utf-8")
    for line in text.splitlines()[1:]:
        if line == "---":
            break
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip()
    raise PilotError(f"missing frontmatter field: {key}")


def _assertion_count(payload: bytes) -> int:
    lowered = payload.decode("utf-8", errors="replace").lower()
    return sum(assertion.lower() in lowered for assertion in ASSERTIONS)


def _benchmark(payload: bytes, repeat: int) -> int:
    samples: list[int] = []
    for _ in range(7):
        started = time.perf_counter_ns()
        for _ in range(repeat):
            _assertion_count(payload)
        samples.append((time.perf_counter_ns() - started) // repeat)
    return int(statistics.median(samples))


def build_report(root: Path, repeat: int) -> dict[str, Any]:
    root = root.resolve()
    baseline = _baseline(root)
    current = (root / ENTRY).read_bytes()
    if _frontmatter_value(baseline, "name") != _frontmatter_value(current, "name"):
        raise PilotError("public skill name changed")
    if _frontmatter_value(baseline, "description") != _frontmatter_value(current, "description"):
        raise PilotError("public skill description changed")
    skill_root = root / Path(ENTRY).parent
    routes: list[dict[str, Any]] = []
    for name, relative in ROUTES.items():
        resource = (skill_root / relative).read_bytes()
        before = baseline + resource
        after = current + resource
        assertions_before = _assertion_count(before)
        assertions_after = _assertion_count(after)
        reduction = len(before) - len(after)
        routes.append(
            {
                "route": name,
                "resource": relative,
                "context_before_bytes": len(before),
                "context_after_bytes": len(after),
                "context_reduction_bytes": reduction,
                "context_reduction_percent": round(reduction * 100 / len(before), 2),
                "assertions_before": assertions_before,
                "assertions_after": assertions_after,
                "assertion_success_rate": round(assertions_after / len(ASSERTIONS), 4),
                "evaluation_time_before_ns_median": _benchmark(before, repeat),
                "evaluation_time_after_ns_median": _benchmark(after, repeat),
            }
        )
    assertions_preserved = all(
        route["assertions_before"] == len(ASSERTIONS)
        and route["assertions_after"] == route["assertions_before"]
        for route in routes
    )
    context_reduced = all(route["context_reduction_bytes"] > 0 for route in routes)
    return {
        "schema_version": SCHEMA_VERSION,
        "pilot": "figma-generate-library",
        "baseline": {
            "commit": BASELINE_COMMIT,
            "entry_sha256": BASELINE_SHA256,
            "entry_bytes": len(baseline),
        },
        "router": {
            "entry_sha256": hashlib.sha256(current).hexdigest(),
            "entry_bytes": len(current),
        },
        "measurement": {
            "token_estimate": "ceil(utf8_bytes/4)",
            "timing_operation": "case-insensitive contract assertion scan",
            "timing_repeat": repeat,
            "timing_samples": 7,
            "timing_is_observational": True,
        },
        "assertions": list(ASSERTIONS),
        "routes": routes,
        "decision": {
            "assertions_preserved": assertions_preserved,
            "context_reduced": context_reduced,
            "generalize_router_pattern": assertions_preserved and context_reduced,
        },
    }


def _stable(payload: dict[str, Any]) -> dict[str, Any]:
    copy = json.loads(json.dumps(payload))
    for route in copy.get("routes", []):
        route.pop("evaluation_time_before_ns_median", None)
        route.pop("evaluation_time_after_ns_median", None)
    return copy


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeat", type=int, default=500)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.repeat < 1:
            raise PilotError("repeat must be positive")
        report = build_report(args.root, args.repeat)
        output = args.output if args.output.is_absolute() else args.root / args.output
        if args.check:
            existing = json.loads(output.read_text(encoding="utf-8"))
            if _stable(existing) != _stable(report):
                raise PilotError("router pilot report is stale")
            print(f"router pilot report is fresh: {args.output}")
            return 0
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote router pilot report: {args.output}")
        return 0
    except (OSError, json.JSONDecodeError, PilotError) as error:
        print(f"router pilot failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
