# Publication checks

The publication copy was checked on November 16, 2026:

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
