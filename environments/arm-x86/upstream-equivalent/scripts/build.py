#!/usr/bin/env python3
"""Build native ARM ports and record unmodified upstream test-script results."""

import argparse
import concurrent.futures
import datetime
import hashlib
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def save(path, data):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    tmp.replace(path)


def run(argv, log, timeout):
    with log.open("w") as out:
        try:
            return subprocess.run(
                argv, check=False, stdout=out, stderr=subprocess.STDOUT, timeout=timeout
            ).returncode
        except subprocess.TimeoutExpired:
            out.write("\nTIMEOUT\n")
            return 124


def build(item, out, tests):
    name = item["instance_id"]
    task = ROOT / "tasks" / name
    dest = out / name
    dest.mkdir(parents=True, exist_ok=True)
    image = item["image"]
    result = {
        "instance_id": name,
        "image": image,
        "upstream_image": item["upstream_image"],
        "started_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "status": "building",
        "architecture": "arm64",
        "native_host_architecture": platform.machine(),
        "dockerfile_sha256": hashlib.sha256(
            (task / "arm/Dockerfile").read_bytes()
        ).hexdigest(),
    }
    result["input_sha256"] = {}
    for relative in [
        "arm/Dockerfile",
        "packages.txt",
        "install-java.sh",
        "upstream-reference.json",
    ]:
        source = task / relative
        if source.is_file():
            target = dest / "inputs" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            result["input_sha256"][relative] = hashlib.sha256(
                source.read_bytes()
            ).hexdigest()
    save(dest / "result.json", result)
    code = run(
        [
            "docker",
            "buildx",
            "build",
            "--platform",
            "linux/arm64",
            "--load",
            "--progress",
            "plain",
            "-t",
            image,
            "-f",
            str(task / "arm/Dockerfile"),
            str(task),
        ],
        dest / "build.log",
        3600,
    )
    result["build_exit"] = code
    if code:
        result["status"] = "build_failed"
        save(dest / "result.json", result)
        print(name, "BUILD FAILED", code, flush=True)
        return
    metadata = json.loads(
        subprocess.check_output(["docker", "image", "inspect", image], text=True)
    )[0]
    save(
        dest / "image-inspect.json",
        {
            k: metadata.get(k)
            for k in [
                "Id",
                "RepoDigests",
                "Architecture",
                "Os",
                "Created",
                "Config",
                "RootFS",
            ]
        },
    )
    result["image_id"] = metadata["Id"]
    result["image_architecture"] = metadata["Architecture"]
    assert metadata["Architecture"] == "arm64"
    shell = (
        "set -e; uname -m; cd /home/"
        + item["repository_name"]
        + "; git rev-parse HEAD; git status --porcelain; sha256sum /home/*.sh /home/*.patch; "
    )
    shell += {
        "rust": "rustc -Vv; cargo -V; sha256sum Cargo.toml Cargo.lock; rustup component list --installed",
        "go": "go version; sha256sum go.mod go.sum",
        "java": "java -version; if command -v mvn >/dev/null; then mvn -version; fi; sha256sum pom.xml",
    }[item["language"]]
    result["smoke_exit"] = run(
        [
            "docker",
            "run",
            "--rm",
            "--network=none",
            "--cpus=4",
            "--memory=8g",
            image,
            "bash",
            "-c",
            shell,
        ],
        dest / "smoke.log",
        120,
    )
    result["packages_exit"] = run(
        [
            "docker",
            "run",
            "--rm",
            "--network=none",
            image,
            "dpkg-query",
            "-W",
            "-f=${Package}\t${Version}\t${Architecture}\t${db:Status-Status}\n",
        ],
        dest / "packages.tsv",
        120,
    )
    result["status"] = "built"
    save(dest / "result.json", result)
    print(name, "BUILT", metadata["Id"], flush=True)
    if tests:
        for stage, script in [("baseline", "test-run.sh"), ("gold", "fix-run.sh")]:
            cname = (
                "upstream-arm-"
                + name.lower().replace("_", "-")
                + "-"
                + stage
                + "-"
                + str(os.getpid())
            )
            result["status"] = "testing_" + stage
            save(dest / "result.json", result)
            code = run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "--name",
                    cname,
                    "--network=bridge",
                    "--cpus=8",
                    "--memory=24g",
                    "--pids-limit=2048",
                    image,
                    "bash",
                    "/home/" + script,
                ],
                dest / (stage + ".log"),
                1800,
            )
            if code == 124:
                subprocess.run(
                    ["docker", "rm", "-f", cname],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            result[stage + "_exit"] = code
            save(dest / "result.json", result)
        result["test_commands"] = (
            "Unmodified /home/test-run.sh and /home/fix-run.sh from the pinned official image."
        )
        result["test_network"] = (
            "default Docker bridge; external downloads permitted, as in upstream scripts"
        )
    result["status"] = "built_tests_recorded" if tests else "built_smoke_checked"
    result["finished_at"] = datetime.datetime.now(datetime.UTC).isoformat()
    save(dest / "result.json", result)
    print(
        name, "DONE", result.get("baseline_exit"), result.get("gold_exit"), flush=True
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=3)
    parser.add_argument("--tests", action="store_true")
    parser.add_argument("tasks", nargs="*")
    args = parser.parse_args()
    if platform.machine() not in ["aarch64", "arm64"]:
        raise SystemExit("Native ARM host required.")
    items = [
        x
        for x in json.loads((ROOT / "images.json").read_text())
        if not args.tasks or x["instance_id"] in args.tasks
    ]
    args.output.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [
            pool.submit(build, item, args.output.resolve(), args.tests)
            for item in items
        ]
        for f in concurrent.futures.as_completed(futures):
            f.result()


if __name__ == "__main__":
    main()
