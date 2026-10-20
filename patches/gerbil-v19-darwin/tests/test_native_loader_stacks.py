import unittest
import xml.etree.ElementTree as ET

from attribute_native_loader_stacks import attribute


class NativeLoaderStackTest(unittest.TestCase):
    def root(self, state='Running', weight=100):
        return ET.fromstring(f'''<table>
          <binary id="image" path="/usr/lib/dyld"/>
          <frame id="atlas" name="dyld4::ExternallyViewableState::generateAtlas()"><binary ref="image"/></frame>
          <frame id="open" name="dyld4::APIs::dlopen_from()"/>
          <frame id="caller" name="___dynamic_load"/>
          <row><time/><process/><thread/><core/><state>{state}</state><weight>{weight}</weight>
          <sample><backtrace><frame ref="atlas"/><frame ref="open"/><frame ref="caller"/></backtrace></sample></row>
          </table>''')

    def test_references_and_overlapping_actual_stacks(self):
        report = attribute(self.root())
        groups = {row['name']: row['cycles'] for row in report['groups']}
        self.assertEqual(report['totalCycles'], 100)
        self.assertTrue(report['overlappingCategories'])
        self.assertEqual(groups['dlopen-stack-inclusive'], 100)
        self.assertEqual(groups['atlas-inside-dlopen-inclusive'], 100)
        self.assertEqual(report['loaderCallers'][0]['name'], '___dynamic_load')

    def test_nonrunning_and_negative_cycles_do_not_qualify(self):
        with self.assertRaisesRegex(ValueError, 'no positive'):
            attribute(self.root('Blocked'))
        with self.assertRaisesRegex(ValueError, 'negative'):
            attribute(self.root(weight=-1))


if __name__ == '__main__':
    unittest.main()
