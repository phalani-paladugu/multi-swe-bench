# fasterxml__jackson-dataformat-xml-644: architecture evidence

arm/Dockerfile and x86/Dockerfile are matched CARP adaptations. The unmodified Multi-SWE-bench recipes and scripts are retained under upstream/; shared changes are not labeled as ARM requirements.

- Architecture: FROM explicitly selects linux/arm64 or linux/amd64. Package managers and multiarch base images supply the native binaries.
- Shared compatibility/preparation: Both variants pin the same multiarchitecture base-image index; apt package versions are recorded after building but are not frozen by this recipe.
- Shared compatibility/preparation: Both variants check out the exact CARP/dataset base commit and preserve source and evaluation patches.
- Shared compatibility/preparation: Both variants keep gold/test patches outside the image; validation mounts them into disposable containers.
- Shared compatibility/preparation: Both variants provide /testbed as a symlink to the upstream /home repository path.
- Shared compatibility/preparation: JDK 17 follows CARP on both architectures. Upstream fastjson2 and Jackson used JDK 8; Dubbo already used 17.
- Shared compatibility/preparation: The repository Maven wrapper is used on both architectures to preserve its declared Maven version.
- Shared compatibility/preparation: Preparation requires test compilation; a separate baseline warm-up records its exit status without treating expected test failures as build failures.
- Shared compatibility/preparation: Six dependency repositories are pinned to the CARP revisions and installed locally. This retains the original 2.17.0-SNAPSHOT pom instead of upstream rewriting it to 2.17.4-SNAPSHOT.
- Shared compatibility/preparation: Runtime compatibility: map an otherwise unresolved container hostname to loopback in /etc/hosts. Docker network=none omitted this entry on the build host, preventing Dubbo Surefire from starting its test JVM.

Review the [full x86 → ARM diff](evidence/x86-to-arm.diff) and [hashes and validation provenance](evidence/architecture.json).

See [environment settings](environment.json), [dataset and harness provenance](provenance.json), and `evidence/upstream-to-*` for the shared adaptations.

New ARM build: see [build/test results](evidence/build-results.json). Native x86 execution has not been revalidated in this work.
