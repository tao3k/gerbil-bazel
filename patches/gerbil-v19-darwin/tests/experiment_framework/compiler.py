"""GNU diagnostic object compilation without changing runtime inputs."""
import argparse
import json
from pathlib import Path
import subprocess
import struct
import hashlib

from bazel_host_environment import build_environment
from native_object_manifest import digest
from experiment_framework.context import data_path
from experiment_framework.process import record


def text_identity(path, *, include_relocations=False):
    data = path.read_bytes()
    if len(data) < 32 or struct.unpack_from('<I', data)[0] != 0xFEEDFACF:
        raise ValueError('thin little-endian Mach-O object required')
    if struct.unpack_from('<I', data, 12)[0] != 1:
        raise ValueError('relocatable Mach-O object required')
    cursor = 32
    result = None
    sections = []
    symbols = None
    relocation_data = None
    for _ in range(struct.unpack_from('<I', data, 16)[0]):
        if cursor + 8 > len(data):
            raise ValueError('complete object load command required')
        kind, size = struct.unpack_from('<II', data, cursor)
        if size < 8 or cursor + size > len(data):
            raise ValueError('invalid object load command')
        if kind == 0x19:
            if size < 72:
                raise ValueError('complete segment command required')
            count = struct.unpack_from('<I', data, cursor + 64)[0]
            if 72 + count * 80 > size:
                raise ValueError('complete object section table required')
            for index in range(count):
                start = cursor + 72 + index * 80
                name = data[start:start + 16].split(b'\0')[0]
                segment = data[start + 16:start + 32].split(b'\0')[0]
                address = struct.unpack_from('<Q', data, start + 32)[0]
                sections.append((segment.decode(), name.decode(), address))
                if (segment, name) != (b'__TEXT', b'__text'):
                    continue
                length = struct.unpack_from('<Q', data, start + 40)[0]
                offset = struct.unpack_from('<I', data, start + 48)[0]
                reloc, reloc_count = struct.unpack_from('<II', data, start + 56)
                if result is not None or not length or offset + length > len(data) or reloc + reloc_count * 8 > len(data):
                    raise ValueError('one complete nonempty text and relocation table required')
                relocation_data = data[reloc:reloc + reloc_count * 8]
                result = dict(textSha256=hashlib.sha256(data[offset:offset + length]).hexdigest(),
                              relocationSha256=hashlib.sha256(data[reloc:reloc + reloc_count * 8]).hexdigest(),
                              textBytes=length, relocations=reloc_count,
                              cpuType=struct.unpack_from('<I', data, 4)[0],
                              cpuSubtype=struct.unpack_from('<I', data, 8)[0])
        elif kind == 2:
            if size != 24 or symbols is not None:
                raise ValueError('one valid object symbol table required')
            symbols = struct.unpack_from('<IIII', data, cursor + 8)
        cursor += size
    if result is None:
        raise ValueError('native object text required')
    canonical = []
    for offset in range(0, len(relocation_data), 8):
        address, bits = struct.unpack_from('<iI', relocation_data, offset)
        number, external, kind = bits & 0xFFFFFF, (bits >> 27) & 1, bits >> 28
        if not 0 <= address < result['textBytes']:
            raise ValueError('unscattered native relocation required')
        if result['cpuType'] == 0x100000C and kind == 10:
            target = ('arm64-addend', number)
        elif external:
            if symbols is None:
                raise ValueError('external relocation symbol table required')
            symoff, count, stroff, strsize = symbols
            if number >= count or symoff + count * 16 > len(data) or stroff + strsize > len(data):
                raise ValueError('complete relocation symbol metadata required')
            string, symkind, section, desc, value = struct.unpack_from('<IBBHQ', data, symoff + number * 16)
            if string >= strsize or section > len(sections):
                raise ValueError('valid referenced symbol and section required')
            end = data.find(b'\0', stroff + string, stroff + strsize)
            if end < 0:
                raise ValueError('terminated referenced symbol required')
            section_id = sections[section - 1][:2] if section else None
            relative_value = value - sections[section - 1][2] if section else value
            target = (data[stroff + string:end].decode(), symkind, section_id, desc, relative_value)
        else:
            if number > len(sections):
                raise ValueError('valid local relocation section required')
            target = sections[number - 1][:2] if number else ('absolute',)
        canonical.append((address, (bits >> 24) & 1, (bits >> 25) & 3, external, kind, target))
    result['canonicalRelocationSha256'] = hashlib.sha256(
        json.dumps(canonical, separators=(',', ':')).encode()).hexdigest()
    if include_relocations:
        result['relocationRecords'] = canonical
    return result


def diagnostic_environment(base, home, source, output, source_lines=False, frame_dumps=True):
    env = dict(base)
    env.update(GAMBITDIR_INCLUDE=str(home / 'include'), GAMBITDIR_LIB=str(home / 'lib'),
               BUILD_OBJ_INPUT_FILENAMES_PARAM=str(source),
               BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(output / 'diagnostic.o'),
               BUILD_OBJ_META_INFO_FILE_PARAM=str(source),
               BUILD_OBJ_CC_OPTIONS_PARAM='-O1')
    if frame_dumps:
        env['BUILD_OBJ_CC_OPTIONS_PARAM'] += (' -fstack-usage -fdump-rtl-expand '
                                             '-fdump-rtl-pro_and_epilogue')
    if source_lines:
        env['BUILD_OBJ_CC_OPTIONS_PARAM'] += ' -g1'
    return env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--reference-object', type=Path, required=True)
    parser.add_argument('--home', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--shared-parameter-result', action='store_true',
                        help='private activation-local parameter-result storage candidate')
    parser.add_argument('--source-lines', action='store_true',
                        help='GNU debug sidecar; text/relocation identity required before attribution')
    parser.add_argument('--allocation-sites', action='store_true',
                        help='original generated heap-word census, never performance admission')
    args = parser.parse_args()
    if args.allocation_sites and (args.source_lines or args.shared_parameter_result):
        parser.error('allocation census excludes other source transformations')
    if args.source_lines and args.shared_parameter_result:
        parser.error('source attribution must use unchanged original source')
    root = Path(__file__).resolve().parents[4]
    source = data_path(root, args.source)
    reference = data_path(root, args.reference_object)
    home = data_path(root, args.home)
    output = data_path(root, args.output, fresh=True)
    driver = home / 'bin/gambuild-C'
    env = build_environment()
    compiler = subprocess.check_output([str(driver), 'C_COMPILER'], env=env, text=True).strip()
    if 'gcc' not in compiler or 'clang' in compiler.lower():
        raise ValueError('original GNU GCC driver required')
    inputs = {str(p.relative_to(root)): digest(p) for p in (source, reference, driver)}
    output.mkdir()
    report = dict(scope='original-gnu-compiler-frame-diagnostic-not-runtime-admission',
                  diagnosticOnly=True, performanceQualified=False, productionAdmitted=False,
                  inputHashes=inputs, compiler=compiler, completed=False)
    try:
        compile_source = source
        if args.allocation_sites:
            control = output / 'control'
            control.mkdir()
            control_env = diagnostic_environment(env, home, source, control, frame_dumps=False)
            try:
                report['controlExitCode'] = record([str(driver), 'obj'], root, control_env,
                    control / 'compiler.log', timeout=300, termination_grace=2)
            except subprocess.TimeoutExpired:
                report['stopReason'] = 'control-construction-timeout-300s'
                return 1
            report['controlMatchesReference'] = (report['controlExitCode'] == 0 and
                digest(control / 'diagnostic.o') == digest(reference))
            if not report['controlMatchesReference']:
                return 1
            from gambit_allocation_sites import instrument
            compile_source = output / 'carrier.c'
            compile_source.write_text(instrument(source.read_text()))
            report['candidate'] = 'original-carrier-physical-allocation-census'
        if args.shared_parameter_result:
            from gambit_parameter_entry import share_result_storage
            compile_source = output / 'carrier.c'
            compile_source.write_text(share_result_storage(source.read_text()))
            report['candidate'] = 'guarded-activation-local-parameter-result'
        compile_env = diagnostic_environment(env, home, compile_source, output,
            args.source_lines, frame_dumps=not args.allocation_sites)
        report['compileOptions'] = compile_env['BUILD_OBJ_CC_OPTIONS_PARAM']
        try:
            report['exitCode'] = record([str(driver), 'obj'], root, compile_env,
                output / 'compiler.log', timeout=300, termination_grace=2)
        except subprocess.TimeoutExpired:
            report['stopReason'] = 'construction-timeout-300s'
            return 1
        if report['exitCode'] != 0:
            return 1
        report['inputsUnchanged'] = all(digest(root / p) == sha for p, sha in inputs.items())
        report['objectMatchesReference'] = digest(output / 'diagnostic.o') == digest(reference)
        if args.source_lines:
            report['referenceText'] = text_identity(reference)
            report['diagnosticText'] = text_identity(output / 'diagnostic.o')
            report['textAndRelocationsMatch'] = {
                key: value for key, value in report['referenceText'].items()
                if key != 'relocationSha256'} == {
                key: value for key, value in report['diagnosticText'].items()
                if key != 'relocationSha256'}
        report['artifacts'] = {p.name: digest(p) for p in output.iterdir() if p.is_file()}
        report['completed'] = report['inputsUnchanged'] and (
            not args.source_lines or report['textAndRelocationsMatch'])
        return 0 if report['completed'] else 1
    finally:
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({k: v for k, v in report.items() if k != 'inputHashes'}), flush=True)
