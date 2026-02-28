#!/usr/bin/env python3
"""Bump the project version in pyproject.toml.

Usage:
    python scripts/bump_version.py patch      # 0.1.0 -> 0.1.1
    python scripts/bump_version.py minor      # 0.1.0 -> 0.2.0
    python scripts/bump_version.py major      # 0.1.0 -> 1.0.0
    python scripts/bump_version.py --set 1.2.3

    # Bump AND commit + tag + push in one step:
    python scripts/bump_version.py minor --release
    python scripts/bump_version.py --set 1.2.3 --release
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

PYPROJECT = Path(__file__).parent.parent / "pyproject.toml"
VERSION_RE = re.compile(r'^(version\s*=\s*")[^"]+(")', re.MULTILINE)


def read_version(text: str) -> str:
    m = VERSION_RE.search(text)
    if not m:
        sys.exit("Could not find version in pyproject.toml")
    return VERSION_RE.search(text).group(0).split('"')[1]


def bump(version: str, part: str) -> str:
    major, minor, patch = (int(x) for x in version.split("."))
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    if part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    sys.exit(f"Unknown bump part: {part!r}")


def write_version(text: str, new_version: str) -> str:
    return VERSION_RE.sub(lambda m: f'{m.group(0).split(chr(34))[0]}"{new_version}"', text)


def run(cmd: list[str]) -> None:
    """Run a shell command, printing it first.  Exit on failure."""
    print("  $", " ".join(cmd))
    result = subprocess.run(cmd, cwd=PYPROJECT.parent)
    if result.returncode != 0:
        sys.exit(f"Command failed (exit {result.returncode}): {' '.join(cmd)}")


def release(new_version: str) -> None:
    """Commit pyproject.toml, create a tag, and push both to origin."""
    tag = f"v{new_version}"
    print(f"\nReleasing {tag}...")
    run(["git", "add", str(PYPROJECT)])
    run(["git", "commit", "-m", f"chore: bump version to {new_version}"])
    run(["git", "tag", tag])
    run(["git", "push"])
    run(["git", "push", "--tags"])
    print(f"\nDone — tag {tag} pushed.  The release workflow will publish to PyPI.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bump the project version.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "part",
        nargs="?",
        choices=["major", "minor", "patch"],
        help="Version part to increment",
    )
    group.add_argument(
        "--set",
        dest="new_version",
        metavar="VERSION",
        help="Set an explicit version (e.g. 1.2.3)",
    )
    parser.add_argument(
        "--release",
        action="store_true",
        help="After bumping, commit pyproject.toml, create a git tag, and push",
    )
    args = parser.parse_args()

    text = PYPROJECT.read_text(encoding="utf-8")
    current = read_version(text)

    if args.new_version:
        if not re.fullmatch(r"\d+\.\d+\.\d+", args.new_version):
            sys.exit(f"Invalid version format: {args.new_version!r}. Expected X.Y.Z")
        new_version = args.new_version
    else:
        new_version = bump(current, args.part)

    if new_version == current:
        print(f"Version is already {current}, nothing to do.")
        return

    PYPROJECT.write_text(write_version(text, new_version), encoding="utf-8")
    print(f"{current} -> {new_version}")

    if args.release:
        release(new_version)


if __name__ == "__main__":
    main()
