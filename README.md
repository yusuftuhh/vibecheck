<div align="center">

# vibecheck

**Find and remove AI authorship traces from your GitHub presence.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](#tests)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-FFDD00?logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/yusuftuhh)

</div>

---

## Preview

```text
$ vibecheck scan yusuftuhh

vibecheck 0.1.0 - scanning yusuftuhh

CRITICAL (4 findings)
  abc12345  commit_message     yusuftuhh/foo commit a1b2c3d
            "Co-Authored-By: Claude <noreply@anthropic.com>"
            -> strip line from commit message

  def67890  tracked_file       yusuftuhh/bar/CLAUDE.md
            "CLAUDE.md"
            -> remove file via commit + push

  9a8b7c6d  commit_author      yusuftuhh/baz commit 4d5e6f7
            "copilot[bot]@users.noreply.github.com"
            -> rewrite commit author (requires force-push)

  1f2e3d4c  profile_readme     github.com/yusuftuhh profile README
            "...As an AI, I would be happy to help with..."
            -> remove or rephrase 'As an AI'

WARNING (2 findings)
  ...

INFO (7 findings)
  ...

Run vibecheck fix --interactive to walk through fixes, or
    vibecheck fix --items abc12345,def67890 to apply specific items.
```

---

## Why this exists

You ship a repo, get hired off it, share it on Twitter. The reviewer sees `Co-Authored-By: Claude` in a commit from 6 months ago. Or your profile bio still says "I would be happy to help you with anything". Or your gist has `# Generated with ChatGPT` at the top.

None of this is wrong. AI tools are mainstream. But sometimes you want to decide what shows up on your public profile, and "I forgot about that one PR comment from 2025" is a bad reason to leak that decision.

**vibecheck is an audit tool, not a cover-up generator.** It shows you exactly what AI traces exist across your GitHub presence, ranks them by severity, and lets you pick which ones to remove. Nothing gets edited without your explicit yes.

## Use cases

* **Pre-publish check.** Before you open-source that side project, scan it.
* **Profile audit.** "What does my GitHub look like to a recruiter who searches for 'claude' or 'gpt' in my commit messages?" One command answers that.
* **Bulk cleanup after a tool switch.** You used Cursor for two months, decided to go back to vanilla. Find every `.cursorrules` file you forgot to gitignore.
* **CI gate.** Pipe `vibecheck scan . --json` into your CI and fail the build if `critical` findings appear.
* **Privacy.** Some clients have policies against AI-assisted contributions. Scan before billing.

## What it catches

| Category | Severity | Example |
|---------|---------|---------|
| Co-Authored-By footers | critical | `Co-Authored-By: Claude <noreply@anthropic.com>` |
| Bot account commits | critical | author = `copilot[bot]@users.noreply.github.com` |
| Tracked AI files | critical | `CLAUDE.md`, `AGENTS.md`, `.claude/`, `.cursor/`, `.aider*`, `docs/superpowers/` |
| AI-tagged branches | warning | `claude/wip`, `ai/refactor`, `agent/feature` |
| Robot emoji in commit messages | warning | `feat: thing Generated with Claude` |
| AI-typical phrases | info | "As an AI", "I would be happy to", "Let me know if" |
| Em-dashes in markdown | info | a common giveaway for AI-written text |

Coverage across your entire profile: every repo you own, profile bio, profile README, gists, issue and PR comments you wrote.

## Quickstart

```bash
brew install python@3.12
git clone https://github.com/yusuftuhh/vibecheck.git
cd vibecheck
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# auth (optional but recommended)
gh auth login

# scan everything you own
python3 -m vibecheck.cli scan yusuftuhh
```

That is the whole onboarding.

## Authentication

The CLI reads `GITHUB_TOKEN` from env or falls back to `gh auth token`. For private repos and for editing your own bio, gists, comments and profile README, the token needs scopes `repo`, `gist`, `user`. Without a token, scans are public-only with reduced rate limits.

```bash
export GITHUB_TOKEN=ghp_xxx
# or
gh auth login
```

## Detailed usage

### Scan

```bash
# current local repo (no args)
python3 -m vibecheck.cli

# single remote repo
python3 -m vibecheck.cli scan https://github.com/yusuftuhh/foo

# entire profile: all your repos + bio + gists + comments + profile README
python3 -m vibecheck.cli scan yusuftuhh

# specific issue or PR
python3 -m vibecheck.cli scan https://github.com/u/r/issues/123
python3 -m vibecheck.cli scan https://github.com/u/r/pull/456

# mixed targets in one run
python3 -m vibecheck.cli scan . https://github.com/u/r yusuftuhh

# from a file (one target per line, # for comments)
python3 -m vibecheck.cli scan --from-file targets.txt

# machine-readable for CI / further processing
python3 -m vibecheck.cli scan yusuftuhh --json > report.json
```

### Fix

```bash
# walk through every finding, decide one by one
python3 -m vibecheck.cli fix --interactive

# apply specific finding IDs from a previous scan
python3 -m vibecheck.cli fix --items abc12345,def67890,9a8b7c6d

# combine: scan a target and fix specific items in one go
python3 -m vibecheck.cli fix yusuftuhh --items abc12345
```

Every destructive action (force-push, comment edit, bio change) requires explicit per-batch confirmation. There is no `--yes` shortcut on purpose.

## Use it as a Claude Code skill

```bash
mkdir -p ~/.claude/skills/vibecheck
cp -r skill/* ~/.claude/skills/vibecheck/
```

Once installed, asking "check my github for AI traces" or "vibecheck repo X" triggers the skill, which runs the CLI, presents findings, and walks you through fixes interactively.

## Configuration

Drop a `.vibecheck.yml` in your repo root or `~/.config/vibecheck/config.yml` to override defaults:

```yaml
rules:
  text_patterns:
    enabled: true
    patterns:
      - my custom phrase
  files:
    paths:
      - CLAUDE.md
      - my-private-notes.md
  commit_author:
    bot_emails:
      - "@anthropic.com"
      - "myteam-bot@company.com"

ignore:
  repos:
    - yusuftuhh/legacy-thing
  paths:
    - third_party/
```

## Safety

* All destructive actions (force-push, comment edit, bio change) require explicit per-batch confirmation.
* Force-pushing rewrites history. Backup your branch first if uncertain.
* GitHub keeps dangling commits reachable via direct SHA URL for roughly two weeks before garbage collection. The tool warns about this.
* Private repos are only scanned when the token grants access. Public-only scans require no token.

## How it works under the hood

```
                    target string
                          |
                          v
                    targets.py  ->  LocalRepoTarget / RemoteRepoTarget / ProfileTarget / ...
                          |
                          v
                    scanners/*  ->  local_git, remote_repo, profile, comments, text_patterns
                          |
                          v   list[Finding]
                    report.py   ->  human (rich) or JSON
                          |
                  user picks IDs
                          |
                          v
                    fixers/*    ->  file_replace, git_history, github_api
```

Each scanner produces `Finding` objects with a stable 8-character ID. Fixers are stateless and idempotent. The CLI glues them together. The Claude Code skill in `skill/SKILL.md` wraps the CLI for natural-language flows.

## Tests

```bash
pip install -r requirements-dev.txt
python3 -m pytest
```

Tests mock all GitHub API calls via `respx`. No network, no live token needed.

## FAQ

**Will this destroy my git history?**
`git_history` fixer uses `filter-branch` and then `--force` pushes. It rewrites SHAs. Open PRs and forks of the affected branch break. You always get a per-batch confirm prompt that spells out exactly what will happen.

**Does GitHub actually forget the old commits?**
Dangling commits stay reachable by direct SHA URL for roughly two weeks before GitHub's garbage collection. The tool warns about this and prints the affected SHAs so you can monitor.

**Why is the em-dash flagged?**
LLMs love em-dashes. A human writer typing on a US keyboard rarely produces them by hand. It is a weak signal, marked `info` severity, off-by-default-fix. Toggle in `.vibecheck.yml`.

**Will it edit private repos?**
Only with a token that has access, and only after you explicitly select those findings.

**Can I scan a repo I do not own?**
Yes for reading. No for fixing. The API will return 403 on PATCH attempts and the tool will mark those findings unfixable.

## Limitations

* Discussions and Wikis are not scanned in this version. REST endpoints exist, GraphQL would be cleaner. Planned for v0.2.
* AI-generated-code detection (semantic analysis of source) is out of scope. This tool looks at metadata and text, not at code quality.
* Repo deletion + recreation for immediate GC of dangling commits is not automated. Manual step if you need it.
* Org-wide scans where you are not the owner are not supported.

## Roadmap

* v0.2: Discussions and Wiki scanners via GraphQL
* v0.3: pre-commit hook for blocking AI traces before they enter history
* v0.4: GitHub Actions workflow template for CI gating
* v0.5: profile photo similarity check against known AI-generated avatars (experimental)

## Support the project

If vibecheck saved you a long manual cleanup, a tip keeps the side projects shipping:

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-FFDD00?logo=buy-me-a-coffee&logoColor=black&style=for-the-badge)](https://buymeacoffee.com/yusuftuhh)
[![GitHub Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-EA4AAA?logo=github-sponsors&logoColor=white&style=for-the-badge)](https://github.com/sponsors/yusuftuhh)

Stars on the repo are free and also help.

## License

MIT. See [LICENSE](LICENSE).
