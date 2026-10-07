import struct

import pytest

from rename_macho_entry import rename_entry


def fixture(names=(('_entry', 0x0F), ('_external', 0x01))):
    strings = bytearray(b'\0')
    symbols = bytearray()
    for name, kind in names:
        offset = len(strings)
        strings.extend(name.encode() + b'\0')
        symbols.extend(struct.pack('<IBBHQ', offset, kind, 1 if kind == 0x0F else 0, 0, 32))
    header = struct.pack('<8I', 0xFEEDFACF, 0x100000C, 0, 1, 1, 24, 0, 0)
    command = struct.pack('<6I', 2, 24, 56, len(names), 56 + len(symbols), len(strings))
    return header + command + symbols + strings


def test_only_entry_string_reference_and_extent_change():
    original = fixture()
    result = rename_entry(original, '_entry', '_provider_001')
    assert result.endswith(b'_provider_001\0')
    assert result[60:88] == original[60:88]
    assert result[88:len(original)] == original[88:]
    assert struct.unpack_from('<I', result, 56)[0] == len(original) - 88


def test_multiple_external_definitions_are_not_silently_localized():
    with pytest.raises(ValueError, match='only the native entry'):
        rename_entry(fixture((('_entry', 0x0F), ('_foreign', 0x0F))), '_entry', '_new')


def test_new_name_collision_is_rejected():
    with pytest.raises(ValueError, match='already exists'):
        rename_entry(fixture(), '_entry', '_external')


@pytest.mark.parametrize('data', [b'', fixture()[:40], fixture() + b'trailing'])
def test_malformed_objects_are_rejected(data):
    with pytest.raises(ValueError):
        rename_entry(data, '_entry', '_new')


def test_non_object_macho_is_rejected():
    data = bytearray(fixture())
    struct.pack_into('<I', data, 12, 8)
    with pytest.raises(ValueError, match='object required'):
        rename_entry(bytes(data), '_entry', '_new')
