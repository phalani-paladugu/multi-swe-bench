"""Reuse an audited repository lockfile without changing dependency selection."""

import hashlib
import json
import re
from pathlib import Path

CARGO = re.compile(r"\bcargo (?:test|build)\b")


def repository_lock(task: Path, instance: dict, snapshot: str | None = None) -> str | None:
    evidence = task / "evidence/cargo-lock-source.json"
    if not evidence.exists():
        return None
    source = json.loads(evidence.read_text())
    if not source.get("reuse_committed_lock"):
        return None
    if (source.get("repository", "").lower() != instance["repo"].lower()
            or source.get("base_commit") != instance["base_commit"]):
        raise ValueError("Cargo.lock source evidence does not match the task checkout")
    digest = source.get("sha256", "")
    if (not source.get("exists") or not source.get("matches_saved")
            or not re.fullmatch(r"[a-f0-9]{64}", digest)
            or digest != source.get("saved_sha256")):
        raise ValueError("Cargo.lock source evidence does not prove snapshot equivalence")
    if snapshot is not None and hashlib.sha256(snapshot.encode()).hexdigest() != digest:
        raise ValueError("Cargo.lock snapshot differs from the audited repository lock")
    return digest


def checksum_command(digest: str) -> str:
    if not re.fullmatch(r"[a-f0-9]{64}", digest):
        raise ValueError("Invalid Cargo.lock checksum")
    return f"echo '{digest}  /testbed/Cargo.lock' | sha256sum -c -"


def enforce_locked(command: str) -> str:
    return re.sub(r"\bcargo (test|build)\b(?! --locked)", r"cargo \1 --locked", command)


def pin_x86_dockerfile(text: str, digest: str) -> str:
    """Add fail-fast and post-build checks around the audited single-line commands."""
    check = checksum_command(digest)
    lines = text.splitlines(keepends=True)
    output = []
    count = 0
    for index, line in enumerate(lines):
        if not CARGO.search(line) or line.lstrip().startswith("#"):
            output.append(line)
            continue
        if line.rstrip().endswith("\\") or line.startswith("RUN "):
            raise ValueError("Expected a single-line Cargo command inside the repository setup")
        count += 1
        if not output or output[-1].strip() != check:
            output.append(check + "\n")
        output.append(enforce_locked(line))
        if index + 1 == len(lines) or lines[index + 1].strip() != check:
            output.append(check + "\n")
    if not count:
        raise ValueError("No Cargo build/test command found for the audited lockfile")
    return "".join(output)
