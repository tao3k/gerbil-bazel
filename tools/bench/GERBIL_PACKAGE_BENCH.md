# Package qualification

`gerbil_package_bench.py` owns execution and cleanup in Git. It does not load
Python controllers from `.data`. Existing historical runners and receipts are
not rewritten or silently replaced by this new entrypoint.

## Profiles

Keep shareable package profiles in Git; keep local toolchain configuration and
large outputs in `.data`. All configuration paths are workspace-relative.
A package profile has this shape (replace the explicit test inventory with the
complete inventory of the selected package):

```json
{
  "schema": 1,
  "name": "example",
  "source": ".data/example-source",
  "clean": ["{gerbil}", "clean"],
  "build": ["{gerbil}", "build"],
  "artifactGlobs": [".gerbil/bin/example"],
  "tests": [["{gerbil}", "test", "-v", "5", "test/example-test.ss"]],
  "testGlobs": ["test/*-test.ss"],
  "fixturePatches": [],
  "environment": {}
}
```

Fixture patches are applied only to isolated copies. Package-specific variables
may use `{project}` and `{bin}`; they cannot override the selected toolchain.
The execution engine has no package-name branches. A complete explicit test
inventory must match discovery globs exactly; duplicate or missing files fail.
Builds must produce declared artifacts, whose hashes must survive the tests.
`tools/bench/profiles/mcp.json` supplies the retained 39-file inventory and its
separate selected-toolchain fixture adapter. Other packages use the same schema.

The local toolchain file selects `binary`, `home`, `driver`, `binarySha256`, and
`gccEnvironment` (the environment variable containing the GNU GCC executable).
`additionalInputs` lists workspace-relative provider objects, link carriers,
archives or other transitive construction inputs to hash and protect explicitly.
Runtime, home and driver must live under `.data`. The GCC executable is checked
for GNU identity and hashed; its external absolute path is not put in receipts.

```sh
python3 tools/bench/gerbil_package_bench.py run \
  --profile tools/bench/profiles/example.json \
  --toolchain .data/toolchain.json --id example-candidate-01 --rounds 3
```

Each round uses a fresh source copy, then real `clean`, `build`, and all declared
test commands. Physical hardware cores determine test parallelism on Darwin.
Hard gates: first **compile** log 5s, full build 50s, whole concurrent test wave
112s (first real test output 5s). There is no per-file silence timeout. A test
requires exit zero, final `OK`, and no recognized failure marker. Failure stops
later rounds. Original inputs/source hashes and atomic terminal receipts are
retained in `.data/bench/runs/<id>/receipt.json`; raw logs remain local.
Each round also records redacted selected compiler flags and toolchain paths.
Toolchain construction inputs must be declared rather than inferred from old
experiment numbers. The runner does not reconstruct historical flags by guess.

## Cleanup

Cleanup defaults to a plan. It removes only registered per-round `project`
copies, never logs, receipts, toolchains, or arbitrary historical `.data` trees.
The byte count is logical file bytes, not promised APFS reclaimed disk space.
Symlinks, active leases, nonterminal runs, protected inputs, changed trees and
changed receipts are denied. Shared run leases block exclusive cleanup.

```sh
python3 tools/bench/gerbil_package_bench.py cleanup-plan \
  --run example-candidate-01 --output .data/cleanup-plan.json
python3 tools/bench/gerbil_package_bench.py cleanup-apply \
  --plan .data/cleanup-plan.json --sha256 REVIEWED_PLAN_SHA256
```

The apply receipt records each completed removal, including partial failure.
Old unregistered experiments require separate reviewed migration; this tool
does not guess that an old numbered directory is disposable.

Bounded read-only inventory reports observed logical bytes and explicitly marks
partial scans. It does not authorize deletion of old experiments:

```sh
python3 tools/bench/gerbil_package_bench.py inventory --output .data/cache-inventory.json
```

## Verification

```sh
python3 -m unittest discover -s tools/bench -p gerbil_package_bench_test.py
```

Framework tests verify safety and admission logic. They are not a new MCP or
standard-library performance receipt. Historical 47-second numbers remain
historical until the selected complete package profile is run against its
exact toolchain and inventory.
