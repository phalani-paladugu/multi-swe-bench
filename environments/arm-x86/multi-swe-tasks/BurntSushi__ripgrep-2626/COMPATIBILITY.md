# BurntSushi__ripgrep-2626: architecture evidence

arm/Dockerfile and x86/Dockerfile are matched CARP adaptations. The unmodified Multi-SWE-bench recipes and scripts are retained under upstream/; shared changes are not labeled as ARM requirements.

- Architecture: FROM explicitly selects linux/arm64 or linux/amd64. Package managers and multiarch base images supply the native binaries.
- Shared compatibility/preparation: Both variants pin the same multiarchitecture base-image index; apt package versions are recorded after building but are not frozen by this recipe.
- Shared compatibility/preparation: Both variants check out the exact CARP/dataset base commit and preserve source and evaluation patches.
- Shared compatibility/preparation: Both variants keep gold/test patches outside the image; validation mounts them into disposable containers.
- Shared compatibility/preparation: Both variants provide /testbed as a symlink to the upstream /home repository path.
- Shared compatibility/preparation: Pin the CARP compiler (bat/ripgrep 1.77.2; nushell 1.70.0) instead of upstream rust:latest, on both architectures.
- Shared compatibility/preparation: Use the committed Cargo.lock with --locked; do not re-resolve the historical dependency graph.
- Shared compatibility/preparation: Four Cargo workers bound memory use during both preparation and runtime on both architectures.
- Shared compatibility/preparation: Official Rust bookworm images provide native toolchains; CARP uses Ubuntu with rustup, so OS parity with CARP is not claimed.
- Shared compatibility/preparation: Runtime compatibility: map an otherwise unresolved container hostname to loopback in /etc/hosts. Docker network=none omitted this entry on the build host, preventing Dubbo Surefire from starting its test JVM.
- Shared compatibility/preparation: Offline evaluation: prefetch dependencies from the patched manifest in a single BuildKit bind-mount step, then reset source to the base commit. The patch files and patched source do not persist in the image layer.

Review the [full x86 → ARM diff](evidence/x86-to-arm.diff) and [hashes and validation provenance](evidence/architecture.json).

See [environment settings](environment.json), [dataset and harness provenance](provenance.json), and `evidence/upstream-to-*` for the shared adaptations.

New ARM build: see [build/test results](evidence/build-results.json). Native x86 execution has not been revalidated in this work.
