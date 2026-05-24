"""Tests for text-pattern scanning."""
from vibecheck.config import Config
from vibecheck.scanners.text_patterns import scan_text


def test_scan_text_finds_patterns():
    cfg = Config()
    text = "Hello — I'd be happy to help! 🤖 Generated with Claude."
    findings = scan_text(text, source="README.md", config=cfg)
    snippets = [f.snippet for f in findings]
    assert any("I'd be happy to" in s for s in snippets)
    assert any("🤖" in s for s in snippets)


def test_scan_text_em_dash():
    cfg = Config()
    text = "Here is a thing — and another."
    findings = scan_text(text, source="bio", config=cfg)
    em_dash_findings = [f for f in findings if "em-dash" in f.suggested_fix.lower() or "—" in f.snippet]
    assert len(em_dash_findings) >= 1


def test_scan_text_no_matches():
    cfg = Config()
    text = "Plain ordinary text without anything suspicious."
    findings = scan_text(text, source="x", config=cfg)
    assert findings == []


def test_scan_text_disabled():
    cfg = Config(text_patterns_enabled=False)
    text = "🤖 Generated with Claude"
    findings = scan_text(text, source="x", config=cfg)
    assert findings == []


def test_scan_text_severity_info():
    cfg = Config()
    text = "Just an em-dash — here."
    findings = scan_text(text, source="x", config=cfg)
    assert all(f.severity == "info" for f in findings)
