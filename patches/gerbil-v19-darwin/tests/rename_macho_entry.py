"""Rename one Mach-O object entry without touching code or relocation indices."""
import struct


def rename_entry(data, old, new):
    if len(data) < 32:
        raise ValueError('truncated Mach-O header')
    magic, cpu, subtype, kind, count, extent, flags, reserved = struct.unpack_from('<8I', data)
    if magic != 0xFEEDFACF or kind != 1:
        raise ValueError('thin little-endian Mach-O object required')
    end, cursor, symtab = 32 + extent, 32, None
    for _ in range(count):
        if cursor + 8 > end or end > len(data):
            raise ValueError('truncated commands')
        command, size = struct.unpack_from('<II', data, cursor)
        if size < 8 or cursor + size > end:
            raise ValueError('invalid command extent')
        if command == 2:
            if size != 24 or symtab is not None:
                raise ValueError('exactly one complete symbol table required')
            symtab = (cursor, *struct.unpack_from('<4I', data, cursor + 8))
        cursor += size
    if cursor != end or symtab is None:
        raise ValueError('invalid command inventory')
    command, symbols, count, strings, length = symtab
    if symbols < end or symbols + 16 * count > strings or strings + length != len(data):
        raise ValueError('bounded symbol table with final string table required')
    old_bytes, new_bytes = old.encode('ascii'), new.encode('ascii')
    if not old_bytes or not new_bytes or b'\0' in new_bytes or old_bytes == new_bytes:
        raise ValueError('distinct nonempty symbol names required')
    definitions, target = [], None
    for index in range(count):
        position = symbols + 16 * index
        offset, ntype, section, descriptor, value = struct.unpack_from('<IBBHQ', data, position)
        if offset >= length:
            raise ValueError('invalid symbol string offset')
        raw = data[strings + offset:strings + length]
        if b'\0' not in raw:
            raise ValueError('unterminated symbol')
        name = raw.split(b'\0', 1)[0]
        if name == new_bytes:
            raise ValueError('new symbol already exists')
        if ntype & 0xE0 or not ntype & 1:
            continue
        if ntype & 0x0E == 0x0E:
            definitions.append(name)
            if name == old_bytes:
                target = position
        elif ntype & 0x0E != 0:
            raise ValueError('unsupported external symbol type')
    if definitions != [old_bytes] or target is None:
        raise ValueError('only the native entry may be externally defined')
    output = bytearray(data)
    output.extend(new_bytes + b'\0')
    struct.pack_into('<I', output, target, length)
    struct.pack_into('<I', output, command + 20, length + len(new_bytes) + 1)
    changed = set(range(target, target + 4)) | set(range(command + 20, command + 24))
    if any(a != b and i not in changed for i, (a, b) in enumerate(zip(data, output))):
        raise AssertionError('unexpected object-byte change')
    return bytes(output)
