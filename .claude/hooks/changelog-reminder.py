#!/usr/bin/env python3
"""PostToolUse hook: remind Claude to record documentation changes in CHANGELOG.md.

CLAUDE.md requires every documentation change to be summarised in CHANGELOG.md with
the reason for it. This fires after a tool run in which ANY file under docs/ was
actually modified, and injects that reminder back into the model's context.

Detection is by file modification time, not by inspecting the tool's arguments:

  - it catches a change however it was made — the Edit and Write tools, a scripted
    Bash heredoc, sed -i, a redirect, a generator;
  - it stays silent for reads. Opening or grepping a file under docs/ mentions the
    path but changes nothing, so nothing fires;
  - it needs no knowledge of which argument of which tool holds a path.

It also stays silent when CHANGELOG.md was part of the same change, and will not
repeat itself for a change it has already reported.
"""

import hashlib
import json
import os
import pathlib
import sys
import tempfile
import time

WINDOW_SECONDS = 20   # how recently a file must have changed to count as "just now"
MAX_LISTED = 8        # cap the file list in the reminder

REMINDER = (
    "{files} under docs/ {was} just modified. Per CLAUDE.md, documentation changes must be "
    "recorded in CHANGELOG.md before this turn ends: append to today's entry, or start a new "
    "dated entry at the top of the file if today has none. Summarise WHAT changed and WHY — "
    "not a file diff; Git already has the diff. Never edit an entry that is already committed. "
    "If this is part of a larger change you are still making, update the changelog once at the "
    "end rather than after each file."
)


def project_dir() -> pathlib.Path:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return pathlib.Path(env)
    # .claude/hooks/<this file>  ->  project root
    return pathlib.Path(__file__).resolve().parent.parent.parent


def state_file(root: pathlib.Path) -> pathlib.Path:
    key = hashlib.sha1(str(root).encode()).hexdigest()[:12]
    return pathlib.Path(tempfile.gettempdir()) / f"claude-changelog-hook-{key}"


def main() -> int:
    sys.stdin.read()  # drain the payload; we do not need it

    root = project_dir()
    docs = root / "docs"
    if not docs.is_dir():
        return 0

    now = time.time()
    changed = []
    newest = 0.0
    for path in docs.rglob("*"):
        if not path.is_file():
            continue
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if now - mtime <= WINDOW_SECONDS:
            changed.append(path.relative_to(root))
            newest = max(newest, mtime)

    if not changed:
        return 0

    # The changelog was part of this same change — nothing to remind about.
    changelog = root / "CHANGELOG.md"
    try:
        if now - changelog.stat().st_mtime <= WINDOW_SECONDS:
            return 0
    except OSError:
        pass

    # Do not repeat a reminder for a change already reported.
    marker = state_file(root)
    try:
        if float(marker.read_text().strip()) >= newest:
            return 0
    except (OSError, ValueError):
        pass
    try:
        marker.write_text(str(newest))
    except OSError:
        pass

    names = sorted(str(p) for p in changed)
    shown = ", ".join(names[:MAX_LISTED])
    if len(names) > MAX_LISTED:
        shown += f", and {len(names) - MAX_LISTED} more"
    was = "was" if len(names) == 1 else "were"

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": REMINDER.format(files=shown, was=was),
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
