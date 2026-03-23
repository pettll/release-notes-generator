"""
Parse git log output into structured commits.

Conventional Commits spec: https://www.conventionalcommits.org/
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field


COMMIT_PATTERN = re.compile(
    r"^(?P<type>feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
    r"(?:\((?P<scope>[^)]+)\))?"
    r"(?P<breaking>!)?"
    r":\s*(?P<subject>.+)$"
)

BREAKING_FOOTER = re.compile(r"^BREAKING[\- ]CHANGE:", re.MULTILINE)

ISSUE_PATTERN = re.compile(r"(?:closes?|fixes?|resolves?)\s+#(\d+)", re.IGNORECASE)


@dataclass
class Commit:
    hash: str
    short_hash: str
    author: str
    date: str
    raw_subject: str
    body: str
    commit_type: str = "other"
    scope: str | None = None
    subject: str = ""
    breaking: bool = False
    issues: list[str] = field(default_factory=list)


def parse_commits(from_ref: str, to_ref: str, repo_path: str = ".") -> list[Commit]:
    """Run git log and return a list of parsed Commit objects."""
    separator = "----COMMIT----"
    fmt = f"{separator}%n%H%n%h%n%an%n%ad%n%s%n%b"

    result = subprocess.run(
        [
            "git", "-C", repo_path,
            "log",
            f"--pretty=format:{fmt}",
            "--date=short",
            f"{from_ref}..{to_ref}",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    commits: list[Commit] = []
    raw_blocks = result.stdout.split(separator)

    for block in raw_blocks:
        lines = block.strip().splitlines()
        if len(lines) < 5:
            continue

        full_hash = lines[0].strip()
        short_hash = lines[1].strip()
        author = lines[2].strip()
        date = lines[3].strip()
        raw_subject = lines[4].strip()
        body = "\n".join(lines[5:]).strip()

        commit = Commit(
            hash=full_hash,
            short_hash=short_hash,
            author=author,
            date=date,
            raw_subject=raw_subject,
            body=body,
        )

        match = COMMIT_PATTERN.match(raw_subject)
        if match:
            commit.commit_type = match.group("type")
            commit.scope = match.group("scope")
            commit.subject = match.group("subject")
            commit.breaking = bool(match.group("breaking")) or bool(
                BREAKING_FOOTER.search(body)
            )
        else:
            commit.subject = raw_subject

        issue_matches = ISSUE_PATTERN.findall(raw_subject + "\n" + body)
        commit.issues = [f"#{n}" for n in issue_matches]

        commits.append(commit)

    return commits
