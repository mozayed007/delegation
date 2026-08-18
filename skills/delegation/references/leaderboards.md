# Leaderboard snapshot (2026-08-18)

Used to set T0 / T1 / T2 pins. Not a live scrape. `doctor.py --refresh` only stamps `generated_at`.

Pricing gate: never pin a model whose published API output is $30/MTok or higher (Fable, Mythos, Opus Fast, Sol Fast/priority, Cyber). Subscription Sol remains T0 because Codex/Cursor/Devin burn quota, not the $5/$30 API. Do not send Sol or Opus through OpenCode Zen.

Aider polyglot public tables still peak on 2025 GPT-5 / Opus 4 rows. Ignored for 2026 cuts.

## Role cut

| Role | Cut | Why |
| --- | --- | --- |
| T0 | Opus 5, Grok 4.6, Sol (sub), Kimi K3 | AA Intelligence 63 / 61 / 61 / 60. SWE-bench Verified saturated at 97 / 95.6 / 96.2 / 93.4. CursorBench Grok 70.8, Opus 70.0, Sol 67.2. DeepSWE Opus 73.6, Sol 72.7, K3 68.5, Grok 66.7. |
| T1 | Terra, Gemini 3.7 Flash, Sonnet 5, DeepSeek V4 Pro | DeepSWE Terra 69.6, Gemini 3.7 Flash 65.3, Sonnet 5 53.8, V4 Pro 62.8. Terminal-Bench 3.7 Flash 85.8. Composer 2.5 is 56.1 on CursorBench: T2. GLM-5.2 DeepSWE 43.8: T2-adjacent, kept as free OpenCode T1 pin only. |
| T2 | Luna high/max, Composer 2.5, V4 Flash, GLM-5.2, Zen free | Luna Max DeepSWE 67.2 / CursorBench 61.1 at $0.39/task. Luna medium/low collapse (combined 29% / 20%). |
| Excluded | Fable, Mythos, Opus Fast, Sol Fast, Cyber | Fable/Mythos $50/M out. Opus Fast $50. Sol Fast $60. Cyber $75. |

## Scores used

| Model | AA Intelligence | CursorBench 3.2 | DeepSWE pass@1 | Terminal-Bench 2.1 | Vals SWE-bench Verified | API out $/M |
| --- | --- | --- | --- | --- | --- | --- |
| Claude Opus 5 max | 63 | 70.0 | 73.6 | 89.1 | 97.00 | 25 |
| Claude Fable 5 max | 62 | 70.5 | 69.7 | 84.6 | (cluster) | 50 (excluded) |
| GPT-5.6 Sol max | 61 | 67.2 | 72.7 | 89.5 | 96.20 | 30 API / sub OK |
| Grok 4.6 xhigh/high | 61 | 70.8 / 69.9 | 66.7 | 88.4 | (Grok 4.6 row) | 6 |
| Kimi K3 max | 60 | 60.8 | 68.5 | 85.0 | 93.40 | 15 |
| GPT-5.6 Terra max | 55 (Jul AA family) | 64.9 | 69.6 | 88.0 | (lower band) | 12 |
| Gemini 3.7 Flash high | - | (not on 3.2 table yet) | 65.3 | 85.8 | (mid band) | 3.75 intro |
| GPT-5.6 Luna max | 51 (Jul AA family) | 61.1 | 67.2 | - | (Luna row) | 1.20 |
| Claude Sonnet 5 max | - | 61.5 | 53.8 | 80.4 | (Sonnet 5 row) | 10 |
| DeepSeek V4 Pro 0813 | 53 | - | 62.8 | 78.6 | 96.40 | ~3.48 |
| Composer 2.5 | - | 56.1 | - | - | (Composer row) | Cursor sub |
| GLM-5.2 max | - | 55.0 | 43.8 | 77.9 | (GLM 5.2 row) | ~2.2 |
| DeepSeek V4 Flash | - | - | 53.3 | 78.6 | (Flash row) | 0.28 |
| Gemini 3.1 Pro | - | - | 11.7 | 73.8 | (old Pro row) | dropped from pins |
| Claude Sonnet 4.6 | - | - | 29.9 | 71.2 | (old Sonnet row) | dropped from pins |

## Sources

- [Artificial Analysis models (Intelligence Index v4.1.1)](https://artificialanalysis.ai/models?intelligence=artificial-analysis-intelligence-index) (Aug 2026)
- [Grok 4.6 on Artificial Analysis](https://artificialanalysis.ai/articles/grok-4-6-benchmarks-and-analysis) (12 Aug 2026)
- [GPT-5.6 on Artificial Analysis](https://artificialanalysis.ai/articles/gpt-5-6-has-landed) (9 Jul 2026)
- [AA Coding Index mirror](https://benchlm.ai/benchmarks/aaCodingIndex) (Jul 15 / Aug 17 2026 mirrors)
- [CursorBench 3.2](https://cursor.com/cursorbench) (11 Aug 2026)
- [DeepSWE mirror](https://benchlm.ai/benchmarks/deepswe) (13 Aug 2026)
- [Vals SWE-bench Verified](https://vals.ai/benchmarks/swebench) (Aug 2026)
- [Terminal-Bench v2.1 on Artificial Analysis](https://artificialanalysis.ai/evaluations/terminalbench-v2-1)
- [OpenAI API pricing](https://developers.openai.com/api/docs/pricing)
- [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- [Gemini 3.7 Flash announcement](https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-3-7-flash/) (13 Aug 2026)
- [Gemini 3.7 Flash model card](https://deepmind.google/models/model-cards/gemini-3-7-flash/)
