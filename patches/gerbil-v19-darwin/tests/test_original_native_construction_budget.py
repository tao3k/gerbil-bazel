import unittest

from retry_original_native_units import construction_budget


class OriginalNativeConstructionBudgetTests(unittest.TestCase):
    def receipt(self):
        return dict(qualified=True, consumerFlagsChanged=False, runtimeAbiChanged=False,
                    runtimeOptimization='O1', compileWallBudgetSeconds=900)

    def test_existing_successful_construction_budget(self):
        self.assertEqual(construction_budget(self.receipt()), 900)

    def test_failed_or_changed_configuration_cannot_supply_budget(self):
        for key, value in (('qualified', False), ('consumerFlagsChanged', True),
                           ('runtimeAbiChanged', True), ('runtimeOptimization', 'O3')):
            receipt = self.receipt()
            receipt[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                construction_budget(receipt)

    def test_arbitrary_budget_is_not_accepted(self):
        for value in (180, 901, None):
            receipt = self.receipt()
            receipt['compileWallBudgetSeconds'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                construction_budget(receipt)
