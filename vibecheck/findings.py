"""Finding dataclass and helper functions."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Literal

Severity = Literal["critical", "warning", "info"]


@dataclass
class Finding:
    id: str
    severity: Severity
    category: str
    source: str
    snippet: str
    suggested_fix: str
    fixer: str
    fix_payload: dict = field(default_factory=dict)


def generate_id(category: str, source: str, snippet: str) -> str:
    """Stable 8-character hash for a finding."""
    key = f"{category}|{source}|{snippet}".encode("utf-8")
    return hashlib.sha256(key).hexdigest()[:8]


def group_by_severity(findings: list[Finding]) -> dict[str, list[Finding]]:
    """Group findings into {critical, warning, info} lists."""
    groups: dict[str, list[Finding]] = {"critical": [], "warning": [], "info": []}
    for f in findings:
        groups.setdefault(f.severity, []).append(f)
    return groups
