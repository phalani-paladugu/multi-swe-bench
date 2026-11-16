# Reuse committed Cargo.lock files where byte-identical

Audited all 11 Rust environments against `Cargo.lock` at their exact pinned public source commits. Four saved dependency snapshots match the repository files byte-for-byte. Their ARM Dockerfiles now use those files directly, removing 4,198 lines of duplicated lockfile content. Dependency versions, source commits, benchmark patches, and test selectors are unchanged.

Both current architecture variants for these four tasks verify the same SHA-256 before compilation, use `cargo test --locked`, and verify the hash afterward. The original x86 recipes remain byte-preserved under `upstream/x86/Dockerfile`; `Dockerfile.amd` points there. Build the current x86 variant using `x86/Dockerfile`. The `Cargo.lock.arm64` files remain as historical audit snapshots and generator inputs; they are not copied into the simplified images.

| Task | Lock committed upstream | Decision |
|---|---|---|
| [burntsushi__ripgrep-2209](tasks/burntsushi__ripgrep-2209/evidence/cargo-lock-source.json) | Yes | Reuse committed lock; ARM 649 → 48 lines; lock both architectures |
| [burntsushi__ripgrep-2576](tasks/burntsushi__ripgrep-2576/evidence/cargo-lock-source.json) | Yes | Reuse committed lock; ARM 612 → 48 lines; lock both architectures |
| [sharkdp__bat-2393](tasks/sharkdp__bat-2393/evidence/cargo-lock-source.json) | Yes | Reuse committed lock; ARM 1472 → 48 lines; lock both architectures |
| [sharkdp__bat-2650](tasks/sharkdp__bat-2650/evidence/cargo-lock-source.json) | Yes | Reuse committed lock; ARM 1657 → 48 lines; lock both architectures |
| [tokio-rs__tokio-4867](tasks/tokio-rs__tokio-4867/evidence/cargo-lock-source.json) | No | No Cargo.lock at the pinned commit; retain required ARM/x86 snapshots |
| [tokio-rs__tokio-6603](tasks/tokio-rs__tokio-6603/evidence/cargo-lock-source.json) | No | No Cargo.lock at the pinned commit; retain required ARM/x86 snapshots |
| [tokio-rs__tokio-6724](tasks/tokio-rs__tokio-6724/evidence/cargo-lock-source.json) | No | No Cargo.lock at the pinned commit; retain required ARM/x86 snapshots |
| [tokio-rs__tokio-6838](tasks/tokio-rs__tokio-6838/evidence/cargo-lock-source.json) | No | No Cargo.lock at the pinned commit; retain required ARM/x86 snapshots |
| [BurntSushi__ripgrep-2626](multi-swe-tasks/BurntSushi__ripgrep-2626/evidence/cargo-lock-source.json) | Yes | Already uses the committed lock with --locked; Dockerfiles unchanged |
| [nushell__nushell-10381](multi-swe-tasks/nushell__nushell-10381/evidence/cargo-lock-source.json) | Yes | Already uses the committed lock with --locked; Dockerfiles unchanged |
| [sharkdp__bat-3108](multi-swe-tasks/sharkdp__bat-3108/evidence/cargo-lock-source.json) | Yes | Already uses the committed lock with --locked; Dockerfiles unchanged |

The four Tokio source commits do not track `Cargo.lock`. Removing their supplied snapshots would change dependency resolution, so those recipes are preserved. The three newer Multi-SWE-bench Rust tasks already follow the requested approach.

## Generator behavior

`dockerfile_gen/cargo_lock.py` reads the per-task source audit. Reuse requires a matching repository, base commit, valid content hash, and an exact match to the saved snapshot. Stale checkout evidence or altered snapshot contents are rejected. Without proof of equivalence, the ARM generator retains the explicit snapshot. The x86 generator applies the matching checksum and `--locked` policy only to the four audited tasks. Regeneration preserves the original x86 archives and the ARM aliases.

Existing `verified_at`, `verification_inputs`, and baseline/gold results keep their original historical values. `generator_input_updates` records why current generator fingerprints changed, including the C++ tasks that import shared generator modules. All 28 historical task fingerprints were checked; unaffected recipes regenerate byte-for-byte identically. Per-task `evidence/cargo-lock-reuse.json` records previous/current recipe hashes and line counts; `COMPATIBILITY.md` and architecture diffs describe the current recipes.

## Checks for this change

- All 37 unit/regression tests pass, including guarded reuse, snapshot fallback, stale-evidence rejection, and generation round trips.
- All 37 architecture manifests match their file hashes.
- All source records, benchmark patches, test selectors, and evaluation scripts are byte-preserved.
- All 66 canonical Dockerfiles outside the four changed ARM/x86 pairs are byte-preserved.
- Each changed ARM recipe is exactly the prior recipe with its identical lockfile heredoc replaced by a pre-compilation checksum check, apart from the generated outer heredoc delimiter.
- All 12 checksum-guard checks pass on the native aarch64 Linux host: the matching file is accepted; missing or changed files stop execution before the following step.

Evidence: [recipe equivalence](evidence/cargo-lock-reuse/recipe-equivalence.json), [Linux checksum guards](evidence/cargo-lock-reuse/checksum-guards.json), and [regression checks](tests/test_cargo_lock_reuse.py).

No fresh native ARM or x86 image build was performed for this simplification. Published image references and their historical baseline/gold validation continue to describe the original builds.

## Relationship to the upstream Multi-SWE-bench harness

The historical `tasks/` collection uses the bundled SWE-bench Multilingual generator. The newer `multi-swe-tasks/` collection retains the original output of Multi-SWE-bench's registered Python recipe classes under each task's `upstream/` directory and publishes its adapted ARM/x86 build contexts separately. This update changes the standalone environment collection; it does not change `multi_swe_bench/harness/repos/` or register these adaptations with the standard Multi-SWE-bench evaluation runner.
