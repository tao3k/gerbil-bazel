import copy
import unittest

from admit_d1510_cold_build import admission


class ColdBuildAdmissionTests(unittest.TestCase):
    def report(self):
        return dict(buildPerformanceCeilingSeconds=55, candidateDriverSha256='driver',
                    qualified=True, sourceUnchanged=True, runs=[dict(
                        role='candidate', passed=True, sourceUnchanged=True,
                        nativeImagesAfterClean=0, cleanExitCode=0, buildExitCode=0,
                        cleanTerminalExitCode=0, buildTerminalExitCode=0,
                        buildWallSeconds=55)])

    def test_inclusive_ceiling(self):
        self.assertTrue(admission(self.report(), 'driver')['admitted'])

    def test_over_ceiling_is_denied_despite_product_success(self):
        for duration in (55.000001, 55.962595, 56.689304, float('nan'), float('inf'), -1, True):
            with self.subTest(duration=duration):
                report = self.report()
                report['runs'][0]['buildWallSeconds'] = duration
                self.assertEqual(admission(report, 'driver')['decision'], 'DENY')

    def test_no_averaging_away_a_slow_run(self):
        report = self.report()
        report['runs'][0]['buildWallSeconds'] = 47
        slow = copy.deepcopy(report['runs'][0])
        slow['buildWallSeconds'] = 56
        report['runs'].append(slow)
        self.assertFalse(admission(report, 'driver')['admitted'])

    def test_changed_ceiling_and_driver_are_denied(self):
        report = self.report()
        report['buildPerformanceCeilingSeconds'] = 56
        self.assertFalse(admission(report, 'driver')['admitted'])
        self.assertFalse(admission(self.report(), 'other')['admitted'])

    def test_missing_or_failed_cold_build_is_denied(self):
        report = self.report()
        report['runs'] = []
        self.assertFalse(admission(report, 'driver')['admitted'])
        for key, value in [('nativeImagesAfterClean', 1), ('buildExitCode', 1),
                           ('cleanTerminalExitCode', -15), ('sourceUnchanged', False)]:
            report = self.report()
            report['runs'][0][key] = value
            self.assertFalse(admission(report, 'driver')['admitted'])


if __name__ == '__main__':
    unittest.main()
