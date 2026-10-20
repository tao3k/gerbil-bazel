"""Aggregate running hardware samples; validate native functions, never GVM label proximity."""
import argparse
import bisect
import collections
import hashlib
import json
from pathlib import Path
import struct
import uuid
import xml.etree.ElementTree as ET


def macho_functions(path):
    data = path.read_bytes()
    magic, _, _, _, ncmds, _, _, _ = struct.unpack_from('<8I', data)
    if magic != 0xFEEDFACF:
        raise ValueError('thin little-endian Mach-O required')
    cursor, sections, text_base, text_range = 32, [], None, None
    executable_sections = []
    function_data = symbols = image_uuid = None
    for _ in range(ncmds):
        kind, size = struct.unpack_from('<II', data, cursor)
        if size < 8 or cursor + size > len(data):
            raise ValueError('invalid Mach-O load command')
        if kind == 0x19:
            segment = data[cursor+8:cursor+24].split(b'\0')[0]
            if segment == b'__TEXT':
                text_base = struct.unpack_from('<Q', data, cursor+24)[0]
            count = struct.unpack_from('<I', data, cursor+64)[0]
            for index in range(count):
                start = cursor + 72 + index * 80
                name = data[start:start+16].split(b'\0')[0]
                address, length = struct.unpack_from('<QQ', data, start+32)
                flags = struct.unpack_from('<I', data, start+64)[0]
                sections.append((segment, name))
                if segment == b'__TEXT' and flags & (0x80000000 | 0x400):
                    executable_sections.append((address, address+length, name.decode()))
                if segment == b'__TEXT' and name == b'__text':
                    text_range = (address, address+length, len(sections))
        elif kind == 0x1B:
            image_uuid = str(uuid.UUID(bytes=data[cursor+8:cursor+24])).upper()
        elif kind == 0x26:
            function_data = struct.unpack_from('<II', data, cursor+8)
        elif kind == 0x2:
            symbols = struct.unpack_from('<IIII', data, cursor+8)
        cursor += size
    if None in (text_base, text_range, function_data, symbols, image_uuid):
        raise ValueError('actual UUID/text/function-start/symbol metadata required')
    offset, length = function_data
    starts, relative, value, shift = [], 0, 0, 0
    for byte in data[offset:offset+length]:
        value |= (byte & 127) << shift
        if byte & 128:
            shift += 7
            continue
        if not value:
            break
        relative += value
        address = text_base + relative
        if text_range[0] <= address < text_range[1]:
            starts.append(address)
        value, shift = 0, 0
    if not starts:
        raise ValueError('no actual native function starts')
    symoff, count, stroff, strsize = symbols
    names = collections.defaultdict(set)
    start_set = set(starts)
    for index in range(count):
        string_index, kind, section, _, address = struct.unpack_from('<IBBHQ', data, symoff+index*16)
        if kind & 0xE0 or kind & 0x0E != 0x0E or section != text_range[2] or address not in start_set:
            continue
        if string_index >= strsize:
            raise ValueError('invalid native symbol string index')
        end = data.index(b'\0', stroff+string_index, stroff+strsize)
        name = data[stroff+string_index:end].decode()
        names[address].add(name[1:] if name.startswith('_') else name)
    return dict(uuid=image_uuid, textBase=text_base, textStart=text_range[0],
                textEnd=text_range[1], starts=starts, names=names,
                executableSections=executable_sections,
                sha256=hashlib.sha256(data).hexdigest())


def classify_native_pc(native, pc, name):
    if not native['textStart'] <= pc < native['textEnd']:
        for start, end, section in native['executableSections']:
            if start <= pc < end:
                return f'NATIVE_SECTION:{section}', 'nonFunctionNativeCycles'
        return 'UNKNOWN_NATIVE_PC', 'outsideExecutableNativeCycles'
    index = bisect.bisect_right(native['starts'], pc)-1
    if index < 0:
        return 'UNKNOWN_NATIVE_PC', 'outsideFunctionNativeCycles'
    begin = native['starts'][index]
    if name not in native['names'].get(begin, set()):
        return f'NATIVE_FUNCTION@{begin:#x}', 'unresolvedNativeCycles'
    return name, 'validatedNativeCycles'


def target_pid(target, first_window=None):
    if first_window is None:
        if target.get('type') == 'attached' or target.get('return-exit-status') != '0':
            raise ValueError('original launched target must exit zero; attached windows need their actual build receipt')
        return int(target.get('pid'))
    required = {'hardwareFirstWindow': True, 'hardwareRecordingExported': True,
                'sampleCompleted': True, 'sampleExitCode': 0, 'officialCleanPassed': True,
                'buildDeliberatelyStoppedAfterFirstCompile': True,
                'buildCompleted': False, 'diagnosticOnly': True, 'performanceQualified': False}
    if (any(first_window.get(key) != value for key, value in required.items())
            or target.get('type') != 'attached' or target.get('name') not in ('gxi', 'gerbil')
            or int(target.get('pid')) != first_window.get('sampledPid')
            or not 0 <= first_window.get('sampleStartSeconds', -1)
                < first_window.get('firstCompileSeconds', -1) <= 60):
        raise ValueError('actual deliberately stopped first-window hardware receipt required')
    return int(target.get('pid'))


def first_window_binary(repo, receipt, override=None):
    if override is not None:
        binary = override.resolve()
        if (receipt.get('actualBuilderChildVerified') is not True
                or receipt.get('sampleTarget') != 'build-child'
                or receipt.get('sampledChildBinarySha256') != receipt['binarySha256']['gxi']):
            raise ValueError('explicit native binary requires verified actual builder identity')
    else:
        binary = (repo / receipt['binaryHome'] / 'bin/gxi').resolve()
    if not binary.is_relative_to(repo / '.data'):
        raise ValueError('isolated actual first-window binary required')
    return binary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--first-window-receipt', type=Path)
    parser.add_argument('--native-binary', type=Path)
    args = parser.parse_args()
    directory = args.profile.resolve()
    toc = ET.parse(directory / 'toc.xml').getroot()
    target = toc.find('./run/info/target/process')
    first_window = json.loads(args.first_window_receipt.read_text()) if args.first_window_receipt else None
    if args.native_binary and not first_window:
        parser.error('explicit native binary requires an actual first-window receipt')
    pid = target_pid(target, first_window)
    table = toc.find('./run/data/table[@schema="kdebug-counters-with-pmi-sample"]')
    if table is None or 'CORE_ACTIVE_CYCLE' not in table.get('pmi-event', ''):
        raise ValueError('hardware active-cycle samples required')
    root = ET.parse(directory / 'cpu-profile.xml').getroot()
    identifiers = {node.get('id'): node for node in root.iter() if node.get('id')}
    def resolve(node):
        return identifiers[node.get('ref')] if node.get('ref') else node
    columns = [node.text for node in root.findall('./node/schema/col/mnemonic')]
    if columns != ['time', 'thread', 'process', 'core', 'thread-state', 'weight', 'stack']:
        raise ValueError('CPU profile schema changed')
    cycles = collections.Counter()
    cores = collections.Counter()
    pcs = collections.Counter()
    prefixes = {size: collections.Counter() for size in (16, 32, 64, 128)}
    native_cache = {}
    checks = collections.Counter()
    rows = 0
    for row in root.iter('row'):
        fields = list(row)
        process = resolve(fields[2])
        if int(resolve(process.find('pid')).text) != pid:
            raise ValueError('CPU table contains a different process')
        if resolve(fields[4]).text != 'Running':
            raise ValueError('non-running sample cannot be used as active CPU weight')
        weight = int(resolve(fields[5]).text)
        if weight < 0:
            raise ValueError('invalid hardware cycle weight')
        rows += 1
        if weight == 0:
            checks['zeroWeightRows'] += 1
            continue
        cores[resolve(fields[3]).get('fmt')] += weight
        backtrace = resolve(fields[6]).find('backtrace')
        if backtrace is None or not len(resolve(backtrace)):
            cycles['NO_STACK'] += weight
            continue
        frame = resolve(list(resolve(backtrace))[0])
        name = frame.get('name')
        image = frame.find('binary')
        if image is not None:
            image = resolve(image)
            path = Path(image.get('path'))
            if '/.data/' in str(path) and path.exists():
                if path not in native_cache:
                    native_cache[path] = macho_functions(path)
                native = native_cache[path]
                if native['uuid'] != image.get('UUID').upper():
                    raise ValueError('native image UUID drifted')
                pc = (int(frame.get('addr'), 16) & ~3) - int(image.get('load-addr'), 16) + native['textBase']
                name, classification = classify_native_pc(native, pc, name)
                checks[classification] += weight
                if classification == 'validatedNativeCycles':
                    begin = native['starts'][bisect.bisect_right(native['starts'], pc)-1]
                    for size, counts in prefixes.items():
                        if pc-begin < size:
                            counts[name] += weight
                pcs[(name, pc)] += weight
        cycles[name] += weight
    total = sum(cycles.values())
    if total <= 0:
        raise ValueError('positive active CPU cycles required')
    if first_window:
        repo = Path(__file__).resolve().parents[3]
        binary = first_window_binary(repo, first_window, args.native_binary)
        digest = hashlib.sha256(binary.read_bytes()).hexdigest()
        if digest != first_window['binarySha256']['gxi'] or not any(
                path.resolve() == binary and native['sha256'] == digest for path, native in native_cache.items()):
            raise ValueError('actual attached runtime identity absent or changed')
    report = dict(scope='running-hardware-cycle-self-samples-not-wall-time-or-GVM-procedure-attribution',
                  targetPid=pid, rows=rows, totalCycles=total, hardwareEvent=table.get('pmi-event'),
                  nativeFunctionValidation=dict(checks), cores=dict(cores),
                  nativeFunctionPrefixCycles={str(size): dict(counts.most_common())
                                              for size, counts in prefixes.items()},
                  images={str(p): {'uuid': n['uuid'], 'sha256': n['sha256']} for p, n in native_cache.items()},
                  selfCycles=[{'function': name, 'cycles': value, 'percent': value/total*100}
                              for name, value in cycles.most_common()],
                  hotNativePCs=[{'function': name, 'unslidPC': hex(pc), 'cycles': value}
                                for (name, pc), value in pcs.most_common(100)],
                  nativePCs=[{'function': name, 'unslidPC': hex(pc), 'cycles': value}
                             for (name, pc), value in pcs.most_common()])
    if first_window:
        report.update(firstWindowReceiptSha256=hashlib.sha256(args.first_window_receipt.read_bytes()).hexdigest(),
                      deliberatelyStoppedBuild=True, performanceQualified=False,
                      attachedExitStatusNotBuildSuccess=True,
                      scope='actual-mcp-first-window-running-cycle-self-samples-not-complete-prefix-or-speedup')
    (directory / 'cpu-summary.json').write_text(json.dumps(report, indent=2)+'\n')
    print('NATIVE-CPU-SUMMARY', rows, 'running samples', total, 'cycles', dict(checks))
    for row in report['selfCycles'][:20]:
        print(f"{row['percent']:.2f}% {row['function']}")


if __name__ == '__main__':
    main()
