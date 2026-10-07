from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

from hd2_archive import entries, make_archive, read_resource, resource_hash


class ToolchainTests(unittest.TestCase):
    def test_archive_round_trip(self):
        resources = {
            resource_hash('mods/netherdivers/probe'): b'\x01\x02hello',
            resource_hash('mods/netherdivers/second'): b'payload',
        }
        archive = make_archive(resources)
        self.assertEqual(len(entries(archive)), 2)
        self.assertEqual(read_resource(archive, 'mods/netherdivers/probe'), b'\x01\x02hello')

    def test_luajit21_runtime_is_available(self):
        from lupa.luajit21 import LuaRuntime
        lua = LuaRuntime(unpack_returned_tuples=True)
        self.assertEqual(lua.eval('6 * 7'), 42)
        self.assertTrue(lua.eval('bit and true or false'))
        self.assertEqual(lua.eval('bit.band(0xF0, 0x0F)'), 0)


if __name__ == '__main__':
    unittest.main()
