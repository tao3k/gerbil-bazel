"""Join validated native hardware PCs to exact debug-object line intervals."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import subprocess

from map_native_cpu_hotspots import host_address, relocations, text_bytes
from native_dwarf_lines import line_intervals, lookup_line
from summarize_native_cpu_profile import macho_functions
from experiment_framework.compiler import text_identity
from experiment_framework.context import FROZEN_47_SHA256
from native_object_manifest import digest


def matching_text_layout(left, right):
    fields = ('textSha256', 'canonicalRelocationSha256', 'textBytes',
              'relocations', 'cpuType', 'cpuSubtype')
    return all(left[field] == right[field] for field in fields)


def matching_image(summary, native):
    expected = {'uuid': native['uuid'], 'sha256': native['sha256']}
    matches = [path for path, identity in summary['images'].items() if identity == expected]
    if len(matches) != 1 or hashlib.sha256(Path(matches[0]).read_bytes()).hexdigest() != native['sha256']:
        raise ValueError('one byte-identical actual profile image required')
    return matches[0]


def main():
    parser = argparse.ArgumentParser()
    runtime = parser.add_mutually_exclusive_group(required=True)
    runtime.add_argument('--baseline', type=Path)
    runtime.add_argument('--flat-binary', type=Path)
    parser.add_argument('--carrier-source', type=Path)
    parser.add_argument('--carrier-object', type=Path)
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--mapping', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source-proof', type=Path)
    parser.add_argument('--function', choices=('gb_coalesced_host',
        '___H_gerbil____expander____core', '___H_gerbil____expander____stx'), required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    profile, mapping, output = (p.resolve() for p in
                               (args.profile, args.mapping, args.output))
    inputs = [profile, mapping, output]
    inputs.extend(p.resolve() for p in (args.baseline, args.flat_binary,
                                       args.carrier_source, args.carrier_object) if p)
    if not all(p.is_relative_to(root / '.data') for p in inputs):
        parser.error('native diagnostic inputs and outputs must remain under .data')
    report = json.loads((mapping / 'report.json').read_text())
    summary = json.loads((profile / 'cpu-summary.json').read_text())
    sidecar = (args.flat_binary is not None and report.get('scope') ==
               'original-gnu-compiler-frame-diagnostic-not-runtime-admission')
    if ((not sidecar and report.get('qualified') is not True)
            or report.get('diagnosticOnly') is not True):
        parser.error('successful exact-code native mapping required')
    baseline = args.baseline.resolve() if args.baseline else None
    binary = args.flat_binary.resolve() if args.flat_binary else baseline / 'build/bin/gerbil'
    native = macho_functions(binary)
    recorded_image = matching_image(summary, native)
    if args.flat_binary:
        if (args.function != 'gb_coalesced_host' or not args.carrier_source
                or not args.carrier_object or native['sha256'] != FROZEN_47_SHA256):
            parser.error('flat mode requires the frozen host and explicit carrier source/object')
        source, original = args.carrier_source.resolve(), args.carrier_object.resolve()
        if sidecar:
            if report.get('exitCode') != 0 or report.get('inputsUnchanged') is not True:
                parser.error('completed original compiler execution required')
            for path, expected_hash in report['inputHashes'].items():
                target = (root / path).resolve()
                if not target.is_relative_to(root / '.data') or digest(target) != expected_hash:
                    parser.error('debug sidecar input identity changed')
            obj = mapping / 'diagnostic.o'
            if digest(obj) != report['artifacts']['diagnostic.o']:
                parser.error('debug sidecar object changed')
            expected_source_digest = report['inputHashes'].get(str(source.relative_to(root)))
            if expected_source_digest is None or digest(original) not in report['inputHashes'].values():
                parser.error('explicit carrier is not the recorded original source/object')
        else:
            obj = mapping / 'carrier-debug.o'
            expected_source_digest = report['sourceSha256']
        unit = report
    elif args.function == 'gb_coalesced_host':
        stem, source = 'coalesced-link', baseline.parent / 'gerbil-link.c'
    else:
        stem = args.function.removeprefix('___H_').replace('____', '__')
        source = baseline / 'build/lib/static' / (stem+'.c')
    if not args.flat_binary:
        if args.carrier_source or args.carrier_object:
            parser.error('explicit carrier inputs require flat mode')
        units = [unit for unit in report['units'] if unit['module'] == stem]
        if len(units) != 1:
            parser.error('mapping has no unique requested native unit')
        unit = units[0]
        original, obj = source.with_suffix('.o'), mapping / (stem+'-debug.o')
        expected_source_digest = unit.get('generatedCSha256')
    source_digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if expected_source_digest is None:
        if not args.source_proof:
            parser.error('older mapping requires an existing source/object hash receipt')
        proof_path = args.source_proof.resolve()
        if not proof_path.is_relative_to(root / '.data'):
            parser.error('source proof must remain under .data')
        proof = json.loads(proof_path.read_text())
        records = [row for row in proof.get('objects', [])
                   if row.get('module') == stem.replace('__', '/')]
        if (proof.get('qualified') is not True or len(records) != 1
                or records[0].get('reusedOriginalObject') is not True
                or records[0].get('objectSha256') != hashlib.sha256(original.read_bytes()).hexdigest()):
            parser.error('original object/source proof failed')
        expected_source_digest = records[0].get('generatedCSha256')
    if expected_source_digest != source_digest:
        parser.error('generated source changed since exact debug mapping')
    old_identity, new_identity = text_identity(original), text_identity(obj)
    if not matching_text_layout(old_identity, new_identity):
        parser.error('symbol-resolved native relocation identity failed')
    if not sidecar:
        old, new = text_bytes(original), text_bytes(obj)
        if (unit.get('textIdentical') is not True or unit.get('relocationsIdentical') is not True
                or hashlib.sha256(old).hexdigest() != unit['originalTextSha256']
                or hashlib.sha256(new).hexdigest() != unit['debugTextSha256']
                or old != new or relocations(original) != relocations(obj)):
            parser.error('native text/relocation identity no longer holds')
    starts = [start for start, names in native['names'].items() if args.function in names]
    if len(starts) != 1:
        parser.error('native host start is not unique')
    object_begin = host_address(obj, args.function)
    dump = subprocess.check_output(['xcrun', 'dwarfdump', '--debug-line', str(obj)], text=True, timeout=60)
    ranges, files = line_intervals(dump)
    range_starts = [row[0] for row in ranges]
    rows = [row for row in summary['nativePCs'] if row['function'] == args.function]
    total = sum(row['cycles'] for row in rows)
    expected = [row['cycles'] for row in summary['selfCycles'] if row['function'] == args.function]
    if len(expected) != 1 or total != expected[0]:
        parser.error('complete native PC weights do not match function self cycles')
    counts, unmapped = collections.Counter(), 0
    for row in rows:
        address = object_begin+int(row['unslidPC'], 16)-starts[0]
        line = lookup_line(ranges, range_starts, address)
        if line is None:
            unmapped += row['cycles']
        else:
            counts[line] += row['cycles']
    lines, groups, source_files = [], collections.Counter(), {}
    for (file_index, number), weight in counts.most_common():
        directory, name = files[file_index]
        path = (Path(directory) / name).resolve()
        code = None
        if (path.is_relative_to(root / '.data') and path.is_file()
                and (not args.flat_binary or path == source)):
            if path not in source_files:
                data = path.read_bytes()
                source_files[path] = (data.decode().splitlines(), hashlib.sha256(data).hexdigest())
            content, _ = source_files[path]
            if not 1 <= number <= len(content):
                raise ValueError('DWARF line exceeds current source bounds')
            code = content[number-1].strip()
        macro = re.search(r'\b(___[A-Z][A-Z0-9_]+|GB_[A-Z][A-Z0-9_]+)\b', code or '')
        category = macro[1] if macro else 'OTHER_OR_UNKNOWN_SOURCE'
        groups[category] += weight
        lines.append(dict(file=name, line=number, code=code, cycles=weight,
                          percentOfHost=weight/total*100, firstMacro=category))
    output.mkdir(parents=True, exist_ok=False)
    (output / 'debug-line.txt').write_text(dump)
    result = dict(qualified=True, performanceQualified=False,
                  scope='compiler-assigned-native-line-self-cycle-weights-not-GVM-procedure-costs',
                  function=args.function, totalHostCycles=total, unmappedCycles=unmapped,
                  distinctPCs=len(rows), sourceLines=lines,
                  recordedImage=recorded_image, runtimeSha256=native['sha256'],
                  mappingReceiptSha256=digest(mapping / 'report.json'),
                  textIdentity=old_identity,
                  sourceHashes={str(path): value[1] for path, value in source_files.items()},
                  firstMacroCycleWeights=dict(groups.most_common()))
    (output / 'report.json').write_text(json.dumps(result, indent=2)+'\n')
    print('NATIVE-LINE-CYCLES', args.function, len(rows), 'PCs', unmapped, 'unmapped cycles')
    for category, weight in groups.most_common(15):
        print(f'{weight/total*100:.2f}% {category}')


if __name__ == '__main__':
    main()
