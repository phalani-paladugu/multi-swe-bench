# ARM and x86 task environments

This fork publishes 37 task environments with `arm/Dockerfile` and `x86/Dockerfile`, build instructions, architecture diffs, hashes, and validation evidence.

| Source collection | C++ | Java | Rust | Go | Total |
|---|---:|---:|---:|---:|---:|
| Historical SWE-bench Multilingual (`tasks/`) | 12 | 8 | 8 | 0 | 28 |
| Selected Multi-SWE-bench (`multi-swe-tasks/`) | 0 | 3 | 3 | 3 | 9 |
| Total | 12 | 11 | 11 | 3 | 37 |

The 28 historical tasks retain their SWE-bench Multilingual metadata and evaluation expectations. Their inclusion here does not assert that all 28 belong to the Multi-SWE-bench dataset. [Task-source coverage](TASK_SOURCES.md) documents the selected overlap.

- [All 37 task environments and compatibility reports](ARCHITECTURE_INDEX.md)
- [Build instructions for ARM and x86](BUILD_ARCHITECTURES.md)
- [Native ARM build and test results](BUILD_RESULTS.md)
- [Source and publication provenance](provenance/publication.json)

All nine new ARM images built successfully. Seven configured gold test commands passed; Java module scopes are narrower than the complete dataset selectors. gRPC passes the focused affected-package check, while its full suite has recorded vet/timeout issues. Go-zero has recorded ARM dependency and benchmark-fixture blockers. Native x86 execution has not been validated. The historical 28 environments retain their dated ARM validation records.

Run the bundled scripts from this directory. These task build contexts use their own build/evaluation runner; copying them here does not automatically register their images with the upstream harness. Upstream code remains available at the repository root.

```bash
cd environments/arm-x86
python3 scripts/build_multiswe.py --arch arm --jobs 3 --internal-network \
  --output evidence/builds/manual-01
```

This publication contains source recipes and evidence. It does not upload the nine newly built images to a container registry. Historical image-registry references are documented in [DOCKER_HUB.md](DOCKER_HUB.md).

Public source material is attributed in per-task provenance and the [source coverage record](TASK_SOURCES.md). The upstream Multi-SWE-bench license is retained in [provenance/Multi-SWE-bench-LICENSE](provenance/Multi-SWE-bench-LICENSE). Private CARP templates and unrelated local files are excluded; all runtime preparation inputs required by these recipes are included.
