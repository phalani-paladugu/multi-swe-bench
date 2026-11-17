# BurntSushi__ripgrep-2626: upstream-aligned ARM environment

Baseline: `mswebench/burntsushi_m_ripgrep@sha256:83375231f11af4e8762767d0cd0fbb429e8c44fee92f8ddc4eff5c86700e064e`. ARM output: `msweb.eval.arm64.burntsushi__ripgrep-2626:upstream-v1`.

The selected base is `rust:1.85.0-bookworm@sha256:0ff31c9ffa641a62e48d543fb00b4960955ea375f40776f40f585b89e654cc5e`. Its x86 layers exactly match the first 5 layers of the official task image; the ARM recipe selects the ARM variant of that same index.

| Change | Reason |
|---|---|
| Native ARM base and binaries | Required CPU architecture change. |
| Copy original scripts and patches from the pinned x86 image | Ensures actual published upstream behavior is the reference. No x86 commands are executed. |
| Recreate the checkout from upstream Git objects and refs | Retains the historical source and version metadata without copying x86 project build products. |
| Retain upstream dependency downloads | Reuses the actual upstream dependency sources/artifacts, including versions no longer served by moving repositories. |
| Build-time `CARGO_BUILD_JOBS=4` | Bounds preparation resources; it is not a runtime image setting. Rust 1.85.0 and unmodified `cargo test` commands match upstream. |

The ARM recipe does not add CARP-specific runtime tools, compiler versions, test filters, or test-command overrides. The original upstream preparation may tolerate test failures with `|| true`; build success alone is not validation.

See [ARM Dockerfile](arm/Dockerfile), [official x86 reference](x86/Dockerfile), [image references](upstream-reference.json), and [measured comparison](evidence/comparison.json). The comparison records package versions, script/dependency hashes, runtime settings, literal test exits, and expected benchmark-selector coverage. Native x86 runtime equivalence is not established by the ARM test run.

## Measured validation

Full gold script passes; expected fail-to-pass tests reproduced.

- Build, smoke, and package-query exits: `0`, `0`, `0`. [Build evidence](../../evidence/builds/attempt-1/BurntSushi__ripgrep-2626/result.json).
- Original baseline/gold script exits: `101` / `0`. [Baseline log](../../evidence/builds/attempt-1/BurntSushi__ripgrep-2626/baseline.log.gz), [gold log](../../evidence/builds/attempt-1/BurntSushi__ripgrep-2626/gold.log.gz).
- Expected gold selectors observed PASS: **404/404**; 0 unobserved by the parser and 0 observed nonpassing.
- Installed package counts: x86 **413**, ARM **413**; **0 shared-package version differences**.
- Source commit, inspected scripts/patches and dependency manifests, runtime environment, entrypoint, and default command match upstream. `/home/` and `/home` resolve to the same working directory.
- Both the upstream x86 base ancestry and the built ARM base ancestry were verified against the recorded multiarchitecture index.

Package names present only upstream: `binutils-x86-64-linux-gnu`, `libquadmath0`. Package names present only on ARM: `binutils-aarch64-linux-gnu`, `libhwasan0`. These are the architecture-specific differences recorded in the official base variants or documented Intel-driver exclusion.

See [all results and remaining limitations](../../RESULTS.md).
