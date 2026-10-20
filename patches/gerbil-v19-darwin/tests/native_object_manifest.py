"""Admit only a current-image, content-locked native assembler object."""
import hashlib
from pathlib import Path
import re
import struct


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def executable_rpaths(data):
    if len(data) < 32 or struct.unpack_from('<I', data)[0] != 0xFEEDFACF or struct.unpack_from('<I', data, 12)[0] != 2:
        raise ValueError('thin little-endian Mach-O executable required')
    count, extent = struct.unpack_from('<II', data, 16)
    cursor, end, paths = 32, 32 + extent, []
    if end > len(data):
        raise ValueError('truncated commands')
    for _ in range(count):
        if cursor + 8 > end:
            raise ValueError('truncated command')
        kind, size = struct.unpack_from('<II', data, cursor)
        if size < 8 or cursor + size > end:
            raise ValueError('invalid command extent')
        if kind == 0x8000001C:
            if size < 12:
                raise ValueError('truncated RPATH')
            offset = struct.unpack_from('<I', data, cursor + 8)[0]
            raw = data[cursor + offset:cursor + size]
            if not 12 <= offset < size or b'\0' not in raw:
                raise ValueError('invalid RPATH string')
            paths.append(raw.split(b'\0', 1)[0].decode('utf-8'))
        cursor += size
    if cursor != end or not paths:
        raise ValueError('complete executable RPATH list required')
    return paths


def read_manifest(image):
    image = Path(image)
    if image.is_symlink() or not image.is_file():
        raise ValueError('regular native image required')
    reference = image.with_name(image.name+'.gambit-native-objects')
    if reference.is_symlink() or not reference.is_file():
        raise ValueError('regular native-object reference required')
    fields = {}
    for line in reference.read_text().splitlines():
        name, separator, value = line.partition('=')
        if not separator or name in fields:
            raise ValueError('malformed or duplicate native-object field')
        fields[name] = value
    if set(fields) != {'schema', 'image-sha256', 'object-sha256', 'directory'} or fields['schema'] != '1':
        raise ValueError('exact native-object schema required')
    for name in ('image-sha256', 'object-sha256'):
        if not re.fullmatch('[0-9a-f]{64}', fields[name]):
            raise ValueError('native-object SHA-256 required')
    expected = image.name+'.gambit-native-objects.'+fields['image-sha256']+'.'+fields['object-sha256']
    if fields['directory'] != expected:
        raise ValueError('native-object directory identity changed')
    directory = image.parent/expected
    obj = directory/'object.o'
    if directory.is_symlink() or not directory.is_dir() or obj.is_symlink() or not obj.is_file():
        raise ValueError('regular isolated native object required')
    if digest(image) != fields['image-sha256'] or digest(obj) != fields['object-sha256']:
        raise ValueError('native-object image/object identity changed')
    original, captured = image.read_bytes(), obj.read_bytes()
    if (len(original) < 32 or len(captured) < 32 or
            struct.unpack_from('<I', original)[0] != 0xFEEDFACF or
            struct.unpack_from('<I', captured)[0] != 0xFEEDFACF or
            struct.unpack_from('<I', original, 12)[0] != 8 or
            struct.unpack_from('<I', captured, 12)[0] != 1 or
            original[4:12] != captured[4:12]):
        raise ValueError('matching thin Mach-O bundle/object architecture required')
    return dict(objectPath=obj, imageSha256=fields['image-sha256'], objectSha256=fields['object-sha256'])


def text_section(data):
    if len(data) < 32 or struct.unpack_from('<I', data)[0] != 0xFEEDFACF:
        raise ValueError('thin little-endian Mach-O required')
    count, extent = struct.unpack_from('<II', data, 16)
    cursor, end, sections = 32, 32+extent, []
    if end > len(data):
        raise ValueError('truncated commands')
    for _ in range(count):
        if cursor+8 > end:
            raise ValueError('truncated command')
        kind, size = struct.unpack_from('<II', data, cursor)
        if size < 8 or cursor+size > end:
            raise ValueError('invalid command')
        if kind == 0x19:
            if size < 72:
                raise ValueError('truncated segment')
            entries = struct.unpack_from('<I', data, cursor+64)[0]
            if size != 72+80*entries:
                raise ValueError('invalid sections')
            for index in range(entries):
                pos = cursor+72+80*index
                if data[pos:pos+16].split(b'\0', 1)[0] == b'__text':
                    length = struct.unpack_from('<Q', data, pos+40)[0]
                    offset = struct.unpack_from('<I', data, pos+48)[0]
                    if offset+length > len(data):
                        raise ValueError('truncated text')
                    sections.append(data[offset:offset+length])
        cursor += size
    if cursor != end or len(sections) != 1:
        raise ValueError('one complete text section required')
    return sections[0]
