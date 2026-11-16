#!/usr/bin/env python3
"""Snapshot selected recipes from the pinned Multi-SWE-bench checkout."""

import argparse
import dataclasses
import hashlib
import importlib.util
import json
import subprocess
import sys
import types
from pathlib import Path

REVISION = "24f493f8a103e72312ded4f6b9c89f081d69cb09"
MODULES = {
    "alibaba__fastjson2-2775": "java/alibaba/fastjson2.py",
    "apache__dubbo-11781": "java/apache/dubbo.py",
    "fasterxml__jackson-dataformat-xml-644": "java/fasterxml/jackson_dataformat_xml.py",
    "sharkdp__bat-3108": "rust/sharkdp/bat.py",
    "nushell__nushell-10381": "rust/nushell/nushell.py",
    "BurntSushi__ripgrep-2626": "rust/BurntSushi/ripgrep.py",
    "zeromicro__go-zero-964": "golang/zeromicro/go_zero.py",
    "cli__cli-2316": "golang/cli/cli.py",
    "grpc__grpc-go-3119": "golang/grpc/grpc_go.py",
}


def load_harness(checkout):
    revision = subprocess.check_output(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True
    ).strip()
    if revision != REVISION:
        raise ValueError(f"Expected {REVISION}; got {revision}")
    # Avoid the initializer importing all repositories, including case-colliding
    # Qiskit/qiskit modules on macOS. Selected recipe code remains unchanged.
    for name in ("multi_swe_bench", "multi_swe_bench.harness"):
        module = types.ModuleType(name)
        module.__path__ = [str(checkout.joinpath(*name.split(".")))]
        sys.modules[name] = module
    from multi_swe_bench.harness.image import Config
    from multi_swe_bench.harness.instance import Instance
    from multi_swe_bench.harness.pull_request import PullRequest

    for index, rel in enumerate(MODULES.values()):
        path = checkout / "multi_swe_bench/harness/repos" / rel
        spec = importlib.util.spec_from_file_location(f"selected_recipe_{index}", path)
        spec.loader.exec_module(importlib.util.module_from_spec(spec))
    return Config, Instance, PullRequest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    args = parser.parse_args()
    Config, Instance, PullRequest = load_harness(args.checkout)
    root = Path(__file__).resolve().parents[1] / "multi-swe-tasks"
    for name, rel in MODULES.items():
        task = root / name
        source = json.loads((task / "source.json").read_text())
        keys = {f.name for f in dataclasses.fields(PullRequest)}
        pr = PullRequest.from_json(
            json.dumps({k: v for k, v in source.items() if k in keys})
        )
        instance = Instance.create(pr, Config(True, None, False))
        recipe = instance.dependency()
        upstream = task / "upstream"
        for stage, obj in (("base", recipe.dependency()), ("task", recipe)):
            directory = upstream / stage
            directory.mkdir(parents=True, exist_ok=True)
            (directory / "Dockerfile").write_text(obj.dockerfile())
            for file in obj.files():
                (directory / file.name).write_text(file.content)
        path = args.checkout / "multi_swe_bench/harness/repos" / rel
        (upstream / "recipe.py").write_bytes(path.read_bytes())
        provenance = json.loads((task / "provenance.json").read_text())
        provenance.update(
            harness_recipe=rel,
            harness_recipe_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        )
        (task / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
        print(name)


if __name__ == "__main__":
    main()
