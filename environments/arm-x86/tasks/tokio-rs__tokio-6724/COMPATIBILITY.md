# tokio-rs__tokio-6724: architecture evidence

x86/Dockerfile is the byte-preserved original upstream recipe. arm/Dockerfile is the byte-preserved previously verified ARM image recipe.

- Architecture: select linux/arm64 and an architecture-specific base-image digest. x86 retains the original upstream image tag.
- Reproducibility: generated syntax/header and ARM64_REBUILD_TOKEN support explicit rebuilds; they do not change repository source or tests.
- Dependency reproducibility: the pinned upstream commit has no Cargo.lock, so retain the recorded snapshot. ARM compilation uses --locked and verifies its SHA-256; x86 retains the original upstream snapshot recipe. The source commit and test selectors remain unchanged.
- Resource compatibility: CARGO_BUILD_JOBS=2 bounds compilation memory and persists for runtime Cargo commands as well as the build.
- Shell compatibility: omit the upstream conda activation line; these Rust images do not provide that conda environment.

Review the [full x86 → ARM diff](evidence/x86-to-arm.diff) and [hashes and validation provenance](evidence/architecture.json).

See the [source lockfile audit](evidence/cargo-lock-source.json) for the pinned repository, commit, content hash, and reuse decision.

Historical ARM validation: 2026-11-05T03:31:51.155960+00:00. Native x86 execution has not been revalidated in this work.
