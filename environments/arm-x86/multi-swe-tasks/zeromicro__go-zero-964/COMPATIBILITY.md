# zeromicro__go-zero-964: architecture evidence

arm/Dockerfile and x86/Dockerfile are matched CARP adaptations. The unmodified Multi-SWE-bench recipes and scripts are retained under upstream/; shared changes are not labeled as ARM requirements.

- Architecture: FROM explicitly selects linux/arm64 or linux/amd64. Package managers and multiarch base images supply the native binaries.
- Shared compatibility/preparation: Both variants pin the same multiarchitecture base-image index; apt package versions are recorded after building but are not frozen by this recipe.
- Shared compatibility/preparation: Both variants check out the exact CARP/dataset base commit and preserve source and evaluation patches.
- Shared compatibility/preparation: Both variants keep gold/test patches outside the image; validation mounts them into disposable containers.
- Shared compatibility/preparation: Both variants provide /testbed as a symlink to the upstream /home repository path.
- Shared compatibility/preparation: Ubuntu 22.04 golang-go follows CARP Go 1.18 instead of the moving upstream golang:latest image, on both architectures.
- Shared compatibility/preparation: Module downloads and go build must succeed; evaluation runs independently and records failures.
- Shared compatibility/preparation: Runtime compatibility: map an otherwise unresolved container hostname to loopback in /etc/hosts. Docker network=none omitted this entry on the build host, preventing Dubbo Surefire from starting its test JVM.
- Shared compatibility/preparation: Offline evaluation: prefetch dependencies from the patched manifest in a single BuildKit bind-mount step, then reset source to the base commit. The patch files and patched source do not persist in the image layer.

Review the [full x86 → ARM diff](evidence/x86-to-arm.diff) and [hashes and validation provenance](evidence/architecture.json).

See [environment settings](environment.json), [dataset and harness provenance](provenance.json), and `evidence/upstream-to-*` for the shared adaptations.

Known compatibility limitations and required follow-up:

- Image/application build succeeds, but the gold manifest adds gomonkey v2.0.2, which has no ARM64 buildJmpDirective. Gold tests fail to compile in that dependency. An ARM backend backport or a documented, pinned dependency migration is required. Both options remain unimplemented.
- The supplied gold/test combination also calls UnaryCrashInterceptor() with a signature incompatible with the pinned source. This requires correcting the benchmark fixture upstream, not an architecture-only Dockerfile edit.

New ARM build: see [build/test results](evidence/build-results.json). Native x86 execution has not been revalidated in this work.
