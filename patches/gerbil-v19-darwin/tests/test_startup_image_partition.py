import unittest

from repack_startup_images import partition_images


class ImagePartitionTest(unittest.TestCase):
    def test_default_keeps_original_greedy_shape(self):
        rows = [dict(index=i, linkerBasename=name) for i, name in enumerate(['a', 'b', 'a', 'c', 'b'])]
        self.assertEqual([[row['index'] for row in group] for group in partition_images(rows)],
                         [[0, 1, 3], [2, 4]])

    def test_bounded_groups_keep_every_entry_once(self):
        rows = [dict(index=i, linkerBasename=str(i % 7)) for i in reversed(range(53))]
        groups = partition_images(rows, 4)
        self.assertEqual(sorted(row['index'] for group in groups for row in group), list(range(53)))
        for group in groups:
            self.assertLessEqual(len(group), 4)
            self.assertEqual(len({row['linkerBasename'] for row in group}), len(group))
            self.assertEqual([row['index'] for row in group], sorted(row['index'] for row in group))

    def test_empty(self):
        self.assertEqual(partition_images([], 32), [])

    def test_refuses_invalid_limits(self):
        for limit in [-1, 1, True, 2.5, '32']:
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                partition_images([], limit)
