"""Tests for config loading."""
from pathlib import Path

from vibecheck.config import Config, load_config, DEFAULT_TEXT_PATTERNS


def test_default_config():
    cfg = load_config(None)
    assert isinstance(cfg, Config)
    assert cfg.text_patterns_enabled is True
    assert "As an AI" in cfg.text_patterns
    assert "CLAUDE.md" in cfg.file_paths
    assert any("anthropic.com" in p for p in cfg.bot_email_patterns)


def test_user_config_overrides(tmp_path: Path):
    cfg_file = tmp_path / ".vibecheck.yml"
    cfg_file.write_text(
        "rules:\n"
        "  text_patterns:\n"
        "    enabled: false\n"
        "    patterns:\n"
        "      - my custom phrase\n"
        "  files:\n"
        "    paths:\n"
        "      - extra.md\n"
        "ignore:\n"
        "  repos:\n"
        "    - foo/bar\n"
    )
    cfg = load_config(cfg_file)
    assert cfg.text_patterns_enabled is False
    assert cfg.text_patterns == ["my custom phrase"]
    assert "extra.md" in cfg.file_paths
    assert "foo/bar" in cfg.ignore_repos


def test_default_text_patterns_constant():
    assert "🤖" in DEFAULT_TEXT_PATTERNS
    assert "Co-Authored-By:" in DEFAULT_TEXT_PATTERNS
