# sharkdp__bat-2650: architecture evidence

x86/Dockerfile is the byte-preserved original upstream recipe. arm/Dockerfile is the byte-preserved previously verified ARM image recipe.

- Architecture: select linux/arm64 and an architecture-specific base-image digest. x86 retains the original upstream image tag.
- Reproducibility: generated syntax/header and ARM64_REBUILD_TOKEN support explicit rebuilds; they do not change repository source or tests.
- Dependency reproducibility: embed the recorded Cargo.lock, build/test with --locked and verify its SHA-256. The source commit and test selectors remain unchanged.
- Resource compatibility: CARGO_BUILD_JOBS=2 bounds compilation memory and persists for runtime Cargo commands as well as the build.
- Shell compatibility: omit the upstream conda activation line; these Rust images do not provide that conda environment.

Review the [full x86 → ARM diff](evidence/x86-to-arm.diff) and [hashes and validation provenance](evidence/architecture.json).

Historical ARM validation: 2026-11-05T03:29:35.085601+00:00. Native x86 execution has not been revalidated in this work.
