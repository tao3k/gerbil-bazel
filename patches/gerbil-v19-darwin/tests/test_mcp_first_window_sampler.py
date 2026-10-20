from pathlib import Path
from types import SimpleNamespace
import unittest

from sample_mcp_first_compile import first_window_observer, first_window_sampler, first_window_target, observed_child_usage


class FirstWindowSamplerTests(unittest.TestCase):
    def test_quiet_parent_is_observable_before_build_child_exists(self):
        self.assertEqual(first_window_target(100, []), (100, 'official-parent'))
        self.assertEqual(first_window_target(100, [['101', '/usr/bin/sample 100']]),
                         (100, 'official-parent'))

    def test_actual_build_child_takes_precedence(self):
        rows = [['101', '/bin/sh wrapper'], ['102', '/tool/bin/gerbil build.ss compile']]
        self.assertEqual(first_window_target(100, rows), (102, 'build-child'))

    def test_hardware_attaches_to_actual_child_without_launch_substitution(self):
        command = first_window_sampler(123, Path('receipt'), True)
        self.assertEqual(command[command.index('--attach')+1], '123')
        self.assertNotIn('--launch', command)
        self.assertEqual(command[command.index('--time-limit')+1], '5s')
        self.assertEqual(command[command.index('--output')+1], 'receipt/profile.trace')

    def test_original_wall_sampler_remains_unchanged(self):
        self.assertEqual(first_window_sampler(123, Path('receipt'), False),
            ['/usr/bin/sample', '123', '2', '1', '-file', 'receipt/first-window.sample.txt'])

    def test_verification_only_cannot_attach_sampler(self):
        self.assertIsNone(first_window_observer(123, Path('receipt'), False, True))
        with self.assertRaises(ValueError):
            first_window_observer(123, Path('receipt'), True, True)

    def test_sampling_modes_keep_original_commands(self):
        for hardware in (False, True):
            self.assertEqual(first_window_observer(123, Path('receipt'), hardware, False),
                             first_window_sampler(123, Path('receipt'), hardware))

    def test_cpu_receipt_is_a_child_delta_not_wall_or_peak_rss(self):
        before = SimpleNamespace(ru_utime=10, ru_stime=4, ru_nvcsw=100, ru_nivcsw=50, ru_maxrss=1000)
        after = SimpleNamespace(ru_utime=12, ru_stime=5, ru_nvcsw=130, ru_nivcsw=70, ru_maxrss=2000)
        usage = observed_child_usage(before, after)
        self.assertEqual(usage['userCpuSeconds'], 2)
        self.assertEqual(usage['systemCpuSeconds'], 1)
        self.assertEqual(usage['voluntaryContextSwitches'], 30)
        self.assertEqual(usage['involuntaryContextSwitches'], 20)
        self.assertNotIn('maximumRss', usage)
        self.assertNotIn('speedup', usage)
        self.assertIn('including-observers', usage['scope'])


if __name__ == '__main__':
    unittest.main()
