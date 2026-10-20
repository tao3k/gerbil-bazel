"""Conservative linkage audit for the existing immutable image-packing candidate."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from macho_image_dependencies import validate_packed_image_inventory


def image_semantics(data):
    if len(data) < 32 or struct.unpack_from('<I', data)[0] != 0xFEEDFACF:
        raise ValueError('thin little-endian Mach-O required')
    _, cpu, subtype, filetype, count, extent, flags, _ = struct.unpack_from('<8I', data)
    if filetype != 8:
        raise ValueError('Mach-O bundle required')
    end, cursor = 32+extent, 32
    if end > len(data):
        raise ValueError('truncated load commands')
    rpaths, hooks, symtab = [], [], None
    for _ in range(count):
        if cursor+8 > end:
            raise ValueError('truncated command')
        kind, size = struct.unpack_from('<II', data, cursor)
        if size < 8 or cursor+size > end:
            raise ValueError('invalid command extent')
        if kind == 0x8000001C:
            if size < 12:
                raise ValueError('truncated RPATH command')
            offset = struct.unpack_from('<I', data, cursor+8)[0]
            if offset < 12 or offset >= size:
                raise ValueError('invalid RPATH offset')
            raw = data[cursor+offset:cursor+size]
            if b'\0' not in raw:
                raise ValueError('unterminated RPATH')
            rpaths.append(raw.split(b'\0', 1)[0].decode('utf-8'))
        elif kind == 2:
            if size != 24 or symtab is not None:
                raise ValueError('one complete symbol table required')
            symtab = struct.unpack_from('<4I', data, cursor+8)
        elif kind == 0x19:
            if size < 72:
                raise ValueError('truncated segment')
            sections = struct.unpack_from('<I', data, cursor+64)[0]
            if size != 72+80*sections:
                raise ValueError('invalid section extent')
            for index in range(sections):
                pos = cursor+72+80*index
                section_flags = struct.unpack_from('<I', data, pos+64)[0]
                section_size = struct.unpack_from('<Q', data, pos+40)[0]
                if section_flags & 0xFF in (9, 10) and section_size:
                    hooks.append(dict(kind=section_flags & 0xFF, bytes=section_size))
        elif kind == 0x1A:
            if size < 24:
                raise ValueError('truncated routines command')
            if struct.unpack_from('<Q', data, cursor+8)[0]:
                hooks.append(dict(kind='routines64'))
        cursor += size
    if cursor != end or symtab is None:
        raise ValueError('load-command extent or symbol table missing')
    offset, count, strings, length = symtab
    if offset < end or offset+16*count > len(data) or strings+length > len(data):
        raise ValueError('invalid symbol table extent')
    definitions, undefined = {}, []
    for index in range(count):
        name_offset, kind, section, descriptor, value = struct.unpack_from('<IBBHQ', data, offset+16*index)
        if kind & 0xE0 or not kind & 1:
            continue
        if name_offset >= length:
            raise ValueError('invalid symbol string offset')
        raw = data[strings+name_offset:strings+length]
        if b'\0' not in raw:
            raise ValueError('unterminated symbol')
        name = raw.split(b'\0', 1)[0].decode('utf-8')
        symbol_type = kind & 0x0E
        if symbol_type == 0 and not value:
            undefined.append(dict(name=name, ordinal=descriptor >> 8))
        elif symbol_type == 0x0E:
            definitions[name] = dict(weak=bool(descriptor & 0x80), private=bool(kind & 0x10))
        else:
            raise ValueError('unsupported external symbol type')
    return dict(cpu=cpu, subtype=subtype, flags=flags, rpaths=rpaths,
                initializationHooks=hooks, definitions=definitions, undefined=undefined)


def compare_group(originals, packed):
    providers = {}
    for alias, semantics in originals.items():
        for name in semantics['definitions']:
            providers.setdefault(name, []).append(alias)
    resolutions = []
    for alias, semantics in originals.items():
        for symbol in semantics['undefined']:
            other = [provider for provider in providers.get(symbol['name'], []) if provider != alias]
            if other:
                resolutions.append(dict(alias=alias, symbol=symbol['name'],
                                        originalOrdinal=symbol['ordinal'], providers=other))
    return dict(
        architectureMatch=all((row['cpu'], row['subtype']) == (packed['cpu'], packed['subtype'])
                              for row in originals.values()),
        originalFlagValues=sorted({row['flags'] for row in originals.values()}),
        packedFlags=packed['flags'],
        architectureAndFlagsMatch=all((row['cpu'], row['subtype'], row['flags']) ==
                                      (packed['cpu'], packed['subtype'], packed['flags'])
                                      for row in originals.values()),
        literalRpathsMatch=all(row['rpaths'] == packed['rpaths'] for row in originals.values()),
        relativeRpaths=sorted({path for row in [*originals.values(), packed] for path in row['rpaths']
                              if not path.startswith('/')}),
        duplicateDefinitions={name: aliases for name, aliases in providers.items() if len(aliases) > 1},
        addedDefinitions=sorted(set(packed['definitions'])-set(providers)),
        removedDefinitions=sorted(set(providers)-set(packed['definitions'])),
        possibleChangedInImageBindings=resolutions,
        originalInitializationHooks={alias: row['initializationHooks'] for alias, row in originals.items()
                                     if row['initializationHooks']},
        packedInitializationHooks=packed['initializationHooks'])


def preserve_original_image(semantics):
    return bool(semantics['initializationHooks'] or semantics['flags'] & (0x8000 | 0x10000)
                or any(row['weak'] for row in semantics['definitions'].values()))


def main():
    parser = argparse.ArgumentParser()
    for name in ('original-home', 'packed-home', 'build-receipt', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    original, packed, receipt, output = [path.resolve() for path in
        (args.original_home, args.packed_home, args.build_receipt, args.output)]
    if not all(path.is_relative_to(root/'.data') for path in (original, packed, receipt, output)):
        parser.error('isolated immutable .data artifacts required')
    build = json.loads(receipt.read_text())
    validate_packed_image_inventory(packed, build)
    rows = {row['path']: row for row in build['units']}
    output.mkdir(parents=True, exist_ok=False)
    report = dict(diagnosticOnly=True, performanceQualified=False, productionQualified=False,
                  buildReceiptSha256=hashlib.sha256(receipt.read_bytes()).hexdigest(), groups=[])
    for image in build['images']:
        originals = {}
        for alias in image['aliases']:
            data = (original/alias).read_bytes()
            if hashlib.sha256(data).hexdigest() != rows[alias]['originalSha256']:
                raise ValueError('original image identity changed')
            originals[alias] = image_semantics(data)
        details = compare_group(originals, image_semantics((packed/image['path']).read_bytes()))
        report['groups'].append(dict(path=image['path'], originalImages=len(originals), **details))
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print('PACKING-LINKAGE-AUDIT-RECORDED production qualification unchanged', flush=True)


if __name__ == '__main__':
    main()
