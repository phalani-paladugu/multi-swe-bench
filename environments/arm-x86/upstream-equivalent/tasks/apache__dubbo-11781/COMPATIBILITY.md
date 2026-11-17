# apache__dubbo-11781: upstream-aligned ARM environment

Baseline: `mswebench/apache_m_dubbo@sha256:9a628fe0e60fd6d5a45aa4ce3239ac75ccc41b3f82c9a4fa28133e2c9170aeca`. ARM output: `msweb.eval.arm64.apache__dubbo-11781:upstream-v1`.

The selected base is `ubuntu:jammy-20250126@sha256:ed1544e454989078f5dec1bfdabd8c5cc9c48e0705d07b678ab6ae3fb61952d2`. Its x86 layers exactly match the first 1 layer of the official task image; the ARM recipe selects the ARM variant of that same index.

| Change | Reason |
|---|---|
| Native ARM base and binaries | Required CPU architecture change. |
| Copy original scripts and patches from the pinned x86 image | Ensures actual published upstream behavior is the reference. No x86 commands are executed. |
| Recreate the checkout from upstream Git objects and refs | Retains the historical source and version metadata without copying x86 project build products. |
| Retain upstream dependency downloads | Reuses the actual upstream dependency sources/artifacts, including versions no longer served by moving repositories. |
| Pin every requested installed package version and use Ubuntu snapshot 20250311T135000Z | Reproduces the actual upstream JDK, Maven, and OS dependencies instead of installing current versions. The image retains these snapshot APT sources. |
| Exclude `libdrm-intel1` | Intel graphics userspace driver; absent from the ARM64 package archive. The task does not use an Intel GPU. |

The ARM recipe does not add CARP-specific runtime tools, compiler versions, test filters, or test-command overrides. The original upstream preparation may tolerate test failures with `|| true`; build success alone is not validation.

See [ARM Dockerfile](arm/Dockerfile), [official x86 reference](x86/Dockerfile), [image references](upstream-reference.json), and [measured comparison](evidence/comparison.json). The comparison records package versions, script/dependency hashes, runtime settings, literal test exits, and expected benchmark-selector coverage. Native x86 runtime equivalence is not established by the ARM test run.

## Measured validation

Full gold script passes; expected fail-to-pass tests reproduced.

- Build, smoke, and package-query exits: `0`, `0`, `0`. [Build evidence](../../evidence/builds/attempt-3/apache__dubbo-11781/result.json).
- Original baseline/gold script exits: `1` / `0`. [Baseline log](../../evidence/builds/attempt-2/apache__dubbo-11781/baseline.log.gz), [gold log](../../evidence/builds/attempt-2/apache__dubbo-11781/gold.log.gz).
- Expected gold selectors observed PASS: **675/675**; 0 unobserved by the parser and 0 observed nonpassing.
- Installed package counts: x86 **349**, ARM **348**; **0 shared-package version differences**.
- Source commit, inspected scripts/patches and dependency manifests, runtime environment, entrypoint, and default command match upstream. `/home/` and `/home` resolve to the same working directory.
- Both the upstream x86 base ancestry and the built ARM base ancestry were verified against the recorded multiarchitecture index.

Package names present only upstream: `libdrm-intel1`. Package names present only on ARM: none. These are the architecture-specific differences recorded in the official base variants or documented Intel-driver exclusion.

Java metadata correction: the final image has the same filesystem layers as the tested image; only default `Cmd` changed from `bash` to upstream `/bin/bash`. Tests supplied explicit commands and override `Cmd`. Full suites were not rerun after this correction; both image IDs and the layer/configuration proof are retained in the comparison.

See [all results and remaining limitations](../../RESULTS.md).
