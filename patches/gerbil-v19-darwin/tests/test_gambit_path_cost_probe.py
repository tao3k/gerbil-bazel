import unittest

from prepare_path_cost_probe import SPECS, instrument


class PathCostTests(unittest.TestCase):
    def test_wrappers_preserve_original_body_arguments_and_errno(self):
        for filename, specs in SPECS.items():
            source = '#include "setup.h"\n' + ''.join(
                result + name + '\n ORIGINAL-BODY\n' for result, name, *_ in specs)
            changed = instrument(source, filename[:-2])
            self.assertEqual(changed.count('ORIGINAL-BODY'), len(specs))
            for _, name, arguments, call, slot, _ in specs:
                self.assertIn(f'{name}({arguments})', changed)
                self.assertIn(f'gb_path_original_{name}({call})', changed)
                self.assertIn(f'gb_path_finish(&stamp,{slot})', changed)
            self.assertEqual(changed.count('int saved=errno;'), len(specs))
            self.assertEqual(changed.count('errno=saved;'), len(specs))

    def test_unknown_include_or_definition_is_refused(self):
        with self.assertRaises(ValueError):
            instrument('', 'os_files')
        with self.assertRaises(ValueError):
            instrument('#include "setup.h"\n', 'os_files')


if __name__ == '__main__':
    unittest.main()
