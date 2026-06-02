# SPDX-License-Identifier: GPL-2.0-or-later
import unittest
from unittest.mock import patch

from PyQt5.QtCore import QSettings

from protocol.dummy_keyboard import DummyKeyboard
from editor import macro_recorder as macro_recorder_module
from keycodes.keycodes import Keycode, recreate_keyboard_keycodes, update_macro_labels, \
    get_macro_text_preview, get_macro_key_preview, get_macro_alias, format_macro_label, KEYCODES_MACRO, \
    update_tap_dance_labels, KEYCODES_TAP_DANCE
from macro.macro_action import ActionTap, ActionDown, ActionText, ActionDelay, ActionUp
from macro.macro_key import KeyDown, KeyTap, KeyUp, KeyString
from macro.macro_optimizer import remove_repeats, replace_with_tap, replace_with_string

KC_A = Keycode.find_by_qmk_id("KC_A")
KC_B = Keycode.find_by_qmk_id("KC_B")
KC_C = Keycode.find_by_qmk_id("KC_C")

CMB_TOG = Keycode.find_by_qmk_id("CMB_TOG")


class FakeMacroRecorderTab:

    def __init__(self, alias, actions):
        self._alias = alias
        self._actions = actions

    def alias(self):
        return self._alias

    def set_alias(self, alias):
        self._alias = alias

    def actions(self):
        return self._actions

    def replace_actions(self, actions):
        self._actions = actions


class FakeMacroRecorderTabs:

    def __init__(self):
        self.current_index = None

    def setCurrentIndex(self, index):
        self.current_index = index


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

    def test_macro_key_preview(self):
        actions = [ActionTap(["KC_A"])]
        self.assertEqual(get_macro_key_preview(actions), "A")

        actions = [ActionDown(["KC_A"])]
        self.assertEqual(get_macro_key_preview(actions), "A↓")

        actions = [ActionUp(["KC_B"])]
        self.assertEqual(get_macro_key_preview(actions), "B↑")

        actions = [ActionDown(["KC_A", "KC_B"]), ActionTap(["KC_C"])]
        self.assertEqual(get_macro_key_preview(actions), "A↓ B↓ C")

        actions = [ActionDelay(10)]
        self.assertIsNone(get_macro_key_preview(actions))

    def test_format_macro_label(self):
        # Short text fits on one line
        self.assertEqual(format_macro_label(0, "hi"), "M(0)\nhi")

        # Medium text wraps to multiple lines
        label = format_macro_label(0, "git log -1")
        self.assertTrue(label.startswith("M(0)\n"))
        # Text is split across lines, so check without newlines
        self.assertIn("git", label)
        self.assertIn("log -1", label)

        # Long text gets split across lines
        label = format_macro_label(12, "this is a longer text")
        self.assertTrue(label.startswith("M(12)\n"))
        self.assertIn('\n', label)

        # Very long text gets truncated on third line
        label = format_macro_label(0, "a" * 50)
        lines = label.split('\n')
        self.assertLessEqual(len(lines), 3)
        self.assertTrue(lines[-1].endswith('…'))

        # Empty preview returns simple label
        self.assertEqual(format_macro_label(5, None), 'M(5)')

    def _macro_recorder_for_alias_reorder(self):
        recorder = macro_recorder_module.MacroRecorder.__new__(macro_recorder_module.MacroRecorder)
        keyboard = DummyKeyboard(None)
        keyboard.keyboard_id = "unit-test-macro-recorder-alias-reorder"
        keyboard.macro_count = 3
        keyboard.layout = {}
        keyboard.encoder_layout = {}
        keyboard.save_macro_aliases(["One", "Two", "Three"])

        recorder.keyboard = keyboard
        recorder.suppress_change = False
        recorder.macro_tabs = [
            FakeMacroRecorderTab("One", ["action-0"]),
            FakeMacroRecorderTab("Two", ["action-1"]),
            FakeMacroRecorderTab("Three", ["action-2"]),
        ]
        recorder.tabs = FakeMacroRecorderTabs()
        recorder.on_change = lambda: None
        recorder._reload_tab = lambda index, actions: recorder.macro_tabs[index].replace_actions(actions)
        return recorder

    def test_macro_reorder_helpers_move_aliases_with_macro_contents(self):
        recorder = macro_recorder_module.MacroRecorder.__new__(macro_recorder_module.MacroRecorder)
        cases = [
            (False, [["macro-1"], ["macro-2"], ["macro-0"]], ["numbers", "symbols", "language switch"]),
            (True, [["macro-2"], ["macro-1"], ["macro-0"]], ["symbols", "numbers", "language switch"]),
        ]

        for is_swap, expected_actions, expected_aliases in cases:
            with self.subTest(is_swap=is_swap):
                actions = [["macro-0"], ["macro-1"], ["macro-2"]]
                aliases = ["language switch", "numbers", "symbols"]

                self.assertEqual(recorder._reorder_items(actions, 0, 2, is_swap), expected_actions)
                self.assertEqual(recorder._reorder_items(aliases, 0, 2, is_swap), expected_aliases)

    def test_macro_tab_reorder_moves_aliases_with_actions_without_persisting_them(self):
        settings = QSettings("Vial", "Vial")
        settings.remove("macro_aliases/unit-test-macro-recorder-alias-reorder")
        recorder = self._macro_recorder_for_alias_reorder()
        expected_aliases = ["Two", "Three", "One"]

        def assert_labels_refreshed_after_aliases_are_updated(keyboard):
            self.assertEqual(keyboard.macro_aliases, expected_aliases)

        with patch.object(macro_recorder_module, "update_macro_labels",
                          side_effect=assert_labels_refreshed_after_aliases_are_updated) as update_labels, \
                patch.object(macro_recorder_module.KeycodeDisplay, "refresh_clients") as refresh_clients:
            recorder.on_tabs_reordered(0, 2, False)

        self.assertEqual([tab.alias() for tab in recorder.macro_tabs], expected_aliases)
        self.assertEqual([tab.actions() for tab in recorder.macro_tabs], [["action-1"], ["action-2"], ["action-0"]])
        self.assertEqual(recorder.keyboard.macro_aliases, expected_aliases)
        self.assertEqual(recorder.tabs.current_index, 2)
        update_labels.assert_called_once_with(recorder.keyboard)
        refresh_clients.assert_called_once_with()
        self.assertEqual(recorder.keyboard.load_macro_aliases(), ["One", "Two", "Three"])
        settings.remove(recorder.keyboard._macro_alias_settings_key())

    def test_macro_tab_swap_swaps_aliases_with_actions_without_persisting_them(self):
        settings = QSettings("Vial", "Vial")
        settings.remove("macro_aliases/unit-test-macro-recorder-alias-reorder")
        recorder = self._macro_recorder_for_alias_reorder()
        expected_aliases = ["Three", "Two", "One"]

        def assert_labels_refreshed_after_aliases_are_updated(keyboard):
            self.assertEqual(keyboard.macro_aliases, expected_aliases)

        with patch.object(macro_recorder_module, "update_macro_labels",
                          side_effect=assert_labels_refreshed_after_aliases_are_updated) as update_labels, \
                patch.object(macro_recorder_module.KeycodeDisplay, "refresh_clients") as refresh_clients:
            recorder.on_tabs_reordered(0, 2, True)

        self.assertEqual([tab.alias() for tab in recorder.macro_tabs], expected_aliases)
        self.assertEqual([tab.actions() for tab in recorder.macro_tabs], [["action-2"], ["action-1"], ["action-0"]])
        self.assertEqual(recorder.keyboard.macro_aliases, expected_aliases)
        self.assertEqual(recorder.tabs.current_index, 2)
        update_labels.assert_called_once_with(recorder.keyboard)
        refresh_clients.assert_called_once_with()
        self.assertEqual(recorder.keyboard.load_macro_aliases(), ["One", "Two", "Three"])
        settings.remove(recorder.keyboard._macro_alias_settings_key())

    def test_tap_dance_labels_use_macro_aliases_instead_of_macro_content(self):
        kb = DummyKeyboard(None)
        kb.vial_protocol = 2
        kb.tap_dance_count = 1
        kb.macro_count = 1
        kb.macro_memory = 900
        kb.macro_aliases = ["language switch"]
        recreate_keyboard_keycodes(kb)

        macro0 = kb.macro_serialize([ActionText("git log -1")])
        kb.macro = macro0 + b"\x00"
        kb.tap_dance_entries = [("M0", "KC_NO", "KC_NO", "KC_NO", 200)]

        update_macro_labels(kb)
        update_tap_dance_labels(kb)

        label = KEYCODES_TAP_DANCE[0].label.replace("\n", " ")
        self.assertIn("language switch", label)
        self.assertNotIn("git log -1", label)
        self.assertNotIn("git", KEYCODES_TAP_DANCE[0].label)
        self.assertNotIn("log -1", KEYCODES_TAP_DANCE[0].label)

    def test_macro_alias_normalization_and_persistence(self):
        kb = DummyKeyboard(None)
        kb.keyboard_id = "unit-test-macro-aliases"
        kb.macro_count = 3

        settings = QSettings("Vial", "Vial")
        settings.remove(kb._macro_alias_settings_key())

        self.assertEqual(kb.normalize_macro_aliases([" First ", 12]), ["First", "12", ""])

        kb.save_macro_aliases([" First ", "Second", "Extra", "Ignored"])
        self.assertEqual(kb.macro_aliases, ["First", "Second", "Extra"])

        reloaded = DummyKeyboard(None)
        reloaded.keyboard_id = kb.keyboard_id
        reloaded.macro_count = 3
        self.assertEqual(reloaded.load_macro_aliases(), ["First", "Second", "Extra"])

        settings.remove(kb._macro_alias_settings_key())

    def test_get_macro_alias_ignores_missing_and_empty_aliases(self):
        kb = DummyKeyboard(None)
        kb.macro_count = 3
        kb.macro_aliases = [" Build ", "", None]

        self.assertEqual(get_macro_alias(kb, 0), "Build")
        self.assertIsNone(get_macro_alias(kb, 1))
        self.assertIsNone(get_macro_alias(kb, 2))
        self.assertIsNone(get_macro_alias(kb, 3))

        del kb.macro_aliases
        self.assertIsNone(get_macro_alias(kb, 0))

    def test_update_macro_labels_prefers_aliases_over_macro_content(self):
        kb = DummyKeyboard(None)
        kb.vial_protocol = 2
        kb.tap_dance_count = 0
        kb.macro_count = 2
        kb.macro_memory = 900
        kb.macro_aliases = [" Build Firmware ", ""]
        recreate_keyboard_keycodes(kb)

        macro0 = kb.macro_serialize([ActionText("secret content")])
        macro1 = kb.macro_serialize([ActionText("public content")])
        kb.macro = macro0 + b"\x00" + macro1 + b"\x00"

        update_macro_labels(kb)

        self.assertEqual(KEYCODES_MACRO[0].label, "M(0)\nBuild\nFirmware")
        self.assertEqual(KEYCODES_MACRO[0].tooltip, "Macro 0: Build Firmware")
        self.assertEqual(KEYCODES_MACRO[0].font_scale, 0.7)
        self.assertNotIn("secret", KEYCODES_MACRO[0].label)
        self.assertNotIn("secret", KEYCODES_MACRO[0].tooltip)

        self.assertIn("public", KEYCODES_MACRO[1].label)
        self.assertIn("public", KEYCODES_MACRO[1].tooltip)

    def test_update_macro_labels(self):
        kb = DummyKeyboard(None)
        kb.vial_protocol = 2
        kb.tap_dance_count = 0
        kb.macro_count = 4
        kb.macro_memory = 900
        kb.macro_aliases = ["language switch", "", "", ""]
        recreate_keyboard_keycodes(kb)

        # Set up macros: one text macro, two keycode macros, one empty
        macro0 = kb.macro_serialize([ActionText("git log -1")])
        macro1 = kb.macro_serialize([ActionTap(["KC_A", "KC_B"])])
        macro2 = kb.macro_serialize([ActionDown(["KC_C"])])
        macro3 = b""
        kb.macro = macro0 + b"\x00" + macro1 + b"\x00" + macro2 + b"\x00" + macro3 + b"\x00"

        update_macro_labels(kb)

        # Macro 0 should prefer the alias and hide macro content previews
        self.assertTrue(KEYCODES_MACRO[0].label.startswith("M(0)\n"))
        self.assertIn("language switch", KEYCODES_MACRO[0].label.replace("\n", " "))
        self.assertNotIn("git log -1", KEYCODES_MACRO[0].label.replace("\n", " "))
        self.assertNotIn("git", KEYCODES_MACRO[0].label)
        self.assertNotIn("log -1", KEYCODES_MACRO[0].label)
        self.assertNotIn("A B", KEYCODES_MACRO[0].label)
        self.assertEqual(KEYCODES_MACRO[0].font_scale, 0.7)

        # Macro 1 (keycode tap) should show key preview and smaller font
        self.assertEqual(KEYCODES_MACRO[1].label, "M(1)\nA B")
        self.assertEqual(KEYCODES_MACRO[1].font_scale, 0.7)

        # Macro 2 (key down) should show key preview with arrow and smaller font
        self.assertEqual(KEYCODES_MACRO[2].label, "M(2)\nC↓")
        self.assertEqual(KEYCODES_MACRO[2].font_scale, 0.7)

        # Macro 3 (empty) should have default label and normal font
        self.assertEqual(KEYCODES_MACRO[3].label, "M(3)")
        self.assertEqual(KEYCODES_MACRO[3].font_scale, 1.0)
