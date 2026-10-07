from __future__ import annotations

import unittest
from pathlib import Path

from lupa.luajit21 import LuaRuntime


ROOT = Path(__file__).resolve().parents[1]


class Plas15LogicTests(unittest.TestCase):
    def setUp(self) -> None:
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(
            "package.preload['mods/skyeshade/hd2runtime'] = function() "
            "return {mod=function() return {log=function() end} end, "
            "every=function() return {cancel=function() end} end} end"
        )
        self.lua.execute((ROOT / 'mods/netherdivers/plas15.lua').read_text(encoding='utf-8'))
        self.behavior = self.lua.globals().NetherdiversPlas15Behavior

    def tick(self, state, now, unsafe, held):
        return self.behavior.tick(state, now, unsafe, held)

    def test_safe_mode_is_noop(self):
        state = self.behavior.new()
        self.tick(state, 0.0, False, True)
        self.tick(state, 5.0, False, True)
        self.assertIsNone(state['result'])
        self.assertFalse(state['magazine_clear_required'])

    def test_warning_and_overcharge_at_four_seconds(self):
        state = self.behavior.new()
        self.tick(state, 0.0, True, True)
        self.tick(state, 4.0, True, True)
        self.assertTrue(state['warning'])
        self.tick(state, 4.1, True, False)
        self.assertEqual(state['result'], 'overcharge')
        self.assertTrue(state['magazine_clear_required'])

    def test_penalty_at_four_point_five_seconds(self):
        state = self.behavior.new()
        self.tick(state, 0.0, True, True)
        self.tick(state, 4.5, True, True)
        self.assertEqual(state['result'], 'penalty')
        self.assertTrue(state['magazine_clear_required'])

    def test_penalty_persists_when_trigger_is_released(self):
        state = self.behavior.new()
        self.tick(state, 0.0, True, True)
        self.tick(state, 4.5, True, True)
        self.tick(state, 4.6, True, False)
        self.assertEqual(state['result'], 'penalty')
        self.assertTrue(state['magazine_clear_required'])

    def test_new_charge_starts_with_clean_state(self):
        state = self.behavior.new()
        self.tick(state, 0.0, True, True)
        self.tick(state, 4.0, True, False)
        self.tick(state, 5.0, True, True)
        self.assertIsNone(state['result'])
        self.assertFalse(state['magazine_clear_required'])


if __name__ == '__main__':
    unittest.main()
