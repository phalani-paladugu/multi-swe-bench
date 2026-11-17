# alibaba__fastjson2-2775: upstream-aligned ARM environment

Baseline: `mswebench/alibaba_m_fastjson2@sha256:03561c4a35cab50a78c18ae6f8b29d30141e119c9e0df8444a3fbc82e23eda15`. ARM output: `msweb.eval.arm64.alibaba__fastjson2-2775:upstream-v1`.

The selected base is `ubuntu:focal-20241011@sha256:8e5c4f0285ecbb4ead070431d29b576a530d3166df73ec44affc1cd27555141b`. Its x86 layers exactly match the first 1 layer of the official task image; the ARM recipe selects the ARM variant of that same index.

| Change | Reason |
|---|---|
| Native ARM base and binaries | Required CPU architecture change. |
| Copy original scripts and patches from the pinned x86 image | Ensures actual published upstream behavior is the reference. No x86 commands are executed. |
| Recreate the checkout from upstream Git objects and refs | Retains the historical source and version metadata without copying x86 project build products. |
| Retain upstream dependency downloads | Reuses the actual upstream dependency sources/artifacts, including versions no longer served by moving repositories. |
| Pin every requested installed package version and use Ubuntu snapshot 20250331T074000Z | Reproduces the actual upstream JDK, Maven, and OS dependencies instead of installing current versions. The image retains these snapshot APT sources. |

The ARM recipe does not add CARP-specific runtime tools, compiler versions, test filters, or test-command overrides. The original upstream preparation may tolerate test failures with `|| true`; build success alone is not validation.

See [ARM Dockerfile](arm/Dockerfile), [official x86 reference](x86/Dockerfile), [image references](upstream-reference.json), and [measured comparison](evidence/comparison.json). The comparison records package versions, script/dependency hashes, runtime settings, literal test exits, and expected benchmark-selector coverage. Native x86 runtime equivalence is not established by the ARM test run.

## Measured validation

Full gold script passes. The dataset lists no fail-to-pass selectors for this task.

- Build, smoke, and package-query exits: `0`, `0`, `0`. [Build evidence](../../evidence/builds/attempt-3/alibaba__fastjson2-2775/result.json).
- Original baseline/gold script exits: `1` / `0`. [Baseline log](../../evidence/builds/attempt-1/alibaba__fastjson2-2775/baseline.log.gz), [gold log](../../evidence/builds/attempt-1/alibaba__fastjson2-2775/gold.log.gz).
- Expected gold selectors observed PASS: **2724/2724**; 0 unobserved by the parser and 0 observed nonpassing.
- Installed package counts: x86 **191**, ARM **191**; **0 shared-package version differences**.
- Source commit, inspected scripts/patches and dependency manifests, runtime environment, entrypoint, and default command match upstream. `/home/` and `/home` resolve to the same working directory.
- Both the upstream x86 base ancestry and the built ARM base ancestry were verified against the recorded multiarchitecture index.

Java metadata correction: the final image has the same filesystem layers as the tested image; only default `Cmd` changed from `bash` to upstream `/bin/bash`. Tests supplied explicit commands and override `Cmd`. Full suites were not rerun after this correction; both image IDs and the layer/configuration proof are retained in the comparison.

See [all results and remaining limitations](../../RESULTS.md).
