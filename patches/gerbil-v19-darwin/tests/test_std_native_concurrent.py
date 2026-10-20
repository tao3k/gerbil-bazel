import unittest

from run_std_native_concurrent import batch_cases, admitted_owners, OWNERS


class StandardNativeTests(unittest.TestCase):
    def test_admission_requires_exact_prior_baseline_failure(self):
        previous = dict(qualified=False, stagingHead='head', projectHead='project',
                        sourceSha256={'source': 'digest'}, wallBudgetSeconds=90,
                        silenceBudgetSeconds=5, waves=[dict(role='baseline',
                            failures=[dict(owner='string/path-test.ss')],
                            runs=[dict(owner=name) for name in OWNERS if name != 'string/path-test.ss'])])
        selected = admitted_owners(previous, 'head', 'project', {'source': 'digest'})
        self.assertEqual(len(selected), 10)
        self.assertNotIn('string/path-test.ss', selected)
        with self.assertRaises(RuntimeError):
            admitted_owners(previous, 'changed', 'project', {'source': 'digest'})
        with self.assertRaises(RuntimeError):
            admitted_owners(previous, 'head', 'project', {'source': 'changed'})
        previous['waves'][0]['failures'].append(dict(owner='number/misc-test.ss'))
        with self.assertRaises(RuntimeError):
            admitted_owners(previous, 'head', 'project', {'source': 'digest'})

    def test_actual_case_identity_and_final_contract(self):
        lines = ['CASE-OK first', 'CASE-OK second', 'HARNESS-RETURN status=0',
                 'FINAL-GC-OK', 'NATIVE-SUITE-OK modules=1', 'OK']
        self.assertEqual(batch_cases('\n'.join(lines)), lines[:2])
        for missing in lines:
            with self.subTest(missing=missing):
                if missing.startswith('CASE-OK '):
                    continue
                with self.assertRaises(RuntimeError):
                    batch_cases('\n'.join(line for line in lines if line != missing))
        with self.assertRaises(RuntimeError):
            batch_cases('\n'.join(lines[2:]))
        with self.assertRaises(RuntimeError):
            batch_cases('\n'.join(['*** ERROR hidden failure']+lines))


if __name__ == '__main__':
    unittest.main()
