# Darwin Multi-Entry Bundle Mechanism

Status: mechanism PASS, consumer performance NOT QUALIFIED. This is an isolated
test fixture, not a new optimization in `mcp-v4-driver.series`.

## Review Before Implementation

1. Correct route: reduce distinct Mach-O images while retaining each original
   Gambit module entry. `lib/os_dyn.c` resolves a path and a linker symbol
   separately; `lib/setup.c` rejects a repeated entry, not a second different
   entry in the same physical image. Gerbil's `runtime/loader.ss` invokes the
   ordinary loader, so default filename-derived entries must also work.
2. Previously explored: this differs from rejected packed-string emission,
   provider pre-registration and RTLD visibility changes. The fixture neither
   rewrites generated C nor changes Gambit initialization/loading guards.
   Earlier fixture attempts are retained as failures, not performance results.
3. Worthwhile: mapping fewer physical images is a direct mechanism for the
   observed Darwin loader cost. Whether that cost is material in the admitted
   consumer configuration still needs measurement; this fixture cannot answer it.
4. Expected gain: two logical entries require one rather than two new images.
   No seconds-scale or whole-package speedup is inferred from that count.

## Actual Native Checks

The driver generates alpha and beta once each, then links those same unmodified
C files both separately and together. Every entry uses its original filename
alias, `alpha.o1` or `beta.o1`. Logical paths are symlinks to either the individual
image or the combined image. `##load` receives no explicit linker-name override.
The platform guard requires Darwin; both configured drivers use GNU GCC 16.

Receipts, each terminal with exit status zero:

- `.data/d1510-gambit-multi-entry-default-single-v1`: original MCP compiler ABI,
  `___SINGLE_VM`, GSC SHA256
  `9a1b842156fe15bb0c9415b87aebad0e72707bd793fe00353e7b68956929ab00`.
- `.data/d1510-gambit-multi-entry-default-multiple-v1`: original isolated ASCENT
  compiler ABI, `___MULTIPLE_VMS`, GSC SHA256
  `dd32a1694062deb4175641bbfe51c23f2d9d9efa5770fe5b1a2f75d68557984e`.

Each receipt contains four fresh processes: individual/grouped, forward/reverse
initialization order. All verify:

- Only the requested module initializes; initialization order is unchanged.
- Mutable vectors and closures remain independent across alpha/beta modules.
- Repeating an entry raises the original OS exception and does not initialize
  again or invoke the script callback again.
- A missing entry leaves initialized values, callbacks and image count intact.
- `_dyld_image_count` increases by two for individual images and one for grouped
  images. The success marker is emitted only after all assertions pass.

Generated C is byte-identical across these two compiler fixtures: alpha SHA256
`4cb349554d05a9d4b82af7f964a70def9b82bb493057a88ad378e410498f284b`, beta SHA256
`9d8a087cccba6436db2d31cd2572d17d68045fdecb92f8f13d0fec88e51225da`.
This is not simultaneous multi-VM-instance isolation qualification.

Final fixture identities:

| File in `tests/` | SHA256 |
| --- | --- |
| `bundle_alpha.scm` | `b5716c0e02fca0371ec4dafd0817dcce5efc0d6dced2ab223821976af23edfaa` |
| `bundle_beta.scm` | `a6fe7f06bc543f55768a9606bbcdb073f64a35ddf8be65849a9f478a1353f28e` |
| `bundle_image_counter.scm` | `9ee4fb95e23ebfb5eafdd9962f8c97d78c514584a595c43c601e7f8f6d6bd5c6` |
| `gambit_multi_entry_bundle_contract.scm` | `8d83843150da641d64261dec21a39d9c121173979689fef23e3b3ed8b6f3c910` |
| `check_gambit_multi_entry_bundle.sh` | `4c033da97ba6b8a05113ffefc745a89fe1a901b1a4ad1b42489df09710b042b0` |

## Retained Failures

The first attempt lacked the counter's dynamic-lookup link option. The second
used the wrong explicit counter entry alias. The third incorrectly required
repeat loading to succeed. The fourth compared the complete exception display
against just its message, omitting the printed call arguments. These attempts
are fixture failures, not evidence that changing native semantics is necessary.
v5 passed the basic explicit-entry contract; subsequent state fixtures passed
both ABIs. The final fixtures above additionally pass the default-loader route.

## Admission Boundary

Frozen MCP remains first log 4.004-4.049 seconds, cold builds
37.365 / 37.406 / 36.467 seconds, and one complete test pass at 87.409 seconds
with 39 files / 965 cases. Active ceilings remain 4.5 / 42 / 97 seconds.

The static-closure snapshot candidate's isolated ASCENT 135-second DENY remains
closed; this mechanism does not reverse that result or admit that candidate.
Before any bundle patch enters the measured series, it needs real Gerbil module
integration, source/options/toolchain group invalidation, immutable publication,
failure and concurrency checks, plus both consumers' complete correctness and
performance gates. No timed consumer run, active checkout modification, global
installation, commit or push is claimed here.
