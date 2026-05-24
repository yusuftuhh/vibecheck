"""Load default and user-provided rule configuration."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


DEFAULT_TEXT_PATTERNS: list[str] = [
    "As an AI",
    "I'd be happy to",
    "I am happy to",
    "Let me know if",
    "🤖",
    "Generated with Claude",
    "Generated with ChatGPT",
    "Co-Authored-By:",
    "Co-authored-by: Claude",
    "Here's a comprehensive",
    "Hope this helps",
]

DEFAULT_FILE_PATHS: list[str] = [
    "CLAUDE.md",
    "AGENTS.md",
    "GEMINI.md",
    "COPILOT.md",
    ".claude/",
    ".cursor/",
    ".cursorrules",
    ".aider.conf.yml",
    ".aider.input.history",
    ".aider.chat.history.md",
    ".continue/",
    ".superpowers/",
    "docs/superpowers/",
]

DEFAULT_BOT_EMAIL_PATTERNS: list[str] = [
    "@anthropic.com",
    "@openai.com",
    "copilot[bot]",
    "noreply@anthropic.com",
    "noreply@openai.com",
]

DEFAULT_BRANCH_PATTERNS: list[str] = [
    "^claude/",
    "^ai/",
    "^agent/",
    "^gpt/",
    "^copilot/",
]


@dataclass
class Config:
    text_patterns_enabled: bool = True
    text_patterns: list[str] = field(default_factory=lambda: list(DEFAULT_TEXT_PATTERNS))
    file_paths: list[str] = field(default_factory=lambda: list(DEFAULT_FILE_PATHS))
    bot_email_patterns: list[str] = field(default_factory=lambda: list(DEFAULT_BOT_EMAIL_PATTERNS))
    branch_patterns: list[str] = field(default_factory=lambda: list(DEFAULT_BRANCH_PATTERNS))
    ignore_repos: list[str] = field(default_factory=list)
    ignore_paths: list[str] = field(default_factory=list)


def load_config(path: Path | None) -> Config:
    cfg = Config()
    if path is None or not path.exists():
        return cfg

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rules = data.get("rules", {})
    ignore = data.get("ignore", {})

    if "text_patterns" in rules:
        tp = rules["text_patterns"]
        if "enabled" in tp:
            cfg.text_patterns_enabled = bool(tp["enabled"])
        if "patterns" in tp:
            cfg.text_patterns = list(tp["patterns"])

    if "files" in rules and "paths" in rules["files"]:
        cfg.file_paths = list(rules["files"]["paths"])

    if "commit_author" in rules and "bot_emails" in rules["commit_author"]:
        cfg.bot_email_patterns = list(rules["commit_author"]["bot_emails"])

    if "branches" in rules and "patterns" in rules["branches"]:
        cfg.branch_patterns = list(rules["branches"]["patterns"])

    cfg.ignore_repos = list(ignore.get("repos", []))
    cfg.ignore_paths = list(ignore.get("paths", []))

    return cfg
