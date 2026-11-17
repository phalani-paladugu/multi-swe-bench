# ARM environments matching published Multi-SWE-bench images

These nine environments target the actual published upstream x86 images. They are separate from the CARP adaptations in `../multi-swe-tasks/` and use `:upstream-v1` tags. Existing `:carp-v1` images remain available.

The baseline is an immutable upstream image digest, not a reconstruction from today's moving base tags. For every task, the x86 layers of the selected historical multiarchitecture base exactly match the starting layers of its published upstream image. The ARM build selects the ARM variant of that same base release.

- Rust: `rust:1.85.0-bookworm`, matching all three published Rust images.
- Go: `golang:1.24.1-bookworm`, matching all three published Go images.
- Fastjson2: Ubuntu focal-20241011 and Zulu 8u442, with upstream package versions pinned.
- Dubbo: Ubuntu jammy-20250126, OpenJDK 17.0.14, Maven 3.6.3, with upstream package versions pinned.
- Jackson: Ubuntu jammy-20250126, OpenJDK 8u442, Maven 3.6.3, with upstream package versions pinned.

Ubuntu Java package installs use the signed [Ubuntu snapshot service](https://snapshot.ubuntu.com/) at the original installation dates. Zulu's original 8.0.442-1 packages remain available for ARM64. `libdrm-intel1` is excluded from Dubbo and Jackson because that Intel graphics driver is unavailable for ARM64; all other requested package versions remain pinned.

See [measured results and remaining failures](RESULTS.md) for the completed native ARM builds. The word “equivalent” describes the environment target; it does not certify identical runtime results.

## Recipes

| Task | Official x86 tag, pinned by digest in the recipe | ARM recipe | x86 baseline | Changes and evidence |
|---|---|---|---|---|
| BurntSushi__ripgrep-2626 | `mswebench/burntsushi_m_ripgrep:pr-2626` | [Dockerfile](tasks/BurntSushi__ripgrep-2626/arm/Dockerfile) | [Official reference](tasks/BurntSushi__ripgrep-2626/x86/Dockerfile) | [Changes](tasks/BurntSushi__ripgrep-2626/COMPATIBILITY.md) · [Comparison](tasks/BurntSushi__ripgrep-2626/evidence/comparison.json) |
| alibaba__fastjson2-2775 | `mswebench/alibaba_m_fastjson2:pr-2775` | [Dockerfile](tasks/alibaba__fastjson2-2775/arm/Dockerfile) | [Official reference](tasks/alibaba__fastjson2-2775/x86/Dockerfile) | [Changes](tasks/alibaba__fastjson2-2775/COMPATIBILITY.md) · [Comparison](tasks/alibaba__fastjson2-2775/evidence/comparison.json) |
| apache__dubbo-11781 | `mswebench/apache_m_dubbo:pr-11781` | [Dockerfile](tasks/apache__dubbo-11781/arm/Dockerfile) | [Official reference](tasks/apache__dubbo-11781/x86/Dockerfile) | [Changes](tasks/apache__dubbo-11781/COMPATIBILITY.md) · [Comparison](tasks/apache__dubbo-11781/evidence/comparison.json) |
| cli__cli-2316 | `mswebench/cli_m_cli:pr-2316` | [Dockerfile](tasks/cli__cli-2316/arm/Dockerfile) | [Official reference](tasks/cli__cli-2316/x86/Dockerfile) | [Changes](tasks/cli__cli-2316/COMPATIBILITY.md) · [Comparison](tasks/cli__cli-2316/evidence/comparison.json) |
| fasterxml__jackson-dataformat-xml-644 | `mswebench/fasterxml_m_jackson-dataformat-xml:pr-644` | [Dockerfile](tasks/fasterxml__jackson-dataformat-xml-644/arm/Dockerfile) | [Official reference](tasks/fasterxml__jackson-dataformat-xml-644/x86/Dockerfile) | [Changes](tasks/fasterxml__jackson-dataformat-xml-644/COMPATIBILITY.md) · [Comparison](tasks/fasterxml__jackson-dataformat-xml-644/evidence/comparison.json) |
| grpc__grpc-go-3119 | `mswebench/grpc_m_grpc-go:pr-3119` | [Dockerfile](tasks/grpc__grpc-go-3119/arm/Dockerfile) | [Official reference](tasks/grpc__grpc-go-3119/x86/Dockerfile) | [Changes](tasks/grpc__grpc-go-3119/COMPATIBILITY.md) · [Comparison](tasks/grpc__grpc-go-3119/evidence/comparison.json) |
| nushell__nushell-10381 | `mswebench/nushell_m_nushell:pr-10381` | [Dockerfile](tasks/nushell__nushell-10381/arm/Dockerfile) | [Official reference](tasks/nushell__nushell-10381/x86/Dockerfile) | [Changes](tasks/nushell__nushell-10381/COMPATIBILITY.md) · [Comparison](tasks/nushell__nushell-10381/evidence/comparison.json) |
| sharkdp__bat-3108 | `mswebench/sharkdp_m_bat:pr-3108` | [Dockerfile](tasks/sharkdp__bat-3108/arm/Dockerfile) | [Official reference](tasks/sharkdp__bat-3108/x86/Dockerfile) | [Changes](tasks/sharkdp__bat-3108/COMPATIBILITY.md) · [Comparison](tasks/sharkdp__bat-3108/evidence/comparison.json) |
| zeromicro__go-zero-964 | `mswebench/zeromicro_m_go-zero:pr-964` | [Dockerfile](tasks/zeromicro__go-zero-964/arm/Dockerfile) | [Official reference](tasks/zeromicro__go-zero-964/x86/Dockerfile) | [Changes](tasks/zeromicro__go-zero-964/COMPATIBILITY.md) · [Comparison](tasks/zeromicro__go-zero-964/evidence/comparison.json) |

The x86 Dockerfile simply references the immutable official image. It does not recreate or change upstream's x86 environment.

## What is preserved

The ARM Dockerfiles copy the original scripts and benchmark patches directly from the pinned upstream image. They retain its Git history and refs, then recreate the source checkout. They reuse portable Cargo registry/Git downloads, Go module sources, or Maven downloads—including historical SNAPSHOT dependencies—but do not copy the x86 base-image toolchains or project compilation caches. Maven downloads can include architecture-specific artifacts; the original build resolves any required ARM variants. BuildKit reads the x86 image as a source without executing any x86 commands.

The upstream preparation and test scripts are unmodified: full upstream test scope, compiler versions, lockfile behavior, patches, workdir, entrypoint, and runtime environment are retained. Jackson also retains upstream's POM rewrite to 2.17.4-SNAPSHOT. These images do not add CARP-specific toolchain pins, `--locked`, `-vet=off`, module narrowing, `/testbed`, `rg`, `rustfmt`, or a hostname wrapper.

Four Cargo build jobs or four Go scheduler threads bound preparation resource use only; these are not retained as image environment variables. Java APT sources point to fixed snapshots to reproduce package versions. ARM executables and architecture-specific system libraries necessarily differ from x86. BuildKit retains a trailing slash in the configured `/home/` working directory; upstream records `/home`. The comparison reports both strings and treats them as the same resolved directory.

## Build and validate

Run builds on the native ARM SUT, using Ansible to dispatch work from the controller. The existing `arm-image-builds` tmux session was used for this build series. No container image is pushed by these commands.

For one task, from this directory on the SUT:

```sh
docker buildx build --platform linux/arm64 --load \
  -f tasks/nushell__nushell-10381/arm/Dockerfile \
  -t msweb.eval.arm64.nushell__nushell-10381:upstream-v1 \
  tasks/nushell__nushell-10381
```

For all nine, including original baseline/gold test scripts:

```sh
python3 scripts/build.py --tests --jobs 3 --output evidence/builds/manual
```

The runner records each exit code and bounded test run separately. Runtime tests receive 8 CPUs, 24 GiB RAM, a 30-minute timeout, and the default Docker bridge. External downloads are permitted, as in the upstream scripts; network services and mutable Maven SNAPSHOT checks can therefore affect results. Built images are not automatically declared equivalent merely because upstream's preparation script exits successfully: those scripts often contain `|| true`.

## Evidence

- `images.json`: immutable upstream and base-image references, source commits, ARM tags, and documented package exclusions.
- `evidence/registry/`: actual registry manifests and image configs, including matching x86 base layers and available ARM variants.
- `evidence/upstream/<task>/`: files, package versions, and metadata extracted from the official x86 images. Original `.git/HEAD` contents are saved under `git-metadata/HEAD` so Git can track the evidence; `files.json` records that storage mapping. Raw upstream files retain their original whitespace.
- `evidence/builds/<attempt>/<task>/`: native ARM build logs, original baseline/gold execution logs, package inventories, metadata, and literal exit codes.
- `tasks/<task>/evidence/comparison.json`: installed-package, runtime-configuration, source/lockfile, script-hash, and expected-test comparisons.
- `arm-images.json`: final server-local image tags and IDs, with links to build and test evidence.
- `evidence/log-checksums.json`: hashes of compressed and original log contents; published logs use `.log.gz`.
- `comparison-results.json`: combined generated comparison, produced by `python3 scripts/compare.py` after fetching build evidence.

For the three Java images, a final metadata-only rebuild changes the default command from `bash` to the upstream `/bin/bash`. The comparison verifies that every filesystem layer is identical to the tested image and that `Cmd` is the only changed configuration field. It explicitly links the earlier test image ID and logs: those tests invoked `bash /home/test-run.sh` and `bash /home/fix-run.sh`, overriding the default command. Build and smoke checks were repeated on the final images; the full test suites were not rerun after this metadata correction.

Native x86 runtime tests have not been run in this work. Matching software versions and scripts is evidence of environment alignment, not proof that all test outcomes or performance are identical across CPUs. Failures and any remaining differences must be read from the per-task comparison before using a pair as an architecture-only experiment.
