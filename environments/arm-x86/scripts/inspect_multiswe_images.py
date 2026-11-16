#!/usr/bin/env python3
"""Verify the retained images against current preparation files without rebuilding."""

import concurrent.futures
import datetime
import hashlib
import json
import platform
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def inspect(task):
    image = "msweb.eval.arm64." + task.name.lower() + ":carp-v1"
    metadata = json.loads(
        subprocess.check_output(["docker", "image", "inspect", image], text=True)
    )[0]
    files = sorted(p for p in (task / "common").iterdir() if p.is_file())
    command = ["docker", "run", "--rm", "--network=none", image]
    output = subprocess.check_output(
        command + ["sha256sum"] + ["/opt/task/" + p.name for p in files], text=True
    )
    observed = {
        "common/" + line.split(None, 1)[1].strip().split("/")[-1]: line.split()[0]
        for line in output.splitlines()
    }
    expected = {
        "common/" + p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files
    }
    commit = subprocess.check_output(
        command + ["git", "rev-parse", "HEAD"], text=True
    ).strip()
    environment = json.loads((task / "environment.json").read_text())
    report = {
        "instance_id": task.name,
        "image": image,
        "image_id": metadata["Id"],
        "architecture": metadata["Architecture"],
        "host_architecture": platform.machine(),
        "source_commit": commit,
        "input_sha256": observed,
        "matches_current_preparation": observed == expected,
        "matches_source_commit": commit == environment["base_commit"],
        "verified_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    dest = ROOT / "evidence/inspections" / task.name
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    with (dest / "environment.log").open("w") as log:
        subprocess.run(
            command
            + [
                "bash",
                "-c",
                'dpkg-query -W; printf "\\nTOOLCHAINS\\n"; for tool in java mvn rustc cargo go; do if command -v "$tool" >/dev/null; then case "$tool" in java) java -version;; mvn) mvn -version;; rustc) rustc -Vv;; cargo) cargo -V;; go) go version;; esac; fi; done',
            ],
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )
    assert (
        report["matches_current_preparation"]
        and report["matches_source_commit"]
        and report["architecture"] == "arm64"
    ), report
    return report


if __name__ == "__main__":
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        reports = list(pool.map(inspect, sorted((ROOT / "multi-swe-tasks").iterdir())))
    (ROOT / "multi-swe-images.json").write_text(json.dumps(reports, indent=2) + "\n")
    print("Verified", len(reports), "retained ARM images and their preparation files")
