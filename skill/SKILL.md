---
name: vibecheck
description: "Scan GitHub repositories, user profiles, gists, issue and PR comments, and local git history for AI-attribution traces (Co-Authored-By bot footers, AI helper files, AI-typical text patterns, em-dashes, AI-tagged branches). Interactively pick which findings to remove. Use whenever the user wants to audit their GitHub presence for AI-coding traces or clean up a specific repo before publishing."
---

# vibecheck

Audit and clean AI authorship traces across a user's GitHub resources and local repos.

## When to invoke

Trigger this skill when the user asks to:

* Scan a repo, profile, gist, or local checkout for AI traces
* Clean up Co-Authored-By footers from commits
* Remove leftover CLAUDE.md, AGENTS.md or similar helper files
* Replace em-dashes and AI-typical phrases in their README, bio, comments, or gists
* "Run vibecheck", "check my github", "audit for AI markers", "make this repo look human-written"

## How to run

The CLI is installed in the user's repo at the path they cloned (default `~/projects/vibecheck/`). Always use `python3` and invoke from inside that repo's venv.

**1. Ask the user what to scan.** Accept any combination of:

* Local repo path (`.` or absolute path)
* A repo URL (`https://github.com/user/repo`)
* A profile (`https://github.com/user` or just the handle `yusuftuhh`)
* An issue or PR URL
* A gist URL
* A text file with one target per line

If unclear, ask one focused question with examples.

**2. Run the scan.**

```bash
python3 -m vibecheck.cli scan <targets...> --json
```

Parse the JSON. Each finding has `id`, `severity` (critical/warning/info), `category`, `source`, `snippet`, `suggested_fix`.

**3. Present findings as a numbered checklist.** Group by severity. Show each finding's source, the offending snippet, and the proposed fix. Example layout:

```
[critical] 3 findings
  1. abc12345  yusuftuhh/foo commit a1b2c3d
     "Co-Authored-By: Claude <noreply@anthropic.com>"
     -> strip line from commit message
  ...
```

**4. Ask the user what to fix.** Accept:

* Comma-separated IDs ("fix 1, 3, 7")
* By severity ("all critical")
* By category ("only README findings")
* "all" or "nothing"

**5. Confirm destructive actions.** Before applying any fix that involves `git_history` or `github_api`, restate what will happen (force-push, comment edit, bio change) and require an explicit "yes".

**6. Apply fixes.**

```bash
python3 -m vibecheck.cli fix --items id1,id2,id3
```

**7. Report what changed.** Show the user the actual changes (commits rewritten, comments edited, files deleted). For force-pushed branches, remind that dangling commits may still be visible via GitHub commit-search for up to two weeks.

## Authentication

The CLI reads `GITHUB_TOKEN` from env or falls back to `gh auth token`. If neither works, point the user at `gh auth login`. For private repos and editing your own bio/gists/comments, the token needs `repo`, `gist`, and `user` scopes.

## Do not

* Do not run `vibecheck fix` without explicit per-finding or per-batch user approval.
* Do not run `git push --force` outside of what the `git_history` fixer does itself.
* Do not surface or store the user's GitHub token in any file or log.
* Do not assume the user wants to fix every finding. `info` severity items are often intentional style choices.
