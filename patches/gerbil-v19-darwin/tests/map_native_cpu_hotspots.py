"""Map native hardware PCs through byte-identical debug objects, not GVM labels."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import time

from bazel_host_environment import build_environment
from summarize_native_cpu_profile import classify_native_pc, macho_functions


def crash_pc(path, native):
    content = path.read_text()
    decoder, records = json.JSONDecoder(), []
    while content.strip():
        record, end = decoder.raw_decode(content.lstrip())
        records.append(record)
        content = content.lstrip()[end:]
    bodies = [record for record in records if 'threads' in record]
    if len(bodies) != 1:
        raise ValueError('unique native crash body required')
    body = bodies[0]
    thread = body['threads'][body['faultingThread']]
    frame = thread['frames'][0]
    image = body['usedImages'][frame['imageIndex']]
    if (image['uuid'].lower() != native['uuid'].lower() or image['arch'] != 'arm64'
            or thread['threadState']['flavor'] != 'ARM_THREAD_STATE64'
            or body['exception']['signal'] != 'SIGSEGV'):
        raise ValueError('crash image or native exception does not match retained binary')
    offset = frame['imageOffset']
    if not 0 <= offset < image['size'] or image['base']+offset != thread['threadState']['pc']['value']:
        raise ValueError('crash PC does not match image frame offset')
    pc = native['textBase']+offset
    name, kind = classify_native_pc(native, pc, frame['symbol'])
    if kind != 'validatedNativeCycles':
        raise ValueError('crash PC is not in the named actual native function')
    return dict(function=name, unslidPC=hex(pc), source='native-crash-not-hardware-cycles')


def retained_link_budget(runtime, binary_digest, source_size):
    budget = runtime.get('compileWallBudgetSeconds')
    if (runtime.get('qualified') is not True or runtime.get('diagnosticOnly') is not False
            or runtime.get('consumerFlagsChanged') is not False
            or runtime.get('runtimeAbiChanged') is not False
            or runtime.get('gscUnchanged') is not True
            or runtime.get('binaryHashes', {}).get('gxi') != binary_digest
            or runtime.get('coalescedLinkBytes') != source_size
            or type(budget) is not int or not 300 <= budget <= 1200):
        raise ValueError('qualified matching link build and bounded original budget required')
    return budget


def text_bytes(path):
    dump = subprocess.check_output(['otool', '-s', '__TEXT', '__text', str(path)], text=True)
    return b''.join(bytes.fromhex(''.join(line.split()[1:]))
                    for line in dump.splitlines()[2:])


def relocations(path):
    dump = subprocess.check_output(['xcrun', 'llvm-objdump', '--reloc', str(path)], text=True)
    lines = dump.splitlines()
    start = lines.index('RELOCATION RECORDS FOR [__text]:')
    records = []
    for line in lines[start+1:]:
        if not line.strip():
            break
        records.append(line.strip())
    return records


def host_address(path, name):
    symbols = subprocess.check_output(['nm', '-n', str(path)], text=True)
    rows = [line.split() for line in symbols.splitlines()]
    matches = [row for row in rows if len(row) == 3 and row[-1] == '_'+name]
    if len(matches) != 1:
        raise ValueError('native host is not unique')
    return int(matches[0][0], 16)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    evidence = parser.add_mutually_exclusive_group(required=True)
    evidence.add_argument('--profile', type=Path)
    evidence.add_argument('--crash-report', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--link-source', type=Path)
    parser.add_argument('--minimal-debug', action='store_true')
    parser.add_argument('--build-receipt', type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[3]
    baseline, output = (p.resolve() for p in (args.baseline, args.output))
    profile = args.profile.resolve() if args.profile else None
    if platform.system() != 'Darwin' or not all(p.is_relative_to(repo / '.data')
                                               for p in (baseline, output, *([profile] if profile else []))):
        parser.error('isolated Darwin original objects and CPU evidence under .data required')
    binary = baseline / 'build/bin/gerbil'
    native = macho_functions(binary)
    if profile:
        summary = json.loads((profile / 'cpu-summary.json').read_text())
        if summary['images'][str(binary)] != {'uuid': native['uuid'], 'sha256': native['sha256']}:
            raise ValueError('hardware profile does not match original binary')
        native_pcs = summary['hotNativePCs']
    else:
        native_pcs = [crash_pc(args.crash_report, native)]
    link_source = args.link_source.resolve() if args.link_source else None
    if link_source and not link_source.is_relative_to(repo / '.data'):
        parser.error('existing native link source must remain under .data')
    budget, build_receipt = 180, None
    if link_source:
        if not args.build_receipt:
            parser.error('coalesced diagnostic requires its successful original build receipt')
        build_receipt = args.build_receipt.resolve()
        if (not build_receipt.is_relative_to(repo / '.data')
                or link_source != build_receipt.parent / 'gerbil-link.c'
                or baseline != build_receipt.parent / 'source'):
            parser.error('coalesced source and home must belong to the retained build')
        runtime = json.loads(build_receipt.read_text())
        budget = retained_link_budget(runtime, native['sha256'], link_source.stat().st_size)
        if runtime['binaryHashes'].get('gsc') != hashlib.sha256(
                (baseline / 'build/bin/gsc').read_bytes()).hexdigest():
            parser.error('original compiler changed since successful build')
    elif args.build_receipt:
        parser.error('build budget receipt is only for its original coalesced link')
    output.mkdir(parents=True, exist_ok=False)
    env = build_environment()
    macros = subprocess.check_output([env['CC'], '-dM', '-E', '-x', 'c', os.devnull],
                                    env=env, text=True)
    if '#define __clang__' in macros or '#define __GNUC__ 16\n' not in macros:
        raise ValueError('real GNU GCC 16 required')
    debug_flag = '-g1' if args.minimal_debug else '-g'
    report = dict(qualified=False, performanceQualified=False, diagnosticOnly=True,
                  debugFlag=debug_flag, compileWallBudgetSeconds=budget, units=[])
    report['pcEvidence'] = 'hardware-profile' if profile else 'native-crash'
    if build_receipt:
        report['buildReceiptSha256'] = hashlib.sha256(build_receipt.read_bytes()).hexdigest()
    try:
        specs = [('gerbil__expander__core', '___H_gerbil____expander____core'),
                 ('gerbil__expander__stx', '___H_gerbil____expander____stx')]
        if link_source:
            specs = [('coalesced-link', 'gb_coalesced_host')]
        for stem, name in specs:
            source = link_source or baseline / 'build/lib/static' / (stem+'.c')
            original = source.with_suffix('.o')
            obj = output / (stem+'-debug.o')
            source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
            e = dict(env, GAMBITDIR_INCLUDE=str(baseline / 'build/include'),
                     GAMBITDIR_LIB=str(baseline / 'build/lib'),
                     BUILD_OBJ_INPUT_FILENAMES_PARAM=str(source),
                     BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(obj),
                     BUILD_OBJ_META_INFO_FILE_PARAM=str(source),
                     BUILD_OBJ_CC_OPTIONS_PARAM=f'-O1 {debug_flag} -fno-var-tracking -fno-var-tracking-assignments')
            started = time.monotonic()
            with (output / (stem+'-compile.log')).open('w') as log:
                child = subprocess.Popen([str(baseline / 'build/bin/gambuild-C'), 'obj'],
                                         env=e, stdout=log, stderr=subprocess.STDOUT,
                                         start_new_session=True)
                try:
                    code = child.wait(timeout=budget)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait()
                    raise RuntimeError('debug-only object compile exceeded its bounded budget')
            if code or hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
                raise ValueError('debug compilation failed or original source drifted')
            old, new = text_bytes(original), text_bytes(obj)
            unit = dict(module=stem, compileSeconds=time.monotonic()-started,
                        generatedCSha256=source_hash,
                        originalTextSha256=hashlib.sha256(old).hexdigest(),
                        debugTextSha256=hashlib.sha256(new).hexdigest(),
                        textIdentical=old == new,
                        relocationsIdentical=relocations(original) == relocations(obj), lookups=[])
            report['units'].append(unit)
            if not unit['textIdentical'] or not unit['relocationsIdentical']:
                raise ValueError('debug object is not identical executable code')
            starts = [address for address, names in native['names'].items() if name in names]
            if len(starts) != 1:
                raise ValueError('native image host metadata is ambiguous')
            object_begin = host_address(obj, name)
            rows = [row for row in native_pcs if row['function'] == name
                    and int(row['unslidPC'], 16)-starts[0] >= 64]
            for index, row in enumerate(rows[:12]):
                offset = int(row['unslidPC'], 16)-starts[0]
                address = object_begin+offset
                result = subprocess.run(['xcrun', 'dwarfdump', '--lookup', hex(address), str(obj)],
                                        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        timeout=30)
                lookup = output / (stem+f'-lookup-{index}.log')
                lookup.write_text(result.stdout)
                unit['lookups'].append(dict(offset=offset, cycles=row.get('cycles'),
                                            lookup=lookup.name, exitCode=result.returncode,
                                            lineInfo='Line info' in result.stdout))
                if result.returncode or 'Line info' not in result.stdout:
                    raise ValueError('exact native PC has no qualified DWARF line')
            if not rows:
                raise ValueError('no body hot PCs available for native host')
            print('EXACT-NATIVE-MAP', stem, len(unit['lookups']), 'body PCs', flush=True)
        report['qualified'] = True
    except Exception as error:
        report['failure'] = str(error)
        raise
    finally:
        (output / 'report.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
