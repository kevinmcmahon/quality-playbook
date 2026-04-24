#!/usr/bin/env python3
"""Tests for quality_gate.extract_req_pattern (v1.5.2, Lever 2 REQ Pattern field)."""

import sys
import unittest
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PACKAGE_DIR))

import quality_gate  # noqa: E402


class ReqPatternTests(unittest.TestCase):
    def test_absent_returns_none(self):
        block = "### REQ-001: do a thing\n- Summary: foo\n"
        self.assertIsNone(quality_gate.extract_req_pattern(block))

    def test_whitelist_accepted(self):
        block = "### REQ-010: feature bits\n- Pattern: whitelist\n"
        self.assertEqual(quality_gate.extract_req_pattern(block), "whitelist")

    def test_parity_accepted(self):
        block = "### REQ-020: encode/decode parity\n- Pattern: parity\n"
        self.assertEqual(quality_gate.extract_req_pattern(block), "parity")

    def test_compensation_accepted(self):
        block = "### REQ-030: filter compensation\n- Pattern: compensation\n"
        self.assertEqual(quality_gate.extract_req_pattern(block), "compensation")

    def test_invalid_raises(self):
        block = "### REQ-010: x\n- Pattern: bogus\n"
        with self.assertRaises(ValueError):
            quality_gate.extract_req_pattern(block)

    def test_case_insensitive_key(self):
        block = "### REQ-010: x\n- pattern: whitelist\n"
        self.assertEqual(quality_gate.extract_req_pattern(block), "whitelist")


if __name__ == "__main__":
    unittest.main()
