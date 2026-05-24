"""Scan arbitrary text for AI-typical patterns and em-dashes."""
from __future__ import annotations

from vibecheck.config import Config
from vibecheck.findings import Finding, generate_id


def scan_text(text: str, source: str, config: Config) -> list[Finding]:
    if not config.text_patterns_enabled or not text:
        return []

    findings: list[Finding] = []

    for pattern in config.text_patterns:
        if pattern in text:
            snippet = _extract_context(text, pattern)
            findings.append(
                Finding(
                    id=generate_id("text_pattern", source, pattern),
                    severity="info",
                    category="text_pattern",
                    source=source,
                    snippet=snippet,
                    suggested_fix=f"remove or rephrase '{pattern}'",
                    fixer="file_replace",
                    fix_payload={"source": source, "find": pattern, "replace": ""},
                )
            )

    if "—" in text:  # em-dash
        snippet = _extract_context(text, "—")
        findings.append(
            Finding(
                id=generate_id("em_dash", source, snippet),
                severity="info",
                category="em_dash",
                source=source,
                snippet=snippet,
                suggested_fix="replace em-dash with comma or period",
                fixer="file_replace",
                fix_payload={"source": source, "find": "—", "replace": "-"},
            )
        )

    return findings


def _extract_context(text: str, needle: str, window: int = 40) -> str:
    idx = text.find(needle)
    if idx == -1:
        return needle
    start = max(0, idx - window)
    end = min(len(text), idx + len(needle) + window)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return f"{prefix}{text[start:end]}{suffix}"
