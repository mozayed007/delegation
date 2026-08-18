"""Probe installed agent CLIs and write roster.local.yaml. Stdlib only."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import socket
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

HOME = Path.home()
CCR_HOST = "127.0.0.1"
CCR_PORT = 3456

TOOL_SPECS: tuple[dict[str, Any], ...] = (
    {"name": "agy", "bins": ("agy",), "homes": (), "role": "T1"},
    {"name": "opencode", "bins": ("opencode",), "homes": ("config/opencode",), "role": "T2"},
    {"name": "kimi", "bins": ("kimi", "kimi-cli"), "homes": (".kimi-code",), "role": "T0"},
    {"name": "cursor", "bins": ("cursor",), "homes": (".cursor",), "role": "T2"},
    {
        "name": "cursor-agent",
        "bins": ("cursor-agent", "agent"),
        "homes": (".cursor",),
        "role": "T2",
    },
    {"name": "grok", "bins": ("grok",), "homes": (".grok",), "role": "T0"},
    {"name": "dsh", "bins": ("dsh",), "homes": (".dsh",), "role": "T2"},
    {"name": "codex", "bins": ("codex",), "homes": (".codex",), "role": "T0"},
    {"name": "claude", "bins": ("claude",), "homes": (".claude",), "role": "T0"},
    {"name": "gnhf", "bins": ("gnhf",), "homes": (), "role": None},
    {"name": "no-mistakes", "bins": ("no-mistakes",), "homes": (), "role": None},
    {"name": "treehouse", "bins": ("treehouse",), "homes": (), "role": None},
    {"name": "devin", "bins": ("devin",), "homes": (".config/devin",), "role": "T1"},
    {"name": "gemini", "bins": ("gemini",), "homes": (".gemini",), "role": None},
    {"name": "qwen", "bins": ("qwen",), "homes": (".qwen",), "role": None},
    {"name": "copilot", "bins": ("copilot",), "homes": (".copilot",), "role": None},
)

SECRET_KEY_PARTS = (
    "key",
    "token",
    "secret",
    "password",
    "authorization",
    "credential",
)


def skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


def repo_root() -> Path:
    return skill_root().parent.parent


def source_clone_root() -> Path | None:
    """Return the git clone of this pack, or None when running from an installed copy."""
    candidate = skill_root().parent.parent
    if (candidate / ".git").exists() and (candidate / "adapters" / "cursor" / "agents").is_dir():
        return candidate
    return None


def which(names: tuple[str, ...]) -> Path | None:
    for name in names:
        found = shutil.which(name)
        if found:
            return Path(found)
    return None


def run_version(binary: Path) -> str | None:
    try:
        proc = subprocess.run(
            [str(binary), "--version"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = (proc.stdout or proc.stderr or "").strip().splitlines()
    if not text:
        return None
    return text[0].strip()[:200]


def ccr_reachable() -> str:
    try:
        with socket.create_connection((CCR_HOST, CCR_PORT), timeout=0.6):
            return "true"
    except OSError:
        return "false"


def first_existing(paths: tuple[Path, ...]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def read_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def read_toml(path: Path) -> dict[str, Any] | None:
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError):
        return None
    if isinstance(data, dict):
        return data
    return None


def yaml_scalar_after(text: str, key: str) -> str | None:
    needle = key + ":"
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith(needle):
            value = line[len(needle) :].strip().strip("'\"")
            return value or None
    return None


def default_model_for(name: str) -> tuple[str | None, Path | None, list[str]]:
    env_names: list[str] = []
    if name == "opencode":
        home = HOME / ".config" / "opencode"
        data = read_json(home / "opencode.json")
        model = None
        if isinstance(data, dict):
            raw = data.get("model")
            if isinstance(raw, str):
                model = raw
            provider = data.get("provider")
            if isinstance(provider, dict):
                for spec in provider.values():
                    if not isinstance(spec, dict):
                        continue
                    options = spec.get("options")
                    if isinstance(options, dict):
                        for key in options:
                            if any(part in key.lower() for part in SECRET_KEY_PARTS):
                                env_names.append("OPENCODE_API_KEY")
                                break
        return model, home if home.exists() else None, sorted(set(env_names))
    if name == "kimi":
        home = HOME / ".kimi-code"
        data = read_toml(home / "config.toml")
        model = None
        if isinstance(data, dict) and isinstance(data.get("default_model"), str):
            model = data["default_model"]
        return model, home if home.exists() else None, []
    if name in {"cursor", "cursor-agent"}:
        home = HOME / ".cursor"
        data = read_json(home / "cli-config.json")
        model = None
        if isinstance(data, dict):
            block = data.get("model")
            if isinstance(block, dict) and isinstance(block.get("modelId"), str):
                model = block["modelId"]
        return model, home if home.exists() else None, []
    if name == "grok":
        home = HOME / ".grok"
        data = read_toml(home / "config.toml")
        model = None
        if isinstance(data, dict):
            models = data.get("models")
            if isinstance(models, dict) and isinstance(models.get("default"), str):
                model = models["default"]
        return model, home if home.exists() else None, []
    if name == "dsh":
        home = HOME / ".dsh"
        settings = home / "settings.yaml"
        model = None
        env_names = [
            "OPENCODE_API_KEY",
            "FIREWORKS_API_KEY",
            "GEMINI_API_KEY",
            "OPENROUTER_API_KEY",
            "MIMO_API_KEY",
            "NEURALWATT_API_KEY",
            "COMPOSER_API_KEY",
            "DASHSCOPE_API_KEY",
        ]
        if settings.is_file():
            text = settings.read_text(encoding="utf-8")
            provider = yaml_scalar_after(text, "provider")
            raw_model = yaml_scalar_after(text, "model")
            if provider and raw_model:
                model = f"{provider}/{raw_model}"
            elif raw_model:
                model = raw_model
        return model, home if home.exists() else None, env_names
    if name == "codex":
        home = HOME / ".codex"
        data = read_toml(home / "config.toml")
        model = None
        if isinstance(data, dict) and isinstance(data.get("model"), str):
            effort = data.get("model_reasoning_effort")
            model = data["model"]
            if isinstance(effort, str):
                model = f"{model} ({effort})"
        return model, home if home.exists() else None, []
    if name == "claude":
        home = HOME / ".claude"
        data = read_json(home / "settings.json")
        model = None
        if isinstance(data, dict) and isinstance(data.get("model"), str):
            model = data["model"]
        return model, home if home.exists() else None, []
    if name == "devin":
        roaming = Path(os.environ.get("APPDATA", "")) / "devin"
        xdg = HOME / ".config" / "devin"
        home = first_existing((xdg, roaming if roaming != Path("devin") else xdg))
        model = None
        for cfg_dir in (roaming, xdg):
            if not cfg_dir.is_dir():
                continue
            data = read_json(cfg_dir / "config.json")
            if not isinstance(data, dict):
                continue
            agent = data.get("agent")
            if isinstance(agent, dict) and isinstance(agent.get("model"), str):
                model = agent["model"]
                break
            for key in ("default_model", "model", "defaultModel"):
                raw = data.get(key)
                if isinstance(raw, str):
                    model = raw
                    break
            if model:
                break
        return model, home, []
    if name == "agy":
        return None, None, []
    mapped = {
        "gemini": HOME / ".gemini",
        "qwen": HOME / ".qwen",
        "copilot": HOME / ".copilot",
    }
    home = mapped.get(name)
    return None, home if home and home.exists() else None, []


def yaml_escape(value: str) -> str:
    if value == "" or any(ch in value for ch in ":#{}[]&*!|>'\"%@`"):
        return json.dumps(value)
    return value


def dump_yaml(obj: Any, indent: int = 0) -> str:
    pad = "  " * indent
    if obj is None:
        return "null"
    if isinstance(obj, bool):
        return "true" if obj else "false"
    if isinstance(obj, (int, float)):
        return str(obj)
    if isinstance(obj, str):
        return yaml_escape(obj)
    if isinstance(obj, list):
        if not obj:
            return "[]"
        parts: list[str] = []
        for item in obj:
            if isinstance(item, (dict, list)):
                nested = dump_yaml(item, indent + 1)
                nested_lines = nested.splitlines()
                parts.append(f"{pad}- {nested_lines[0].lstrip()}")
                for extra in nested_lines[1:]:
                    parts.append(extra)
            else:
                parts.append(f"{pad}- {dump_yaml(item)}")
        return "\n".join(parts)
    if isinstance(obj, dict):
        if not obj:
            return "{}"
        parts = []
        for key, value in obj.items():
            if isinstance(value, dict):
                if not value:
                    parts.append(f"{pad}{key}: {{}}")
                else:
                    parts.append(f"{pad}{key}:")
                    parts.append(dump_yaml(value, indent + 1))
            elif isinstance(value, list):
                if not value:
                    parts.append(f"{pad}{key}: []")
                else:
                    parts.append(f"{pad}{key}:")
                    parts.append(dump_yaml(value, indent + 1))
            else:
                parts.append(f"{pad}{key}: {dump_yaml(value)}")
        return "\n".join(parts)
    return yaml_escape(str(obj))


def probe_tools() -> tuple[dict[str, Any], list[dict[str, str]]]:
    tools: dict[str, Any] = {}
    coverage: list[dict[str, str]] = []
    for spec in TOOL_SPECS:
        name = spec["name"]
        binary = which(spec["bins"])
        version = run_version(binary) if binary else None
        model, config_home, env_names = default_model_for(name)
        present = binary is not None
        tools[name] = {
            "present": present,
            "binary": str(binary) if binary else None,
            "version": version,
            "config_home": str(config_home) if config_home else None,
            "default_model": model,
            "role_if_used_as_is": spec["role"] if present else None,
            "notes": None,
            "env_var_names": env_names,
        }
        if name == "cursor" and present:
            tools[name]["notes"] = (
                "Default Composer is T2. T0/T1 quota fallback: pick Sol/Opus/Grok 4.6; "
                "do not drop to Composer Fast"
            )
        if name == "cursor-agent" and present:
            tools[name]["notes"] = (
                "Ignore empty --list-models in headless; use ~/.cursor/cli-config.json. "
                "Default Composer is T2. T0/T1 quota fallback: pick Sol/Opus/Grok 4.6; "
                "do not drop to Composer Fast"
            )
        if name == "devin" and present:
            tools[name]["notes"] = (
                "Default swe is not T0. T0/T1: devin --model opus|gpt-5.6-sol|grok-4.6|kimi-k3. "
                "Never Fable/Mythos/fast SKUs"
            )
        if name == "agy" and present:
            tools[name]["notes"] = (
                "Prefer Gemini 3.7 Flash over Gemini 3.1 Pro for T1. Opus on Agy is T0."
            )
        if name == "kimi" and (HOME / ".kimi").exists() and not (HOME / ".kimi-code").exists():
            tools[name]["notes"] = "legacy ~/.kimi present; expected active home is ~/.kimi-code"
        coverage.append(
            {
                "source": name,
                "result": "found" if present else "missing",
                "detail": str(binary) if binary else f"not on PATH: {', '.join(spec['bins'])}",
            }
        )
    return tools, coverage


def load_role_policy() -> dict[str, Any]:
    path = skill_root() / "references" / "roster.yaml"
    if not path.is_file():
        return {}
    # Keep role policy as raw text copy target; doctor does not parse full YAML.
    return {"path": str(path)}


def build_roster() -> dict[str, Any]:
    tools, coverage = probe_tools()
    reachable = ccr_reachable()
    coverage.append(
        {
            "source": "claude-code-router",
            "result": "found" if reachable == "true" else "missing",
            "detail": f"{CCR_HOST}:{CCR_PORT} reachable={reachable}",
        }
    )
    agents_skills = HOME / ".agents" / "skills"
    coverage.append(
        {
            "source": "~/.agents/skills",
            "result": "found" if agents_skills.is_dir() else "missing",
            "detail": str(agents_skills),
        }
    )
    return {
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ccr": {"host": CCR_HOST, "port": CCR_PORT, "reachable": reachable},
        "role_policy": str(skill_root() / "references" / "roster.yaml"),
        "tools": tools,
        "coverage": coverage,
    }


def write_roster(roster: dict[str, Any], dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    body = dump_yaml(roster) + "\n"
    dest.write_text(body, encoding="utf-8", newline="\n")
    policy_src = skill_root() / "references" / "roster.yaml"
    policy_dest = dest.parent / "roster.yaml"
    if policy_src.is_file():
        shutil.copy2(policy_src, policy_dest)


def print_map(roster: dict[str, Any]) -> None:
    print(f"CCR {CCR_HOST}:{CCR_PORT} reachable={roster['ccr']['reachable']}")
    print("tool\tpresent\trole\tdefault_model\tbinary")
    tools = roster["tools"]
    for name, spec in tools.items():
        print(
            f"{name}\t{spec['present']}\t{spec['role_if_used_as_is']}\t"
            f"{spec['default_model']}\t{spec['binary']}"
        )
    print("coverage:")
    for row in roster["coverage"]:
        print(f"- {row['source']}: {row['result']}. {row['detail']}")


def copytree(src: Path, dest: Path) -> None:
    if not src.is_dir():
        raise FileNotFoundError(str(src))
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() or dest.is_symlink():
        dest = dest.resolve()
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))


def patch_kimi_skills(agents_skills: Path) -> str:
    config = HOME / ".kimi-code" / "config.toml"
    if not config.is_file():
        return "kimi extra_skill_dirs skipped. ~/.kimi-code/config.toml missing"
    text = config.read_text(encoding="utf-8")
    marker = "~/.agents/skills"
    if marker in text:
        return "kimi extra_skill_dirs already lists ~/.agents/skills"
    old = 'extra_skill_dirs = [ "~/.config/opencode/skills" ]'
    new = 'extra_skill_dirs = [ "~/.config/opencode/skills", "~/.agents/skills" ]'
    if old in text:
        config.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
        return "kimi extra_skill_dirs appended ~/.agents/skills"
    if "extra_skill_dirs" in text:
        return "kimi extra_skill_dirs present but not the expected list; left unchanged"
    config.write_text(
        'extra_skill_dirs = [ "~/.agents/skills" ]\n' + text,
        encoding="utf-8",
        newline="\n",
    )
    return "kimi extra_skill_dirs created with ~/.agents/skills"


def patch_dsh_skills(agents_skills: Path) -> str:
    patch = HOME / ".dsh" / "profiles" / "web" / "cordis.patch.yml"
    if not patch.is_file():
        return "dsh customSkillDirs skipped. cordis.patch.yml missing"
    text = patch.read_text(encoding="utf-8")
    rendered = str(agents_skills)
    home_skills = str(HOME / ".agents" / "skills")
    if rendered in text or home_skills in text:
        return "dsh customSkillDirs already lists ~/.agents/skills"
    marker = "    customSkillDirs:"
    if marker not in text:
        return "dsh customSkillDirs block not found; left unchanged"
    lines = text.splitlines(keepends=True)
    start = None
    for index, line in enumerate(lines):
        if line.startswith(marker):
            start = index
            break
    if start is None:
        return "dsh customSkillDirs block not found; left unchanged"
    last_item = start
    index = start + 1
    while index < len(lines):
        stripped = lines[index].strip()
        if stripped.startswith("- "):
            last_item = index
            index += 1
            continue
        break
    lines.insert(last_item + 1, f"      - '{home_skills}'\n")
    patch.write_text("".join(lines), encoding="utf-8", newline="\n")
    return f"dsh customSkillDirs appended {home_skills}"


def adapters_dir() -> Path | None:
    candidates = (
        repo_root() / "adapters",
        HOME / ".agents" / "delegation" / "adapters",
    )
    for candidate in candidates:
        if (candidate / "cursor" / "agents").is_dir():
            return candidate
    return None


REFRESH_STALE_DAYS = 14


def bundled_skills() -> list[Path]:
    root = skill_root().parent
    if root.is_dir():
        found = sorted(
            path for path in root.iterdir() if path.is_dir() and (path / "SKILL.md").is_file()
        )
        if found:
            return found
    return [skill_root()]


def skill_install_dests_for(name: str) -> list[Path]:
    dests = [
        HOME / ".agents" / "skills" / name,
        HOME / ".cursor" / "skills" / name,
    ]
    xdg_devin = HOME / ".config" / "devin"
    roaming = Path(os.environ.get("APPDATA", "")) / "devin"
    if xdg_devin.is_dir():
        dests.append(xdg_devin / "skills" / name)
    if roaming.is_dir():
        dests.append(roaming / "skills" / name)
    return dests


def snapshot_path() -> Path:
    return skill_root() / "references" / "leaderboards.snapshot.json"


def refresh_script_path() -> Path | None:
    candidates = (
        skill_root().parent / "roster-refresh" / "scripts" / "refresh_roster.py",
        repo_root() / "skills" / "roster-refresh" / "scripts" / "refresh_roster.py",
        HOME / ".agents" / "skills" / "roster-refresh" / "scripts" / "refresh_roster.py",
    )
    for path in candidates:
        if path.is_file():
            return path
    return None


def snapshot_stale_note() -> str | None:
    path = snapshot_path()
    if not path.is_file():
        return (
            "leaderboards.snapshot.json missing. "
            "First-time fetch: doctor.py --install or doctor.py --refresh."
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        stamp = data.get("generated_at") if isinstance(data, dict) else None
        when = dt.datetime.strptime(str(stamp), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        when = dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.timezone.utc)
    age = (dt.datetime.now(dt.timezone.utc) - when).days
    if age >= REFRESH_STALE_DAYS:
        return (
            f"leaderboards snapshot is {age} days old. "
            "Run doctor.py --refresh or ask to refresh the roster."
        )
    return None


def run_roster_refresh() -> str:
    script = refresh_script_path()
    if script is None:
        return "roster-refresh skipped. refresh_roster.py missing"
    try:
        proc = subprocess.run(
            [sys.executable, str(script), "--apply"],
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"roster-refresh failed. {exc}"
    snippet = ((proc.stdout or "") + (proc.stderr or "")).strip().splitlines()
    tail = snippet[-12:] if snippet else []
    status = "ok" if proc.returncode == 0 else f"exit {proc.returncode}"
    return "roster-refresh " + status + (": " + " | ".join(tail) if tail else "")


def install_adapters_and_skill() -> list[str]:
    notes: list[str] = []
    seen: set[Path] = set()
    for skill_src in bundled_skills():
        for dest in skill_install_dests_for(skill_src.name):
            if dest.exists() or dest.is_symlink():
                dest = dest.resolve()
            if dest in seen:
                notes.append(f"installed skill skipped (alias of {dest})")
                continue
            seen.add(dest)
            copytree(skill_src, dest)
            notes.append(f"installed skill -> {dest}")

    adapters = adapters_dir()
    if adapters is None:
        notes.append("adapter skipped. adapters/ not found next to the skill pack")
        notes.append(patch_kimi_skills(HOME / ".agents" / "skills"))
        notes.append(patch_dsh_skills(HOME / ".agents" / "skills"))
        return notes
    durable = HOME / ".agents" / "delegation" / "adapters"
    if adapters.resolve() != durable.resolve():
        copytree(adapters, durable)
        notes.append(f"adapters snapshot -> {durable}")
    mapping = (
        (adapters / "cursor" / "agents", HOME / ".cursor" / "agents"),
        (adapters / "opencode" / "agents", HOME / ".config" / "opencode" / "agents"),
        (adapters / "codex" / "agents", HOME / ".codex" / "agents"),
        (adapters / "agy" / "agents", HOME / ".agents" / "agents"),
    )
    for src, dest in mapping:
        if not src.is_dir():
            notes.append(f"adapter skipped. missing {src}")
            continue
        dest.mkdir(parents=True, exist_ok=True)
        for item in src.iterdir():
            if item.is_file():
                shutil.copy2(item, dest / item.name)
        notes.append(f"adapters -> {dest}")
    notes.append(patch_kimi_skills(HOME / ".agents" / "skills"))
    notes.append(patch_dsh_skills(HOME / ".agents" / "skills"))
    return notes


def try_npx_skills_add() -> list[str]:
    repo = source_clone_root()
    if repo is None:
        return [
            "npx skills add skipped. not a source clone "
            "(doctor --install from ~/.agents/skills is enough)"
        ]
    npx = shutil.which("npx")
    if not npx:
        return ["npx skills add skipped. npx missing"]
    notes: list[str] = []
    for skill in bundled_skills():
        try:
            proc = subprocess.run(
                [
                    npx,
                    "-y",
                    "skills",
                    "add",
                    str(repo),
                    "--skill",
                    skill.name,
                    "-g",
                    "-a",
                    "*",
                    "-y",
                ],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            notes.append(f"npx skills add {skill.name} failed. {exc}")
            continue
        snippet = (proc.stdout or proc.stderr or "").strip().splitlines()
        tail = snippet[-8:] if snippet else []
        status = "ok" if proc.returncode == 0 else f"exit {proc.returncode}"
        notes.append(
            f"npx skills add {skill.name} " + status + (": " + " | ".join(tail) if tail else "")
        )
    return notes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe CLIs and write delegation roster")
    parser.add_argument(
        "--out",
        type=Path,
        default=HOME / ".agents" / "delegation" / "roster.local.yaml",
    )
    parser.add_argument("--install", action="store_true")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Fetch public leaderboards and apply T0/T1/T2 pins (roster-refresh).",
    )
    args = parser.parse_args(argv)
    if sys.version_info < (3, 11):
        print("Python 3.11+ required (tomllib).", file=sys.stderr)
        return 2
    load_role_policy()
    should_fetch = args.refresh or (args.install and not snapshot_path().is_file())
    if should_fetch:
        print(run_roster_refresh())
    else:
        stale = snapshot_stale_note()
        if stale:
            print(stale)
    roster = build_roster()
    write_roster(roster, args.out)
    print(f"wrote {args.out}")
    print_map(roster)
    if args.install:
        for note in install_adapters_and_skill():
            print(note)
        for note in try_npx_skills_add():
            print(note)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
