#!/usr/bin/env python3
"""Deterministic fixture runner for harness and workflow contract tests only."""

import json
from pathlib import Path
import sys


SCENARIOS = {
    "dev": (0, ["probe", "explore", "plan"], "Plan presented before write"),
    "discovery": (0, ["probe", "explore", "plan", "approval"], "Approval required"),
    "quick-fix": (0, ["probe", "implement", "gate"], "Quick fix gated"),
    "ship": (0, ["gate-verify", "handoff"], "Fresh gate required"),
    "quality-gate-stale": (3, ["gate-verify", "reject"], "Stale gate rejected"),
    "status": (0, ["probe", "status"], "Status is evidence-labelled"),
}


def main() -> int:
    scenario = sys.argv[1] if len(sys.argv) > 1 else ""
    if scenario not in SCENARIOS:
        print("unknown fixture scenario", file=sys.stderr)
        return 2
    exit_code, events, message = SCENARIOS[scenario]
    payload = {
        "schema_version": 1,
        "scenario": scenario,
        "events": events,
        "verdict": "PASS" if exit_code == 0 else "REJECTED",
        "fixture_only": True,
    }
    Path("run-result.json").write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    for event in events:
        print(f"EVENT:{event}")
    print(message)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
