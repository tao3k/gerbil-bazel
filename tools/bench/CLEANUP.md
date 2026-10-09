# Experiment Data Retention

The Python cleanup engine lives in Git, never in `.data`. Package qualification
already defaults to `--retention receipts`: terminal runs discard owned project
copies but retain logs, identities and verdicts. Native build/test commands are
not changed by the cleanup engine.

## Historical Experiments

Generate and review a bounded plan before deleting legacy trees:

```sh
python3 tools/bench/gerbil_package_bench.py tree-plan \
  --older-days 7 --batch 100 --output .data/cleanup-plan.json
python3 tools/bench/gerbil_package_bench.py cleanup-apply \
  --plan .data/cleanup-plan.json --sha256 REVIEWED_PLAN_SHA256
```

The exact plan digest is mandatory. Only immediate numbered experiment roots
qualify. Frozen receipt graphs, selected toolchains, package sources, registered
Git worktrees, active runs and explicitly excluded roots are protected.
An incomplete Git or open-file inventory, active lease, changed identity or
changed receipt refuses deletion. Symlinks are not followed during removal.

Top-two-level text evidence is archived before each tree is isolated and
removed. This is not a complete source backup. Keep any needed uncommitted
source tree in `retention.json` before authorizing retirement. Cleanup preserves
negative evidence without carrying its compiled images into the next run.

## Bounded Maintenance

The same engine supports a dry sweep, generating distinct bounded plans without
deletion (`--batches` previews additional batches for explicit review):

```sh
python3 tools/bench/gerbil_package_bench.py sweep \
  --id weekly-preview --older-days 7 --batch 100
```

`--apply` enables removal; `--batches` bounds repeated plan/apply cycles. Use this
only with explicit authorization covering the complete maintenance policy and
scope. It does not replace individual plan review when approval is batch-bound.
`--exclude .data/name` protects extra inputs for that invocation. Defaults are
dry-run, seven days, one batch, twenty targets. No background deletion is added.

Receipts live under `.data/bench/cleanup/<id>/`; archives under
`.data/bench/archives/`. Partial failure stops further batches and preserves the
actual completed removals in the terminal summary. Logical deleted bytes and
observed available-disk delta are separate fields: APFS clones, compression and
concurrent writes mean they are not equal.

## Clean Revalidation

Keep the frozen source, declared dependencies and toolchain as read-only inputs.
Create a new owned run directory; never reuse a previous run's project outputs.
Run real clean/build/test commands there, record the selected revision and hashes,
then discard the generated project after its terminal receipt. Cleaning caches
does not itself establish performance or correctness admission.
