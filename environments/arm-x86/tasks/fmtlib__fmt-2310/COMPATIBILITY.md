# fmtlib__fmt-2310: architecture evidence

x86/Dockerfile is the byte-preserved original upstream recipe. arm/Dockerfile is the byte-preserved previously verified ARM image recipe.

- Architecture: select linux/arm64 and an architecture-specific base-image digest. x86 retains the original upstream image tag.
- Reproducibility: generated syntax/header and ARM64_REBUILD_TOKEN support explicit rebuilds; they do not change repository source or tests.
- Reproducibility: expand the apt install to the recorded system package versions, including native :arm64 packages and aarch64 binutils; allow downgrades to restore the snapshot.
- Verification: verify the complete dpkg package inventory with SHA-256. This freezes more than the minimum architecture translation.
- The minimal arm/recipe/Dockerfile changes only FROM. The build/test recipe, original parallelism, source checkout and shell initialization are otherwise preserved.

Review the [full x86 → ARM diff](evidence/x86-to-arm.diff) and [hashes and validation provenance](evidence/architecture.json).

The [minimal recipe diff](evidence/x86-to-arm-recipe.diff) separates the architecture change from package freezing.

Historical ARM validation: 2026-11-05T22:22:40.279994+00:00. Native x86 execution has not been revalidated in this work.
