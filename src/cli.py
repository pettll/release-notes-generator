#!/usr/bin/env python3
"""
release-notes — generate structured release notes from git log.

Usage:
    release-notes --from v1.1.0 --to v1.2.0
    release-notes --from HEAD~20 --to HEAD --version 1.2.0 --format markdown
    release-notes --from main --to feature/xyz --format json
"""

from __future__ import annotations

import argparse
import subprocess
import sys

from .parser import parse_commits
from .renderer import render, OutputFormat


def _latest_tag(repo_path: str) -> str:
    result = subprocess.run(
        ["git", "-C", repo_path, "describe", "--tags", "--abbrev=0"],
        capture_output=True, text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "HEAD~1"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate release notes from git commit history",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "-f", "--from", dest="from_ref", required=True,
        help="Base git ref (e.g. v1.1.0, HEAD~10, main)",
    )
    parser.add_argument(
        "-t", "--to", dest="to_ref", default="HEAD",
        help="Target git ref (default: HEAD)",
    )
    parser.add_argument(
        "-v", "--version", default=None,
        help="Version label in the output (default: derived from --to)",
    )
    parser.add_argument(
        "--format", dest="fmt", default="markdown",
        choices=["markdown", "text", "json"],
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "-o", "--output", default=None,
        help="Write output to this file instead of stdout",
    )
    parser.add_argument(
        "-r", "--repo", default=".",
        help="Path to git repository (default: .)",
    )
    parser.add_argument(
        "--repo-url", default=None,
        help="GitHub/GitLab repo URL for commit and issue hyperlinks in Markdown",
    )

    args = parser.parse_args()

    version = args.version or args.to_ref

    try:
        commits = parse_commits(args.from_ref, args.to_ref, args.repo)
    except subprocess.CalledProcessError as e:
        print(f"Error running git: {e.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    if not commits:
        print(f"No commits found between {args.from_ref} and {args.to_ref}.", file=sys.stderr)
        sys.exit(0)

    output = render(commits, version, fmt=args.fmt, repo_url=args.repo_url)  # type: ignore[arg-type]

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(output)
        print(f"Release notes written to {args.output}  ({len(commits)} commits)", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
