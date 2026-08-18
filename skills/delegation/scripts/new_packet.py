"""Create a delegation packet directory from templates."""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

PACKET_FILES = (
    "TASK.md",
    "CONTEXT.md",
    "PLAN.md",
    "WORK.md",
    "RESULT.md",
    "DECISIONS.md",
    "FILES.md",
)


def _template_dir(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit
    here = Path(__file__).resolve()
    candidates = [
        here.parent.parent / "templates" / "packet",
        here.parents[2] / "templates" / "packet",
    ]
    for candidate in candidates:
        if (candidate / "TASK.md").is_file():
            return candidate
    raise FileNotFoundError(
        "packet templates not found; pass --templates or run from the Delegation repo"
    )


def _fill(text: str, packet_id: str, created: str) -> str:
    return text.replace("{{PACKET_ID}}", packet_id).replace("{{CREATED}}", created)


def new_packet(
    repo: Path,
    packet_id: str,
    templates: Path,
    force: bool,
) -> Path:
    dest = repo / ".agents" / "packets" / packet_id
    if dest.exists() and not force:
        raise FileExistsError(f"packet already exists: {dest}")
    dest.mkdir(parents=True, exist_ok=True)
    created = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    missing = []
    for name in PACKET_FILES:
        src = templates / name
        if not src.is_file():
            missing.append(name)
            continue
        (dest / name).write_text(
            _fill(src.read_text(encoding="utf-8"), packet_id, created),
            encoding="utf-8",
            newline="\n",
        )
    if missing:
        raise FileNotFoundError("missing templates: " + ", ".join(missing))
    gitignore = repo / ".agents" / "packets" / ".gitignore"
    if not gitignore.is_file():
        gitignore.write_text("*\n!.gitignore\n", encoding="utf-8", newline="\n")
    repo_ignore = repo / ".gitignore"
    marker = ".agents/packets/"
    if repo_ignore.is_file():
        current = repo_ignore.read_text(encoding="utf-8")
        if marker not in current:
            with repo_ignore.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write("\n" + marker + "\n")
    else:
        repo_ignore.write_text(marker + "\n", encoding="utf-8", newline="\n")
    return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a delegation packet")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--id", dest="packet_id", default="")
    parser.add_argument("--templates", type=Path, default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    packet_id = args.packet_id.strip()
    if not packet_id:
        packet_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    try:
        dest = new_packet(
            repo=args.repo.resolve(),
            packet_id=packet_id,
            templates=_template_dir(args.templates),
            force=args.force,
        )
    except (FileExistsError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(str(dest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
