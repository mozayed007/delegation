"""Fetch public leaderboards and apply T0/T1/T2 roster pins. Stdlib only."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

try:
    import certifi
except ImportError:
    certifi = None

HERE = Path(__file__).resolve()
SKILL_ROOT = HERE.parent.parent
SOURCES_PATH = SKILL_ROOT / "references" / "sources.yaml"
UA = "DelegationRosterRefresh/1.0"

MODELS: tuple[dict[str, Any], ...] = (
    {"id": "claude-opus-5", "aliases": ("claude opus 5", "opus 5"), "family": "t0"},
    {"id": "claude-fable-5", "aliases": ("claude fable 5", "fable 5"), "family": "exclude"},
    {"id": "claude-mythos-5", "aliases": ("claude mythos 5", "mythos 5"), "family": "exclude"},
    {"id": "gpt-5.6-sol", "aliases": ("gpt-5.6 sol", "gpt 5.6 sol"), "family": "t0"},
    {"id": "grok-4.6", "aliases": ("grok 4.6",), "family": "t0"},
    {"id": "kimi-k3", "aliases": ("kimi k3",), "family": "t0"},
    {"id": "gpt-5.6-terra", "aliases": ("gpt-5.6 terra", "gpt 5.6 terra"), "family": "t1"},
    {"id": "gemini-3.7-flash", "aliases": ("gemini 3.7 flash",), "family": "t1"},
    {"id": "claude-sonnet-5", "aliases": ("claude sonnet 5", "sonnet 5"), "family": "t1"},
    {"id": "deepseek-v4-pro", "aliases": ("deepseek v4 pro",), "family": "t1"},
    {"id": "gpt-5.6-luna", "aliases": ("gpt-5.6 luna", "gpt 5.6 luna"), "family": "t2"},
    {"id": "composer-2.5", "aliases": ("composer 2.5",), "family": "t2"},
    {"id": "glm-5.2", "aliases": ("glm-5.2", "glm 5.2"), "family": "t1"},
    {"id": "deepseek-v4-flash", "aliases": ("deepseek v4 flash",), "family": "t2"},
    {"id": "gemini-3.1-pro", "aliases": ("gemini 3.1 pro",), "family": "drop"},
    {"id": "claude-sonnet-4.6", "aliases": ("claude sonnet 4.6", "sonnet 4.6"), "family": "drop"},
)

ALWAYS_NEVER_PIN = (
    "claude-fable-5",
    "claude-mythos-5",
    "claude-opus-5-fast",
    "gpt-5.6-sol-fast",
    "gpt-5.6-sol-priority",
    "gpt-5.6-cyber",
)

T0_ALIASES = {
    "claude-opus-5": ("claude-opus-5", "opus"),
    "gpt-5.6-sol": ("gpt-5.6-sol",),
    "grok-4.6": ("grok-4.6",),
    "kimi-k3": ("kimi-code/k3", "kimi-k3"),
}

T1_KEEP_INHARNESS = ("glm-5.2",)
T2_ALIASES = {
    "deepseek-v4-flash": ("deepseek-v4-flash", "opencode/deepseek-v4-flash-free"),
    "gpt-5.6-luna": ("gpt-5.6-luna",),
    "composer-2.5": ("composer-2.5",),
    "glm-5.2": ("glm-5.2",),
}
T2_DEFAULT_EXTRAS = ("opencode/deepseek-v4-flash-free", "mimo-v2.5-free", "big-pickle")
NEVER_PIN_USD = 30
GEN_START = "<!-- refresh:generated -->"
GEN_END = "<!-- /refresh:generated -->"


def policy_dir() -> Path:
    sibling = SKILL_ROOT.parent / "delegation" / "references"
    if (sibling / "roster.yaml").is_file():
        return sibling
    home = Path.home() / ".agents" / "skills" / "delegation" / "references"
    return home


def load_sources() -> tuple[list[tuple[str, str]], int, set[str], int]:
    text = SOURCES_PATH.read_text(encoding="utf-8") if SOURCES_PATH.is_file() else ""
    timeout = 20
    max_out = 25
    urls: list[tuple[str, str]] = []
    current: str | None = None
    sub_ok: set[str] = set()
    in_sub = False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("timeout_sec:"):
            timeout = int(line.split(":", 1)[1].strip())
        elif line.startswith("max_api_output_usd_per_m:"):
            max_out = int(float(line.split(":", 1)[1].strip()))
        elif line.startswith("subscription_ok_at_30:"):
            in_sub = True
        elif in_sub and line.startswith("- "):
            sub_ok.add(line[2:].strip())
        elif in_sub and line and not line.startswith("-"):
            in_sub = False
        if line.startswith("- id:"):
            current = line.split(":", 1)[1].strip()
        elif line.startswith("url:") and current:
            urls.append((current, line.split(":", 1)[1].strip()))
            current = None
    return urls, timeout, sub_ok, max_out


def ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    if certifi is not None:
        ctx.load_verify_locations(certifi.where())
    return ctx


def fetch(url: str, timeout: int) -> tuple[str, str | None]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    ctx = ssl_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            raw = resp.read()
        return "found", raw.decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        return "missing", str(exc)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).lower()


def match_model(haystack: str) -> str | None:
    h = _norm(haystack)
    best: str | None = None
    best_len = 0
    for spec in MODELS:
        for alias in spec["aliases"]:
            if alias in h and len(alias) > best_len:
                best = spec["id"]
                best_len = len(alias)
    return best


def add_score(scores: dict[str, dict[str, float]], model_id: str, key: str, value: float) -> None:
    row = scores.setdefault(model_id, {})
    prev = row.get(key)
    if prev is None or value > prev:
        row[key] = value


def parse_percent_near_name(text: str, key: str, scores: dict[str, dict[str, float]]) -> None:
    pattern = re.compile(
        r"(.{0,80}?)(\d{1,3}(?:\.\d+)?)\s*%",
        re.IGNORECASE | re.DOTALL,
    )
    for pref, num in pattern.findall(text):
        model_id = match_model(pref[-80:])
        if not model_id:
            continue
        value = float(num)
        if value > 100:
            continue
        add_score(scores, model_id, key, value)


def parse_aa_index(text: str, scores: dict[str, dict[str, float]]) -> None:
    for spec in MODELS:
        for alias in spec["aliases"]:
            found = re.search(
                re.escape(alias) + r".{0,120}?\b(index|score of|scores)\s+(\d{2,3})\b",
                text,
                re.IGNORECASE | re.DOTALL,
            )
            if found:
                add_score(scores, spec["id"], "aa", float(found.group(2)))
            found = re.search(
                r"\b(\d{2})\b.{0,40}" + re.escape(alias),
                text,
                re.IGNORECASE | re.DOTALL,
            )
            if found:
                val = float(found.group(1))
                if 40 <= val <= 80:
                    add_score(scores, spec["id"], "aa", val)


def parse_openai_prices(text: str, prices: dict[str, float]) -> None:
    for model_id, needle in (
        ("gpt-5.6-sol", "gpt-5.6-sol"),
        ("gpt-5.6-terra", "gpt-5.6-terra"),
        ("gpt-5.6-luna", "gpt-5.6-luna"),
    ):
        block = re.search(
            re.escape(needle) + r".{0,400}?\$(\d+(?:\.\d+))",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not block:
            continue
        # Prefer the Output column: take the last $ in the short-context row if present.
        row = re.search(
            re.escape(needle) + r"[^\n]*\$(\d+(?:\.\d+))[^\n]*\$(\d+(?:\.\d+))[^\n]*\$(\d+(?:\.\d+))[^\n]*\$(\d+(?:\.\d+))",
            text,
            re.IGNORECASE,
        )
        if row:
            prices[model_id] = float(row.group(4))
        else:
            prices[model_id] = float(block.group(1))
    if "gpt-5.6-sol" in _norm(text) and "$60.00" in text:
        prices["gpt-5.6-sol-fast"] = 60.0
    if "gpt-5.6-cyber" in _norm(text):
        prices["gpt-5.6-cyber"] = 75.0


def parse_anthropic_prices(text: str, prices: dict[str, float]) -> None:
    mapping = (
        ("claude-fable-5", "Claude Fable 5"),
        ("claude-mythos-5", "Claude Mythos 5"),
        ("claude-opus-5", "Claude Opus 5"),
        ("claude-sonnet-5", "Claude Sonnet 5"),
        ("claude-sonnet-4.6", "Claude Sonnet 4.6"),
    )
    for model_id, label in mapping:
        for line in text.splitlines():
            if label.lower() not in line.lower():
                continue
            if model_id == "claude-opus-5" and re.search(r"\bfast\b", line, re.IGNORECASE):
                continue
            amounts = [float(n) for n in re.findall(r"\$(\d+(?:\.\d+)?)\s*/\s*MTok", line)]
            if amounts:
                prices[model_id] = max(amounts)
                break
    if re.search(r"Fast mode.{0,400}Claude Opus 5.{0,200}\$50", text, re.IGNORECASE | re.DOTALL):
        prices["claude-opus-5-fast"] = 50.0


def parse_source(source_id: str, text: str, scores: dict[str, dict[str, float]], prices: dict[str, float]) -> None:
    if source_id == "cursorbench":
        parse_percent_near_name(text, "cursorbench", scores)
        return
    if source_id == "deepswe":
        parse_percent_near_name(text, "deepswe", scores)
        return
    if source_id in {"swebench-vals", "terminalbench", "gemini-3-7-flash-card"}:
        key = "swebench" if source_id == "swebench-vals" else (
            "terminalbench" if source_id == "terminalbench" else "deepswe"
        )
        parse_percent_near_name(text, key, scores)
        return
    if source_id in {"aa-intelligence", "aa-grok-4-6"}:
        parse_aa_index(text, scores)
        parse_percent_near_name(text, "terminalbench", scores)
        return
    if source_id == "openai-pricing":
        parse_openai_prices(text, prices)
        return
    if source_id in {"anthropic-pricing", "anthropic-pricing-docs"}:
        parse_anthropic_prices(text, prices)


def composite(row: dict[str, float]) -> float | None:
    parts: list[tuple[float, float]] = []
    if "deepswe" in row:
        parts.append((0.5, row["deepswe"]))
    if "cursorbench" in row:
        parts.append((0.4, row["cursorbench"]))
    if "aa" in row:
        parts.append((0.1, row["aa"]))
    if "terminalbench" in row and not parts:
        parts.append((1.0, row["terminalbench"]))
    if not parts:
        return None
    weight = sum(w for w, _ in parts)
    return sum(w * v for w, v in parts) / weight


def propose(
    scores: dict[str, dict[str, float]],
    prices: dict[str, float],
    old_pins: dict[str, list[str]],
    sub_ok: set[str],
    max_out: int,
) -> dict[str, Any]:
    never = list(ALWAYS_NEVER_PIN)
    for model_id, price in prices.items():
        if price >= NEVER_PIN_USD and model_id not in sub_ok and model_id not in never:
            never.append(model_id)
    never = sorted(set(never))

    observed = set(scores) | set(prices)
    t0: list[str] = []
    t1: list[str] = []
    t2: list[str] = []
    dropped: list[str] = []
    for spec in MODELS:
        model_id = spec["id"]
        if model_id in never or spec["family"] == "exclude":
            continue
        row = scores.get(model_id, {})
        score = composite(row)
        family = spec["family"]
        if family == "drop":
            if score is not None and score < 45:
                dropped.append(model_id)
            continue
        if family == "t0" and (score is None or score >= 60):
            t0.extend(T0_ALIASES.get(model_id, (model_id,)))
            continue
        if family == "t1":
            if score is None or score >= 50 or model_id in T1_KEEP_INHARNESS:
                t1.append(model_id)
            if model_id in T1_KEEP_INHARNESS:
                t2.append(model_id)
            continue
        if family == "t2":
            t2.extend(T2_ALIASES.get(model_id, (model_id,)))

    def merge(role: str, proposed: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for item in proposed:
            if item in seen or item in never:
                continue
            seen.add(item)
            out.append(item)
        for item in old_pins.get(role, []):
            canon = item
            family = None
            for spec in MODELS:
                aliases = spec["aliases"] + T0_ALIASES.get(spec["id"], ()) + T2_ALIASES.get(spec["id"], ())
                if item == spec["id"] or item in aliases:
                    canon = spec["id"]
                    family = spec["family"]
                    break
            if role == "T0" and family in {"t1", "t2", "exclude", "drop"}:
                continue
            if role == "T1" and family in {"t0", "t2", "exclude", "drop"}:
                continue
            if canon in observed or item in never or item in seen:
                continue
            seen.add(item)
            out.append(item)
        return out

    t2_merged = merge("T2", t2)
    for extra in T2_DEFAULT_EXTRAS:
        if extra not in t2_merged and extra not in never:
            t2_merged.append(extra)
    t0_merged = merge("T0", t0)
    if not t0_merged:
        t0_merged = old_pins.get("T0") or ["claude-opus-5", "grok-4.6", "gpt-5.6-sol", "kimi-k3"]
    return {
        "never_pin": never,
        "T0": t0_merged,
        "T1": merge("T1", t1),
        "T2": t2_merged,
        "dropped": dropped,
        "observed": sorted(observed),
    }


def extract_pins(roster_text: str, role: str) -> list[str]:
    start = f"# refresh:pins:{role}"
    end = f"# /refresh:pins:{role}"
    if start not in roster_text or end not in roster_text:
        return []
    block = roster_text.split(start, 1)[1].split(end, 1)[0]
    return [line.strip()[2:].strip() for line in block.splitlines() if line.strip().startswith("- ")]


def replace_block(text: str, start: str, end: str, inner: str) -> str:
    idx = text.find(start)
    if idx < 0 or end not in text[idx:]:
        raise ValueError(f"missing markers {start}")
    line_start = text.rfind("\n", 0, idx) + 1
    indent = text[line_start:idx]
    before = text[:idx]
    after = text[idx:].split(end, 1)[1]
    body = inner if inner.endswith("\n") else inner + "\n"
    return before + start + "\n" + body + indent + end + after


def pins_yaml(items: list[str], indent: str = "      ") -> str:
    return "".join(f"{indent}- {item}\n" for item in items)


def apply_roster(roster_path: Path, proposal: dict[str, Any], today: str) -> None:
    text = roster_path.read_text(encoding="utf-8")
    text = re.sub(r"Rankings snapshot: \d{4}-\d{2}-\d{2}", f"Rankings snapshot: {today}", text, count=1)
    text = replace_block(text, "# refresh:never_pin", "# /refresh:never_pin", pins_yaml(proposal["never_pin"], "  "))
    for role in ("T0", "T1", "T2"):
        text = replace_block(
            text,
            f"# refresh:pins:{role}",
            f"# /refresh:pins:{role}",
            pins_yaml(proposal[role]),
        )
    roster_path.write_text(text, encoding="utf-8", newline="\n")


def render_generated(
    coverage: list[dict[str, str]],
    scores: dict[str, dict[str, float]],
    prices: dict[str, float],
    proposal: dict[str, Any],
    urls: list[tuple[str, str]],
) -> str:
    def cell(model_id: str, key: str) -> str:
        row = scores.get(model_id, {})
        if key not in row:
            return "-"
        return f"{row[key]:g}"

    lines = [
        "",
        "## Pins from this fetch",
        "",
        "| Role | Pins |",
        "| --- | --- |",
        f"| T0 | {', '.join(proposal['T0'])} |",
        f"| T1 | {', '.join(proposal['T1'])} |",
        f"| T2 | {', '.join(proposal['T2'])} |",
        f"| never_pin | {', '.join(proposal['never_pin'])} |",
        "",
        "## Scores from this fetch",
        "",
        "| Model | AA | CursorBench | DeepSWE | Terminal-Bench | SWE-bench | API out $/M |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for spec in MODELS:
        mid = spec["id"]
        price = prices.get(mid)
        price_s = f"{price:g}" if price is not None else "-"
        lines.append(
            f"| {mid} | {cell(mid, 'aa')} | {cell(mid, 'cursorbench')} | "
            f"{cell(mid, 'deepswe')} | {cell(mid, 'terminalbench')} | "
            f"{cell(mid, 'swebench')} | {price_s} |"
        )
    lines.extend(["", "## Fetch coverage", ""])
    for row in coverage:
        lines.append(f"- {row['id']}: {row['result']}. {row['detail']}")
    lines.extend(["", "## Sources fetched", ""])
    for source_id, url in urls:
        lines.append(f"- [{source_id}]({url})")
    lines.append("")
    return "\n".join(lines)


def apply_leaderboards(path: Path, generated: str, today: str) -> None:
    if path.is_file():
        text = path.read_text(encoding="utf-8")
    else:
        text = f"# Leaderboard snapshot ({today})\n\n{GEN_START}\n{GEN_END}\n"
    text = re.sub(r"\(20\d{2}-\d{2}-\d{2}\)", f"({today})", text, count=1)
    if GEN_START in text and GEN_END in text:
        before, rest = text.split(GEN_START, 1)
        _, after = rest.split(GEN_END, 1)
        text = before + GEN_START + generated + GEN_END + after
    else:
        text = text.rstrip() + "\n\n" + GEN_START + generated + GEN_END + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def load_snapshot(path: Path) -> tuple[dict[str, dict[str, float]], dict[str, float]]:
    if not path.is_file():
        return {}, {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, {}
    scores = data.get("scores") if isinstance(data, dict) else None
    prices = data.get("prices") if isinstance(data, dict) else None
    out_scores: dict[str, dict[str, float]] = {}
    if isinstance(scores, dict):
        for model_id, row in scores.items():
            if isinstance(model_id, str) and isinstance(row, dict):
                out_scores[model_id] = {
                    str(k): float(v) for k, v in row.items() if isinstance(v, (int, float))
                }
    out_prices: dict[str, float] = {}
    if isinstance(prices, dict):
        for model_id, value in prices.items():
            if isinstance(model_id, str) and isinstance(value, (int, float)):
                out_prices[model_id] = float(value)
    return out_scores, out_prices


def merge_scores(
    previous: dict[str, dict[str, float]], fresh: dict[str, dict[str, float]]
) -> dict[str, dict[str, float]]:
    out = {key: dict(row) for key, row in previous.items()}
    for model_id, row in fresh.items():
        merged = dict(out.get(model_id, {}))
        merged.update(row)
        out[model_id] = merged
    return out


def collect(
    timeout: int,
    urls: list[tuple[str, str]],
) -> tuple[dict[str, dict[str, float]], dict[str, float], list[dict[str, str]]]:
    scores: dict[str, dict[str, float]] = {}
    prices: dict[str, float] = {}
    coverage: list[dict[str, str]] = []
    for source_id, url in urls:
        status, body = fetch(url, timeout)
        if status != "found" or body is None:
            coverage.append({"id": source_id, "result": "missing", "detail": body or url})
            continue
        parse_source(source_id, body, scores, prices)
        coverage.append({"id": source_id, "result": "found", "detail": url})
    return scores, prices, coverage


def run(apply: bool) -> int:
    urls, timeout, sub_ok, max_out = load_sources()
    refs = policy_dir()
    roster_path = refs / "roster.yaml"
    if not roster_path.is_file():
        print(f"roster.yaml missing at {roster_path}", file=sys.stderr)
        return 2
    old = {
        "T0": extract_pins(roster_path.read_text(encoding="utf-8"), "T0"),
        "T1": extract_pins(roster_path.read_text(encoding="utf-8"), "T1"),
        "T2": extract_pins(roster_path.read_text(encoding="utf-8"), "T2"),
    }
    prev_scores, prev_prices = load_snapshot(refs / "leaderboards.snapshot.json")
    scores, prices, coverage = collect(timeout, urls)
    scores = merge_scores(prev_scores, scores)
    prices = {**prev_prices, **prices}
    proposal = propose(scores, prices, old, sub_ok, max_out)
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    snapshot = {
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "coverage": coverage,
        "scores": scores,
        "prices": prices,
        "proposal": proposal,
        "pricing_gate": {
            "max_api_output_usd_per_m": max_out,
            "never_pin_usd_per_m": NEVER_PIN_USD,
        },
    }
    print(json.dumps({"proposal": proposal, "coverage": coverage}, indent=2))
    if not apply:
        print("dry run. pass --apply to write roster.yaml and leaderboards.md")
        return 0
    apply_roster(roster_path, proposal, today)
    (refs / "leaderboards.snapshot.json").write_text(
        json.dumps(snapshot, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    md = render_generated(coverage, scores, prices, proposal, urls)
    apply_leaderboards(refs / "leaderboards.md", md, today)
    print(f"wrote {roster_path}")
    print(f"wrote {refs / 'leaderboards.md'}")
    if "gemini-3.7-flash" in proposal["T1"]:
        print("adapter hint: Cursor t1-submaster stays gemini-3.7-flash-high; Agy t1 stays flash")
    if "gpt-5.6-luna" in proposal["T2"]:
        print("adapter hint: Codex t2-luna stays gpt-5.6-luna high")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refresh T0/T1/T2 roster from public leaderboards")
    parser.add_argument("--apply", action="store_true", help="Write roster.yaml and leaderboards.md")
    args = parser.parse_args(argv)
    return run(apply=args.apply)


if __name__ == "__main__":
    raise SystemExit(main())
