# Publication checks

The initial publication at commit `fc047b05888c6a5ae1675b5d4249d0fed54e917e` was checked on November 16, 2026. These results describe that initial snapshot; see [CARGO_LOCK_REUSE.md](CARGO_LOCK_REUSE.md) for the subsequent selective recipe update:

- All 37 architecture manifests match their recorded file hashes.
- All 74 ARM/x86 Dockerfiles are byte-for-byte identical to the prepared source collection.
- All 91 compressed build/test logs decompress to their recorded original length and SHA-256.
- Regenerating the nine task recipes and all 37 architecture reports preserves the original runtime inputs and manifests.
- Summarizing the compressed logs reproduces all nine original build/test result records exactly.
- All 30 existing generator, validation-parser, and architecture-layout tests pass in the standalone bundle. The two negative-test metadata fixtures live under `tests/fixtures/`.
- Published documentation links and compatibility symlinks resolve.

Run the Python checks from this bundle directory after installing its small generator package:

```bash
python3 -m pip install -e .
python3 -m unittest discover -s tests -v
python3 scripts/generate_multiswe.py
python3 scripts/architecture_evidence.py
python3 scripts/summarize_multiswe.py
```

These publication checks do not constitute new image builds or native x86 runtime validation. See [BUILD_RESULTS.md](BUILD_RESULTS.md) for the previously observed ARM outcomes and limitations.

## Subsequent Cargo.lock simplification

The selective update is documented in [CARGO_LOCK_REUSE.md](CARGO_LOCK_REUSE.md). All 37 current regression tests and 12 Linux checksum-guard cases pass. Exactly four ARM/x86 recipe pairs changed; the remaining 66 canonical Dockerfiles and all benchmark source/test inputs are unchanged. No new native image build is claimed.
