# ARM and x86 task environments

Published fork: https://github.com/phalani-paladugu/multi-swe-bench/tree/arm-x86-task-environments

All commands below run from `environments/arm-x86/` in this fork:

```bash
git clone --branch arm-x86-task-environments https://github.com/phalani-paladugu/multi-swe-bench.git
cd multi-swe-bench/environments/arm-x86
```

This collection contains 28 historical ARM environments from the [SWE-bench Multilingual fork](https://github.com/phalani-paladugu/swe-bench-multilingual-tasks/tree/arm64-cpp-12) and nine Multi-SWE-bench environments prepared for CARP trajectories. These are separate benchmark sources, retained in separate directories. See [publication provenance](provenance/publication.json).

## Task sources

The 300-task SWE-bench Multilingual tree and ByteDance's Multi-SWE-bench are separate datasets. All nine selected CARP Java/Rust/Go tasks exist in Multi-SWE-bench. Only `sharkdp__bat-3108` also exists on the SWE-bench Multilingual fork's `main`; its base commit and both patches match, but the two datasets select different pass-to-pass tests. The new collection remains under `multi-swe-tasks/` to retain its own evaluation provenance.

All 11 requested fmt tasks and `nlohmann__json-4237` exist on the SWE-bench Multilingual fork's `main`. Multi-SWE-bench includes eight of those fmt tasks; it excludes fmt 1683, 2457, 3901 and json 4237 at the recorded dataset revision. See [the source coverage record](TASK_SOURCES.md).

## Layout

```text
tasks/<existing-task>/
  arm/Dockerfile             # previously verified ARM recipe, unchanged bytes
  x86/Dockerfile             # original upstream x86 recipe, unchanged bytes
  arm/recipe/Dockerfile      # C++ only: minimal FROM-only ARM translation
  COMPATIBILITY.md
  evidence/x86-to-arm.diff
  evidence/architecture.json

multi-swe-tasks/<carp-task>/
  arm/Dockerfile
  x86/Dockerfile
  common/                    # shared preparation and evaluation scripts
  upstream/base/Dockerfile   # unmodified Multi-SWE-bench recipe snapshot
  upstream/task/Dockerfile
  source.json                # exact selected dataset record
  provenance.json
  environment.json
  COMPATIBILITY.md
  evidence/
```

Existing root-level `Dockerfile`, `Dockerfile.amd`, and C++ `Dockerfile.arm64` are symlinks to the canonical files. This preserves existing harness commands. The generator follows these aliases safely; the upstream x86 generator writes `x86/Dockerfile` when that layout exists.

[Architecture index: all 37 environments](ARCHITECTURE_INDEX.md) links to full diffs, hashes, and explanations. The old lock files preserve their original `verified_at` and runtime evidence. `layout_migration` records unchanged file hashes and the old generator inputs; the folder move does not represent a new runtime validation.

## Build the nine new ARM images

Use a native Linux ARM64 Docker host with BuildKit enabled. Run from the bundle directory:

```bash
python3 scripts/build_multiswe.py --arch arm --jobs 3 --internal-network \
  --output evidence/builds/manual-01
```

The runner builds all nine images, checks native architecture and the repository, and runs separate baseline (test patch) and gold (test plus fix patches) containers. `--internal-network` creates a temporary Docker bridge with external access disabled; this supplies the non-loopback interface required by Dubbo NetUtils tests. Without that flag, tests use `--network=none`. Each phase records its actual exit status. A successful Docker build is not automatically a passing benchmark validation. A unique output directory should be used for each run.

Build one image directly (the context is the task directory, not `arm/`):

```bash
task=sharkdp__bat-3108
docker buildx build --platform linux/arm64 --load \
  -f "multi-swe-tasks/$task/arm/Dockerfile" \
  -t "msweb.eval.arm64.$task:carp-v1" "multi-swe-tasks/$task"
```

Rust and Go recipes use a BuildKit read-only bind mount to fetch dependencies introduced by the evaluation patches. The same RUN step restores the base checkout. Patch files and patched source are not copied into the final image; the upstream repository history is retained as in CARP. Base image indexes are pinned in [multi-swe-base-images.json](multi-swe-base-images.json). Apt repositories remain live; package versions are recorded in the environment log, so bit-for-bit future rebuilds are not promised.

The image entrypoint supplies a missing local hostname mapping when running with no network. The images run as root, as do their upstream recipes.

## Build x86

Use a native x86 Docker host for meaningful architecture validation:

```bash
python3 scripts/build_multiswe.py --arch x86 --jobs 3 --internal-network \
  --output evidence/builds/x86-manual-01
```

Both new architecture variants share the CARP toolchain settings and preparation scripts. Native x86 runtime validation has not been performed in this work. Building x86 through emulation on the ARM host would not establish native performance parity.

## Rebuild an existing C++ image

```bash
task=fmtlib__fmt-1683
docker buildx build --platform linux/arm64 --load \
  -f "tasks/$task/arm/Dockerfile" \
  -t "sweb.eval.arm64.$task:latest" "tasks/$task"
```

For a fresh package-lock resolution and baseline/gold validation, use the original pipeline:

```bash
python3 -m pip install -e .
dockerfile-gen-arm64-cpp --instance_ids fmtlib__fmt-1683 --refresh-lock --keep-images
```

`--refresh-lock` triggers the rebuild; merely reusing the saved lock does not. See [CPP_ARM64.md](CPP_ARM64.md), [ARM64.md](ARM64.md), and [DOCKER_HUB.md](DOCKER_HUB.md) for the historical validation and published image inventory.

## Regenerate evidence and run local checks

```bash
python3 -m pip install -e .
python3 scripts/generate_multiswe.py
python3 scripts/architecture_evidence.py
python3 -m unittest discover -s tests -v
```

Reimporting upstream recipe snapshots additionally needs the exact harness checkout `24f493f8a103e72312ded4f6b9c89f081d69cb09` and `dataclasses-json`:

```bash
python3 -m pip install dataclasses-json==0.6.7
python3 scripts/import_multiswe.py /path/to/multi-swe-bench
```

Dataset records are pinned to Hugging Face revision `56ff018c04a38e27ada1e9d0a6d5839a51f88f0d`; each task's provenance contains its URL and record hash. The toolchain settings and complete preparation scripts needed for builds are included in `environment.json` and `common/` for each task. Private CARP source templates are not distributed or required. These are CARP-compatible environments, not a claim that every upstream evaluation command or the CARP replay timing protocol is identical. Java evaluation scopes and other shared adaptations are explicit in each task's compatibility report.

## Read the recorded evidence

Build and test logs are losslessly compressed as `.log.gz`. `evidence/log-archive.json` records each original path, byte count, and SHA-256 of the uncompressed content. For example:

```bash
gzip -dc evidence/focused/grpc__grpc-go-3119/gold.log.gz
python3 scripts/summarize_multiswe.py
```

The result summarizer accepts both freshly generated `.log` files and published `.log.gz` files. The image references in `multi-swe-images.json` describe images retained on the original ARM build host; this source publication does not upload those nine images to a registry.
