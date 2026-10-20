"""Check the retained GNU preprocessor branch, not register allocation speed."""
import argparse
import json
import re
import subprocess
from pathlib import Path

from bazel_host_environment import build_environment
from native_object_manifest import digest


def audit_field_addressing(root, output):
    from experiment_framework.process import record
    from experiment_framework.context import retained_47
    retained_47(root)
    home = root / '.data/d1391-runtime-object-source/build'
    source = Path(__file__).with_name('typed_field_addressing.c')
    header = home / 'include/gambit.h'
    env = build_environment()
    inputs = {str(p.relative_to(root)): digest(p) for p in (source, header)}
    output.mkdir()
    report = dict(scope='original-gnu-typed-field-addressing-not-performance',
                  qualified=False, performanceQualified=False, productionAdmitted=False,
                  inputHashes=inputs)
    try:
        obj, executable = output / 'fields.o', output / 'fields'
        report['compileExitCode'] = record([env['CC'], '-O1', '-ftrack-macro-expansion=0',
            '-I' + str(home / 'include'), '-c', str(source), '-o', str(obj)],
            root, env, output / 'compile.log', timeout=30)
        if report['compileExitCode']:
            return 1
        report['linkExitCode'] = record([env['CC'], str(obj), '-o', str(executable)],
            root, env, output / 'link.log', timeout=30)
        if report['linkExitCode']:
            return 1
        report['runExitCode'] = record([str(executable)], root, env, output / 'run.log', timeout=5)
        disassembly = subprocess.check_output(['xcrun', 'llvm-objdump', '--disassemble', str(obj)],
                                             text=True, timeout=30)
        (output / 'disassembly.txt').write_text(disassembly)
        report['inputsUnchanged'] = all(digest(root / p) == sha for p, sha in inputs.items())
        report['qualified'] = (report['runExitCode'] == 0 and
            (output / 'run.log').read_text().splitlines() == ['FIELD-ADDRESSING-OK 6'] and
            report['inputsUnchanged'])
        report['objectSha256'] = digest(obj)
        return 0 if report['qualified'] else 1
    finally:
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report))


def selected_macros(text):
    definitions = dict(re.findall(r'^#define (\w+) ([^\n]*)$', text, re.M))
    names = ('__GNUC__', '__APPLE__', '___MAX_LOCAL_GVM_REGS',
             '___NB_GVM_REGS', '___NB_ARG_REGS', '___R0', '___R1', '___R2',
             '___D_R1', '___R_R1', '___W_R1')
    result = {name: definitions.get(name) for name in names}
    if '__clang__' in definitions or result['__GNUC__'] != '16' or not result['__APPLE__']:
        raise ValueError('Darwin GNU GCC 16 branch required')
    if result['___R1'] != '___r1' or result['___MAX_LOCAL_GVM_REGS'] != '25':
        raise ValueError('unexpected retained register-layout branch')
    return result


def selected_control_transfer(text):
    selected_macros(text)
    definitions = dict(re.findall(
        r'^#define (\w+(?:\([^\n]*?\))?)[ \t]*([^\n]*)$', text, re.M))
    expected = {
        '___USE_TAIL_CALL_TO_EXIT_HOST': '',
        '___USE_PROPER_TAIL_CALL_EXCLUSIVELY_TO_EXIT_HOST': '',
        '___TRUST_C_TCO': '1',
        '___EXIT_HOST()': '___TAIL_CALL_VOID(___CALL_LABEL_HOST(___pc,___ps))',
        '___TAIL_CALL_VOID(call)': '___PROPER_TAIL_CALL(call)',
        '___PROPER_TAIL_CALL(call)': '__attribute__((musttail)) return call',
    }
    if any(definitions.get(name) != value for name, value in expected.items()):
        raise ValueError('unexpected retained host-exit branch')
    if '___USE_UNWIND_C_STACK_TO_TRAMPOLINE' in definitions:
        raise ValueError('unexpected trampoline unwind branch')
    return expected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--existing-preprocessor', type=Path,
                        help='audit saved transcripts without invoking GCC')
    parser.add_argument('--field-addressing', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(root / '.data'):
        parser.error('fresh persistent .data output required')
    if args.field_addressing:
        if args.existing_preprocessor:
            parser.error('field addressing requires its own original-header audit')
        return audit_field_addressing(root, output)
    home = root / '.data/d1391-runtime-object-source/build'
    capture = root / '.data/d1510-provider-extension-objects-v1'
    receipt = json.loads((capture / 'report.json').read_text())
    frozen = root / '.data/d1510-reader-whitespace-native-v2/gerbil'
    expected = '1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21'
    if not receipt['qualified'] or digest(frozen) != expected:
        raise ValueError('retained identity mismatch')
    for path, sha in receipt['inputHashes'].items():
        if digest(home / path) != sha:
            raise ValueError('original capture input changed: ' + path)
    existing = args.existing_preprocessor
    if existing is not None:
        existing = existing.resolve()
        if not existing.is_relative_to(root / '.data'):
            parser.error('existing transcripts must be in persistent .data')
        prior = json.loads((existing / 'report.json').read_text())
        if not prior['qualified'] or not prior['originalInputsUnchanged']:
            raise ValueError('unqualified original preprocessor audit')
    env = None if existing is not None else build_environment()
    output.mkdir()
    rows = []
    for index, item in zip((3, 668, 669), receipt['runs'], strict=True):
        source = capture / str(index) / 'module.c'
        if digest(source) != item['generatedCSha256'] or not item['nativeTextByteExact']:
            raise ValueError('captured C identity mismatch')
        flags = ['-D___SINGLE_HOST', '-D___INLINE_JUMPS', '-D___TRUST_C_TCO',
                 '-D___CAN_IMPORT_CLIB_DYNAMICALLY', '-D___CAN_IMPORT_SETJMP_DYNAMICALLY',
                 '-D___DYNAMIC', '-I' + str(home / 'include')]
        if item['module'].startswith('std/'):
            flags.append('-g')
        if existing is None:
            command = [env['CC'], '-ftrack-macro-expansion=0', *flags, '-dM', '-E', str(source)]
            result = subprocess.run(command, env=env, capture_output=True, text=True,
                                    check=True, timeout=30)
            text = result.stdout
            (output / (str(index) + '.macros.txt')).write_text(text)
        else:
            text = (existing / (str(index) + '.macros.txt')).read_text()
            old = prior['rows'][len(rows)]
            if (old['module'] != item['module'] or
                    old['generatedCSha256'] != digest(source) or
                    old['selectedMacros'] != selected_macros(text)):
                raise ValueError('saved transcript/capture mismatch')
        rows.append(dict(module=item['module'], generatedCSha256=digest(source),
                         selectedMacros=selected_macros(text),
                         **({'selectedControlTransfer': selected_control_transfer(text),
                             'transcriptSha256': digest(existing / (str(index) + '.macros.txt'))}
                            if existing is not None else {})))
    unchanged = digest(frozen) == expected and all(
        digest(home / path) == sha for path, sha in receipt['inputHashes'].items())
    report = dict(scope='preprocessor-register-representation-not-machine-spills',
                  qualified=unchanged, originalInputsUnchanged=unchanged,
                  performanceQualified=False, productionAdmitted=False, rows=rows)
    if existing is not None:
        report['scope'] = 'saved-preprocessor-host-exit-not-execution-speed'
        report['compilerInvoked'] = False
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, separators=(',', ':')))
    return 0 if unchanged else 1


if __name__ == '__main__':
    raise SystemExit(main())
