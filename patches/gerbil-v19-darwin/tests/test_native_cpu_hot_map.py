from pathlib import Path
import copy
import json
import unittest
from unittest.mock import patch

from map_native_cpu_hotspots import crash_pc, host_address, relocations, retained_link_budget, text_bytes


class NativeHotMapTest(unittest.TestCase):
    def crash_fixture(self):
        native = dict(uuid='aabb', textBase=0x100000000, textStart=0x100000100,
                      textEnd=0x100000300, executableSections=[], starts=[0x100000100],
                      names={0x100000100: {'host'}})
        body = dict(faultingThread=0, exception={'signal': 'SIGSEGV'},
                    usedImages=[dict(uuid='AABB', arch='arm64', base=0x200000000, size=0x1000)],
                    threads=[dict(frames=[dict(imageIndex=0, imageOffset=0x140, symbol='host')],
                                  threadState=dict(flavor='ARM_THREAD_STATE64',
                                                   pc={'value': 0x200000140}))])
        return native, body

    @patch.object(Path, 'read_text')
    def test_crash_pc_requires_real_image_and_thread_address(self, read):
        native, body = self.crash_fixture()
        read.return_value = json.dumps({'procName': 'gerbil'})+'\n'+json.dumps(body)+'\n'
        result = crash_pc(Path('crash.ips'), native)
        self.assertEqual(result['unslidPC'], '0x100000140')
        self.assertEqual(result['function'], 'host')
        self.assertNotIn('cycles', result)

    @patch.object(Path, 'read_text')
    def test_crash_pc_rejects_wrong_image_pc_and_function(self, read):
        native, original = self.crash_fixture()
        for field in ('uuid', 'pc', 'function', 'signal', 'outside'):
            body = copy.deepcopy(original)
            if field == 'uuid':
                body['usedImages'][0]['uuid'] = 'wrong'
            elif field == 'pc':
                body['threads'][0]['threadState']['pc']['value'] += 4
            elif field == 'function':
                body['threads'][0]['frames'][0]['symbol'] = 'other'
            elif field == 'signal':
                body['exception']['signal'] = 'SIGABRT'
            else:
                body['threads'][0]['frames'][0]['imageOffset'] = 0x380
                body['threads'][0]['threadState']['pc']['value'] = 0x200000380
            read.return_value = json.dumps(body)
            with self.assertRaises(ValueError):
                crash_pc(Path('crash.ips'), native)

    def test_link_budget_requires_matching_successful_build(self):
        runtime = dict(qualified=True, diagnosticOnly=False, consumerFlagsChanged=False,
                       runtimeAbiChanged=False, gscUnchanged=True,
                       binaryHashes={'gxi': 'binary'}, coalescedLinkBytes=1234,
                       compileWallBudgetSeconds=900)
        self.assertEqual(retained_link_budget(runtime, 'binary', 1234), 900)
        for field in ('qualified', 'diagnosticOnly', 'consumerFlagsChanged',
                      'runtimeAbiChanged', 'gscUnchanged', 'binaryHashes',
                      'coalescedLinkBytes', 'compileWallBudgetSeconds'):
            incomplete = dict(runtime)
            incomplete.pop(field)
            with self.assertRaises(ValueError):
                retained_link_budget(incomplete, 'binary', 1234)
        for budget in (True, 299, 1201, 900.0):
            with self.assertRaises(ValueError):
                retained_link_budget(dict(runtime, compileWallBudgetSeconds=budget), 'binary', 1234)
        with self.assertRaises(ValueError):
            retained_link_budget(runtime, 'changed', 1234)
        with self.assertRaises(ValueError):
            retained_link_budget(runtime, 'binary', 1235)

    @patch('map_native_cpu_hotspots.subprocess.check_output')
    def test_text_comparison_ignores_only_header_and_address_columns(self, output):
        output.return_value = ('object:\nContents of (__TEXT,__text) section\n'
                               '00000000 01020304 aabbccdd\n00000008 00112233\n')
        self.assertEqual(text_bytes(Path('object')), bytes.fromhex('01020304aabbccdd00112233'))

    @patch('map_native_cpu_hotspots.subprocess.check_output')
    def test_relocations_compare_symbolic_text_records_not_other_sections(self, output):
        output.return_value = ('object:\nRELOCATION RECORDS FOR [__text]:\n'
                               'OFFSET TYPE VALUE\n0004 ARM64_RELOC_BRANCH26 _callee\n\n'
                               'RELOCATION RECORDS FOR [__data]:\n0000 other value\n')
        self.assertEqual(relocations(Path('object')),
                         ['OFFSET TYPE VALUE', '0004 ARM64_RELOC_BRANCH26 _callee'])

    @patch('map_native_cpu_hotspots.subprocess.check_output')
    def test_host_requires_unique_exact_symbol(self, output):
        output.return_value = '00000100 t _host\n00000200 t _host_other\n'
        self.assertEqual(host_address(Path('object'), 'host'), 0x100)
        with self.assertRaises(ValueError):
            host_address(Path('object'), 'unknown')
        output.return_value = '00000100 t _host\n00000200 t _host\n'
        with self.assertRaises(ValueError):
            host_address(Path('object'), 'host')


if __name__ == '__main__':
    unittest.main()
