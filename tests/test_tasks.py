# -*- coding: utf-8 -*-
"""Task registry."""
from __future__ import annotations

import unittest

from proveforge.tasks import list_tasks, get_task


class TestTasks(unittest.TestCase):
    def test_five_capabilities(self):
        tasks = list_tasks()
        self.assertEqual(len(tasks), 5)
        ids = [t["id"] for t in tasks]
        self.assertEqual(ids, ["commit", "prove", "verify", "audit", "detect"])

    def test_get_task(self):
        self.assertEqual(get_task("prove")["name"], "生成证明")
        self.assertIsNone(get_task("nope"))


if __name__ == "__main__":
    unittest.main()
