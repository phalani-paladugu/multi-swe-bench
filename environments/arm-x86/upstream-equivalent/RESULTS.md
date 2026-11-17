# Native ARM results against official upstream image references

Validated on `agentic_benchmark` (native Linux ARM64) on 2026-11-16 and 2026-11-17. All nine images built and passed source/toolchain smoke checks. **Six full gold scripts pass: all three Java and all three Rust tasks.** The three Go tasks retain the failures below.

These are environment-alignment results against files and metadata extracted from the actual official x86 images. Native x86 test runs have not been performed, so equal runtime behavior across architectures is not established. The new images are present on the build server under `:upstream-v1` tags; they have not been pushed to a container registry. Final local image IDs are recorded in [arm-images.json](arm-images.json). Existing `:carp-v1` images were preserved.

## Task results

“Gold” runs the original `/home/fix-run.sh`, which applies upstream’s supplied fix and tests. Baseline runs the original `/home/test-run.sh`. Counts below are unique expected dataset selectors observed as PASS, not a raw count of all test executions. Missing selectors can reflect omitted tests, build failures, or selector parsing/naming differences; exact missing names are retained in each comparison.

| Task / comparison | Baseline exit | Gold exit | Expected gold selectors observed PASS | Result |
|---|---:|---:|---:|---|
| [BurntSushi__ripgrep-2626](tasks/BurntSushi__ripgrep-2626/evidence/comparison.json) | 101 | 0 | 404/404 | Full gold script passes; expected fail-to-pass tests reproduced. |
| [alibaba__fastjson2-2775](tasks/alibaba__fastjson2-2775/evidence/comparison.json) | 1 | 0 | 2724/2724 | Full gold script passes. The dataset lists no fail-to-pass selectors for this task. |
| [apache__dubbo-11781](tasks/apache__dubbo-11781/evidence/comparison.json) | 1 | 0 | 675/675 | Full gold script passes; expected fail-to-pass tests reproduced. |
| [cli__cli-2316](tasks/cli__cli-2316/evidence/comparison.json) | 1 | 1 | 801/801 | All expected benchmark selectors pass, but the full gold script exits 1 on Go vet errors in the original source. |
| [fasterxml__jackson-dataformat-xml-644](tasks/fasterxml__jackson-dataformat-xml-644/evidence/comparison.json) | 1 | 0 | 127/127 | Full gold script passes. The dataset lists no fail-to-pass selectors for this task. |
| [grpc__grpc-go-3119](tasks/grpc__grpc-go-3119/evidence/comparison.json) | 1 | 1 | 249/250 | Full gold script exits 1 on Go vet and a 10-minute test timeout. The changed-package diagnostic passes with vet enabled and reproduces the expected fail-to-pass test. |
| [nushell__nushell-10381](tasks/nushell__nushell-10381/evidence/comparison.json) | 101 | 0 | 990/990 | Full gold script passes; expected fail-to-pass tests reproduced. |
| [sharkdp__bat-3108](tasks/sharkdp__bat-3108/evidence/comparison.json) | 101 | 0 | 265/265 | Full gold script passes; expected fail-to-pass tests reproduced. |
| [zeromicro__go-zero-964](tasks/zeromicro__go-zero-964/evidence/comparison.json) | 1 | 1 | 1198/1241 | Full gold script exits 1. gomonkey v2.0.2 lacks the required ARM implementation; the supplied test fixture also has an interceptor signature mismatch, and timing-sensitive tests fail. |

The three Java final image IDs differ from the tested IDs only in default-command metadata (`bash` → `/bin/bash`). Every filesystem layer is unchanged, and `Cmd` is the only changed configuration field. The test runner supplied explicit commands, overriding `Cmd`. Build and smoke checks ran on the final images; full suites were not rerun after that correction. Each comparison records the tested ID, final ID, and proof.

## What matches and what differs

- **Base provenance:** every selected x86 base has exactly the same starting layer fingerprints as its official task image. Each built ARM image starts with the ARM64 layers from that same immutable multiarchitecture index. This is recomputed from saved registry configs by `scripts/compare.py`.
- **Packages:** zero version differences among packages present on both architectures for all nine pairs. Rust has 413 packages per image and Go has 205. Their x86 variants contain `binutils-x86-64-linux-gnu` and `libquadmath0`; ARM variants contain `binutils-aarch64-linux-gnu` and `libhwasan0`. These are inherited from the matched official bases.
- **Java packages:** Fastjson2 has 191 packages on both architectures with matching names and versions. Dubbo has 349 x86 / 348 ARM packages; Jackson has 358 x86 / 357 ARM. The sole omitted package in each is the unavailable Intel driver `libdrm-intel1`. The initial failed attempts are retained as evidence of that incompatibility.
- **Source and inputs:** all nine source commits match. All inspected original scripts, fix/test patches, Cargo manifests/locks, Go manifests/checksums, and Java root POMs match byte-for-byte. This does not claim a hash comparison of every transitive dependency artifact or every file in the images.
- **Runtime metadata:** environment variables, entrypoint, and default command match. Working-directory strings differ only by the trailing slash (`/home/` versus `/home`). No CARP runtime tools or command overrides were added.
- **Expected architectural differences:** native executables, compiler targets, system libraries, and compiled project artifacts differ by architecture. Java uses historical snapshot APT sources to reproduce the original package versions. Build-only concurrency limits are documented in each compatibility report.

## Remaining Go failures

### CLI

All 801 expected selectors pass, but the full upstream script exits 1 because Go 1.24.1 vet rejects `%w` in `testing.Errorf` at `git/git_test.go:67` and a redundant newline passed to `fmt.Fprintln` at `internal/authflow/flow.go:75`. The source and upstream Go version are preserved; vet was not disabled. [Gold log](evidence/builds/attempt-1/cli__cli-2316/gold.log.gz).

### gRPC

The full gold script exits 1. Vet rejects an integer-to-string conversion at `internal/transport/http_util_test.go:195`, and a TLS-related test run reaches the suite’s 10-minute timeout. `TestGetSocketOptions` is the one expected selector not observed. The required `TestFallBackWithNoServerAddress` transition is FAIL → PASS in the full logs and the separate changed-package run. That additional run uses `go test -v -count=1 ./balancer/grpclb` with vet enabled and exits 0 after the fix. [Full gold log](evidence/builds/attempt-1/grpc__grpc-go-3119/gold.log.gz), [focused result](evidence/focused/grpc__grpc-go-3119/result.json).

### Go-zero

The pinned `github.com/agiledragon/gomonkey@v2.0.2+incompatible` cannot build on ARM because `buildJmpDirective` has no ARM implementation. The supplied gold test fixture also calls `UnaryCrashInterceptor` with a signature incompatible with this source checkout. Four expected selectors are observed failing (`TestAdaptiveShedderMaxFlight`, `TestAdaptiveShedderMinRt`, `TestAdaptiveShedderShouldDrop`, `TestRollingWindowReduce`); 39 are not observed by the selector parser. The logs also report a missing cgroup-v1 `cpuacct.usage_percpu` file. These findings do not establish that every failure is caused by architecture. [Gold log](evidence/builds/attempt-1/zeromicro__go-zero-964/gold.log.gz).

A working gomonkey path on ARM requires an ARM implementation or a dependency change; either must be documented and validated as an additional deviation from the original dependency. The fixture mismatch needs separate investigation. These changes were not silently applied to this upstream-aligned variant.

## Reproduce the evidence

Follow [the build instructions](README.md#build-and-validate) on a native ARM host. The full runs use 8 CPUs, 24 GiB RAM, a 30-minute outer timeout, and Docker bridge networking. Network access and timing can affect outcomes. Native x86 runs of the pinned official images are still required to measure actual cross-architecture test parity.

After collecting build outputs into `evidence/builds/`, run:

```sh
python3 scripts/compare.py
```

Published logs are gzip-compressed without changing their contents. [log-checksums.json](evidence/log-checksums.json) records compressed and uncompressed hashes and sizes. `compare.py` reads either plain or compressed logs. Per-task [compatibility reports](README.md#recipes) explain the recipe changes; `x86-reference-to-arm.diff` compares the official-image reference Dockerfile with the ARM construction recipe. This textual diff is not an original upstream Dockerfile diff; the measured image comparison supplies the actual package, file, and runtime evidence.
