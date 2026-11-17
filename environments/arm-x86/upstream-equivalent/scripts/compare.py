#!/usr/bin/env python3
"""Compare observed ARM images with pinned official x86 image evidence."""

import difflib
import hashlib
import importlib.util
import json
import posixpath
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser_spec = importlib.util.spec_from_file_location(
    "multiswe_results", ROOT.parent / "scripts/summarize_multiswe.py"
)
parser = importlib.util.module_from_spec(parser_spec)
parser_spec.loader.exec_module(parser)


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def base_image_provenance(item, arm_metadata):
    """Recompute base ancestry from saved registry configs and built-image layers."""
    records = {
        record["resolved_digest"]: record
        for path in (ROOT / "evidence/registry").glob("*.json")
        for record in [json.loads(path.read_text())]
    }
    base = records[item["base_image"].split("@", 1)[1]]
    upstream = records[item["upstream_image"].split("@", 1)[1]]
    amd64 = base["platforms"]["amd64"]["config"]["rootfs"]["diff_ids"]
    arm64 = base["platforms"]["arm64"]["config"]["rootfs"]["diff_ids"]
    upstream_layers = upstream["platforms"]["amd64"]["config"]["rootfs"]["diff_ids"]
    return {
        "base_index_digest": base["resolved_digest"],
        "amd64_base_diff_ids": amd64,
        "amd64_matches_actual_upstream_prefix": upstream_layers[: len(amd64)] == amd64,
        "arm64_manifest_digest": base["platforms"]["arm64"]["manifest_digest"],
        "arm64_manifest_matches_recipe": (
            base["platforms"]["arm64"]["manifest_digest"] == item["arm_base_manifest"]
        ),
        "arm64_base_diff_ids": arm64,
        "arm64_matches_built_image_prefix": arm_metadata["RootFS"]["Layers"][
            : len(arm64)
        ]
        == arm64,
        "explanation": (
            "Both architectures select the same immutable multiarchitecture index. "
            "The x86 base layers exactly match the original upstream task image's "
            "starting layers; the ARM image starts with that index's native ARM layers."
        ),
    }


def select_test_evidence(directory, result, candidates):
    """Reuse explicit-command tests only after proving a default-Cmd-only change."""
    evidence = {
        "image_id": result.get("image_id"),
        "logs": str(directory.relative_to(ROOT)),
        "reused_after_metadata_change": False,
    }
    metadata_path = directory / "image-inspect.json"
    if "gold_exit" in result or not metadata_path.exists():
        return directory, result, evidence
    current = json.loads(metadata_path.read_text())
    for _, previous_path, previous in sorted(candidates, reverse=True):
        previous_metadata_path = previous_path.parent / "image-inspect.json"
        if "gold_exit" not in previous or not previous_metadata_path.exists():
            continue
        if not previous.get("test_commands", "").startswith(
            "Unmodified /home/test-run.sh and /home/fix-run.sh"
        ):
            continue
        tested = json.loads(previous_metadata_path.read_text())
        changed = sorted(
            field
            for field in current["Config"].keys() | tested["Config"].keys()
            if current["Config"].get(field) != tested["Config"].get(field)
        )
        same_layers = bool(current.get("RootFS", {}).get("Layers")) and (
            current["RootFS"] == tested.get("RootFS")
        )
        if (
            same_layers
            and current["Architecture"] == tested["Architecture"]
            and current["Os"] == tested["Os"]
            and set(changed) <= {"Cmd"}
        ):
            evidence.update(
                image_id=tested["Id"],
                final_image_id=current["Id"],
                logs=str(previous_path.parent.relative_to(ROOT)),
                reused_after_metadata_change=True,
                rootfs_layers_identical=True,
                changed_config_fields=changed,
                reason=(
                    "Final image differs only in default command metadata. "
                    "Recorded tests used explicit bash /home/test-run.sh and "
                    "bash /home/fix-run.sh commands, which override that default. "
                    "Tests were not rerun on the final image ID."
                ),
            )
            return previous_path.parent, previous, evidence
    return directory, result, evidence


def compare(item):
    name = item["instance_id"]
    task = ROOT / "tasks" / name
    upstream = ROOT / "evidence/upstream" / name
    candidates = []
    for path in (ROOT / "evidence/builds").glob("*/" + name + "/result.json"):
        result = json.loads(path.read_text())
        candidates.append((result["started_at"], path, result))
    if not candidates:
        return {"instance_id": name, "status": "pending"}
    _, result_path, result = max(candidates)
    directory = result_path.parent
    result["logs"] = str(directory.relative_to(ROOT))
    result["matches_current_dockerfile"] = (
        result["dockerfile_sha256"]
        == hashlib.sha256((task / "arm/Dockerfile").read_bytes()).hexdigest()
    )
    comparison = {
        "instance_id": name,
        "upstream_image": item["upstream_image"],
        "base_amd64_is_exact_upstream_layer_prefix": item[
            "base_amd64_matches_upstream_layers"
        ],
        "runtime_equivalence_to_x86": "not established; native x86 tests were not run",
        "build": result,
    }
    arm_metadata_path = directory / "image-inspect.json"
    if arm_metadata_path.exists():
        arm_metadata = json.loads(arm_metadata_path.read_text())
        comparison["base_image_provenance"] = base_image_provenance(item, arm_metadata)
        x86_metadata = json.loads((upstream / "image-inspect.json").read_text())
        comparison["image_ids"] = {
            "arm": arm_metadata["Id"],
            "upstream_x86": x86_metadata["Id"],
        }
        comparison["runtime_configuration"] = {}
        for field in ["WorkingDir", "Entrypoint", "Cmd", "Env"]:
            arm_value = arm_metadata["Config"].get(field)
            x86_value = x86_metadata["Config"].get(field)
            match = (
                sorted(arm_value or []) == sorted(x86_value or [])
                if field == "Env"
                else arm_value == x86_value
            )
            detail = {"matches": match, "arm": arm_value, "upstream": x86_value}
            if field == "WorkingDir":
                detail["raw_matches"] = match
                detail["matches"] = posixpath.normpath(
                    arm_value or "/"
                ) == posixpath.normpath(x86_value or "/")
                detail["comparison"] = (
                    "Normalize trailing slash; both paths resolve to the same directory."
                )
            comparison["runtime_configuration"][field] = detail
        smoke = parser.read_log(directory / "smoke.log")
        commits = re.findall(r"^([0-9a-f]{40})$", smoke, re.MULTILINE)
        comparison["source_commit"] = {
            "expected": item["source_commit"],
            "observed": commits,
            "matches": commits == [item["source_commit"]],
        }
        observed_hashes = {
            path: digest
            for digest, path in re.findall(
                r"^([0-9a-f]{64})\s+(.+)$", smoke, re.MULTILINE
            )
        }
        comparisons = {}
        for image_path, record in json.loads(
            (upstream / "files.json").read_text()
        ).items():
            short_path = image_path.rsplit("/", 1)[-1]
            key = (
                image_path
                if image_path.startswith("/home/")
                and "/home/" + short_path == image_path
                else short_path
            )
            if key in observed_hashes and record.get("present"):
                comparisons[image_path] = {
                    "upstream_sha256": record["sha256"],
                    "arm_sha256": observed_hashes[key],
                    "matches": record["sha256"] == observed_hashes[key],
                }
        comparison["file_hashes"] = comparisons
        packages = {}
        package_path = directory / "packages.tsv"
        if package_path.exists():
            for line in package_path.read_text().splitlines():
                fields = line.split("\t")
                if len(fields) == 4 and fields[3] == "installed":
                    packages[fields[0]] = {
                        "Version": fields[1],
                        "Architecture": fields[2],
                    }
        original = json.loads((upstream / "packages.json").read_text())
        comparison["packages"] = {
            "upstream_count": len(original),
            "arm_count": len(packages),
            "only_upstream": {
                k: original[k] for k in sorted(original.keys() - packages.keys())
            },
            "only_arm": {
                k: packages[k] for k in sorted(packages.keys() - original.keys())
            },
            "version_differences": {
                k: {"upstream": original[k]["Version"], "arm": packages[k]["Version"]}
                for k in sorted(original.keys() & packages.keys())
                if original[k]["Version"] != packages[k]["Version"]
            },
        }
        comparison["documented_architecture_exclusions"] = item.get(
            "architecture_exclusions", {}
        )
    test_directory, test_result, test_evidence = select_test_evidence(
        directory, result, candidates
    )
    comparison["test_evidence"] = test_evidence
    source = json.loads(
        (ROOT.parent / "multi-swe-tasks" / name / "source.json").read_text()
    )
    observed = {
        stage: parser.parse(
            parser.read_log(test_directory / (stage + ".log")), item["language"]
        )
        for stage in ["baseline", "gold"]
    }
    required = set(source["fixed_tests"]) | set(source["p2p_tests"])
    tests = {
        "baseline_exit": test_result.get("baseline_exit"),
        "gold_exit": test_result.get("gold_exit"),
        "expected_gold_tests": len(required),
        "observed_gold_tests": len(observed["gold"]),
        "missing_gold_tests": sorted(required - observed["gold"].keys()),
        "nonpassing_gold_tests": {
            k: observed["gold"][k]
            for k in sorted(required & observed["gold"].keys())
            if observed["gold"][k] != "PASS"
        },
        "f2p": {
            name: {stage: observed[stage].get(name, "MISSING") for stage in observed}
            for name in source["f2p_tests"]
        },
    }
    tests["all_expected_gold_tests_passed"] = (
        bool(required)
        and not tests["missing_gold_tests"]
        and not tests["nonpassing_gold_tests"]
    )
    tests["all_f2p_reproduced"] = (
        all(x == {"baseline": "FAIL", "gold": "PASS"} for x in tests["f2p"].values())
        if tests["f2p"]
        else None
    )
    comparison["tests"] = tests
    focused_directory = ROOT / "evidence/focused" / name
    focused_path = focused_directory / "result.json"
    if focused_path.exists():
        focused = json.loads(focused_path.read_text())
        focused["logs"] = str(focused_directory.relative_to(ROOT))
        focused["matches_final_image_id"] = focused["image_id"] == result.get(
            "image_id"
        )
        focused_observed = {
            stage: parser.parse(
                parser.read_log(focused_directory / (stage + ".log")), item["language"]
            )
            for stage in ["baseline", "gold"]
        }
        focused["f2p"] = {
            test: {
                stage: focused_observed[stage].get(test, "MISSING")
                for stage in focused_observed
            }
            for test in source["f2p_tests"]
        }
        comparison["focused_validation"] = focused
    dump(task / "evidence/comparison.json", comparison)
    diff = "".join(
        difflib.unified_diff(
            (task / "x86/Dockerfile").read_text().splitlines(True),
            (task / "arm/Dockerfile").read_text().splitlines(True),
            fromfile="official-x86-reference/Dockerfile",
            tofile="arm/Dockerfile",
        )
    )
    (task / "evidence/x86-reference-to-arm.diff").write_text(diff)
    return comparison


def main():
    results = [compare(item) for item in json.loads((ROOT / "images.json").read_text())]
    dump(ROOT / "comparison-results.json", results)
    for result in results:
        packages = result.get("packages", {})
        tests = result.get("tests", {})
        print(
            result["instance_id"],
            result.get("build", {}).get("status", "pending"),
            "package-version-differences="
            + str(len(packages.get("version_differences", {}))),
            "gold=" + str(tests.get("gold_exit")),
            "f2p=" + str(tests.get("all_f2p_reproduced")),
        )


if __name__ == "__main__":
    main()
