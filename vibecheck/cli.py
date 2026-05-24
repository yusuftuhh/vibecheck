"""CLI entry point: vibecheck [scan|fix|...] [targets...] [--json] [--items]."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from vibecheck.config import load_config
from vibecheck.findings import Finding
from vibecheck.fixers.file_replace import apply_file_fix
from vibecheck.fixers.git_history import apply_git_history_fix
from vibecheck.fixers.github_api import apply_github_api_fix
from vibecheck.github_client import GitHubClient
from vibecheck.report import render_human, render_json
from vibecheck.scanners.comments import scan_user_comments
from vibecheck.scanners.local_git import scan_local_repo
from vibecheck.scanners.profile import scan_profile
from vibecheck.scanners.remote_repo import scan_remote_repo
from vibecheck.targets import (
    GistTarget,
    IssueTarget,
    LocalRepoTarget,
    ProfileTarget,
    PullRequestTarget,
    RemoteRepoTarget,
    TargetParseError,
    parse_target,
    parse_targets_file,
)


def _scan_targets(targets: list, client: GitHubClient, config) -> list[Finding]:
    findings: list[Finding] = []
    for t in targets:
        if isinstance(t, LocalRepoTarget):
            findings.extend(scan_local_repo(t.path, config))
        elif isinstance(t, RemoteRepoTarget):
            findings.extend(scan_remote_repo(t, client, config))
        elif isinstance(t, ProfileTarget):
            inv = scan_profile(t, client, config)
            findings.extend(inv.findings)
            for rt in inv.repo_targets:
                findings.extend(scan_remote_repo(rt, client, config))
            findings.extend(scan_user_comments(t.user, client, config))
    return findings


def _apply_fix(finding: Finding, client: GitHubClient) -> None:
    if finding.fixer == "file_replace":
        apply_file_fix(finding)
    elif finding.fixer == "git_history":
        apply_git_history_fix(finding)
    elif finding.fixer == "github_api":
        apply_github_api_fix(finding, client)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="vibecheck",
                                     description="Find and remove AI authorship traces from GitHub resources.")
    parser.add_argument("--config", type=Path, help="Path to .vibecheck.yml")
    parser.add_argument("--json", action="store_true", help="Machine-readable output")

    subparsers = parser.add_subparsers(dest="command")
    scan_p = subparsers.add_parser("scan", help="Scan one or more targets")
    scan_p.add_argument("targets", nargs="*")
    scan_p.add_argument("--from-file", type=Path)

    fix_p = subparsers.add_parser("fix", help="Apply fixes for selected findings")
    fix_p.add_argument("--items", help="Comma-separated finding IDs")
    fix_p.add_argument("--interactive", action="store_true")
    fix_p.add_argument("targets", nargs="*")
    fix_p.add_argument("--from-file", type=Path)

    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    config = load_config(args.config)
    client = GitHubClient()

    targets: list = []
    if args.command in (None, "scan", "fix"):
        raw_targets = getattr(args, "targets", []) or []
        for r in raw_targets:
            try:
                targets.append(parse_target(r))
            except TargetParseError as exc:
                print(f"Skipping invalid target: {exc}", file=sys.stderr)
        if getattr(args, "from_file", None):
            targets.extend(parse_targets_file(args.from_file))
        if not targets:
            targets.append(LocalRepoTarget(path=Path.cwd().resolve()))

    findings = _scan_targets(targets, client, config)

    if args.command == "fix":
        selected_ids = set()
        if args.items:
            selected_ids = {s.strip() for s in args.items.split(",") if s.strip()}
        if args.interactive:
            for f in findings:
                resp = input(f"Apply fix for [{f.severity}] {f.id} {f.source}? [y/N] ")
                if resp.lower() == "y":
                    selected_ids.add(f.id)
        for f in findings:
            if f.id in selected_ids:
                _apply_fix(f, client)
        print(f"Applied {len(selected_ids)} fixes.")
        return 0

    if args.json:
        print(render_json(findings, [str(t) for t in targets]))
    else:
        render_human(findings, [str(t) for t in targets])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
