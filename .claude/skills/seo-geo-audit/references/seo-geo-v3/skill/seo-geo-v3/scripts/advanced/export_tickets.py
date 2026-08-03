#!/usr/bin/env python3
"""Export V3 actions to import-ready CSV without calling Jira or Notion APIs."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from typing import Any, Iterable

from _advanced_common import compact_join, read_json, write_text


JIRA_PRIORITY = {"P0": "Highest", "P1": "High", "P2": "Medium", "P3": "Low"}
TERMINAL_STATUSES = {"done", "cancelled"}


def _safe_cell(value: Any) -> str:
    """Prevent spreadsheet formula execution while preserving readable text."""
    if value is None:
        return ""
    if isinstance(value, bool):
        text = "true" if value else "false"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, (list, tuple, set)):
        text = compact_join(value)
    elif isinstance(value, dict):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        text = str(value)
    if text.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def load_actions(path: Path) -> list[dict[str, Any]]:
    source = path / "actions.json" if path.is_dir() else path
    value = read_json(source)
    if not isinstance(value, dict) or not isinstance(value.get("actions"), list):
        raise ValueError(f"{source}: registre actions V3 attendu")
    return value["actions"]


def select_actions(
    actions: Iterable[dict[str, Any]],
    priorities: set[str] | None = None,
    statuses: set[str] | None = None,
    include_terminal: bool = False,
) -> list[dict[str, Any]]:
    selected = []
    for action in actions:
        if not include_terminal and action.get("status") in TERMINAL_STATUSES:
            continue
        if priorities and action.get("priority") not in priorities:
            continue
        if statuses and action.get("status") not in statuses:
            continue
        selected.append(action)
    return selected


def _description(action: dict[str, Any]) -> str:
    sections = [action.get("description", "")]
    if action.get("acceptance_criteria"):
        sections.append("Critères d'acceptation:\n- " + "\n- ".join(action["acceptance_criteria"]))
    if action.get("validation_method"):
        sections.append("Validation: " + str(action["validation_method"]))
    if action.get("rollback"):
        sections.append("Rollback: " + str(action["rollback"]))
    if action.get("target_urls"):
        sections.append("URLs: " + compact_join(action["target_urls"]))
    return "\n\n".join(section for section in sections if section)


def rows_for_format(actions: list[dict[str, Any]], target_format: str) -> tuple[list[str], list[dict[str, Any]]]:
    if target_format == "jira":
        fields = ["External ID", "Summary", "Issue Type", "Description", "Priority", "Assignee", "Due Date", "Labels", "Status"]
        rows = []
        for action in actions:
            labels = ["seo-geo-v3", action.get("stream"), action.get("impact"), *action.get("finding_ids", [])]
            rows.append({
                "External ID": action.get("action_id"), "Summary": action.get("title"), "Issue Type": "Task",
                "Description": _description(action), "Priority": JIRA_PRIORITY.get(str(action.get("priority")), "Medium"),
                "Assignee": action.get("owner"), "Due Date": action.get("due_date"), "Labels": compact_join(labels, ","),
                "Status": action.get("status"),
            })
        return fields, rows
    if target_format == "notion":
        fields = [
            "Name", "Action ID", "Status", "Priority", "Owner", "Due Date", "Stream", "Impact", "Effort",
            "Description", "Acceptance Criteria", "Validation", "Rollback", "Finding IDs", "Dependencies", "Target URLs",
        ]
        rows = [{
            "Name": action.get("title"), "Action ID": action.get("action_id"), "Status": action.get("status"),
            "Priority": action.get("priority"), "Owner": action.get("owner"), "Due Date": action.get("due_date"),
            "Stream": action.get("stream"), "Impact": action.get("impact"), "Effort": action.get("effort", {}).get("size"),
            "Description": action.get("description"), "Acceptance Criteria": compact_join(action.get("acceptance_criteria", [])),
            "Validation": action.get("validation_method"), "Rollback": action.get("rollback"),
            "Finding IDs": compact_join(action.get("finding_ids", [])), "Dependencies": compact_join(action.get("dependencies", [])),
            "Target URLs": compact_join(action.get("target_urls", [])),
        } for action in actions]
        return fields, rows
    fields = [
        "action_id", "title", "description", "stream", "priority", "status", "effort_size", "person_days",
        "impact", "owner", "due_date", "finding_ids", "evidence_ids", "dependencies", "acceptance_criteria",
        "validation_method", "rollback", "target_urls", "risk", "approval_required", "automation",
    ]
    rows = [{
        "action_id": action.get("action_id"), "title": action.get("title"), "description": action.get("description"),
        "stream": action.get("stream"), "priority": action.get("priority"), "status": action.get("status"),
        "effort_size": action.get("effort", {}).get("size"), "person_days": action.get("effort", {}).get("person_days"),
        "impact": action.get("impact"), "owner": action.get("owner"), "due_date": action.get("due_date"),
        "finding_ids": compact_join(action.get("finding_ids", [])), "evidence_ids": compact_join(action.get("evidence_ids", [])),
        "dependencies": compact_join(action.get("dependencies", [])),
        "acceptance_criteria": compact_join(action.get("acceptance_criteria", [])),
        "validation_method": action.get("validation_method"), "rollback": action.get("rollback"),
        "target_urls": compact_join(action.get("target_urls", [])), "risk": action.get("risk"),
        "approval_required": action.get("approval_required"), "automation": action.get("automation"),
    } for action in actions]
    return fields, rows


def render_csv(actions: list[dict[str, Any]], target_format: str = "generic", excel_bom: bool = False) -> str:
    fields, rows = rows_for_format(actions, target_format)
    output = io.StringIO(newline="")
    if excel_bom:
        output.write("\ufeff")
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: _safe_cell(row.get(field)) for field in fields})
    return output.getvalue()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Projet V3 ou actions.json")
    parser.add_argument("--format", choices=["generic", "jira", "notion"], default="generic")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--priority", action="append", choices=["P0", "P1", "P2", "P3"])
    parser.add_argument("--status", action="append")
    parser.add_argument("--include-terminal", action="store_true", help="Inclure done et cancelled")
    parser.add_argument("--excel-bom", action="store_true", help="Préfixer le CSV d'un BOM UTF-8")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        actions = select_actions(
            load_actions(args.input), set(args.priority or []), set(args.status or []), args.include_terminal,
        )
        write_text(args.output, render_csv(actions, args.format, args.excel_bom))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"ERREUR: {exc}") from exc
    print(f"{len(actions)} ticket(s) exporté(s) vers {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
