import contextlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from run_parser_native_admission_cost import run


class NativeAdmissionSupervisorTest(unittest.TestCase):
    def execute(self, script, idle=None, capture_phases=False, on_start=None):
        children = []
        original = subprocess.Popen

        def spawn(*args, **kwargs):
            child = original(*args, **kwargs)
            children.append(child)
            return child

        with tempfile.TemporaryDirectory() as name, patch('subprocess.Popen', spawn):
            directory = Path(name)
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    result = run([sys.executable, '-c', script], directory, dict(os.environ),
                                 directory / 'child.log', 3, idle, capture_phases=capture_phases,
                                 on_start=on_start)
                return result, (directory / 'child.log').read_text()
            finally:
                self.assertEqual(len(children), 1)
                self.assertIsNotNone(children[0].poll())
                self.assertTrue(children[0].stdout.closed)

    def test_real_lines_are_retained_even_when_not_forwarded_to_tool(self):
        result, content = self.execute('print("INTERFACE-IMPORTED real-module", flush=True)\n'
                                      'print("NATIVE-ADMISSION-PREFIX-OK", flush=True)', 1)
        self.assertEqual(result['exitCode'], 0)
        self.assertIsNotNone(result['firstOutputSeconds'])
        self.assertEqual(content.splitlines(), ['INTERFACE-IMPORTED real-module', 'NATIVE-ADMISSION-PREFIX-OK'])

    def test_silence_is_failure_and_child_is_reaped(self):
        with self.assertRaisesRegex(RuntimeError, 'silence budget'):
            self.execute('import time\ntime.sleep(20)', 0.15)

    def test_first_case_is_measured_from_real_case_line(self):
        result, _ = self.execute('import time\nprint("MODULE-IMPORTED real", flush=True)\n'
                                 'time.sleep(0.05)\nprint("CASE-OK actual", flush=True)', 1)
        self.assertGreater(result['firstCaseSeconds'], result['firstOutputSeconds'])

    def test_nonzero_exit_is_not_a_completed_prefix(self):
        with self.assertRaisesRegex(RuntimeError, 'exited 7'):
            self.execute('raise SystemExit(7)')

    def test_phase_events_are_real_lines_not_progress_output(self):
        result, content = self.execute('print("MODULE-BATCH-START actual", flush=True)\n'
                                      'print("MODULE-IMPORTED dependency", flush=True)\n'
                                      'print("CASE-OK actual", flush=True)', 1, True)
        events = result['observedPhaseEvents']
        self.assertEqual([row['line'] for row in events], content.splitlines())
        self.assertEqual(events[-1]['elapsedSeconds'], result['firstCaseSeconds'])
        self.assertEqual(sorted(row['elapsedSeconds'] for row in events),
                         [row['elapsedSeconds'] for row in events])

    def test_observer_receives_actual_pid_without_product_log_output(self):
        observed = []
        result, content = self.execute('print("actual", flush=True)', 1, on_start=observed.append)
        self.assertEqual(result['exitCode'], 0)
        self.assertEqual(content, 'actual\n')
        self.assertEqual(len(observed), 1)
        self.assertGreater(observed[0], 0)

    def test_observer_failure_still_reaps_product_child(self):
        def fail(pid):
            raise ValueError('observer failed')
        with self.assertRaisesRegex(ValueError, 'observer failed'):
            self.execute('import time\ntime.sleep(20)', on_start=fail)


if __name__ == '__main__':
    unittest.main()
