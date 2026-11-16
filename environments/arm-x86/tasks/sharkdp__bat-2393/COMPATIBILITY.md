# sharkdp__bat-2393: architecture evidence

Both current recipes reuse the same audited repository Cargo.lock. The original x86 recipe is preserved under upstream/x86/Dockerfile and through Dockerfile.amd. The historical ARM validation predates this equivalent lockfile simplification; no new native image build is claimed.

- Architecture: select linux/arm64 and an architecture-specific base-image digest. x86 retains the original upstream image tag.
- Reproducibility: generated syntax/header and ARM64_REBUILD_TOKEN support explicit rebuilds; they do not change repository source or tests.
- Shared dependency locking: both architectures use the byte-identical Cargo.lock already committed at the pinned source revision, verify its SHA-256 before compilation, compile with --locked, and verify it afterward. No lockfile is embedded or overwritten. The saved Cargo.lock.arm64 remains an audit artifact.
- Resource compatibility: CARGO_BUILD_JOBS=2 bounds compilation memory and persists for runtime Cargo commands as well as the build.
- Shell compatibility: omit the upstream conda activation line; these Rust images do not provide that conda environment.

Review the [full x86 → ARM diff](evidence/x86-to-arm.diff) and [hashes and validation provenance](evidence/architecture.json).

See the [source lockfile audit](evidence/cargo-lock-source.json) for the pinned repository, commit, content hash, and reuse decision.

See the [lockfile simplification evidence](evidence/cargo-lock-reuse.json) and [original-to-current x86 diff](evidence/upstream-to-x86.diff). Both current builds enforce --locked; benchmark source and test selectors are unchanged.

Historical ARM validation: 2026-11-05T03:26:42.402925+00:00. Native x86 execution has not been revalidated in this work.
