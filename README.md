# Delegation

[![tests](https://github.com/mozayed007/delegation/actions/workflows/test.yml/badge.svg)](https://github.com/mozayed007/delegation/actions/workflows/test.yml)

Portable T0 / T1 / T2 handoff for coding agents. Packets on disk. No daemon.

T0 plans. T1 splits packets. T2 implements. Context survives a harness switch because the packet is files, not chat.

MIT. Python 3.11+ (`tomllib` in `doctor.py`).

```text
git clone https://github.com/mozayed007/delegation.git
```

## Install

Canonical setup: clone this repo, then:

```text
python skills/delegation/scripts/doctor.py --install
```

That copies `delegation` and `roster-refresh` into `~/.agents/skills` (plus Cursor/Devin copies), copies harness adapters, writes `~/.agents/delegation/roster.local.yaml`, and appends `~/.agents/skills` to Kimi `extra_skill_dirs` and DSH `customSkillDirs`. If `leaderboards.snapshot.json` is missing, it also fetches public boards and applies T0/T1/T2 pins.

Optional npx (still run `doctor.py --install` after):

```text
npx -y skills add https://github.com/mozayed007/delegation --skill delegation -g -a '*' -y
npx -y skills add https://github.com/mozayed007/delegation --skill roster-refresh -g -a '*' -y
python skills/delegation/scripts/doctor.py --install
```

Do not run `npx skills add` from the installed copy under `~/.agents`. Clone first.

Tests (stdlib only):

```text
python -m unittest discover -s skills/delegation/scripts -p "test_*.py"
python -m unittest discover -s skills/roster-refresh/scripts -p "test_*.py"
```

## Keep the roster current

First time (no snapshot yet): `doctor.py --install` fetches.

Later, when you want a new cut:

```text
python skills/delegation/scripts/doctor.py --refresh
```

Or tell any agent: `refresh the roster` (loads the `roster-refresh` skill). Direct script:

```text
python skills/roster-refresh/scripts/refresh_roster.py --apply
```

Dry run (print only): omit `--apply`. This is not a cron job. Re-run when you ask, or when doctor warns the snapshot is older than 14 days.

## Use it on a real project

Nothing to install inside the project. Open the project in Cursor, Codex, Grok, Claude, Kimi, or Devin. Stay on a T0 model for planning.

Create a packet **in that repo**:

```powershell
python "$env:USERPROFILE\.agents\skills\delegation\scripts\new_packet.py" --repo F:\projects\MyApp --id billing
```

```bash
python "$HOME/.agents/skills/delegation/scripts/new_packet.py" --repo ~/src/myapp --id billing
```

That writes gitignored `.agents/packets/billing/` (`TASK.md`, `CONTEXT.md`, `PLAN.md`, `WORK.md`, `RESULT.md`, `DECISIONS.md`, `FILES.md`).

Tell T0:

> Read `.agents/packets/billing/` first. Fill TASK, CONTEXT, and PLAN. Split into T2 packets with allowlists. Do not implement yet.

Spawn a worker with the path, not a transcript:

> Use `t2-clanker` on `.agents/packets/billing/`. Read the packet first. Do WORK.md. Edit only the allowlist. Write RESULT.md.

Skip packets for a 20-line fix. Use them when the job needs a plan and a pile of file edits.

## Who does what

| Need | Do this |
| --- | --- |
| Architecture / review / stop | Codex Sol, SuperGrok 4.6, Claude Opus 5, or Kimi K3 |
| Those subs are out of quota | Stay on Cursor or Devin. Pick the **same** family (`t0-sol`, `t0-opus`, `t0-master`, or `devin --model opus`) |
| Split the plan | Terra, Gemini 3.7 Flash, Sonnet 5 (`t1-submaster`) |
| Implement, grep, tests | Luna **high/max**, Composer 2.5, OpenCode/DSH flash (`t2-clanker`) |
| Overnight | Packet first, then `gnhf` with `--stop-when` from TASK.md |

Cursor on Composer Fast is T2. Devin on `swe` is not T0. Luna medium/low is not a useful T2 pin.

Never pick Fable, Mythos, Opus Fast, Sol Fast, or Cyber. Those are $50-$75 per million output tokens. Subscription Sol is allowed; Sol through OpenCode Zen is not.

Pin evidence: `skills/delegation/references/leaderboards.md`. Policy: `skills/delegation/references/roster.yaml`.

License: [MIT](LICENSE).
