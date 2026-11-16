# Exact selected task coverage

Checked SWE-bench Multilingual fork `main` commit `6e08cbcd763c869abd7aae4bcb9e1b3991180777` and ByteDance Multi-SWE-bench dataset revision `56ff018c04a38e27ada1e9d0a6d5839a51f88f0d`.

The Multi-SWE-bench GitHub repository contains the harness and repository recipes. Exact task records are published in its linked Hugging Face dataset.

| Task | SWE-bench Multilingual main | Multi-SWE-bench dataset |
|---|---|---|
| alibaba__fastjson2-2775 | No | Yes |
| apache__dubbo-11781 | No | Yes |
| fasterxml__jackson-dataformat-xml-644 | No | Yes |
| sharkdp__bat-3108 | Yes | Yes |
| nushell__nushell-10381 | No | Yes |
| BurntSushi__ripgrep-2626 | No | Yes |
| zeromicro__go-zero-964 | No | Yes |
| cli__cli-2316 | No | Yes |
| grpc__grpc-go-3119 | No | Yes |
| fmtlib__fmt-1683 | Yes | No |
| fmtlib__fmt-2310 | Yes | Yes |
| fmtlib__fmt-2317 | Yes | Yes |
| fmtlib__fmt-2457 | Yes | No |
| fmtlib__fmt-3158 | Yes | Yes |
| fmtlib__fmt-3248 | Yes | Yes |
| fmtlib__fmt-3272 | Yes | Yes |
| fmtlib__fmt-3729 | Yes | Yes |
| fmtlib__fmt-3750 | Yes | Yes |
| fmtlib__fmt-3863 | Yes | Yes |
| fmtlib__fmt-3901 | Yes | No |
| nlohmann__json-4237 | Yes | No |

For bat-3108, the base commit, test patch (977 bytes), and fix patch (3001 bytes) are identical across the datasets. SWE-bench Multilingual selects 2 fail-to-pass and 27 pass-to-pass tests; the selected Multi-SWE record has 2 fail-to-pass and 234 pass-to-pass entries, plus additional none-to-pass entries. Presence of the same task ID does not imply identical evaluation scope.

Sources: [fork task tree](https://github.com/phalani-paladugu/swe-bench-multilingual-tasks/tree/6e08cbcd763c869abd7aae4bcb9e1b3991180777/tasks), [Multi-SWE harness](https://github.com/multi-swe-bench/multi-swe-bench/tree/24f493f8a103e72312ded4f6b9c89f081d69cb09), [pinned dataset files](https://huggingface.co/datasets/ByteDance-Seed/Multi-SWE-bench/tree/56ff018c04a38e27ada1e9d0a6d5839a51f88f0d).
