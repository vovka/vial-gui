# SPDX-License-Identifier: GPL-2.0-or-later
import unittest

from protocol.dummy_keyboard import DummyKeyboard
from keycodes.keycodes import Keycode, recreate_keyboard_keycodes, update_macro_labels, \
    get_macro_text_preview, format_macro_label, KEYCODES_MACRO
from macro.macro_action import ActionTap, ActionDown, ActionText, ActionDelay, ActionUp
from macro.macro_key import KeyDown, KeyTap, KeyUp, KeyString
from macro.macro_optimizer import remove_repeats, replace_with_tap, replace_with_string

KC_A = Keycode.find_by_qmk_id("KC_A")
KC_B = Keycode.find_by_qmk_id("KC_B")
KC_C = Keycode.find_by_qmk_id("KC_C")

CMB_TOG = Keycode.find_by_qmk_id("CMB_TOG")


class TestMacro(unittest.TestCase):

    def test_remove_repeats(self):
        self.assertEqual(remove_repeats([KeyDown(KC_A), KeyDown(KC_A)]), [KeyDown(KC_A)])
        self.assertEqual(remove_repeats([KeyDown(KC_A), KeyDown(KC_B), KeyDown(KC_B), KeyDown(KC_C), KeyDown(KC_C)]),
                         [KeyDown(KC_A), KeyDown(KC_B), KeyDown(KC_C)])

        # don't remove repeated taps
        self.assertEqual(remove_repeats([KeyTap(KC_A), KeyTap(KC_A)]), [KeyTap(KC_A), KeyTap(KC_A)])

    def test_replace_tap(self):
        self.assertEqual(replace_with_tap([KeyDown(KC_A)]), [KeyDown(KC_A)])
        self.assertEqual(replace_with_tap([KeyDown(KC_A), KeyUp(KC_A)]), [KeyTap(KC_A)])
        self.assertEqual(replace_with_tap([KeyUp(KC_A), KeyDown(KC_A)]), [KeyUp(KC_A), KeyDown(KC_A)])

    def test_replace_string(self):
        self.assertEqual(replace_with_string([KeyTap(KC_A), KeyTap(KC_B)]), [KeyString("ab")])

    def test_serialize_v1(self):
        kb = DummyKeyboard(None)
        kb.vial_protocol = 1
        data = kb.macro_serialize([ActionText("Hello"), ActionTap(["KC_A", "KC_B", "KC_C"]), ActionText("World"),
                                   ActionDown(["KC_C", "KC_B", "KC_A"])])
        self.assertEqual(data, b"Hello\x01\x04\x01\x05\x01\x06World\x02\x06\x02\x05\x02\x04")

    def test_deserialize_v1(self):
        kb = DummyKeyboard(None)
        kb.vial_protocol = 1
        macro = kb.macro_deserialize(b"Hello\x01\x04\x01\x05\x01\x06World\x02\x06\x02\x05\x02\x04")
        self.assertEqual(macro, [ActionText("Hello"), ActionTap(["KC_A", "KC_B", "KC_C"]), ActionText("World"),
                                 ActionDown(["KC_C", "KC_B", "KC_A"])])

    def test_serialize_v2(self):
        kb = DummyKeyboard(None)
        kb.vial_protocol = 2
        data = kb.macro_serialize([ActionText("Hello"), ActionTap(["KC_A", "KC_B", "KC_C"]), ActionText("World"),
                                   ActionDown(["KC_C", "KC_B", "KC_A"]), ActionDelay(1000)])
        self.assertEqual(data, b"Hello\x01\x01\x04\x01\x01\x05\x01\x01\x06World\x01\x02\x06\x01\x02\x05\x01\x02\x04"
                               b"\x01\x04\xEC\x04")
        data = kb.macro_serialize([ActionText("Hello"), ActionTap(["KC_A", "KC_B", "KC_C"]), ActionText("World"),
                                   ActionDown(["KC_C", "KC_B", "KC_A"]), ActionDelay(0)])
        self.assertEqual(data, b"Hello\x01\x01\x04\x01\x01\x05\x01\x01\x06World\x01\x02\x06\x01\x02\x05\x01\x02\x04"
                               b"\x01\x04\x01\x01")
        data = kb.macro_serialize([ActionText("Hello"), ActionTap(["KC_A", "KC_B", "KC_C"]), ActionText("World"),
                                   ActionDown(["KC_C", "KC_B", "KC_A"]), ActionDelay(1)])
        self.assertEqual(data, b"Hello\x01\x01\x04\x01\x01\x05\x01\x01\x06World\x01\x02\x06\x01\x02\x05\x01\x02\x04"
                               b"\x01\x04\x02\x01")
        data = kb.macro_serialize([ActionText("Hello"), ActionTap(["KC_A", "KC_B", "KC_C"]), ActionText("World"),
                                   ActionDown(["KC_C", "KC_B", "KC_A"]), ActionDelay(256)])
        self.assertEqual(data, b"Hello\x01\x01\x04\x01\x01\x05\x01\x01\x06World\x01\x02\x06\x01\x02\x05\x01\x02\x04"
                               b"\x01\x04\x02\x02")

    def test_deserialize_v2(self):
        kb = DummyKeyboard(None)
        kb.vial_protocol = 2
        macro = kb.macro_deserialize(b"Hello\x01\x01\x04\x01\x01\x05\x01\x01\x06World\x01\x02\x06\x01\x02\x05"
                                     b"\x01\x02\x04\x01\x04\xEC\x04")
        self.assertEqual(macro, [ActionText("Hello"), ActionTap(["KC_A", "KC_B", "KC_C"]), ActionText("World"),
                                 ActionDown(["KC_C", "KC_B", "KC_A"]), ActionDelay(1000)])
        macro = kb.macro_deserialize(b"Hello\x01\x01\x04\x01\x01\x05\x01\x01\x06World\x01\x02\x06\x01\x02\x05"
                                     b"\x01\x02\x04\x01\x04\x01\x01")
        self.assertEqual(macro, [ActionText("Hello"), ActionTap(["KC_A", "KC_B", "KC_C"]), ActionText("World"),
                                 ActionDown(["KC_C", "KC_B", "KC_A"]), ActionDelay(0)])
        macro = kb.macro_deserialize(b"Hello\x01\x01\x04\x01\x01\x05\x01\x01\x06World\x01\x02\x06\x01\x02\x05"
                                     b"\x01\x02\x04\x01\x04\x02\x01")
        self.assertEqual(macro, [ActionText("Hello"), ActionTap(["KC_A", "KC_B", "KC_C"]), ActionText("World"),
                                 ActionDown(["KC_C", "KC_B", "KC_A"]), ActionDelay(1)])
        macro = kb.macro_deserialize(b"Hello\x01\x01\x04\x01\x01\x05\x01\x01\x06World\x01\x02\x06\x01\x02\x05"
                                     b"\x01\x02\x04\x01\x04\x02\x02")
        self.assertEqual(macro, [ActionText("Hello"), ActionTap(["KC_A", "KC_B", "KC_C"]), ActionText("World"),
                                 ActionDown(["KC_C", "KC_B", "KC_A"]), ActionDelay(256)])

    def test_save(self):
        down = ActionDown(["KC_A", "KC_B", "CMB_TOG"])
        self.assertEqual(down.save(), ["down", "KC_A", "KC_B", "CMB_TOG"])
        tap = ActionTap(["CMB_TOG", "KC_B", "KC_A"])
        self.assertEqual(tap.save(), ["tap", "CMB_TOG", "KC_B", "KC_A"])
        text = ActionText("Hello world")
        self.assertEqual(text.save(), ["text", "Hello world"])
        delay = ActionDelay(123)
        self.assertEqual(delay.save(), ["delay", 123])

    def test_restore(self):
        down = ActionDown()
        down.restore(["down", "KC_A", "KC_B", "CMB_TOG"])
        self.assertEqual(down, ActionDown(["KC_A", "KC_B", "CMB_TOG"]))
        tap = ActionTap()
        tap.restore(["tap", "CMB_TOG", "KC_B", "KC_A"])
        self.assertEqual(tap, ActionTap(["CMB_TOG", "KC_B", "KC_A"]))
        text = ActionText()
        text.restore(["text", "Hello world"])
        self.assertEqual(text, ActionText("Hello world"))
        delay = ActionDelay()
        delay.restore(["delay", 123])
        self.assertEqual(delay, ActionDelay(123))

    def test_twobyte_keycodes(self):
        kb = DummyKeyboard(None)
        kb.vial_protocol = 2
        # TODO remove once keycodes are properly owned by the Keyboard object
        kb.tap_dance_count = 0
        recreate_keyboard_keycodes(kb)

        data = kb.macro_serialize([ActionTap(["CMB_TOG", "KC_A"])])
        self.assertEqual(data, b"\x01\x05\xF9\x5C\x01\x01\x04")
        data = kb.macro_serialize([ActionDown(["CMB_TOG", "KC_A"])])
        self.assertEqual(data, b"\x01\x06\xF9\x5C\x01\x02\x04")
        data = kb.macro_serialize([ActionUp(["CMB_TOG", "KC_A"])])
        self.assertEqual(data, b"\x01\x07\xF9\x5C\x01\x03\x04")

        macro = kb.macro_deserialize(b"\x01\x05\xF9\x5C\x01\x01\x04")
        self.assertEqual(macro, [ActionTap(["CMB_TOG", "KC_A"])])
        macro = kb.macro_deserialize(b"\x01\x06\xF9\x5C\x01\x02\x04")
        self.assertEqual(macro, [ActionDown(["CMB_TOG", "KC_A"])])
        macro = kb.macro_deserialize(b"\x01\x07\xF9\x5C\x01\x03\x04")
        self.assertEqual(macro, [ActionUp(["CMB_TOG", "KC_A"])])

    def test_twobyte_with_zeroes(self):
        kb = DummyKeyboard(None)
        kb.vial_protocol = 2
        data = kb.macro_serialize([ActionTap([Keycode.serialize(0xA000), Keycode.serialize(0xB100), Keycode.serialize(0xC200)])])
        self.assertEqual(data, b"\x01\x05\xA0\xFF\x01\x05\xB1\xFF\x01\x05\xC2\xFF")

        macro = kb.macro_deserialize(b"\x01\x05\xC2\xFF\x01\x05\xB1\xFF\x01\x05\xA0\xFF")
        self.assertEqual(macro, [ActionTap([Keycode.serialize(0xC200), Keycode.serialize(0xB100), Keycode.serialize(0xA000)])])

    def test_macro_text_preview(self):
        # Test with text only
        actions = [ActionText("git log -1")]
        self.assertEqual(get_macro_text_preview(actions), "git log -1")

        # Test with multiple text actions
        actions = [ActionText("Hello "), ActionText("World")]
        self.assertEqual(get_macro_text_preview(actions), "Hello World")

        # Test with mixed actions - only text should be extracted
        actions = [ActionText("prefix"), ActionTap(["KC_A"]), ActionText("suffix")]
        self.assertEqual(get_macro_text_preview(actions), "prefixsuffix")

        # Test with no text actions
        actions = [ActionTap(["KC_A", "KC_B"])]
        self.assertIsNone(get_macro_text_preview(actions))

        # Test truncation (default max_len is 36)
        long_text = "This is a very long macro text that should be truncated at some point"
        actions = [ActionText(long_text)]
        preview = get_macro_text_preview(actions)
        self.assertEqual(len(preview), 36)
        self.assertTrue(preview.endswith('…'))

        # Test empty macro
        actions = []
        self.assertIsNone(get_macro_text_preview(actions))

    def test_format_macro_label(self):
        # Short text fits on one line
        self.assertEqual(format_macro_label(0, "hi"), 'M0("hi")')

        # Medium text wraps to multiple lines
        label = format_macro_label(0, "git log -1")
        self.assertTrue(label.startswith('M0("'))
        self.assertTrue(label.endswith('")'))
        # Text is split across lines, so check without newlines
        self.assertIn("git", label)
        self.assertIn("log -1", label)

        # Long text gets split across lines
        label = format_macro_label(12, "this is a longer text")
        self.assertTrue(label.startswith('M12("'))
        self.assertTrue(label.endswith('")'))
        self.assertIn('\n', label)

        # Very long text gets truncated on third line
        label = format_macro_label(0, "a" * 50)
        lines = label.split('\n')
        self.assertLessEqual(len(lines), 3)
        self.assertTrue(label.endswith('")'))

        # Empty preview returns simple label
        self.assertEqual(format_macro_label(5, None), 'M5')

    def test_update_macro_labels(self):
        kb = DummyKeyboard(None)
        kb.vial_protocol = 2
        kb.tap_dance_count = 0
        kb.macro_count = 3
        kb.macro_memory = 900
        recreate_keyboard_keycodes(kb)

        # Set up macros: one text macro, one keycode macro, one empty
        macro0 = kb.macro_serialize([ActionText("git log -1")])
        macro1 = kb.macro_serialize([ActionTap(["KC_A", "KC_B"])])
        macro2 = b""
        kb.macro = macro0 + b"\x00" + macro1 + b"\x00" + macro2 + b"\x00"

        update_macro_labels(kb)

        # Macro 0 should have text preview in M0("...") format and smaller font
        self.assertTrue(KEYCODES_MACRO[0].label.startswith('M0("'))
        # Text wraps across lines, check parts are present
        self.assertIn("git", KEYCODES_MACRO[0].label)
        self.assertIn("log -1", KEYCODES_MACRO[0].label)
        self.assertEqual(KEYCODES_MACRO[0].font_scale, 0.7)

        # Macro 1 (keycode only) should have default label and normal font
        self.assertEqual(KEYCODES_MACRO[1].label, "M1")
        self.assertEqual(KEYCODES_MACRO[1].font_scale, 1.0)

        # Macro 2 (empty) should have default label and normal font
        self.assertEqual(KEYCODES_MACRO[2].label, "M2")
        self.assertEqual(KEYCODES_MACRO[2].font_scale, 1.0)
