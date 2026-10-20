"""Read strong absolute Mach-O dependencies; refuse unsupported packing semantics."""
import struct
import hashlib


def dependencies(data):
    if len(data) < 32 or struct.unpack_from('<I', data)[0] != 0xFEEDFACF:
        raise ValueError('thin little-endian Mach-O required')
    count, command_bytes = struct.unpack_from('<II', data, 16)
    end, cursor = 32 + command_bytes, 32
    if end > len(data):
        raise ValueError('truncated Mach-O commands')
    result = set()
    for _ in range(count):
        if cursor + 8 > end:
            raise ValueError('truncated Mach-O command')
        kind, size = struct.unpack_from('<II', data, cursor)
        if size < 8 or cursor + size > end:
            raise ValueError('invalid Mach-O command size')
        if kind in (0x80000018, 0x8000001F, 0x80000023, 0x20):
            raise ValueError('packing refuses weak/reexport/upward/lazy dependencies')
        if kind == 0xC:
            if size < 24:
                raise ValueError('truncated dylib command')
            offset = struct.unpack_from('<I', data, cursor+8)[0]
            if offset < 24 or offset >= size:
                raise ValueError('invalid dylib name offset')
            name = data[cursor+offset:cursor+size].split(b'\0', 1)[0].decode('utf-8')
            if not name.startswith('/') or ',' in name or '\n' in name:
                raise ValueError('packing requires unambiguous absolute dependency paths')
            result.add(name)
        cursor += size
    if cursor != end:
        raise ValueError('Mach-O command extent mismatch')
    return sorted(result)


def validate_packed_image_inventory(home, receipt):
    images = receipt.get('images')
    if not images:
        raise ValueError('hashed packed-image inventory required')
    aliases = set()
    for image in images:
        target = home / image['path']
        if not target.resolve().is_relative_to(home.resolve()):
            raise ValueError('packed image escapes isolated home')
        data = target.read_bytes()
        if hashlib.sha256(data).hexdigest() != image['sha256'] or dependencies(data) != image['dependencies']:
            raise ValueError('packed image hash/dependencies changed')
        for alias in image['aliases']:
            path = home / alias
            if alias in aliases or not path.is_symlink() or path.resolve() != target.resolve():
                raise ValueError('packed image alias changed or duplicated')
            aliases.add(alias)
    if aliases != {row['path'] for row in receipt['units']}:
        raise ValueError('packed aliases differ from original input inventory')
    for row in receipt.get('preservedOriginalImages', []):
        target = home / row['path']
        if (row['path'] in aliases or target.is_symlink() or not target.resolve().is_relative_to(home.resolve())
                or hashlib.sha256(target.read_bytes()).hexdigest() != row['originalSha256']
                or dependencies(target.read_bytes()) != row['dependencies']):
            raise ValueError('preserved original image changed')
        aliases.add(row['path'])
    return True
