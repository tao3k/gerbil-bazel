import unittest
import xml.etree.ElementTree as ET

from summarize_native_cpu_profile import target_pid


class FirstWindowReceiptTests(unittest.TestCase):
    def test_attached_zero_is_not_a_successful_build(self):
        target = ET.fromstring('<process type="attached" return-exit-status="0" name="gxi" pid="123"/>')
        with self.assertRaises(ValueError):
            target_pid(target)
        receipt = dict(hardwareFirstWindow=True, hardwareRecordingExported=True,
                       sampleCompleted=True, sampleExitCode=0, officialCleanPassed=True,
                       buildDeliberatelyStoppedAfterFirstCompile=True, buildCompleted=False,
                       diagnosticOnly=True, performanceQualified=False, sampledPid=123,
                       sampleStartSeconds=1, firstCompileSeconds=20)
        self.assertEqual(target_pid(target, receipt), 123)
        for field, value in [('sampledPid', 124), ('buildCompleted', True),
                             ('hardwareRecordingExported', False), ('firstCompileSeconds', 0)]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                target_pid(target, dict(receipt, **{field: value}))

    def test_original_launch_still_requires_zero(self):
        self.assertEqual(target_pid(ET.fromstring('<process type="launched" return-exit-status="0" pid="123"/>')), 123)
        with self.assertRaises(ValueError):
            target_pid(ET.fromstring('<process type="launched" return-exit-status="70" pid="123"/>'))


if __name__ == '__main__':
    unittest.main()
