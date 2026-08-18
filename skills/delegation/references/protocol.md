# Delegation packet protocol

The packet is the only context that survives a handoff. Chat history does not.

## Layout

In the target repo:

```text
.agents/packets/<id>/
  TASK.md
  CONTEXT.md
  PLAN.md
  WORK.md
  RESULT.md
  DECISIONS.md
  FILES.md
```

Create with the installed skill (after `doctor.py --install`):

```text
python ~/.agents/skills/delegation/scripts/new_packet.py --repo <repo> --id <id>
```

In this pack, before install:

```text
python skills/delegation/scripts/new_packet.py --repo <repo> --id <id>
```

If `--id` is omitted, a UTC timestamp id is used. Packets are gitignored by default (`.agents/packets/` in the repo gitignore).

## Who writes what

| File | Owner | Workers may |
| --- | --- | --- |
| TASK.md | T0 (or the human) | read |
| CONTEXT.md | T0, T1 may add distilled facts | read; T1 may append facts with labels |
| PLAN.md | T0 | T1 may add subtask rows; T2 must not rewrite |
| WORK.md | parent of this spawn | read and follow |
| RESULT.md | the worker | write once, then append |
| DECISIONS.md | anyone who made a decision | append only |
| FILES.md | the worker | write |

## Spawn rules

1. Write or update the packet first.
2. Prefer an in-harness subagent on a cheaper pinned model.
3. If a dedicated T0/T1 sub is out of quota, stay on Cursor or Devin and pick the same model family from that picker (`t0-sol` / `t0-opus` / `t0-master`, or `devin --model opus|gpt-5.6-sol|grok-4.6|kimi-k3`). Do not drop T0/T1 work to Composer Fast, Zen flash-free, or DSH flash. Do not pick Fable, Mythos, Opus Fast, Sol Fast, or Cyber.
4. Cross-CLI only when the current harness cannot run that role, Cursor/Devin also cannot, remaining quota is dead, the user asked, or the run is overnight (`gnhf`).
5. The worker prompt is: read `.agents/packets/<id>/` first, then do WORK.md, then write RESULT.md and FILES.md.
6. Never paste transcripts. Point at the packet path.
7. Never copy API keys, tokens, or `.env` values into the packet.
8. Workers edit only the WORK.md allowlist.
9. If a verification command was not run, RESULT.md must say `Not run:`.

## Overnight / other CLI

```text
gnhf --agent <codex|opencode|agy|acp:...> --stop-when "<from TASK.md>" \
  "Read .agents/packets/<id>/ first. Do WORK.md. Write RESULT.md. Stop when TASK.md is true."
```

DSH: open `dsh web`, point it at the repo, tell it the packet path. No DSH plugin.

Devin T0/T1 (including quota fallback):

```text
devin --model opus -- "Read .agents/packets/<id>/ first. Do WORK.md. Write RESULT.md."
```

Same for `gpt-5.6-sol`, `grok-4.6`, `kimi-k3`. Default `swe` is not T0.

## Isolation and ship

- Isolated implementation: `treehouse get --lease` then work in that tree with the same packet path copied or recreated.
- Shipping: `no-mistakes` after the change is committed on a feature branch. Delegation does not replace the gate.
