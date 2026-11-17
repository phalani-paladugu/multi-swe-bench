#!/usr/bin/env python3
"""Diagnose the task's gRPC package without overriding upstream vet behavior."""

import datetime
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence/focused/grpc__grpc-go-3119"
IMAGE = "msweb.eval.arm64.grpc__grpc-go-3119:upstream-v1"
OUT.mkdir(parents=True, exist_ok=True)
metadata = json.loads(
    subprocess.check_output(["docker", "image", "inspect", IMAGE], text=True)
)[0]
result = {
    "image": IMAGE,
    "image_id": metadata["Id"],
    "command": "go test -v -count=1 ./balancer/grpclb",
    "scope": "Additional diagnostic of the changed package; the full upstream scripts run separately. Vet remains enabled.",
    "started_at": datetime.datetime.now(datetime.UTC).isoformat(),
}
for stage, patches in [
    ("baseline", ["test.patch"]),
    ("gold", ["test.patch", "fix.patch"]),
]:
    name = "upstream-grpc-focused-" + stage
    command = (
        "set -e; cd /home/grpc-go; git apply "
        + " ".join("/home/" + p for p in patches)
        + "; "
        + result["command"]
    )
    with (OUT / (stage + ".log")).open("w") as log:
        try:
            result[stage + "_exit"] = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "--name",
                    name,
                    "--network=bridge",
                    "--cpus=8",
                    "--memory=24g",
                    metadata["Id"],
                    "bash",
                    "-c",
                    command,
                ],
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=600,
                check=False,
            ).returncode
        except subprocess.TimeoutExpired:
            result[stage + "_exit"] = 124
            subprocess.run(
                ["docker", "rm", "-f", name], check=False, capture_output=True
            )
    (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
result["finished_at"] = datetime.datetime.now(datetime.UTC).isoformat()
(OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result))
