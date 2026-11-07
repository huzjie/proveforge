# -*- coding: utf-8 -*-
"""CLI smoke tests: every subcommand runs without error."""
from __future__ import annotations

import unittest

from proveforge.cli import main
from tests.util import small_cfg


class TestCli(unittest.TestCase):
    def _run(self, *argv):
        # main() loads its own default config; we just assert it returns cleanly
        return main(list(argv))

    def test_doctor(self):
        self._run("doctor")

    def test_bench(self):
        self._run("bench")

    def test_modes(self):
        self._run("modes")

    def test_commit(self):
        self._run("commit")

    def test_audit(self):
        self._run("audit")

    def test_run(self):
        self._run("run", "--prompt", "p00")

    def test_prove(self):
        self._run("prove", "--prompt", "p00", "--ratio", "1.0")

    def test_verify(self):
        self._run("verify", "--prompt", "p00")

    def test_train(self):
        self._run("train", "--steps", "3")

    def test_help(self):
        import argparse
        with self.assertRaises(SystemExit):
            main(["--help"])


if __name__ == "__main__":
    unittest.main()
