import datetime
import json
import pathlib
import subprocess

root = pathlib.Path(__file__).resolve().parents[1]
task = root / "multi-swe-tasks/grpc__grpc-go-3119"
out = root / "evidence/focused/grpc__grpc-go-3119"
out.mkdir(parents=True, exist_ok=True)
image = "msweb.eval.arm64.grpc__grpc-go-3119:carp-v1"
result = {
    "image": image,
    "command": "go test -vet=off -v -count=1 ./balancer/grpclb",
    "scope": "Package modified by the task patch. This is additional focused validation, not full upstream-suite validation.",
    "network": "none",
    "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
}
for stage, patches in [("baseline", "test.patch"), ("gold", "test.patch fix.patch")]:
    command = (
        "set -e; git apply --whitespace=nowarn "
        + " ".join("/patches/" + p for p in patches.split())
        + "; "
        + result["command"]
    )
    with (out / (stage + ".log")).open("w") as f:
        result[stage + "_exit"] = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--network=none",
                "--cpus=8",
                "--memory=24g",
                "-v",
                str(task / "upstream/task") + ":/patches:ro",
                image,
                "bash",
                "-c",
                command,
            ],
            stdout=f,
            stderr=subprocess.STDOUT,
            timeout=600,
        ).returncode
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result))
