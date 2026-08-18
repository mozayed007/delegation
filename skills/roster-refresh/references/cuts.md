# Cuts

Used by `refresh_roster.py` and the agent after a fetch. Never invent a score.

## Pricing

- Soft cap in `roster.yaml`: prefer API output at or below $25/MTok.
- Hard `never_pin`: published API output $30/MTok or higher (Fable, Mythos, Opus Fast, Sol Fast/priority, Cyber).
- Exception: subscription Sol stays T0. The $5/$30 API SKU is not the pin. Never send Sol or Opus through OpenCode Zen.

## Role score (when a number exists)

Composite = 0.5 DeepSWE + 0.4 CursorBench + 0.1 AA Index, dropping missing terms.

| Role | Keep when |
| --- | --- |
| T0 | Family T0 and composite missing or at least 60. Opus / Grok 4.6 / Sol-sub / Kimi K3. |
| T1 | Family T1 and composite missing or at least 50. Composer 2.5 is T2. GLM-5.2 stays T1 as the free OpenCode pin even if DeepSWE is weak. |
| T2 | Luna high/max, Composer 2.5, V4 Flash, GLM-5.2, Zen free (mimo, big-pickle). Luna medium/low is not a pin. |

Ignore Aider polyglot public tables (stale 2025 GPT-5 / Opus 4 rows).

If a source is missing, keep the previous snapshot scores and previous pins for models the fetch did not see.
