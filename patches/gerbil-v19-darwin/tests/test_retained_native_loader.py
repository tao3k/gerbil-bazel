import unittest

from probe_retained_native_loader import INITIAL_PHASES, align_initial_interval, instrument_setup, parse_initial_stats, parse_stats, replace_once
from run_loader_stdlib_controls import completed_cases
from probe_retained_native_loader import instrument_dynamic_walks, parse_dynamic_stats
from probe_retained_native_loader import parse_fixup_stats
from probe_retained_native_loader import instrument_loader_cpu, parse_cpu_stats


class LoaderStatsTests(unittest.TestCase):
    def stats(self):
        return dict(digestNs=100, providerNs=120, dlopenNs=0,
                    digestCalls=2, providerCalls=3, dlopenCalls=0,
                    setupNs=50, linkerNs=2, setupCalls=3, linkerCalls=3)

    def test_excludes_nested_digest_from_provider_own(self):
        self.assertEqual(parse_stats(self.stats())['providerOwnNs'], 20)

    def test_zero_dlopen_is_not_missing_measurement(self):
        self.assertEqual(parse_stats(self.stats())['dlopenCalls'], 0)

    def test_cpu_counters_require_matching_original_call_counts(self):
        row = dict(totals=[[1, 2, 3, 4], [0] * 4, [1, 0, 0, 0], [0] * 4],
                   calls=[2, 0, 3, 3])
        self.assertEqual(parse_cpu_stats(row, self.stats())['digest']['systemMicroseconds'], 2)
        for broken in (dict(row, calls=[2, 1, 3, 3]),
                       dict(row, totals=[[1, -1, 0, 0]] * 4),
                       dict(row, totals=[[1, 2, 3]] * 4),
                       dict(row, calls=[True, 0, 3, 3]),
                       dict(row, totals=[[1, 2, 3, 4]] * 4)):
            with self.assertRaises(ValueError):
                parse_cpu_stats(broken, self.stats())

    def test_cpu_instrumentation_preserves_original_call_and_error_boundaries(self):
        loader = '\n'.join(('static int gb_matches(const char *path, const char *expected) {',
            '  int result = gb_matches_original(path, expected);',
            '  void *result = dlopen(path, mode);', 'atexit(gb_loader_report);',
            'const char *prefix = getenv("GB_LOADER_STATS");',
            '  start = gb_now();\n  result = gb_find_provider_original(path, name);'))
        setup = '\n'.join(('extern unsigned long long gb_loader_now(void);',
            'unsigned long long start = gb_loader_now();',
            'result = original_setup();', 'gb_loader_setup_time(gb_loader_now() - start);',
            'if (result) return result;', 'unsigned long long start = gb_loader_now();',
            'mol = original_linker();', 'gb_loader_linker_time(gb_loader_now() - start);'))
        observed_loader, observed_setup = instrument_loader_cpu(loader, setup)
        for call in ('gb_matches_original(path, expected);', 'dlopen(path, mode);'):
            self.assertEqual(observed_loader.count(call), 1)
        for call in ('result = original_setup();', 'if (result) return result;',
                     'mol = original_linker();'):
            self.assertEqual(observed_setup.count(call), 1)
        for index in (2, 3):
            self.assertEqual(observed_setup.count(f'gb_loader_cpu_end({index}, cpu_before);'), 1)
        self.assertIn('getrusage(RUSAGE_SELF, &r)', observed_loader)
        self.assertIn('memset(gb_cpu_totals, 0, sizeof(gb_cpu_totals));', observed_loader)
        self.assertIn('  gb_cpu_enable();\n  start = gb_now();', observed_loader)
        self.assertIn('const char *prefix = gb_wall_prefix;', observed_loader)
        self.assertIn('gb_cpu_capture_prefixes(); atexit(gb_loader_report);', observed_loader)

    def test_requires_real_hits_and_complete_nonnegative_counts(self):
        for key, value in [('providerCalls', 0), ('providerNs', 99),
                           ('digestNs', -1), ('dlopenCalls', True), ('digestCalls', 4)]:
            row = self.stats()
            row[key] = value
            with self.assertRaises(ValueError):
                parse_stats(row)
        row = self.stats()
        del row['dlopenNs']
        with self.assertRaises(ValueError):
            parse_stats(row)

    def test_exact_source_anchor_required(self):
        self.assertEqual(replace_once('abc', 'b', 'x'), 'axc')
        for source in ('ac', 'abbc'):
            with self.assertRaises(ValueError):
                replace_once(source, 'b', 'x')

    def test_all_original_cases_must_finish(self):
        self.assertEqual(completed_cases(['CASE x', 'CASE-OK x', 'OK']), ['x'])
        for lines in (['OK'], ['CASE x', 'OK'], ['CASE x', 'CASE-OK y', 'OK'],
                      ['CASE x', 'CASE-OK x', 'CASE-FAIL y', 'OK']):
            with self.assertRaises(ValueError):
                completed_cases(lines)

    def test_initial_setup_requires_each_original_phase_once(self):
        row = dict(nanoseconds=[0, 2, 3, 4, 5], calls=[1] * 5, startedNs=100, finishedNs=120)
        result = parse_initial_stats(row)
        self.assertEqual(result['totalObservedNs'], 14)
        self.assertEqual(set(result), set(INITIAL_PHASES) | {'totalObservedNs', 'startedNs',
                         'finishedNs', 'runtimeSinceInitialSetupNs'})
        for broken in (dict(row, calls=[1] * 4), dict(row, calls=[1, 1, 0, 1, 1]),
                       dict(row, calls=[True] * 5), dict(row, nanoseconds=[-1] * 5),
                       dict(row, nanoseconds=[1.0] * 5), dict(row, finishedNs=110),
                       dict(row, startedNs=True)):
            with self.assertRaises(ValueError):
                parse_initial_stats(broken)

    def test_parent_and_child_must_share_a_containing_clock_interval(self):
        child = dict(startedNs=100, finishedNs=120)
        self.assertEqual(align_initial_interval(child, dict(launchedNs=90, finishedNs=130))
                         ['launchToInitialSetupNs'], 10)
        for process in (dict(launchedNs=101, finishedNs=130),
                        dict(launchedNs=90, finishedNs=119)):
            with self.assertRaises(ValueError):
                align_initial_interval(child, process)

    def test_initial_phase_instrumentation_keeps_original_call_bodies(self):
        original = '\n'.join((
            '#include "setup.h"',
            '      mol = linker_to_mod_or_lnk\n'
            '              (___CAST(___mod_or_lnk (*) ___P((___global_state),()),\n'
            '                       linker));',
            '          result = setup_modules (___PSTATE, mol, 1);',
            '  if ((err = setup_os_and_mem ()) != ___FIX(___NO_ERR))\n    return err;',
            '  mol = linker_to_mod_or_lnk (___GSTATE->setup_params.linker);',
            '  init_symkey_glo1 (mol);', '  init_symkey_glo2 (mol);',
            '      err = setup_modules (___ps, mol, 0);'))
        ordinary = instrument_setup(original)
        observed = instrument_setup(original, initial=True)
        self.assertNotIn('gb_initial_begin', ordinary)
        for index in range(5):
            self.assertEqual(observed.count(f'gb_initial_end({index}, start);'), 1)
        for call in ('init_symkey_glo1 (mol);', 'init_symkey_glo2 (mol);',
                     'err = setup_modules (___ps, mol, 0);', 'return err;'):
            self.assertEqual(observed.count(call), original.count(call))

    def test_dynamic_passes_must_fit_complete_original_setups(self):
        loader = self.stats()
        row = dict(nanoseconds=[10, 20, 5], calls=[3] * 3)
        result = parse_dynamic_stats(row, loader)
        self.assertEqual(result['residualSetupNs'], 15)
        for broken in (dict(row, calls=[3, 2, 3]), dict(row, calls=[True] * 3),
                       dict(row, nanoseconds=[60, 0, 0]), dict(row, nanoseconds=[-1, 0, 0]),
                       dict(row, nanoseconds=[1.0, 0, 0])):
            with self.assertRaises(ValueError):
                parse_dynamic_stats(broken, loader)

    def test_dynamic_walks_delegate_callbacks_and_initial_path(self):
        original = '___HIDDEN ___SCMOBJ setup_modules\n' + '\n'.join(
            'for_each_module (ctx,\n' + ' ' * spaces + 'mol,\n' + ' ' * spaces + callback + ')'
            for spaces, callback in ((33, 'setup_module_fixup'),
                (37, 'setup_module_collect_undef_globals'), (33, 'setup_module_collect_moddescrs')))
        observed = instrument_dynamic_walks(original)
        self.assertIn('if (!ctx->collect_undef_glo) return for_each_module(ctx, mol, proc);', observed)
        self.assertIn('result = for_each_module(ctx, mol, proc);', observed)
        for index, callback in enumerate(('setup_module_fixup',
            'setup_module_collect_undef_globals', 'setup_module_collect_moddescrs')):
            self.assertEqual(observed.count(f'gb_dynamic_walk (ctx, mol, {callback}, {index})'), 1)

    def test_fixup_detail_requires_matching_completed_segments(self):
        row = dict(nanoseconds=[10, 20, 30, 40], calls=[5] * 4)
        self.assertEqual(parse_fixup_stats(row, dict(fixup=110))['unclassifiedFixupNs'], 10)
        for broken in (dict(row, calls=[5, 4, 5, 5]), dict(row, calls=[0] * 4),
                       dict(row, calls=[True] * 4), dict(row, nanoseconds=[200, 0, 0, 0]),
                       dict(row, nanoseconds=[-1, 0, 0, 0])):
            with self.assertRaises(ValueError):
                parse_fixup_stats(broken, dict(fixup=110))


if __name__ == '__main__':
    unittest.main()
