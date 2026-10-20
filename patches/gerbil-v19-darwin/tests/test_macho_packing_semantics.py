import struct
import unittest

from macho_packing_semantics import compare_group, image_semantics, preserve_original_image


def fixture(kind=0xF, descriptor=0, value=1, rpath='/original/lib'):
    raw = rpath.encode()+b'\0'
    size = (12+len(raw)+7)//8*8
    path = struct.pack('<3I', 0x8000001C, size, 12)+raw
    path += b'\0'*(size-len(path))
    offset = 32+len(path)+24
    sym = struct.pack('<6I', 2, 24, offset, 1, offset+16, 6)
    header = struct.pack('<8I', 0xFEEDFACF, 0x100000C, 0, 8, 2, len(path)+24, 0x85, 0)
    return header+path+sym+struct.pack('<IBBHQ', 1, kind, 1, descriptor, value)+b'\0_fun\0'


class PackingSemanticsTest(unittest.TestCase):
    def test_definition_and_undefined_ordinal(self):
        defined = image_semantics(fixture(descriptor=0x80))
        self.assertEqual(defined['rpaths'], ['/original/lib'])
        self.assertTrue(defined['definitions']['_fun']['weak'])
        undefined = image_semantics(fixture(kind=1, descriptor=0xFE00, value=0))
        self.assertEqual(undefined['undefined'], [dict(name='_fun', ordinal=0xFE)])

    def test_new_internal_binding_and_relative_rpath_are_not_silently_admitted(self):
        provider = image_semantics(fixture(rpath='@loader_path/lib'))
        user = image_semantics(fixture(kind=1, descriptor=0xFE00, value=0))
        report = compare_group({'a': provider, 'b': user}, provider)
        self.assertFalse(report['literalRpathsMatch'])
        self.assertEqual(report['relativeRpaths'], ['@loader_path/lib'])
        self.assertEqual(report['possibleChangedInImageBindings'][0]['providers'], ['a'])

    def test_duplicate_definitions_are_reported(self):
        data = image_semantics(fixture())
        report = compare_group({'a': data, 'b': data}, data)
        self.assertEqual(report['duplicateDefinitions'], {'_fun': ['a', 'b']})

    def test_weak_or_initialized_images_stay_original(self):
        ordinary = image_semantics(fixture())
        self.assertFalse(preserve_original_image(ordinary))
        self.assertTrue(preserve_original_image(image_semantics(fixture(descriptor=0x80))))
        ordinary['flags'] |= 0x10000
        self.assertTrue(preserve_original_image(ordinary))

    def test_malformed_and_unsupported_symbols_refused(self):
        for data in (fixture()[:-1], fixture(kind=3), b''):
            with self.assertRaises(ValueError):
                image_semantics(data)


if __name__ == '__main__':
    unittest.main()
