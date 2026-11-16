# Native ARM build evidence

Exit codes are reported literally. Baseline nonzero exits may be expected; they are not automatically proof of the intended failure. Gold exit 0 means the configured test command succeeded, while the last column separately checks every expected dataset selector. See per-task JSON for missing tests, exact image IDs, Dockerfile hashes, and log paths.

| Task | Build exit | Baseline exit | Gold exit | Gold tests observed | All dataset gold selectors passed |
|---|---|---|---|---|---|
| [BurntSushi__ripgrep-2626](multi-swe-tasks/BurntSushi__ripgrep-2626/evidence/build-results.json) | 0 | 101 | 0 | 404 | yes |
| [alibaba__fastjson2-2775](multi-swe-tasks/alibaba__fastjson2-2775/evidence/build-results.json) | 0 | 1 | 0 | 1928 | no |
| [apache__dubbo-11781](multi-swe-tasks/apache__dubbo-11781/evidence/build-results.json) | 0 | 1 | 0 | 189 | no |
| [cli__cli-2316](multi-swe-tasks/cli__cli-2316/evidence/build-results.json) | 0 | 2 | 0 | 832 | yes |
| [fasterxml__jackson-dataformat-xml-644](multi-swe-tasks/fasterxml__jackson-dataformat-xml-644/evidence/build-results.json) | 0 | 1 | 0 | 127 | yes |
| [grpc__grpc-go-3119](multi-swe-tasks/grpc__grpc-go-3119/evidence/build-results.json) | 0 | 137 | 137 | 342 | no |
| [nushell__nushell-10381](multi-swe-tasks/nushell__nushell-10381/evidence/build-results.json) | 0 | 101 | 0 | 1015 | yes |
| [sharkdp__bat-3108](multi-swe-tasks/sharkdp__bat-3108/evidence/build-results.json) | 0 | 101 | 0 | 271 | yes |
| [zeromicro__go-zero-964](multi-swe-tasks/zeromicro__go-zero-964/evidence/build-results.json) | 0 | 2 | 2 | 1729 | no |

Build attempts and failures are retained under `evidence/builds/`; published logs use lossless `.log.gz` compression, with uncompressed SHA-256 hashes in `evidence/log-archive.json`. The new x86 Dockerfiles have not been executed on a native x86 host.

gRPC: the full suite has a recorded 10-minute TLS timeout and vet error; duplicate stalled runs were stopped (exit 137). The [focused balancer/grpclb run](evidence/focused/grpc__grpc-go-3119/result.json) reproduces the failing baseline and passes with the fix using -vet=off.

Go-zero: the image/application builds, but benchmark tests require an ARM backend for gomonkey v2.0.2 and correction of the supplied UnaryCrashInterceptor test call. See its [compatibility report](multi-swe-tasks/zeromicro__go-zero-964/COMPATIBILITY.md).
