# google__gson-2134: architecture evidence

x86/Dockerfile is the byte-preserved original upstream recipe. arm/Dockerfile is the byte-preserved previously verified ARM image recipe.

- Architecture: select linux/arm64 and an architecture-specific base-image digest. x86 retains the original upstream image tag.
- Reproducibility: generated syntax/header and ARM64_REBUILD_TOKEN support explicit rebuilds; they do not change repository source or tests.
- Architecture compatibility: replace the x86 native mvnd executable with the bundled JVM client (MVND_CLIENT=jvm and mvnd.sh). Keep mvnd 1.0.2 and its Maven release.
- Download reliability/reproducibility: use the fixed mvnd GitHub release URL, retry downloads and verify the archive SHA-256.
- Offline preparation: run mvnd --version and an existing test to fetch the Surefire provider, then verify Maven dependency artifact checksums.
- Shell compatibility: omit the upstream conda activation line; these Maven images do not provide that conda environment.

Review the [full x86 → ARM diff](evidence/x86-to-arm.diff) and [hashes and validation provenance](evidence/architecture.json).

Historical ARM validation: 2026-11-05T03:38:33.269565+00:00. Native x86 execution has not been revalidated in this work.
