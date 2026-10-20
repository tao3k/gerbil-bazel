# Closed Link Consumer Integration

## Review And Scope

Correct direction: reuse expanded Scheme-to-C at its actual link consumer,
then bind the selected C to every executable object job. The denied singleton
producer deployment is not installed. The earlier 55-input compiled API proved
about 3.6 seconds of generation opportunity, but lacked this CLI/object handoff.
Expected gains apply to repeated identical closed sets, not necessarily an
initial population or a complete cold package.

Experimental 0029 applies after 0024/0025 and removes their singleton hooks
and includes from the compiler. It installs only the closed-link consumer.
Experimental 0028 is the Gerbil handoff and requires backend 0027 after 0026.
All are outside the measured five- and six-patch series. No package names,
special test inventories or MCP-specific branch appear in their implementation.

## Mechanism

GSC admits a narrow Darwin C-link envelope only when explicitly enabled and
given `-closed-c-binding`. Group Scheme inputs by directory with complete
ordered membership in each proof. Reuse the existing snapshot-reader API,
source/include/options/tool/environment guards, lock and immutable C pins.
Pin existing C inputs too. Preserve mixed input order and preload flags.
Write a fresh caller-owned S-expression binding inventory. No manifest is
published for unsupported transformations; errors in admitted work propagate.

Gambit's default link output directory is derived from the original last
input, not the replacement pin. A real native fixture caught this omission
in v1; v2 fixes it according to `link-flat`/`link-incremental` source rules.
Explicit-output generation/link byte parity and default-output native execution
are separate checks.

Gerbil keeps bindings in the executable's lexical scope. It validates the
complete input inventory and maps runtime C/Scheme inputs back to the existing
static object paths. The generated link C has its own digest. Each bound job
receives a private process environment; the threaded parent never calls setenv.
Timestamp-only object shortcuts cannot bypass the bound backend proof.
Default-off and Linux retain ordinary behavior. Binding files are removed
after reading, before queued jobs; the in-memory bindings survive the barrier.

## Real Native Evidence

Genuine GNU GCC, matching Multiple VM headers/libraries; terminal checks pass:

| `.data/` receipt | Evidence |
| --- | --- |
| `d1510-closed-link-consumer-v3` | 55 real modules, two directories, population 3.63 s / HIT 0.24 s; every C and whole explicit-output link identical to original; mixed C/SCM order and preload flags pass; unsupported options/default-off remain ordinary |
| `d1510-closed-link-object-binding-v2` | v2 GSC default output, actual Scheme/native 17; unbound changed C runs 29; bound mutation rejects; restored bound native 17 and exact ordinary object/output |
| `d1510-closed-link-driver-smoke-v2` | Actual Gerbil parallel object handoff, 20 link inputs, three bound backend MISS events, native program correct; binding directory cleaned |
| `d1510-closed-link-canonical-base-v1` | Actual 0024/0025/0029 application to original source; all three changed source files equal native v2 build inputs |
| `d1510-closed-driver-patch-replay-v1` | Actual 0028 application to original Gerbil source; exact compiled-candidate source parity |

v1 of the 55-input fixture accidentally exported manifest-check variables into
the subsequent generation environment. The complete environment check correctly
caused MISS; the corrected fixture unsets only its own checker variables. The
cache identity was not weakened. v2 passes the same checks at 3.84 / 0.24 seconds.
The first manual Gerbil smoke omitted the consumer's sanitized linker environment
and failed at final link; v2 uses that existing environment and passes.

## Actual Isolated ASCENT

Workspace `.data/d1510-closed-link-ascent-v1`, clean project HEAD
`21e3638687d42ecfc36acebb28991987435ebc60`. Dynamic-image identity verification
passes for 1989 retained toolchain images and 2809 dependency images. The driver
overlay owns ten files. Original workspace remains clean and its helper digest
remains the frozen `08d8ebe59d24a7098561c909c5b8e04c66aff78794d5f68f1cedddf1f2168646`.
Project-owned Bash/`just` runs real native tests with 12 host build cores and
the unchanged 135-second component cap; Python only reads terminal receipts.

| Receipt suffix | Complete | User / System | Cases | Generation | Objects |
| --- | ---: | ---: | --- | --- | --- |
| `ascent-receipt-v3` | 50.48 s | 105.74 / 37.44 s | 30/30, final OK, exit 0 | 3 MISS, 224 selected inputs | 74 MISS |
| `ascent-receipt-v4` | 44.55 s | 56.56 / 29.69 s | 30/30, final OK, exit 0 | 1 HIT, 2 MISS, 224 selected inputs | 71 HIT, 3 MISS |

Prefix: `.data/d1510-closed-link-`. Offline extraction is
`d1510-closed-link-ascent-cases.json`; logs are content-digested there.
Both runs reuse an already compiled library and report entry-cache MISS. For v4,
the owned entry binary was archived into v3's receipt then removed, forcing real
compilation/linking again. This is not executable-cache reuse, complete package
cold performance, all 94 Suites, or a matched ordinary/candidate speedup.
`objectCalls` in the existing extractor counts verbose invoke lines only; the
new bound process path lacks those lines. Zero in that field does NOT mean zero
object calls. Actual backend events above prove 74 eligible object operations.

v1 (110.18 s, 30/30) installed the driver files but did not execute them: the
running AOT runtime retained the old implementation. It is excluded from new
mechanism qualification. A private Bash qualification launcher explicitly loads
the owned driver image; it also preserves the consumer's leading Gambit `-:`
heap/debug options. v2 failed before Cases because the initial launcher put
those options after the dispatcher; the corrected v3/v4 preserve them.
This launcher is test infrastructure, not a production/release fix. A delivered
AOT runtime must be relinked with the new compiler implementation.

## Identities

| Artifact | SHA-256 |
| --- | --- |
| 0028 Gerbil patch | `e1efb97fc3eada92c031d2d243c51c8c7c05a60df8248218ef5081be2db9f76c` |
| 0029 GSC patch | `715ab573ccbe58c693351e13b96924ee4562718524c5c8976b9a310b47d7c0cf` |
| Native v2 GSC | `cab85a8199f197a0697756393559c62ca67cd99f4a5acaf0e4c2f69c1a493876` |
| Gerbil source | `faa16f27c11b5265b6aa5cf471d558881070134c060d0b657778beee42cb43d8` |
| Owned driver runtime image | `f25991cd48237e9da5b6aad325ab4ee7d54b3f83def8a08f06b27c0628d7c0f7` |
| Bound backend helper | `86fc6b5610e59af38dfadb9e3853bd1fc694c5dedb1fd7d796b2157e77dd7c39` |
| Bound backend driver | `78eeb8c4e9cec4e9ddfb612662d734d45b1a04ef345fb7c8917cf4f11fe85367` |
| Qualification launcher | `991a53ba551ae7376b500f67bb888222d5c5af884b645cae073c81ef2acbd6ca` |

## Next Evidence, Not Admission

The rebuilt entry Scheme carries a fresh `::timestamp` and shares a directory
group with stable dependencies. Full membership/source checks correctly reject
that entire group. The executable-stub group's logical C is deleted by Gerbil
after linking, also preventing that group's HIT. Do not normalize timestamps or
weaken checks. Investigate explicit caller-role partitioning, then prove raw C
and link parity, membership/source invalidation and concurrency before testing
whole consumers. Directory grouping alone has not delivered the complete win.

The frozen MCP references are untouched and their identity/raw-evidence checks
still pass: first logs 3.950--4.038 s, three cold builds
36.414 / 35.552 / 37.770 s, complete tests 86.924 s, 39 files / 965 cases.
Hard ceilings remain 4.5 / 42 / 97 s. No new MCP qualification, AOT production
runtime, general release admission, full ASCENT performance, commit or GitHub
delivery is claimed. The goal remains active.
Focused patch locks, preparation, receipt parsing and overlay checks pass
84 tests; all changed native shell runners pass Bash syntax checks.
