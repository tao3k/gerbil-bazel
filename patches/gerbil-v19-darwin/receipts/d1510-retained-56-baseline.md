# Retained 56-Second Baseline

The frozen fallback is the original D1510 executable with the D1878 receipt:
first compile **5.053081 s**, complete MCP build **56.255963 s**. Official clean
and build exit zero, clean leaves zero project native images, and sources are
unchanged. This is retained historical evidence, not a new timing measurement.
The original 51.737180/53.496910-second references and **55-second upgrade
ceiling** remain unchanged. The fallback itself does not pass that ceiling.

[The lock](d1510-retained-56-baseline.json) pins the original binary, carrier,
42 C inputs, GSC, runtime archive, gambuild-C, fallback receipt/configuration
and the runtime-home inventory reference. All paths are project-relative.
The D1543 inventory additionally checks actual contiguous native version
selection, native image hashes and generated Scheme hashes for 1,100 modules.
It freezes the verified current home; it is not a historical D1513 SDK manifest.

The verifier also checks the current external GNU GCC driver against the
fallback configuration's recorded file hash, not just its command name. The
driver SHA256 is
`406040ac6e22d01468e601a5aaa548e60af1c151efb056aa45d485d6804f0cd4`;
the recorded version is GNU GCC 16.2.0 and SDK name is MacOSX26.5.sdk. No
personal installation path is added to this manifest. Matching the driver and
SDK name is not historical byte identity of cc1, collect2, assembler/linker,
SDK contents or linked external libraries; those remain distinct boundaries.

Verify separately before any timed run, from the repository root:

```sh
python3 patches/gerbil-v19-darwin/tests/verify_d1510_baseline.py
python3 -m unittest discover -s patches/gerbil-v19-darwin/tests -p test_d1510_baseline.py
```

Verification fails on input replacement, a newly selected native version,
changed Scheme, broken gxi alias or fallback receipt drift. Passing verifies
identity only, never current performance or a complete test-suite pass.

The local original-line execution entry remains `.data/best-line.py`. It
selects the locked original binary/home, disables experimental overrides,
uses the Bazel GNU GCC environment and discovers physical worker count.
Its pre-execution verification is not consumer startup-time evidence.
The 56-second receipt's timing came from the direct original-binary build
driver, not from timing this validation entry.

Persist the retained `.data` inputs across restarts. This lock is not a binary
archive or a promise to recover deleted private artifacts from Git. Do not
overwrite D1878 with later 56/60/70-second runs. New experiments require new
output directories and cannot replace this fallback without separate admission.
See [the original construction closure](d1510-best-line-input-closure.md).

The subsequently built symbol-hash candidate is separate, has only an import
smoke, and is not selected or performance-qualified. It is not part of this lock.
