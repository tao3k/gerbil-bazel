"""Compile original and pure-tree Gambit fixtures; compare real std/test exits."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess

from bazel_host_environment import build_environment
from gambit_guarded_trace import PREAMBLE, inject
from gambit_host_coalescing import section


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--fresh', action='store_true')
    parser.add_argument('--scalarize', action='store_true')
    parser.add_argument('--require-structure-elision', action='store_true')
    parser.add_argument('--hash-scan', action='store_true')
    parser.add_argument('--scalar-boundary', action='store_true')
    args = parser.parse_args()
    if args.scalarize and not args.fresh:
        parser.error('caller scalarization requires the fresh allocation contract')
    if args.require_structure_elision and not args.scalarize:
        parser.error('structure-elision coverage requires scalarization')
    if args.hash_scan and (args.fresh or args.scalarize or args.require_structure_elision):
        parser.error('hash scan is a separate native primitive experiment')
    if args.scalar_boundary and (not args.scalarize or args.require_structure_elision):
        parser.error('scalar boundaries require a separate fresh scalarization contract')
    root = Path(__file__).resolve().parents[3]
    baseline, output = args.baseline.resolve(), args.output.resolve()
    if not all(path.is_relative_to(root / '.data') for path in (baseline, output)):
        parser.error('isolated .data paths required')
    env = build_environment()
    macros = subprocess.check_output([env['CC'], '-dM', '-E', '-x', 'c', os.devnull], env=env, text=True)
    if '#define __clang__' in macros or '#define __GNUC__ 16\n' not in macros:
        parser.error('real GNU GCC 16 required')
    cores = int(subprocess.check_output(['sysctl', '-n', 'hw.physicalcpu'], text=True))
    home = baseline / 'build'
    env.update(GERBIL_HOME=str(home), GERBIL_GSC=str(home / 'bin/gsc'),
               GERBIL_LOADPATH=str(home / 'lib'),
               GAMBOPT=f"~~bin={home / 'bin'},~~lib={home / 'lib'},~~include={home / 'include'}",
               GAMBITDIR_INCLUDE=str(home / 'include'), GAMBITDIR_LIB=str(home / 'lib'))
    for key in list(env):
        if key.startswith('GAMBIT_'):
            env.pop(key)
    output.mkdir(parents=True, exist_ok=False)
    report = dict(qualified=False, performanceQualified=False, cores=cores, runs=[],
                  scope='bounded-pure-tree-native-std-test-contract-not-startup-qualification')
    if args.fresh:
        report['scope'] = 'bounded-fresh-tree-native-std-test-contract-not-startup-qualification'
    if args.scalarize:
        report['scope'] = 'bounded-scalarized-caller-native-std-test-contract-not-startup-qualification'
    if args.hash_scan:
        report['scope'] = 'bounded-small-hash-scan-native-std-test-contract-not-startup-qualification'
    if args.scalar_boundary:
        report['scope'] = 'bounded-scalar-prefix-original-effect-native-contract-not-startup-qualification'
    def run(name, command, process_env, timeout=120):
        with (output / (name+'.log')).open('w') as log:
            child = subprocess.Popen(command, env=process_env, stdout=log, stderr=subprocess.STDOUT,
                                     start_new_session=True)
            try:
                code = child.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
                raise RuntimeError(name+' exceeded bounded contract budget')
        if code:
            raise RuntimeError(name+' failed; inspect retained native log')
        return code
    try:
        source = Path(__file__).with_name('gambit-scalar-boundary-contract.scm' if args.scalar_boundary else 'gambit-small-hash-scan-contract.scm' if args.hash_scan else 'gambit-fresh-tree-contract.scm' if args.fresh
                                        else 'gambit-pure-tree-contract.scm')
        report['fixtureSha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
        original_dir, candidate_dir = output / 'original', output / 'candidate'
        original_dir.mkdir()
        candidate_dir.mkdir()
        cfile = original_dir / (source.stem+'.c')
        run('generate', [str(home / 'bin/gsc'), '-c', '-o', str(cfile), str(source)], env)
        original = cfile.read_text()
        before, host, after = section(original, '___BEGIN_M_COD', '___END_M_COD')
        host_before, body, host_after = section(host, '___BEGIN_M_SW', '___END_M_SW')
        definitions = dict(re.findall(r'^#define[ \t]+([A-Za-z_]\w*)[ \t]+(.*)$',
                                     original.replace('\\\n', ' '), re.MULTILINE))
        module = dict(prefix='', offset=0, path=cfile, controls=definitions,
                      original=original, originalBody=body, body=body)
        if args.hash_scan:
            details = dict(supplementaryPureTrees=[])
        elif args.scalar_boundary:
            from gambit_scalar_boundary import inject as inject_boundary
            details = inject_boundary([module])
        elif args.scalarize:
            from gambit_scalar_caller import inject as inject_scalar
            details = inject_scalar([module])
        else:
            details = inject([module], supplementary_pure_branches=not args.fresh,
                             supplementary_fresh_branches=args.fresh)
        if not args.hash_scan and not details['supplementaryPureTrees']:
            raise RuntimeError('fixture generated no supplementary tree')
        report['supplementaryPureTrees'] = details['supplementaryPureTrees']
        counters = '''
#include <stdio.h>
#include <stdlib.h>
static unsigned long gb_tree_entries,gb_tree_hits,gb_rollback_words;
static unsigned long gb_elided_words;
static unsigned long gb_structure_elided_words;
static unsigned long gb_hash_entries,gb_hash_selected,gb_hash_hits,gb_hash_misses;
#define GB_HASH_SCAN_ENTRY() (++gb_hash_entries)
#define GB_HASH_SCAN_SELECTED(slots) (++gb_hash_selected)
#define GB_HASH_SCAN_HIT() (++gb_hash_hits)
#define GB_HASH_SCAN_MISS() (++gb_hash_misses)
#define GB_PURE_TREE_ENTRY(site) (++gb_tree_entries)
#define GB_PURE_TREE_HIT(site) (++gb_tree_hits)
#define GB_FRESH_TREE_ROLLBACK(site,words) (gb_rollback_words+=(words))
#define GB_SCALAR_ELIDED_WORDS(words) do { gb_elided_words+=(words); if ((words)==4) gb_structure_elided_words+=(words); } while (0)
static void __attribute__((destructor)) gb_tree_dump(void) {
  const char *path=getenv("GAMBIT_PURE_TREE_COUNTER_FILE");
  if (path) { FILE *file=fopen(path,"w");
    if (file) { fprintf(file,"%lu %lu %lu\\n",gb_tree_entries,gb_tree_hits,gb_rollback_words); fclose(file); } }
  if (path) { char extra[4096];
    if (snprintf(extra,sizeof(extra),"%s.structure-elided-words",path)<sizeof(extra)) {
      FILE *file=fopen(extra,"w");
      if (file) { fprintf(file,"%lu\\n",gb_structure_elided_words); fclose(file); } } }
}
'''
        if args.scalarize:
            counters = counters.replace('"%lu %lu %lu\\n",gb_tree_entries,gb_tree_hits,gb_rollback_words',
                                        '"%lu %lu %lu %lu\\n",gb_tree_entries,gb_tree_hits,gb_rollback_words,gb_elided_words')
        extra_header = ''
        if args.hash_scan:
            counters = counters.replace('"%lu %lu %lu\\n",gb_tree_entries,gb_tree_hits,gb_rollback_words',
                                        '"%lu %lu %lu %lu\\n",gb_hash_entries,gb_hash_selected,gb_hash_hits,gb_hash_misses')
            extra_header = Path(__file__).with_name('gambit-small-hash-scan.h').read_text()
            report['hashScanHeaderSha256'] = hashlib.sha256(extra_header.encode()).hexdigest()
        candidate = candidate_dir / cfile.name
        generated = before+'___BEGIN_M_COD\n'+host_before+'___BEGIN_M_SW\n'+module['body']+ \
                    '___END_M_SW\n'+host_after+'___END_M_COD\n'+after
        header = '#include "gambit.h"\n'
        if generated.count(header) != 1:
            raise RuntimeError('fixture lacks unique Gambit header context')
        candidate.write_text(generated.replace(header, header+counters+PREAMBLE+extra_header, 1))
        for name, path in (('original', cfile), ('candidate', candidate)):
            obj = path.with_suffix('.o1')
            e = dict(env, BUILD_DYN_INPUT_FILENAMES_PARAM=str(path),
                     BUILD_DYN_OUTPUT_FILENAME_PARAM=str(obj), BUILD_DYN_CC_OPTIONS_PARAM='',
                     BUILD_DYN_LD_OPTIONS_PARAM='', BUILD_DYN_LD_OPTIONS_PRELUDE_PARAM='')
            run('compile-'+name, [str(home / 'bin/gambuild-C'), 'dyn'], e)
        def check(name, path):
            counters = output / (name+'-counts.txt')
            case = ('live hash values mutation GC rehash and large-table fallback' if args.hash_scan
                    else 'computed results mutation GC rebinding exceptions and values')
            expression = f'''(import :std/test :std/test/base)
(##load {json.dumps(str(path))} (lambda args #f) #t #t {json.dumps(path.stem)} #t)
(def suite (test-suite "pure branch trees"
  (test-case {json.dumps(case)}
    (check (##eval '(##gb-tree-run)) => #t))))
(def harness (TestHarness "pure trees"
  (TestConfig verbosity: VERBOSITY-CASE capture-output?: #f)
  (list (TestModule "native" (list suite) [] void void))))
(def result (test-run! harness))
(when (test-result-error? result) (error "pure tree native contract failed" result))
(displayln "PURE-TREE-NATIVE-OK") (force-output)'''
            e = dict(env, GERBIL_PATH=str(output / (name+'-user')),
                     GAMBIT_PURE_TREE_COUNTER_FILE=str(counters))
            run(name, [str(home / 'bin/gxi'), '-e', expression], e, 90)
            content = (output / (name+'.log')).read_text()
            markers = ('CASE-OK '+case,
                       'HARNESS-OK pure trees', 'PURE-TREE-NATIVE-OK')
            if not all(marker+'\n' in content for marker in markers):
                raise RuntimeError(name+' lacks explicit std/test and final success')
            row = dict(name=name, exitCode=0, finalSuccess=True)
            if name != 'baseline':
                values = counters.read_text().split()
                if args.hash_scan:
                    if len(values) != 4 or any(not value.isdecimal() for value in values):
                        raise RuntimeError(name+' lacks valid hash scan counters')
                    entries, selected, hits, misses = map(int, values)
                    if not entries > selected >= 512 or not hits or not misses or selected != hits+misses:
                        raise RuntimeError(name+' lacks actual hash scan and fallback coverage')
                    row.update(hashEntries=entries, hashSelected=selected, hashHits=hits, hashMisses=misses)
                    print('HASH-SCAN-CONTRACT-OK', name, flush=True)
                    return row
                if len(values) != (4 if args.scalarize else 3) or int(values[0]) < int(values[1]) or int(values[1]) < 512:
                    raise RuntimeError(name+' lacks actual tree hit coverage')
                row['treeEntries'], row['treeHits'], row['rollbackWords'] = map(int, values[:3])
                if args.scalarize:
                    row['elidedWords'] = int(values[3])
                    if row['elidedWords'] < 3*512:
                        raise RuntimeError(name+' lacks actual scalarized return coverage')
                if args.require_structure_elision:
                    value = counters.with_name(counters.name+'.structure-elided-words').read_text().strip()
                    if not value.isdecimal() or not 8 <= int(value) <= row['elidedWords']:
                        raise RuntimeError(name+' lacks actual four-word structure-elision coverage')
                    if not any(tree['maximumHeapWords'] == 0 and tree['minimumElidedWords'] == tree['maximumElidedWords'] == 4
                               for tree in report['supplementaryPureTrees']):
                        raise RuntimeError('fixture has no fully elided four-word structure tree')
                    row['fixtureStructureElidedWords'] = int(value)
                if args.fresh and not row['rollbackWords']:
                    raise RuntimeError(name+' lacks guard failure after real fresh allocation')
            print('PURE-TREE-CONTRACT-OK', name, flush=True)
            return row
        report['runs'].append(check('baseline', cfile.with_suffix('.o1')))
        with ThreadPoolExecutor(max_workers=cores) as pool:
            futures = [pool.submit(check, f'candidate-{index}', candidate.with_suffix('.o1'))
                       for index in range(cores)]
            for future in futures:
                report['runs'].append(future.result())
        report['qualified'] = True
    except BaseException as error:
        report['failure'] = str(error)
        raise
    finally:
        (output / 'report.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
