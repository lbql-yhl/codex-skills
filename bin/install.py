#!/usr/bin/env python3
"""Install selected skills from this repository into a Codex-compatible skills directory."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "manifest.json"


def load_manifest() -> dict:
    with MANIFEST_PATH.open("r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def default_target() -> Path:
    explicit = os.environ.get("CODEX_SKILLS_DIR")
    if explicit:
        return Path(explicit).expanduser()
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser() / "skills"
    return Path.home() / ".codex" / "skills"


def copy_tree(source: Path, destination: Path, dry_run: bool) -> list[str]:
    changed: list[str] = []
    for path in source.rglob("*"):
        relative = path.relative_to(source)
        target = destination / relative
        if path.is_dir():
            if not dry_run:
                target.mkdir(parents=True, exist_ok=True)
            continue
        changed.append(str(target))
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
    return changed


def main() -> int:
    manifest = load_manifest()
    entries = {item["name"]: item for item in manifest["skills"]}

    parser = argparse.ArgumentParser(description="Install reusable skills")
    parser.add_argument("skills", nargs="*", help="skill names to install")
    parser.add_argument("--all", action="store_true", help="install every skill")
    parser.add_argument("--list", action="store_true", help="list available skills")
    parser.add_argument("--target", type=Path, help="destination skills directory")
    parser.add_argument("--dry-run", action="store_true", help="show files without writing")
    args = parser.parse_args()

    if args.list:
        for item in manifest["skills"]:
            print(f"{item['name']}\t{item['status']}\t{item['display_name']}")
        return 0

    requested = list(entries) if args.all or not args.skills else args.skills
    unknown = [name for name in requested if name not in entries]
    if unknown:
        print("Unknown skill(s): " + ", ".join(unknown), file=sys.stderr)
        print("Use --list to see available skills.", file=sys.stderr)
        return 2

    target_root = (args.target or default_target()).expanduser().resolve()
    print(f"Target: {target_root}")
    for name in requested:
        item = entries[name]
        source = (REPO_ROOT / item["path"]).resolve()
        if not source.is_dir() or not (source / "SKILL.md").is_file():
            print(f"Missing skill source: {source}", file=sys.stderr)
            return 3
        destination = target_root / name
        changed = copy_tree(source, destination, args.dry_run)
        marker = destination / ".reusable-skill.json"
        metadata = {
            "name": name,
            "source_repository": manifest.get("repository"),
            "source_path": item["path"],
            "status": item["status"],
        }
        if not args.dry_run:
            marker.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{('[dry-run] ' if args.dry_run else '')}installed {name} ({len(changed)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
