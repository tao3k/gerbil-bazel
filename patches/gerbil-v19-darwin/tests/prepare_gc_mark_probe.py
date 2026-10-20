#!/usr/bin/env python3
"""Count original GC marker work; never a timing candidate."""
import argparse
import hashlib
import json
from pathlib import Path


PREAMBLE = r'''
#if defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__) && \
    defined(___SINGLE_THREADED_VMS) && defined(___SINGLE_VM) && \
    (___MAX_PROCESSORS == 1) && (___WS == 8)
#include <stdio.h>
#include <stdlib.h>
static unsigned long gb_gc_calls,gb_gc_single,gb_gc_visits,gb_gc_allocated;
static unsigned long gb_gc_heads[8],gb_gc_copies[32],gb_gc_words[32];
static unsigned long gb_gc_sizes[10],gb_gc_max_words;
static unsigned long gb_gc_array_calls[8],gb_gc_array_cells[8];
static unsigned long gb_gc_four_ahead_slots,gb_gc_negative_calls;
#define GB_GC_CALL(n) do { \
  long gb_signed_n=(n); \
  unsigned long gb_n=gb_signed_n>0 ? (unsigned long)gb_signed_n : 0; \
  unsigned int gb_bucket=gb_n<=2 ? gb_n : gb_n<=4 ? 3 : gb_n<=8 ? 4 : gb_n<=32 ? 5 : gb_n<=128 ? 6 : 7; \
  gb_gc_negative_calls+=(gb_signed_n<0); \
  ++gb_gc_calls; gb_gc_single+=(gb_n==1); \
  ++gb_gc_array_calls[gb_bucket]; gb_gc_array_cells[gb_bucket]+=gb_n; \
  gb_gc_four_ahead_slots+=(gb_n>4 ? gb_n-4 : 0); \
} while (0)
#define GB_GC_VISIT() (++gb_gc_visits)
#define GB_GC_HEAD(h) do { ++gb_gc_allocated; ++gb_gc_heads[h]; } while (0)
#define GB_GC_COPY(s,w) do { \
  unsigned long gb_w=(w); \
  ++gb_gc_copies[s]; gb_gc_words[s]+=gb_w; \
  ++gb_gc_sizes[gb_w<=4 ? gb_w : gb_w<=8 ? 5 : gb_w<=32 ? 6 : gb_w<=128 ? 7 : gb_w<=1024 ? 8 : 9]; \
  if (gb_w>gb_gc_max_words) gb_gc_max_words=gb_w; \
} while (0)
static void __attribute__((destructor)) gb_gc_mark_dump(void) {
  const char *path=getenv("GAMBIT_GC_MARK_PROBE_FILE");
  if (!path) return;
  FILE *file=fopen(path,"w");
  if (!file) return;
  fprintf(file,"{\"calls\":%lu,\"singleCalls\":%lu,\"visits\":%lu,\"allocatedVisits\":%lu,\"maxCopiedWords\":%lu,\"heads\":[",
          gb_gc_calls,gb_gc_single,gb_gc_visits,gb_gc_allocated,gb_gc_max_words);
  for (int i=0;i<8;++i) fprintf(file,"%s%lu",i?",":"",gb_gc_heads[i]);
  fprintf(file,"],\"copiesBySubtype\":[");
  for (int i=0;i<32;++i) fprintf(file,"%s%lu",i?",":"",gb_gc_copies[i]);
  fprintf(file,"],\"wordsBySubtype\":[");
  for (int i=0;i<32;++i) fprintf(file,"%s%lu",i?",":"",gb_gc_words[i]);
  fprintf(file,"],\"copySizeBuckets\":[");
  for (int i=0;i<10;++i) fprintf(file,"%s%lu",i?",":"",gb_gc_sizes[i]);
  fprintf(file,"],\"arrayLengthBucketCalls\":[");
  for (int i=0;i<8;++i) fprintf(file,"%s%lu",i?",":"",gb_gc_array_calls[i]);
  fprintf(file,"],\"arrayLengthBucketCells\":[");
  for (int i=0;i<8;++i) fprintf(file,"%s%lu",i?",":"",gb_gc_array_cells[i]);
  fprintf(file,"],\"fourAheadSlots\":%lu,\"negativeLengthCalls\":%lu}\n",gb_gc_four_ahead_slots,gb_gc_negative_calls); fclose(file);
}
#else
#define GB_GC_CALL(n) ((void)0)
#define GB_GC_VISIT() ((void)0)
#define GB_GC_HEAD(h) ((void)0)
#define GB_GC_COPY(s,w) ((void)0)
#endif
'''


def array_census(data):
    """Validate array lengths independently of recursive tail-mark visits."""
    def counter(value):
        if type(value) is not int or not 0 <= value < 2**64:
            raise ValueError('unsigned 64-bit census counter required')
        return value
    calls = [counter(value) for value in data['arrayLengthBucketCalls']]
    cells = [counter(value) for value in data['arrayLengthBucketCells']]
    if len(calls) != 8 or len(cells) != 8:
        raise ValueError('eight complete length buckets required')
    ranges = ((0, 0), (1, 1), (2, 2), (3, 4), (5, 8),
              (9, 32), (33, 128), (129, None))
    for count, total, (low, high) in zip(calls, cells, ranges):
        if total < low * count or (high is not None and total > high * count):
            raise ValueError('length bucket calls and cells disagree')
        if count == 0 and total:
            raise ValueError('empty length bucket must have zero cells')
    if sum(calls) != counter(data['calls']) or calls[1] != counter(data['singleCalls']):
        raise ValueError('length census must match original entry counts')
    if counter(data['negativeLengthCalls']) > calls[0]:
        raise ValueError('negative-length calls must be empty scans')
    slots = sum(cells[4:]) - 4 * sum(calls[4:])
    if counter(data['fourAheadSlots']) != slots or sum(cells) > counter(data['visits']):
        raise ValueError('lookahead slots and marker visits disagree')
    return dict(arrayCells=sum(cells), fourAheadSlots=slots,
                fourAheadFractionOfVisits=slots / data['visits'] if data['visits'] else 0,
                diagnosticOnly=True, performanceQualified=False)


def inject(source):
    begin = "___HIDDEN void mark_array\n"
    end = "\n\n___HIDDEN void mark_captured_continuation\n"
    if source.count(begin) != 1 or source.count(end) != 1:
        raise ValueError("original marker boundary differs")
    first = source.index(begin)
    last = source.index(end, first)
    body = source[first:last]
    changes = (("  ___WORD *limit = alloc_heap_limit;", "\n  GB_GC_CALL(n);"),
               ("        ___WORD obj = *cell;", "\n        GB_GC_VISIT();"),
               ("            head_typ = ___HD_TYP(head);", "\n            GB_GC_HEAD(head_typ);"),
               ("                ___SIZE_TS words = ___HD_WORDS(head);", "\n                GB_GC_COPY(subtype,words);"))
    for old, addition in changes:
        if body.count(old) != 1:
            raise ValueError("original marker operation differs")
        body = body.replace(old, old + addition, 1)
    # Declarations must precede both the consistency-check and normal headers.
    anchor = '#ifdef ENABLE_CONSISTENCY_CHECKS\n\n#define mark_array(start,n)'
    result = source[:first] + body + source[last:]
    if result.count(anchor) != 1:
        raise ValueError("marker declaration context differs")
    return result.replace(anchor, PREAMBLE + '\n' + anchor, 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data = Path(__file__).resolve().parents[3] / '.data'
    if not all(path.resolve().is_relative_to(data) for path in (args.source, args.output)):
        parser.error('diagnostic must remain under project .data')
    original = args.source.read_text()
    changed = inject(original)
    args.output.mkdir(parents=True, exist_ok=False)
    args.source.write_text(changed)
    report = {'diagnosticOnly': True, 'performanceQualified': False,
              'originalSha256': hashlib.sha256(original.encode()).hexdigest(),
              'modifiedSha256': hashlib.sha256(changed.encode()).hexdigest(),
              'generatorSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
