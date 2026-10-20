from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from build_runtime_image_composition import SCOPE, digest, validate_composed_runtime


class RuntimeImageCompositionTest(unittest.TestCase):
    def fixture(self, directory):
        original, home = Path(directory)/'original', Path(directory)/'candidate'
        for path in (original, home):
            (path/'bin').mkdir(parents=True)
            (path/'include').mkdir()
            (path/'bin/gsc').write_bytes(b'original compiler')
            (path/'include/gambit.h').write_bytes(b'original public header')
        (home/'bin/gxi').write_bytes(b'qualified optimized runtime')
        runtime = dict(qualified=True, diagnosticOnly=False, gscUnchanged=True,
                       consumerFlagsChanged=False, runtimeAbiChanged=False,
                       binaryHashes=dict(gxi=digest(home/'bin/gxi'), gsc=digest(original/'bin/gsc')))
        report = dict(qualified=True, scope=SCOPE, gscUnchanged=True, runtimeAbiChanged=False,
                      consumerFlagsChanged=False, originalGambitMacroInputsUsed=True,
                      headerSha256=digest(original/'include/gambit.h'), runtimeBuildReceipt=runtime)
        return original, home, report

    def test_composed_runtime_requires_all_boundaries_and_image_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            original, home, report = self.fixture(directory)
            with patch('build_runtime_image_composition.validate_packed_image_inventory', return_value=True) as image:
                self.assertTrue(validate_composed_runtime(home, report, original))
                image.assert_called_once_with(home, report)
                for key in ('qualified', 'gscUnchanged', 'runtimeAbiChanged', 'consumerFlagsChanged',
                            'originalGambitMacroInputsUsed'):
                    incomplete = dict(report)
                    incomplete.pop(key)
                    with self.assertRaises(ValueError):
                        validate_composed_runtime(home, incomplete, original)

    def test_changed_runtime_or_header_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            original, home, report = self.fixture(directory)
            (home/'bin/gxi').write_bytes(b'changed runtime')
            with self.assertRaisesRegex(ValueError, 'provenance'):
                validate_composed_runtime(home, report, original)
        with tempfile.TemporaryDirectory() as directory:
            original, home, report = self.fixture(directory)
            (home/'include/gambit.h').write_bytes(b'changed public layout')
            with self.assertRaisesRegex(ValueError, 'header'):
                validate_composed_runtime(home, report, original)


if __name__ == '__main__':
    unittest.main()
