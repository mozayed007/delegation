# Delegation

Portable T0 / T1 / T2 handoff for coding agents. Packets on disk. No daemon.

T0 plans. T1 splits packets. T2 implements. Context survives a harness switch because the packet is files, not chat.

## Install

```text
python skills/delegation/scripts/doctor.py --install
```

Or:

```text
npx -y skills add <this-repo> --skill delegation -g -a '*' -y
python skills/delegation/scripts/doctor.py --install
```

`--install` restores `~/.agents/skills/delegation` (and Cursor/Devin copies), copies harness adapters, writes `~/.agents/delegation/roster.local.yaml`, and appends `~/.agents/skills` to Kimi `extra_skill_dirs` and DSH `customSkillDirs`.

Tests (stdlib only):

```text
python -m unittest discover -s skills/delegation/scripts -p "test_*.py"
```

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
