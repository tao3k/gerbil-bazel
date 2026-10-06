import copy
import json
from pathlib import Path
import tempfile
import unittest

from verify_d1510_baseline import digest, relative_file, verify


class BaselineLockTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        home = self.root / '.data/home'
        (home / 'lib').mkdir(parents=True)
        binary = self.root / '.data/gerbil'
        binary.write_bytes(b'original-binary')
        (binary.parent / 'gxi').symlink_to('gerbil')
        image = home / 'lib/module.o1'
        image.write_bytes(b'original-native')
        scm = home / 'lib/module.scm'
        scm.write_bytes(b'original-scheme')
        inventory = self.root / '.data/inventory.json'
        inventory.write_text(json.dumps(dict(qualified=True, units=[dict(
            module='module', path='lib/module.o1', originalSha256=digest(image),
            sourceSha256=digest(scm))])))
        fallback = dict(firstCompileSeconds=5.053080874999978,
                        buildWallSeconds=56.255962916000044, cleanExitCode=0,
                        buildExitCode=0, nativeImagesAfterClean=0,
                        performanceGatePassed=False)
        receipt = self.root / '.data/receipt.json'
        receipt.write_text(json.dumps(dict(runs=[dict(fallback,
            binarySha256=digest(binary), sourceUnchanged=True)])))
        compiler = self.root / '.data/gcc'
        compiler.write_bytes(b'original-gnu-driver')
        configuration = self.root / '.data/configuration.json'
        configuration.write_text(json.dumps(dict(
            environment=dict(CC=str(compiler), SDKROOT='SDKs/Test.sdk'),
            files={str(compiler): digest(compiler)}, gccVersion='GNU GCC test\n')))
        self.lock = dict(schemaVersion=1, line='D1510/D1513-B',
            fullBuildCeilingSeconds=55, currentPerformanceReproduced=False,
            baselineBinary='.data/gerbil', runtimeHome='.data/home',
            runtimeHomeReference=dict(receipt='.data/inventory.json', moduleCount=1),
            compilerDriverReference=dict(sha256=digest(compiler),
                                         versionLine='GNU GCC test', sdkName='Test.sdk'),
            fallback=dict(fallback, receipt='.data/receipt.json',
                          configuration='.data/configuration.json'),
            files={str(p.relative_to(self.root)): digest(p)
                   for p in (binary, receipt, inventory, configuration)})

    def test_valid_lock_is_not_performance_admission(self):
        result = verify(self.root, self.lock)
        self.assertTrue(result['verified'])
        self.assertFalse(result['performanceQualified'])
        self.assertFalse(result['currentPerformanceReproduced'])

    def test_changed_binary_rejected(self):
        (self.root / '.data/gerbil').write_bytes(b'new-candidate')
        with self.assertRaisesRegex(ValueError, 'Frozen input changed'):
            verify(self.root, self.lock)

    def test_later_runtime_version_rejected(self):
        (self.root / '.data/home/lib/module.o2').write_bytes(b'later-module')
        with self.assertRaisesRegex(ValueError, 'Runtime module changed'):
            verify(self.root, self.lock)

    def test_changed_scheme_rejected(self):
        (self.root / '.data/home/lib/module.scm').write_bytes(b'new-scheme')
        with self.assertRaisesRegex(ValueError, 'Runtime module changed'):
            verify(self.root, self.lock)

    def test_changed_compiler_driver_rejected(self):
        (self.root / '.data/gcc').write_bytes(b'different-driver')
        with self.assertRaisesRegex(ValueError, 'GNU compiler driver changed'):
            verify(self.root, self.lock)

    def test_relaxed_gate_rejected(self):
        lock = copy.deepcopy(self.lock)
        lock['fullBuildCeilingSeconds'] = 60
        with self.assertRaisesRegex(ValueError, 'admission gate'):
            verify(self.root, lock)

    def test_historical_timing_promotion_rejected(self):
        lock = copy.deepcopy(self.lock)
        lock['currentPerformanceReproduced'] = True
        with self.assertRaisesRegex(ValueError, 'admission gate'):
            verify(self.root, lock)

    def test_absolute_and_parent_paths_rejected(self):
        for name in ('/absolute/private', '.data/../outside'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                relative_file(self.root, name)


if __name__ == '__main__':
    unittest.main()
