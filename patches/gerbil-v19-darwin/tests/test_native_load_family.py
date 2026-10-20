import io
import unittest

from native_load_family import summarize


class NativeLoadFamilyTest(unittest.TestCase):
    def run_record(self):
        return dict(cleanPassed=True, nativeImagesAfterClean=0, buildPassed=True,
                    deliberatelyStoppedAfterFirstCompile=True,
                    buildNativeStartNs=1000000000, firstCompileNativeNs=2000000000,
                    buildPid=10)

    def data(self):
        return ('10\t1\t1\t100\t0\t0\tgerbil\t/home/lib/a.o2\tA\n'
                '10\t1\t1\t200\t1\t1\tgerbil\t/home/lib/a.o2\tA\n'
                '11\t10\t1\t300\t0\t0\tgxi\t/home/lib/b.o2\tB\n'
                '11\t10\t1\t500\t1\t1\tgxi\t/home/lib/b.o2\tB\n')

    def test_child_closure_is_not_parent_closure(self):
        result = summarize(io.StringIO(self.data()), self.run_record(), '/home')
        self.assertEqual(result['paths'], ['lib/a.o2', 'lib/b.o2'])
        self.assertEqual(result['childOnlyPaths'], ['lib/b.o2'])
        self.assertFalse(result['performanceQualified'])

    def test_missing_child_rejected(self):
        with self.assertRaisesRegex(ValueError, 'shebang child'):
            summarize(io.StringIO('\n'.join(self.data().splitlines()[:2])+'\n'),
                      self.run_record(), '/home')

    def test_actual_reuse_and_fallback_are_distinct(self):
        rows = self.data().splitlines()
        stream = io.StringIO('\n'.join(row+'\t'+('1' if row.startswith('11\t') else '0')
                                      for row in rows)+'\n')
        result = summarize(stream, self.run_record(), '/home')
        self.assertEqual(result['processes'][0]['ordinaryNativeLoads'], 1)
        self.assertEqual(result['processes'][1]['embeddedNativeHits'], 1)
        self.assertEqual(result['processes'][1]['ordinaryNativeLoads'], 0)

    def test_unknown_reuse_kind_rejected(self):
        stream = io.StringIO('\n'.join(row+'\t2' for row in self.data().splitlines())+'\n')
        with self.assertRaisesRegex(ValueError, 'reuse kind'):
            summarize(stream, self.run_record(), '/home')

    def test_pending_load_rejected(self):
        with self.assertRaisesRegex(ValueError, 'still pending'):
            summarize(io.StringIO('\n'.join(self.data().splitlines()[:-1])+'\n'),
                      self.run_record(), '/home')

    def test_failed_clean_rejected(self):
        run = self.run_record()
        run['cleanPassed'] = False
        with self.assertRaisesRegex(ValueError, 'successful clean'):
            summarize(io.StringIO(self.data()), run, '/home')

    def test_unrelated_process_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unrelated'):
            summarize(io.StringIO(self.data().replace('11\t10', '11\t99')),
                      self.run_record(), '/home')


if __name__ == '__main__':
    unittest.main()
