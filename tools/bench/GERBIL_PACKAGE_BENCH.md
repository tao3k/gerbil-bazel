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

New runs default to `--retention receipts`: after a terminal outcome, including
exceptions, remove the owned per-round `project` copies automatically. Logs,
source/artifact hashes and acceptance receipts survive. Use `--retention failed`
to retain failed rounds for debugging, or `--retention all` to retain all copies.
An active lease or failed safety check records `retention.state = deferred`;
it never kills another run to make room. Interrupted nonterminal runs remain
protected and require investigation before cleanup.

Manual cleanup first produces a reviewed plan. It removes only registered
per-round `project` copies, never logs, receipts, toolchains, or arbitrary trees.
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
For old unregistered experiments, select explicit directories and one generated
artifact class. `dump-plan` selects GNU numbered compiler-pass dumps, never C
sources or objects. `cache-plan` selects only `.gerbil/lib` and `.gerbil/bin`
inside a `project` with `gerbil.pkg`; it preserves dependency stores, package
sources, raw logs and receipts. Neither command deletes anything:

```sh
python3 tools/bench/gerbil_package_bench.py cache-plan \
  --directory .data/old-experiment --output .data/old-cache-plan.json
python3 tools/bench/gerbil_package_bench.py dump-plan \
  --directory .data/old-experiment --output .data/old-dump-plan.json
```

Review `targets` and the SHA before using `cleanup-apply` as above. Legacy apply
rechecks identities and baseline protections, and refuses deletion if an open
file is detected or `lsof` cannot supply a complete snapshot. This is a snapshot
check, not locking of historical jobs that do not use the framework lease.
Plans are bounded to 15 seconds; `complete: false` means a partial scan, not
permission to infer total disk usage. Applications can still review those exact
listed targets. No whole numbered experiment directory is guessed disposable.

`tools/bench/retention.json` pins baseline roots and receipt graphs. Referenced
`.data` experiment roots, selected toolchain inputs and package sources are
protected across both cleanup modes. Required receipt anchors must exist;
optional local anchors are followed when present. Add a baseline anchor before
retiring its construction directories. This policy is separate from the
package-neutral execution and cleanup engines.

For a larger historical cleanup, `retired-plan` discovers failed experiments
from explicit failure verdicts in `report.json`, follows their local input
references and matches constructed binaries by their recorded SHA256. It also
selects report-bearing old experiments (default seven days), but only deletes
old files from that age-only category. Production-admitted roots and pinned
baselines are excluded. Selection never relies on an experiment number alone.

```sh
python3 tools/bench/gerbil_package_bench.py retired-plan \
  --older-days 7 --scan-seconds 60 --output .data/retired-artifacts-plan.json
```

Only generated Mach-O binaries/objects, object archives and GNU compiler dumps
are listed. Source, scripts, configurations, JSON receipts, logs, dependency
stores and checkout metadata remain in place. Failed-route evidence therefore
survives without retaining its bulky objects. Apply revalidates all associated
report hashes, file identities, protections and open files; use the same
reviewed `cleanup-apply` command. The applied receipt records logical bytes
removed. Partial plans report scanned/selected directories and never claim to
cover all of `.data` or reclaim that many physical APFS bytes.

For disposable numbered experiment directories, `tree-plan` retires entire
failed trees, plus old unprotected trees (seven days by default), in batches:
Use `--completed` only when retiring completed, receipt-qualified experiments
explicitly; this includes recent disposable construction trees. Pinned baselines
and production-admitted roots remain excluded even in this mode.

```sh
python3 tools/bench/gerbil_package_bench.py tree-plan \
  --older-days 7 --batch 20 --output .data/numbered-tree-plan.json
```

After review, `cleanup-apply` archives text evidence from the top two levels
(reports, configurations, logs and candidate source), then atomically moves each
selected tree into `.data/bench/trash` before deleting it. These archives are
evidence, not full backups of build trees or deep profiler recordings. Symlinks
inside a retired tree are removed without following their destinations. Baseline
protections, receipt/directory identity and open-file checks are mandatory.
An interruption leaves an explicit quarantine receipt; do not silently rerun
the old plan. Completed deletions are recorded one directory at a time.
Free-space change is reported as `observedAvailableDeltaBytes`, not an exact
attribution of APFS physical bytes to this cleanup.

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
