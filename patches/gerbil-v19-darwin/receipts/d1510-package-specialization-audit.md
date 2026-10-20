# D1510 Package Specialization Audit

Scope: audit the current numbered Darwin patch files, the frozen reader
helpers, embedded-provider construction, and source/release integration.
This is a source/configuration audit, not a new performance qualification.
No runtime, frozen binary, release recipe or consumer source was changed.

## Package Conditions

No MCP package-name, cookbook, recipe, HTTP-module or MCP source-content
condition was found in the numbered runtime/compiler patches. The MCP
mentions in 0013 and 0018 are explanatory evidence text, not added execution
conditions. The relevant mechanisms operate on ordinary process creation,
compile-output dependencies, literal shell substitutions, generated loader
syntax, and buffered reader characters/readtable handlers.

The reader token and whitespace helpers do not dispatch on filenames or
package identities. The whitespace fast path requires the actual whitespace
handler and retains the original reader fallback. The source-loader predicate
recognizes bounded begin/load-module forms, not MCP module names. These
observations establish implementation scope, not equal gains for every package.

## Frozen Provider Boundary

The local frozen host contains 280 native providers: 60 gerbil and 220 std
modules. No provider module belongs to MCP. Construction uses exact ordinary
native-object entries and verifies image content before returning an embedded
provider; unmatched requests use the original dynamic-loading path.

However, build_embedded_provider_candidate.py emits exact installation-path
aliases for the retained build and the copied test home. One test-home directory
has mcp in its name. Those paths affect provider hits and are not merely labels.
The provider inventory is bound to a captured local closure; this audit does
not establish that it is exhaustive or selected independently of the workload.
Thus the frozen host is environment-bound experimental construction, not a
relocatable, universally qualified release implementation. Removing these
aliases in place would invalidate the existing binary and timing anchor.

Any future generalization must derive eligible providers from the toolchain,
not a consumer name or benchmark import inventory, preserve identity checks and
fallback behavior, and receive independent correctness/performance evidence.
That is a separate candidate; the existing anchor remains unchanged.

## Test Fixture Separation

receipts/mcp-selected-toolchain-fixtures.patch is intentionally MCP-specific.
It changes only MCP test files: selected toolchain paths, syntax balancing and
temporary package-directory isolation. It is applied by the local progressive
MCP test controller, not tools/ci/build_source_toolchain.sh or the publish-v19
workflow. It is not a runtime performance patch and must never be promoted to
the toolchain stack or counted as a compiler speedup.

The current source/release entrypoints also do not integrate the local frozen
provider constructor or 0018 generated-stage patch. Distinguish numbered local
candidates, the frozen experimental host, and the applied release stack.

## Verification And Next Admission Boundary

verify_reader_whitespace_47_baseline.py passes the retained helper/artifact
identity checks. Its historical incomplete-test status is preserved; this
audit does not turn that receipt into a full-suite pass or rerun its timings.

Subsequent public-mechanism research must use independent standard-library
consumers, including make/test and differing import/FFI/executable shapes.
MCP remains a heavy regression sample. No consumer identity branch, assertion
reduction, import trimming or benchmark-selected provider list is admissible
as the general Darwin solution. The 5-second first-log and 50-second cold-build
MCP gates remain sample-specific anchors, not universal duration ceilings for
arbitrarily sized packages; full MCP test policy remains 112 seconds.

Private evidence: .data/d1510-reader-whitespace-native-v2/report.json and the
frozen baseline artifact manifest. The binary remains SHA256
1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21.
