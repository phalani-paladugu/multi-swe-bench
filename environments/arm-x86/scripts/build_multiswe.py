#!/usr/bin/env python3
"""Build native task images and capture independent baseline/gold execution logs."""

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


def dump(path, value):
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, indent=2) + "\n")
    temp.replace(path)


def run(argv, log, timeout):
    with log.open("w") as output:
        try:
            return subprocess.run(
                argv, stdout=output, stderr=subprocess.STDOUT, timeout=timeout
            ).returncode
        except subprocess.TimeoutExpired:
            output.write(f"\nTIMEOUT after {timeout} seconds\n")
            return 124


def build(task, arch, out, timeout, network="none"):
    task = task.resolve()
    env = json.loads((task / "environment.json").read_text())
    directory = out / task.name
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "inputs").mkdir(exist_ok=True)
    shutil.copy2(task / arch / "Dockerfile", directory / "inputs/Dockerfile")
    shutil.copytree(task / "common", directory / "inputs/common", dirs_exist_ok=True)
    cpu = {"arm": "arm64", "x86": "amd64"}[arch]
    image = f"msweb.eval.{cpu}.{task.name.lower()}:carp-v1"
    result = {
        "instance_id": task.name,
        "architecture": cpu,
        "image": image,
        "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "host": platform.node(),
        "source_commit": env["base_commit"],
        "dockerfile_sha256": hashlib.sha256(
            (task / arch / "Dockerfile").read_bytes()
        ).hexdigest(),
        "status": "building",
        "test_scope": env["validation_scope"],
        "evaluation_network": network,
        "external_network_access": False,
    }
    result["input_sha256"] = {
        str(p.relative_to(task)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted((task / "common").glob("*"))
        if p.is_file()
    }
    result["evaluation_patch_sha256"] = {
        name: hashlib.sha256((task / "upstream/task" / name).read_bytes()).hexdigest()
        for name in ("test.patch", "fix.patch")
    }
    dump(directory / "result.json", result)
    code = run(
        [
            "docker",
            "buildx",
            "build",
            "--platform",
            f"linux/{cpu}",
            "--load",
            "--progress",
            "plain",
            "-t",
            image,
            "-f",
            str(task / arch / "Dockerfile"),
            str(task),
        ],
        directory / "build.log",
        timeout,
    )
    result["build_exit"] = code
    if code:
        result["status"] = "build_failed"
        dump(directory / "result.json", result)
        print(task.name, "BUILD FAILED", flush=True)
        return
    inspect = json.loads(
        subprocess.check_output(["docker", "image", "inspect", image], text=True)
    )[0]
    result["image_id"] = inspect["Id"]
    result["image_architecture"] = inspect["Architecture"]
    result["image_size"] = inspect["Size"]
    if inspect["Architecture"] != cpu:
        result["status"] = "wrong_architecture"
        dump(directory / "result.json", result)
        return
    smoke = run(
        [
            "docker",
            "run",
            "--rm",
            "--network=none",
            "--platform",
            f"linux/{cpu}",
            image,
            "bash",
            "-c",
            f'set -e; uname -m; git rev-parse HEAD; test "$(git rev-parse HEAD)" = {env["base_commit"]}; git diff --exit-code; (java -version || rustc --version || go version) 2>&1; test ! -e /home/fix.patch; test ! -e /opt/task/fix.patch',
        ],
        directory / "smoke.log",
        120,
    )
    run(
        [
            "docker",
            "run",
            "--rm",
            "--network=none",
            image,
            "bash",
            "-c",
            'dpkg-query -W; printf "\\nTOOLCHAINS\\n"; java -version; mvn -version; rustc -Vv; cargo -V; go version',
        ],
        directory / "environment.log",
        120,
    )
    result["smoke_exit"] = smoke
    if smoke:
        result["status"] = "smoke_failed"
        dump(directory / "result.json", result)
        return
    result["status"] = "built"
    dump(directory / "result.json", result)
    print(task.name, "BUILT", image, flush=True)
    for stage, patches in [
        ("baseline", "test.patch"),
        ("gold", "test.patch fix.patch"),
    ]:
        result["status"] = "testing_" + stage
        dump(directory / "result.json", result)
        container = (
            f"carp-{arch}-{task.name.lower().replace('_', '-')}-{stage}-{os.getpid()}"
        )
        shell = (
            "set -e; git apply --whitespace=nowarn "
            + " ".join("/patches/" + p for p in patches.split())
            + '; set +e; bash /opt/task/run.sh; rc=$?; printf "\\nEVALUATION_EXIT=%s\\n" "$rc"; exit "$rc"'
        )
        code = run(
            [
                "docker",
                "run",
                "--rm",
                "--name",
                container,
                "--network=" + network,
                "--cpus=8",
                "--memory=24g",
                "--platform",
                f"linux/{cpu}",
                "-v",
                str(task / "upstream/task") + ":/patches:ro",
                image,
                "bash",
                "-c",
                shell,
            ],
            directory / (stage + ".log"),
            timeout,
        )
        if code == 124:
            subprocess.run(
                ["docker", "rm", "-f", container],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        result[stage + "_exit"] = code
        dump(directory / "result.json", result)
    result["status"] = "built_tests_recorded"
    result["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    dump(directory / "result.json", result)
    print(task.name, "TESTS", result["baseline_exit"], result["gold_exit"], flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arch", choices=["arm", "x86"], default="arm")
    parser.add_argument("--jobs", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--internal-network",
        action="store_true",
        help="Use an isolated Docker bridge for tests requiring a non-loopback interface",
    )
    parser.add_argument("tasks", nargs="*")
    args = parser.parse_args()
    tasks = (
        [ROOT / "multi-swe-tasks" / n for n in args.tasks]
        if args.tasks
        else sorted((ROOT / "multi-swe-tasks").iterdir())
    )
    args.output.mkdir(parents=True, exist_ok=True)
    network = f"carp-eval-{os.getpid()}" if args.internal_network else "none"
    if args.internal_network:
        subprocess.run(
            ["docker", "network", "create", "--internal", network], check=True
        )
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            futures = [
                pool.submit(
                    build, t, args.arch, args.output.resolve(), args.timeout, network
                )
                for t in tasks
                if (t / "environment.json").exists()
            ]
            for future in concurrent.futures.as_completed(futures):
                future.result()
    finally:
        if args.internal_network:
            subprocess.run(["docker", "network", "rm", network], check=True)


if __name__ == "__main__":
    main()
