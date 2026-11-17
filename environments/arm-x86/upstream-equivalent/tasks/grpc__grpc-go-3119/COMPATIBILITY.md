# grpc__grpc-go-3119: upstream-aligned ARM environment

Baseline: `mswebench/grpc_m_grpc-go@sha256:91c8094ba6192ac7bbf4b4b26afcd8c0a78389a5e530b54f5fa712c28f8fe804`. ARM output: `msweb.eval.arm64.grpc__grpc-go-3119:upstream-v1`.

The selected base is `golang:1.24.1-bookworm@sha256:fa1a01d362a7b9df68b021d59a124d28cae6d99ebd1a876e3557c4dd092f1b1d`. Its x86 layers exactly match the first 7 layers of the official task image; the ARM recipe selects the ARM variant of that same index.

| Change | Reason |
|---|---|
| Native ARM base and binaries | Required CPU architecture change. |
| Copy original scripts and patches from the pinned x86 image | Ensures actual published upstream behavior is the reference. No x86 commands are executed. |
| Recreate the checkout from upstream Git objects and refs | Retains the historical source and version metadata without copying x86 project build products. |
| Retain upstream dependency downloads | Reuses the actual upstream dependency sources/artifacts, including versions no longer served by moving repositories. |
| Build-time `GOMAXPROCS=4` | Bounds preparation resources; it is not a runtime image setting. Go 1.24.1 and the original test/vet behavior match upstream. |

The ARM recipe does not add CARP-specific runtime tools, compiler versions, test filters, or test-command overrides. The original upstream preparation may tolerate test failures with `|| true`; build success alone is not validation.

See [ARM Dockerfile](arm/Dockerfile), [official x86 reference](x86/Dockerfile), [image references](upstream-reference.json), and [measured comparison](evidence/comparison.json). The comparison records package versions, script/dependency hashes, runtime settings, literal test exits, and expected benchmark-selector coverage. Native x86 runtime equivalence is not established by the ARM test run.

## Measured validation

Full gold script exits 1 on Go vet and a 10-minute test timeout. The changed-package diagnostic passes with vet enabled and reproduces the expected fail-to-pass test.

- Build, smoke, and package-query exits: `0`, `0`, `0`. [Build evidence](../../evidence/builds/attempt-1/grpc__grpc-go-3119/result.json).
- Original baseline/gold script exits: `1` / `1`. [Baseline log](../../evidence/builds/attempt-1/grpc__grpc-go-3119/baseline.log.gz), [gold log](../../evidence/builds/attempt-1/grpc__grpc-go-3119/gold.log.gz).
- Expected gold selectors observed PASS: **249/250**; 1 unobserved by the parser and 0 observed nonpassing.
- Installed package counts: x86 **205**, ARM **205**; **0 shared-package version differences**.
- Source commit, inspected scripts/patches and dependency manifests, runtime environment, entrypoint, and default command match upstream. `/home/` and `/home` resolve to the same working directory.
- Both the upstream x86 base ancestry and the built ARM base ancestry were verified against the recorded multiarchitecture index.

Package names present only upstream: `binutils-x86-64-linux-gnu`, `libquadmath0`. Package names present only on ARM: `binutils-aarch64-linux-gnu`, `libhwasan0`. These are the architecture-specific differences recorded in the official base variants or documented Intel-driver exclusion.

[Additional focused gRPC evidence](../../evidence/focused/grpc__grpc-go-3119/result.json): `go test -v -count=1 ./balancer/grpclb`, with vet enabled, exits 1 before the fix and 0 after it. This diagnostic does not replace the full suite.

See [all results and remaining limitations](../../RESULTS.md).
