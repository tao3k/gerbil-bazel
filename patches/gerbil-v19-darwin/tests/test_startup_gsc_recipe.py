from pathlib import Path
import unittest

from audit_startup_gsc_recipe import gsc_recipe_command


class StartupGscRecipeTest(unittest.TestCase):
    def test_active_version_changes_linker_name_not_module_reference(self):
        command = gsc_recipe_command(Path('/isolated/build'), 'gerbil/core/contract~3',
                                     Path('/isolated/module.c'), native_version=2)
        self.assertEqual(command[command.index('-linker-name')+1], 'contract~3.o2')
        self.assertEqual(command[command.index('-module-ref')+1], 'contract~3')
        default = gsc_recipe_command(Path('/isolated/build'), 'std/test~0', Path('/isolated/0.c'))
        self.assertEqual(default[default.index('-linker-name')+1], 'test~0.o1')

    def test_invalid_native_versions_are_rejected(self):
        for version in (0, -1, True, '2', 2.5):
            with self.subTest(version=version), self.assertRaises(ValueError):
                gsc_recipe_command(Path('/isolated/build'), 'std/test~0',
                                   Path('/isolated/0.c'), native_version=version)

    def test_std_debug_recipe_matches_original_build_without_changing_core(self):
        command = gsc_recipe_command(Path('/isolated/build'), 'std/make~0',
                                     Path('/isolated/0.c'), original_std_debug=True)
        for option in ('-debug-source', '-track-scheme', '-cc-options'):
            self.assertLess(command.index(option), command.index('-e'))
        self.assertEqual(command[command.index('-cc-options')+1], '-g')
        core = gsc_recipe_command(Path('/isolated/build'), 'gerbil/core~0',
                                  Path('/isolated/0.c'), original_std_debug=True)
        self.assertNotIn('-debug-source', core)
        self.assertNotIn('-track-scheme', core)

    def test_compiler_options_precede_evaluation_options(self):
        command = gsc_recipe_command(Path('/isolated/build'), 'std/os/device~0', Path('/isolated/0.c'))
        for option in ('-module-ref', '-linker-name', '-o'):
            self.assertLess(command.index(option), command.index('-e'))
        self.assertEqual(command[-1], '/isolated/build/lib/std/os/device~0.scm')
        self.assertIn('(include "/isolated/build/lib/_gambit#.scm")', command)
        self.assertIn('(define-cond-expand-feature|gerbil-separate-compilation|)', command)

    def test_original_diagnostic_mode_stays_explicit(self):
        command = gsc_recipe_command(Path('/isolated/build'), 'std/test~0', Path('/isolated/0.c'), False)
        self.assertNotIn('-e', command)


if __name__ == '__main__':
    unittest.main()
