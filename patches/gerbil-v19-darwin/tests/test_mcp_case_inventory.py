import tempfile
import unittest
from pathlib import Path
from mcp_case_inventory import case_names


class CaseInventoryTest(unittest.TestCase):
    def inventory(self, source):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'fixture.ss'
            path.write_text(source)
            return case_names(path)

    def test_fixture_strings_and_comments_are_not_cases(self):
        source = '''; (test-case "comment")
(def sample "(test-case \\\"embedded\\\" (check #t))")
(def tests (test-suite "tests" (test-case "real" (check #t))))'''
        self.assertEqual(self.inventory(source), ['real'])

    def test_quoted_examples_are_not_cases(self):
        self.assertEqual(self.inventory("'(test-case \"example\") (test-case \"real\" #t)"), ['real'])

    def test_dynamic_name_is_rejected(self):
        with self.assertRaises(ValueError):
            self.inventory('(test-case name #t)')


if __name__ == '__main__':
    unittest.main()
