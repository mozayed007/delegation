---
name: delegation
description: Routes work across T0 master, T1 sub-master, and T2 clanker roles using on-disk packets. Use when planning a large task, spawning subagents, handing work to another CLI (codex, grok, kimi, opencode, agy, dsh, cursor-agent, devin, gnhf), when a dedicated T0/T1 sub is out of quota, or when context must survive a harness switch.
---

# Delegation

Read [references/protocol.md](references/protocol.md) before spawning. Load `~/.agents/delegation/roster.local.yaml` if it exists, else [references/roster.yaml](references/roster.yaml). Pin evidence: [references/leaderboards.md](references/leaderboards.md).

## Roles

| Role | Job |
| --- | --- |
| T0 master | Architecture, task graph, review, stop |
| T1 sub-master | Split work, assign packets, mid planning |
| T2 clanker | Implement, grep, tests, mechanical edits |

Subscription quota first. Do not send Sol or Opus through OpenCode Zen at API rates. Never pin Fable, Mythos, Opus Fast, Sol Fast, or Cyber ($30+/M output). Free Zen models are T2 because of quality and 200K context caps, not because of data retention.

## In-tool first

1. If this harness can run the cheaper role as a native subagent, do that.
2. If a dedicated T0/T1 sub is out of quota, stay on **Cursor or Devin** and pick the **same model family** from that product's picker. Do not demote the role to Composer Fast, Zen flash-free, or DSH flash.
3. Cross-CLI or `gnhf` only when: this harness cannot run that role, Cursor/Devin also cannot run it, remaining quota is dead, the user asked, or the run is overnight.
4. Write the packet before spawn. The worker prompt is the packet path, not a transcript.

## Quota fallback (same-model picker)

Dedicated T0/T1 homes: Codex, SuperGrok (`grok`), Claude, Kimi, Agy. When one of those is exhausted, keep T0/T1 work on Cursor or Devin and switch the picker / `--model` to the same family:

| Exhausted sub | Cursor picker / stub | Devin `--model` |
| --- | --- | --- |
| Claude Opus | `claude-opus-5-thinking-high` (`t0-opus`) | `opus` |
| SuperGrok | `grok-4.6` (`t0-master`) | `grok-4.6` |
| Codex Sol | `gpt-5.6-sol` (`t0-sol`) | `gpt-5.6-sol` |
| Kimi K3 | `kimi-k3-max` | `kimi-k3` |
| T1 Terra | matching Terra id | `gpt-5.6-terra` |
| T1 Gemini 3.7 Flash | `gemini-3.7-flash-high` (`t1-submaster`) | `gemini-3.7-flash` |
| T1 Sonnet 5 | `claude-sonnet-5` | `claude-sonnet-5` |

Cursor's live default (Composer 2.5 Fast) is T2 **only if the picker stays there**. Devin's live default (`swe`) is not T0. Luna is T2 only at high or max effort.

Cursor stubs: `t0-master`, `t0-sol`, `t0-opus`, `t1-submaster`, `t2-clanker` in `~/.cursor/agents/`.
OpenCode stubs: `t1-submaster` (GLM-5.2, free in-harness), `t2-clanker` in `~/.config/opencode/agents/`.
Codex stubs: `t1-terra` / `t2-luna` (Luna high) in `~/.codex/agents/`. Codex Sol may ignore child model pins; still spawn the named agent and put the packet path in the message. Do not spawn a fleet of Sol clones for T2 work.
Agy stubs: `t1-submaster` and `t2-clanker` both pin Gemini 3.7 Flash (`model: flash`) in `~/.agents/agents/`. Prefer Flash over Gemini 3.1 Pro.
Grok / Kimi: native subagents plus this skill.
DSH: `dsh web` pointed at the repo and packet path.
Devin: packet path plus `devin --model <same-family>`. Devin already loads `~/.agents/skills`. Example:

```text
devin --model opus -- "Read .agents/packets/<id>/ first. Do WORK.md. Write RESULT.md."
```

Reuse existing host patterns (`how`, `why`, `arena`) when those skills are already loaded. Do not reimplement them.

## Packet

Create:

```text
python <this-skill>/scripts/new_packet.py --repo <repo>
```

Worker: read `.agents/packets/<id>/` first, do WORK.md, write RESULT.md and FILES.md. Status labels from AGENTS.md. If a check was not run: `Not run:`.

Overnight:

```text
gnhf --agent <codex|opencode|agy|acp:...> --stop-when "<TASK.md stop>" \
  "Read .agents/packets/<id>/ first. Do WORK.md. Write RESULT.md."
```

Isolated trees: `treehouse get --lease`. Shipping: `no-mistakes`. This skill does not replace either.

## Setup

```text
python <this-skill>/scripts/doctor.py
python <this-skill>/scripts/doctor.py --install
```

Doctor records a null result when a binary, config, or model is absent. It never writes secrets. Rankings in roster.yaml refresh on first `--install` if the snapshot is missing, and anytime with `doctor.py --refresh` or the `roster-refresh` skill.
