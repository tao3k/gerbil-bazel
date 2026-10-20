# Existing Producer C: Non-generating Consumer Lookup

## Direction Review

The denied diagnostic dispatch attempt recorded 154 `-c`, 153 `-obj` and
140 `-target` entries. Its build log contained 136 visible generated-C MISS
markers and no HIT; 154 proof files existed when the whole-build gate stopped
the run. These are partial interrupted-run counts, not complete workload totals.
They show no admitted cold consumer saving from that population-only dispatcher.
Do not retry it unchanged looking for a favorable timing.

The next direction is the actual duplicate-generation boundary: a static-link
consumer reads already-produced immutable C, or falls back to its original
Scheme path. It must not populate a cache on the consumer's miss. The expected
opportunity remains the measured paired-source rewrite component, not a claimed
whole-build multiplier. Cold producer proof cost still has to be addressed.

## Implemented Prototype

`lookup-produced-generated-c` is a read-only, non-generating lookup. It accepts
separate static and dynamic Scheme paths and the original producer options and
directory. Admission requires:

- Darwin, supported options and an uncontaminated source-macro context;
- paired module/linker aliases equal to the static source's stem;
- regular source/proof/pinned files, matching static/dynamic main bytes;
- an exact reconstructed producer context hash, including options, source path,
  output directory, cwd, environment, tools and primary source bytes;
- exactly one recorded source dependency, equal to the dynamic primary source;
- the proven output name and immutable C content digest;
- revalidated source/tool/environment identities before returning the pin.

All failures return false for the caller's original Scheme fallback. The lookup
does not invoke generation, acquire the producer lock, publish proof/C or repair
a missing pin. It uses a caller-owned scratch directory only to hash structured
context, and removes its own context file. Context cleanup now preserves a
preexisting scratch file instead of deleting a file it did not create.

This conservative single-source projection deliberately rejects transitive
includes: equal main bytes alone cannot prove relative include equivalence at
two different Scheme paths. It is not an arbitrary GSC compilation cache.

## Real Native Controls

Receipt `.data/d1510-produced-generated-c-contract-v2` passes adoption, changed
static source, changed producer source, missing-proof fallback, transitive-include
rejection and no-generation/no-publication controls. Earlier pinned C remains
unchanged across producer mutations. Independent default incremental `gsc -link
-target C` calls compare original static Scheme versus the admitted existing C
at the same link output name; complete link C bytes are identical.

The fixture is a deterministic native Scheme module, not an integrated MCP or
ASCENT build. No whole-build or test timing is reported for it.

## Exact Identity

- Prototype: `67e55ba14e80f88fc4fd890cf63a0994b21e105c987899a26a0493b7064cccee`
- Contract: `df802d59f073d3a057412f79b98967df339937cf852af1af4dbe902bce588706`
- Output: `358c7d2170dbe1e7ff0b64f070b0709459358ed4991ff93b6a66becbf4f2ebbc`
- Equal link C: `49577e30b8a7fb0f20f4884dc95dda47f9a228354d285dd25be4e3bfd6445734`

## Remaining Gate

The real Gerbil static-link caller still needs explicit dynamic/static path
binding and original-link fallback integration. Bulk context/tool validation must
be amortized without weakening identity; producer population cannot be assumed
free. Loaded-image/reader/default-diagnostic admission and full-consumer controls
remain required. This prototype is excluded from the frozen v4 driver series.
The best MCP baseline and 4.5/42/97 hard gates are unchanged. General isolated
ASCENT correctness/performance admission is still open.
