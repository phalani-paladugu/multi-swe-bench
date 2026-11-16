#!/usr/bin/env python3
"""Report observed results without treating missing tests or builds as passes."""

import gzip
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def read_log(path):
    if path.exists():
        return path.read_text(errors="replace")
    archived = path.with_name(path.name + ".gz")
    if archived.exists():
        with gzip.open(archived, "rt", errors="replace") as stream:
            return stream.read()
    return ""


def parse(text, language):
    result = {}

    def put(name, status):
        if result.get(name) != "FAIL":
            result[name] = status

    for line in ANSI.sub("", text).splitlines():
        if language == "java":
            match = re.search(
                r"Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+).*?\bin (\S+)",
                line,
            )
            if match:
                count, fail, error, skip = map(int, match.groups()[:4])
                name = match.group(5)
                put(
                    name,
                    "FAIL" if fail or error else "SKIP" if skip == count else "PASS",
                )
        elif language == "rust":
            match = re.match(r"test (.+?) \.\.\. (ok|FAILED|ignored)", line)
            if match:
                put(
                    match.group(1),
                    {"ok": "PASS", "FAILED": "FAIL", "ignored": "SKIP"}[match.group(2)],
                )
        elif language == "go":
            match = re.match(r"\s*--- (PASS|FAIL|SKIP): (\S+)", line)
            if match:
                put(match.group(2), match.group(1))
    return result


def summary(root=ROOT):
    rows = []
    all_results = {}
    for task in sorted((root / "multi-swe-tasks").iterdir()):
        if not (task / "environment.json").exists():
            continue
        expected = json.loads((task / "source.json").read_text())
        env = json.loads((task / "environment.json").read_text())
        candidates = []
        for file in (root / "evidence/builds").glob("*/" + task.name + "/result.json"):
            value = json.loads(file.read_text())
            candidates.append((value["started_at"], file, value))
        if not candidates:
            continue
        _, path, result = max(candidates)
        current_hash = hashlib.sha256(
            (task / "arm/Dockerfile").read_bytes()
        ).hexdigest()
        result["matches_current_dockerfile"] = (
            result["dockerfile_sha256"] == current_hash
        )
        snapshot = path.parent / "inputs/common"
        recorded_inputs = result.get("input_sha256") or {
            "common/" + p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in snapshot.glob("*")
            if p.is_file()
        }
        actual_inputs = {
            "common/" + p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (task / "common").glob("*")
            if p.is_file()
        }
        result["matches_current_preparation"] = recorded_inputs == actual_inputs
        result["input_sha256"] = recorded_inputs
        inspection_file = root / "evidence/inspections" / task.name / "result.json"
        if inspection_file.exists():
            inspection = json.loads(inspection_file.read_text())
            if inspection["image_id"] == result.get("image_id"):
                result["image_inspection"] = str(inspection_file.relative_to(root))
                result["matches_current_preparation"] = inspection[
                    "matches_current_preparation"
                ]
                result["input_sha256"] = inspection["input_sha256"]
        result["known_limitations"] = env.get("known_limitations", [])
        focused_dir = root / "evidence/focused" / task.name
        if (focused_dir / "result.json").exists():
            focused = json.loads((focused_dir / "result.json").read_text())
            focused_results = {
                stage: parse(
                    read_log(focused_dir / (stage + ".log")), env["language"]
                )
                for stage in ("baseline", "gold")
            }
            focused["f2p"] = {
                name: {
                    stage: focused_results[stage].get(name, "MISSING")
                    for stage in ("baseline", "gold")
                }
                for name in expected["f2p_tests"]
            }
            focused["logs"] = str(focused_dir.relative_to(root))
            result["focused_validation"] = focused
        result["logs"] = str(path.parent.relative_to(root))
        observed = {}
        for stage in ("baseline", "gold"):
            log = path.parent / (stage + ".log")
            observed[stage] = (
                parse(read_log(log), env["language"])
            )
            result[stage + "_observed_counts"] = {
                key: sum(v == key for v in observed[stage].values())
                for key in ("PASS", "FAIL", "SKIP")
            }
        result["f2p"] = {
            name: {
                stage: observed[stage].get(name, "MISSING")
                for stage in ("baseline", "gold")
            }
            for name in expected["f2p_tests"]
        }
        required = set(expected["fixed_tests"]) | set(expected["p2p_tests"])
        result["expected_gold_tests"] = len(required)
        result["missing_gold_tests"] = sorted(
            name for name in required if name not in observed["gold"]
        )
        result["nonpassing_gold_tests"] = {
            name: observed["gold"][name]
            for name in sorted(required & observed["gold"].keys())
            if observed["gold"][name] != "PASS"
        }
        result["all_expected_gold_tests_passed"] = (
            bool(required)
            and not result["missing_gold_tests"]
            and not result["nonpassing_gold_tests"]
        )
        result["all_f2p_reproduced"] = bool(result["f2p"]) and all(
            v == {"baseline": "FAIL", "gold": "PASS"} for v in result["f2p"].values()
        )
        # Separate successful patched execution from exact benchmark-selector coverage.
        result["gold_execution_succeeded"] = result.get("gold_exit") == 0 and bool(
            observed["gold"]
        )
        result["note"] = (
            "Java modules follow CARP scope. NONE-to-PASS entries may reflect compile failures, not a failing individual test. No native x86 execution is claimed."
        )
        destination = task / "evidence/build-results.json"
        destination.parent.mkdir(exist_ok=True)
        destination.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        all_results[task.name] = result
        rows.append(
            f"| [{task.name}](multi-swe-tasks/{task.name}/evidence/build-results.json) | {result.get('build_exit', 'pending')} | {result.get('baseline_exit', 'pending')} | {result.get('gold_exit', 'pending')} | {len(observed['gold'])} | {'yes' if result['all_expected_gold_tests_passed'] else 'no'} |"
        )
    (root / "multi-swe-build-results.json").write_text(
        json.dumps(all_results, indent=2, sort_keys=True) + "\n"
    )
    (root / "BUILD_RESULTS.md").write_text(
        "# Native ARM build evidence\n\nExit codes are reported literally. Baseline nonzero exits may be expected; they are not automatically proof of the intended failure. Gold exit 0 means the configured test command succeeded, while the last column separately checks every expected dataset selector. See per-task JSON for missing tests, exact image IDs, Dockerfile hashes, and log paths.\n\n| Task | Build exit | Baseline exit | Gold exit | Gold tests observed | All dataset gold selectors passed |\n|---|---|---|---|---|---|\n"
        + "\n".join(rows)
        + "\n\nBuild attempts and failures are retained under `evidence/builds/`; published logs use lossless `.log.gz` compression, with uncompressed SHA-256 hashes in `evidence/log-archive.json`. The new x86 Dockerfiles have not been executed on a native x86 host.\n\ngRPC: the full suite has a recorded 10-minute TLS timeout and vet error; duplicate stalled runs were stopped (exit 137). The [focused balancer/grpclb run](evidence/focused/grpc__grpc-go-3119/result.json) reproduces the failing baseline and passes with the fix using -vet=off.\n\nGo-zero: the image/application builds, but benchmark tests require an ARM backend for gomonkey v2.0.2 and correction of the supplied UnaryCrashInterceptor test call. See its [compatibility report](multi-swe-tasks/zeromicro__go-zero-964/COMPATIBILITY.md).\n"
    )
    return all_results


if __name__ == "__main__":
    summary()
