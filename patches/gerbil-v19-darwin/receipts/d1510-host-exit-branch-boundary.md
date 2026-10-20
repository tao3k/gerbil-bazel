# D1510 Host-Exit Branch Boundary

## Decision

Do not propose enabling C tail calls as a newly missing Darwin optimization
on the retained configuration. This is a bounded source/native-path audit,
not a new speedup and not a claim about every Scheme call or loaded image.
The retained runtime and production patches are unchanged.

## Existing GNU Evidence

`experiment.py register-branch --existing-preprocessor` reuses the three
saved GNU 16/Darwin transcripts in `.data/d1510-gvm-register-layout-v1`.
It checks original capture inputs, source identities, byte-exact capture
qualification and the frozen runtime before admitting the branch report.
No compiler or target process is invoked. The original local-register
fields must match the prior report; transcript hashes are recorded for the
new audit, not claimed as previously authenticated transcript hashes.

Compiler/base~1, std/make~0 and std/make~1 all select:

```c
#define ___USE_TAIL_CALL_TO_EXIT_HOST
#define ___USE_PROPER_TAIL_CALL_EXCLUSIVELY_TO_EXIT_HOST
#define ___TRUST_C_TCO 1
#define ___EXIT_HOST() ___TAIL_CALL_VOID(___CALL_LABEL_HOST(___pc,___ps))
#define ___TAIL_CALL_VOID(call) ___PROPER_TAIL_CALL(call)
#define ___PROPER_TAIL_CALL(call) __attribute__((musttail)) return call
```

The trampoline-unwind macro is absent. Clang, a missing exclusive flag,
ordinary `return call` or an active unwind flag rejects this audit.
Evidence: `.data/d1510-host-exit-branch-v1/report.json`; both performance
qualification and production admission are false.

## Retained Native Path

The audited binary remains SHA-256
`1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21`.
Read-only LLVM disassembly of its common host at 0x10030d69c-0x10030d6d4
shows VM-register publication, target loading, restoration of saved C
registers and the 8192-byte stack frame, then `br x16`. There is no `blr`
or trampoline call in that block. This proves the existence of this native
host-exit path, not its execution frequency or cost during macro expansion.
LLVM is the inspection tool here; no Clang compilation is introduced.

[GCC's target-hook documentation](https://gcc.gnu.org/onlinedocs/gccint/Tail-Calls.html)
explains why PIC and calling-convention constraints require actual target
verification. That general risk alone is not evidence that this retained
Darwin path lacks a tail transfer.

## Other Premises Rechecked

The original staging `src/std/make.ss` message function explicitly calls
`force-outputs` after `displayln`; `force-outputs` flushes both output and
error ports. The process-semantics fixture's previously missing flush does
not explain the actual first-compile DENY. Do not move std/make logging.

Initial registration has already been measured: five phases total
3.424-13.684 ms, with subsequent empty control starts at 0.185588-0.264073 s.
See [the existing initial-setup follow-up](d1510-native-loader-boundaries-tested.md).
Do not repeat it as an unmeasured seconds-scale startup candidate.

## Three Lines

No new cold build or complete test was run by this audit. Historical retained
results remain separate from current acceptance:

| Measurement | Historical retained evidence | Current hard gate |
| --- | --- | --- |
| First compile log | 4.850866 / 4.573628 / 4.592897 s | <=5 s |
| Complete cold build | 47.771713 / 47.824226 / 47.927094 s | <=50 s |
| Complete test | 105.750982 s; 39 files, 965 passed | <=112 s |

Later strict test DENYs remain DENYs, not stable 112-second acceptance.
Regression candidates stop immediately, retain partial evidence and skip
subsequent phases; uncompleted build/test durations remain null.

Validation: 21 source/framework tests passed. This excludes a missing-flag
premise, but does not establish a new performance mechanism.

## Whole Common-Host Follow-Up

The unified `native-layout --control-transfer` command reads the unchanged
binary and uses its actual function-start metadata to bound disassembly.
Every four-byte instruction address must cover the extent contiguously;
partial, duplicate or reordered disassembly is rejected. Ordinary AArch64
BR/BLR opcodes are decoded from instruction words, not mnemonic substrings.
Authenticated branch opcodes are explicitly outside this count.

`.data/d1510-common-host-control-transfer-v1/report.json` records 264,754
instructions across 1,059,016 bytes. It finds two BR sites, at 0x1002f3fa0
and 0x10030d6d4, and zero BLR sites. This is static native topology, not a
dynamic execution count, a branch-miss measurement or all call instructions.

This does not admit another dispatch-distribution candidate. The original
[D916 distributed-exit experiment](d897-mcp-gambit-startup-candidates.md)
already preserved VM publication and proper-tail-call conventions while
preventing site merging with distinct zero-instruction asm operands. Its
native sites increased, but actual first compilation failed its then-10-second
gate at 10.725 seconds; no complete build was admitted. The retained host's
small site count therefore cannot reopen that same mechanism or an equivalent
flag sweep. It also does not prove branch prediction is cost-free.

No cold/test phase was rerun. The three historical lines and current hard
gates above remain unchanged. Nineteen native/framework checks passed for
this follow-up; no performance-qualified patch was produced.

## Historical First-Window Code Compatibility

A subsequent read-only comparison uses the existing `text_bytes` and
`relocations` parsers, not a new profiler or controller. The old hardware
mapping's `.data/d1510-outline-current-native/gerbil-link.o` and the retained
`.data/d1510-source-loader-linked/gerbil-link.o` have different whole-object
hashes, but their complete 1,126,540-byte executable text and symbolic text
relocation records are identical. Both text hashes are
`087382cb4239ed3bb462a1669d8ce6850b6f26205fb122a74d5f030e00038f7e`.
The common host begins at object offset 0x107c4 in both objects.

This permits using the old byte-identical debug object's instruction/source
relationships to understand unchanged carrier code. It does not transfer old
linked-image addresses, UUIDs, runtime data, procedure/global values, or CPU
weights to a new process. The historical source's line numbers also are not
the current generated source's line numbers: source hashes differ and macro
definition order changed. Native lookup must first use the matched function
offset and exact old debug provenance, not a nearest-line guess.

The existing D1611 diagnostic covers a perturbed 4.506716-second builder window.
Its own code still has separate source identity and dynamic-call checks; a
later source-loader/reader composition cannot be called that same workload.
Nevertheless there is no justification for discarding all that evidence or
recompiling the same debug carrier. Its major code distribution, considered
only for hypothesis selection, already argues against a two-instruction hash
stack removal as a several-fold prefix solution. See
[the original wider capture](d1613-entry-gated-wider-cpu-boundary.md) and
[the actual failed cold-tail candidate](d1510-hash-cold-tail-denied.md).

This resolves code compatibility, not performance admission. No new complete
build/test times exist; all three historical lines above remain historical.

## Reused Standard-Library Sample Locations

A read-only follow-up maps the existing independent standard-library sample
leaves in `.data/d1510-stdlib-counter-profile-v1/time-profile.xml` through the
byte-identical carrier debug object. It validates the completed profile's
runtime identity, precise metric intervals, running target PID, runtime UUID,
actual function boundaries, complete text and relocation identity, and the
historical generated source hash. It also compares the saved DWARF intervals
and file metadata against a fresh dump of that same debug object: all 131,069
intervals match. Raw dump headers differ with object path spelling; those
headers are not used as line evidence. No compiler or workload is launched.

All 81 matched common-host samples map, across 71 distinct PCs. Fifteen map
to shared module macro locations (nine END_M_HLBL and six END_M_COD). These
cannot be charged to the lexically adjacent Scheme procedure. Of the remainder,
source-block annotations include six hash-get samples, five core-bind-import!,
four core-resolve-identifier, three core-expand-module-body and three stx-e.
These annotations are compiler-assigned source locations, not exclusive
procedure costs or a measured fraction of full build/test time. The sparse,
distributed observation does not select a single expansion function for a
large rewrite. It does not reopen distributed host exits or result caching.

Source review also finds that strong memory-key tables are conservatively
marked KEY_MOVED after collection. Tracking only actual changed keys might
avoid some in-situ rehashes, but that observation is not enough to select a
candidate. The already captured historical first-window profile in
`.data/d1611-gated-first-cpu/cpu-summary.json` assigns in-situ rehash 31,880,793
of 10,062,163,921 sampled cycles (0.316838%). That is an older perturbed
workload's weight, not a current runtime forecast. Even there it does not
provide a large budget. No selective-rehash implementation or new campaign is
constructed. This decision applies the budget requirement before source edits,
rather than converting a plausible low-level change into another small-win
experiment. It is not an executed rejection of all possible rehash algorithms.

The frozen production binary and all performance gates remain unchanged.
This follow-up supplies evidence for candidate selection, not an acceleration
claim; no fresh first-log, complete-build or complete-test result exists.
