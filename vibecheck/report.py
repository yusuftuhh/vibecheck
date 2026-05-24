"""Render findings as human or JSON output."""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone

from rich.console import Console

from vibecheck import __version__
from vibecheck.findings import Finding, group_by_severity


_console = Console()


def render_json(findings: list[Finding], scan_targets: list[str]) -> str:
    payload = {
        "version": __version__,
        "scan_targets": scan_targets,
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "findings": [asdict(f) for f in findings],
        "summary": {sev: len(group) for sev, group in group_by_severity(findings).items()},
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def render_human(findings: list[Finding], scan_targets: list[str]) -> None:
    _console.print(f"[bold]vibecheck {__version__}[/bold] - scanning {', '.join(scan_targets)}")
    _console.print()

    if not findings:
        _console.print("[green]No findings. Clean.[/green]")
        return

    severity_colors = {"critical": "red", "warning": "yellow", "info": "cyan"}
    grouped = group_by_severity(findings)
    for sev in ("critical", "warning", "info"):
        bucket = grouped.get(sev, [])
        if not bucket:
            continue
        color = severity_colors[sev]
        _console.print(f"[{color}]{sev.upper()} ({len(bucket)} findings)[/{color}]")
        for f in bucket:
            _console.print(f"  [bold]{f.id}[/bold]  {f.category:17} {f.source}")
            _console.print(f"            [{color}]\"{f.snippet}\"[/{color}]")
            _console.print(f"            -> {f.suggested_fix}")
            _console.print()

    _console.print(
        "Run [bold]vibecheck fix --interactive[/bold] to walk through fixes, or"
    )
    _console.print(
        "    [bold]vibecheck fix --items <id1,id2,...>[/bold] to apply specific items."
    )
