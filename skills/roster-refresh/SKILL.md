---
name: roster-refresh
description: Fetches coding leaderboards and API prices, then updates T0/T1/T2 roster pins. Use when the user asks to refresh the roster, update T0 T1 T2 ranks, re-check leaderboards, or run doctor --refresh / first-time doctor --install.
---

# Roster refresh

Automates the leaderboard pass: fetch public boards, drop $30+/M output API SKUs, rewrite T0/T1/T2 pins.

## When

- First `doctor.py --install` if `leaderboards.snapshot.json` is missing.
- Anytime the user asks to refresh ranks, or `python skills/delegation/scripts/doctor.py --refresh`.
- This skill, named: roster-refresh.

Do not refresh on ordinary coding tasks.

## Run

From the Delegation repo (or after install, from `~/.agents/skills/roster-refresh`):

```text
python scripts/refresh_roster.py --apply
```

Dry run (fetch + print, no file writes):

```text
python scripts/refresh_roster.py
```

Then:

1. Read `skills/delegation/references/leaderboards.snapshot.json`.
2. If a source is `missing` or `skipped`, fetch that URL yourself (JS-heavy AA pages often need this) and fill gaps. Never invent a score.
3. Apply the pricing gate in `references/sources.yaml`: API output $30/MTok or higher is `never_pin`. Subscription Sol stays T0. Never send Sol or Opus through OpenCode Zen.
4. Ignore Aider polyglot public tables (stale).
5. If pins changed, update Cursor/Agy/Codex/OpenCode stubs to match. Print adapter hints from the script.
6. Run:

```text
python -m unittest discover -s skills/delegation/scripts -p "test_*.py"
python -m unittest discover -s skills/roster-refresh/scripts -p "test_*.py"
```

## Cuts

See [references/cuts.md](references/cuts.md). Merge: only overwrite pins for models the fetch actually saw. Keep previous pins for unseen models.

## Files touched

- `skills/delegation/references/roster.yaml` (marker blocks)
- `skills/delegation/references/leaderboards.md` (generated section)
- `skills/delegation/references/leaderboards.snapshot.json`

No API keys. Stdlib only.

## Example

User: "refresh the roster" or "re-check T0 T1 T2 leaderboards"

Agent: run `refresh_roster.py --apply`, fill missing JS-heavy sources, keep $30+/M models in `never_pin`, update adapters if pins moved, run the two unittest discovers.
