#!/usr/bin/env python3
"""Generate reviewable per-task architecture diffs, hashes and change rationale."""

import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def diff(a, b):
    return "".join(
        difflib.unified_diff(
            a.read_text().splitlines(True),
            b.read_text().splitlines(True),
            fromfile=str(a.relative_to(a.parent.parent)),
            tofile=str(b.relative_to(b.parent.parent)),
        )
    )


def main():
    rows = []
    for collection in ("tasks", "multi-swe-tasks"):
        for task in sorted((ROOT / collection).iterdir()):
            arm = task / "arm/Dockerfile"
            x86 = task / "x86/Dockerfile"
            if not arm.is_file() or not x86.is_file():
                continue
            evidence = task / "evidence"
            evidence.mkdir(exist_ok=True)
            (evidence / "x86-to-arm.diff").write_text(diff(x86, arm))
            existing = collection == "tasks"
            if existing:
                lock = json.loads((task / "arm64-lock.json").read_text())
                language = lock["language"]
                changes = [
                    "Architecture: select linux/arm64 and an architecture-specific base-image digest. x86 retains the original upstream image tag.",
                    "Reproducibility: generated syntax/header and ARM64_REBUILD_TOKEN support explicit rebuilds; they do not change repository source or tests.",
                ]
                if language == "cpp":
                    changes += [
                        "Reproducibility: expand the apt install to the recorded system package versions, including native :arm64 packages and aarch64 binutils; allow downgrades to restore the snapshot.",
                        "Verification: verify the complete dpkg package inventory with SHA-256. This freezes more than the minimum architecture translation.",
                        "The minimal arm/recipe/Dockerfile changes only FROM. The build/test recipe, original parallelism, source checkout and shell initialization are otherwise preserved.",
                    ]
                    (evidence / "x86-to-arm-recipe.diff").write_text(
                        diff(x86, task / "arm/recipe/Dockerfile")
                    )
                elif language == "java":
                    changes += [
                        "Architecture compatibility: replace the x86 native mvnd executable with the bundled JVM client (MVND_CLIENT=jvm and mvnd.sh). Keep mvnd 1.0.2 and its Maven release.",
                        "Download reliability/reproducibility: use the fixed mvnd GitHub release URL, retry downloads and verify the archive SHA-256.",
                        "Offline preparation: run mvnd --version and an existing test to fetch the Surefire provider, then verify Maven dependency artifact checksums.",
                        "Shell compatibility: omit the upstream conda activation line; these Maven images do not provide that conda environment.",
                    ]
                else:
                    changes += [
                        "Dependency reproducibility: embed the recorded Cargo.lock, build/test with --locked and verify its SHA-256. The source commit and test selectors remain unchanged.",
                        "Resource compatibility: CARGO_BUILD_JOBS=2 bounds compilation memory and persists for runtime Cargo commands as well as the build.",
                        "Shell compatibility: omit the upstream conda activation line; these Rust images do not provide that conda environment.",
                    ]
                status = "Historical ARM validation: " + str(
                    lock.get("verified_at", "unknown")
                )
                validation = {
                    "kind": "historical",
                    "verified_at": lock.get("verified_at"),
                    "validation": lock.get("validation"),
                    "layout_only": lock["layout_migration"],
                    "x86_runtime": "not revalidated",
                }
                source_commit = lock.get("base_commit")
                baseline = "x86/Dockerfile is the byte-preserved original upstream recipe. arm/Dockerfile is the byte-preserved previously verified ARM image recipe."
            else:
                env = json.loads((task / "environment.json").read_text())
                language = env["language"]
                source_commit = env["base_commit"]
                changes = ["Architecture: " + x for x in env["architecture_changes"]]
                changes += [
                    "Shared compatibility/preparation: " + x
                    for x in env["shared_changes"]
                ]
                status = "New ARM build: see [build/test results](evidence/build-results.json)"
                validation = {
                    "kind": "new",
                    "x86_runtime": "not revalidated",
                    "test_scope": env["validation_scope"],
                }
                baseline = "arm/Dockerfile and x86/Dockerfile are matched CARP adaptations. The unmodified Multi-SWE-bench recipes and scripts are retained under upstream/; shared changes are not labeled as ARM requirements."
                for script in ("prepare.sh", "run.sh"):
                    a = task / "upstream/task" / script
                    b = task / "common" / script
                    (evidence / ("upstream-to-common-" + script + ".diff")).write_text(
                        "".join(
                            difflib.unified_diff(
                                a.read_text().splitlines(True),
                                b.read_text().splitlines(True),
                                fromfile="upstream/task/" + script,
                                tofile="common/" + script,
                            )
                        )
                    )
                original = (
                    (task / "upstream/base/Dockerfile").read_text()
                    + "\n# Original task layer\n"
                    + (task / "upstream/task/Dockerfile").read_text()
                )
                (evidence / "upstream-to-x86.diff").write_text(
                    "".join(
                        difflib.unified_diff(
                            original.splitlines(True),
                            x86.read_text().splitlines(True),
                            fromfile="upstream/base+task/Dockerfile",
                            tofile="x86/Dockerfile",
                        )
                    )
                )
            files = {
                "arm/Dockerfile": digest(arm),
                "x86/Dockerfile": digest(x86),
                "evidence/x86-to-arm.diff": digest(evidence / "x86-to-arm.diff"),
            }
            preserved = (
                ["test.patch", "gold.patch", "task.yaml", "tests.json", "eval.sh"]
                if existing
                else [
                    "source.json",
                    "provenance.json",
                    "upstream/task/test.patch",
                    "upstream/task/fix.patch",
                    "common/prepare.sh",
                    "common/run.sh",
                    "common/entrypoint.sh",
                    "environment.json",
                ]
            )
            for name in preserved:
                files[name] = digest(task / name)
            manifest = {
                "instance_id": task.name,
                "language": language,
                "source_commit": source_commit,
                "comparison": baseline,
                "sha256": files,
                "changes_and_reasons": changes,
                "validation": validation,
                "known_limitations": []
                if existing
                else env.get("known_limitations", []),
            }
            (evidence / "architecture.json").write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n"
            )
            readme = f"# {task.name}: architecture evidence\n\n{baseline}\n\n"
            readme += "\n".join("- " + x for x in changes) + "\n\n"
            readme += "Review the [full x86 → ARM diff](evidence/x86-to-arm.diff) and [hashes and validation provenance](evidence/architecture.json).\n\n"
            if language == "cpp":
                readme += "The [minimal recipe diff](evidence/x86-to-arm-recipe.diff) separates the architecture change from package freezing.\n\n"
            if not existing:
                readme += "See [environment settings](environment.json), [dataset and harness provenance](provenance.json), and `evidence/upstream-to-*` for the shared adaptations.\n\n"
            if not existing and env.get("known_limitations"):
                readme += "Known compatibility limitations and required follow-up:\n\n"
                readme += (
                    "\n".join("- " + item for item in env["known_limitations"]) + "\n\n"
                )
            readme += (
                status
                + ". Native x86 execution has not been revalidated in this work.\n"
            )
            (task / "COMPATIBILITY.md").write_text(readme)
            rows.append(
                f"| [{task.name}]({collection}/{task.name}/COMPATIBILITY.md) | {language} | {'Historical ARM' if existing else 'New ARM'} |"
            )
    (ROOT / "ARCHITECTURE_INDEX.md").write_text(
        "# Architecture evidence for 37 tasks\n\nEach task has `arm/Dockerfile`, `x86/Dockerfile`, a full unified diff, SHA-256 hashes, and reasons for changes. Historical runtime evidence is preserved with its original date; a folder move is not a new image validation.\n\n| Task | Language | Evidence |\n|---|---|---|\n"
        + "\n".join(rows)
        + "\n"
    )
    print(f"{len(rows)} task evidence bundles generated")


if __name__ == "__main__":
    main()
