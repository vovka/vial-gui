# SPDX-License-Identifier: GPL-2.0-or-later
from editor.layer_detector import LayerDetector
from keycodes.keycodes import Keycode


class MatrixLayerManager:
    """Manages layer state for the Matrix Tester."""

    def __init__(self):
        self._current_layer = 0
        self._toggled_layers = set()
        self._momentary_layers = set()
        self._keyboard = None
        self._active_layer_keys = {}
        self._tri_layer_held = set()  # Track which tri-layer keys are held

    def set_keyboard(self, keyboard):
        """Set the keyboard reference for accessing layout data."""
        self._keyboard = keyboard
        self.reset()

    def reset(self):
        """Reset layer state to defaults."""
        self._current_layer = 0
        self._toggled_layers.clear()
        self._momentary_layers.clear()
        self._active_layer_keys.clear()
        self._tri_layer_held.clear()

    @property
    def current_layer(self):
        """Get the currently active layer."""
        return self._current_layer

    @current_layer.setter
    def current_layer(self, layer):
        """Manually set the current layer."""
        if self._keyboard and 0 <= layer < self._keyboard.layers:
            self._current_layer = layer
            self._toggled_layers.clear()
            self._momentary_layers.clear()
            self._active_layer_keys.clear()
            self._tri_layer_held.clear()

    def get_keycode_for_widget(self, widget):
        """Get the keycode for a widget at the current layer."""
        if not self._keyboard:
            return None
        if widget.desc.row is not None:
            key = (self._current_layer, widget.desc.row, widget.desc.col)
            return self._keyboard.layout.get(key)
        elif widget.desc.encoder_idx is not None:
            key = (self._current_layer, widget.desc.encoder_idx, widget.desc.encoder_dir)
            return self._keyboard.encoder_layout.get(key)
        return None

    def _get_keycode_at_layer(self, widget, layer):
        """Get the keycode for a widget at a specific layer."""
        if not self._keyboard:
            return None
        if widget.desc.row is not None:
            key = (layer, widget.desc.row, widget.desc.col)
            return self._keyboard.layout.get(key)
        return None

    def _serialize_keycode(self, keycode):
        """Convert integer keycode to string QMK ID."""
        if keycode is None:
            return None
        if isinstance(keycode, str):
            return keycode
        return Keycode.serialize(keycode)

    def process_key_press(self, widget, is_pressed):
        """Process a key press/release and update layer state if needed."""
        if not self._keyboard:
            return False

        if is_pressed:
            return self._handle_key_down(widget)
        else:
            return self._handle_key_up(widget)

    def _handle_key_down(self, widget):
        """Handle a key being pressed."""
        keycode = self._get_keycode_at_layer(widget, self._current_layer)
        qmk_id = self._serialize_keycode(keycode)
        print(f"[DEBUG] Key down: row={widget.desc.row}, col={widget.desc.col}, "
              f"layer={self._current_layer}, keycode={keycode!r}, qmk_id={qmk_id!r}")
        if not qmk_id:
            return False

        layer_info = LayerDetector.get_layer_info(qmk_id)
        print(f"[DEBUG] LayerDetector result: {layer_info}")
        if not layer_info:
            return False

        key_type, target_layer = layer_info
        if target_layer >= self._keyboard.layers:
            return False

        self._active_layer_keys[widget] = (key_type, target_layer)
        return self._apply_layer_change(key_type, target_layer, True)

    def _handle_key_up(self, widget):
        """Handle a key being released."""
        if widget not in self._active_layer_keys:
            return False

        key_type, target_layer = self._active_layer_keys.pop(widget)
        return self._apply_layer_change(key_type, target_layer, False)

    def _apply_layer_change(self, key_type, target_layer, is_pressed):
        """Apply a layer state change and update effective layer."""
        changed = False

        if key_type == 'momentary':
            changed = self._handle_momentary(target_layer, is_pressed)
        elif key_type == 'toggle' and is_pressed:
            changed = self._handle_toggle(target_layer)
        elif key_type == 'switch' and is_pressed:
            changed = self._handle_switch(target_layer)
        elif key_type == 'one_shot' and is_pressed:
            changed = self._handle_one_shot(target_layer)
        elif key_type in ('tri_layer_1', 'tri_layer_2'):
            changed = self._handle_tri_layer(key_type, is_pressed)

        if changed:
            self._update_effective_layer()
        return changed

    def _handle_momentary(self, layer, is_pressed):
        """Handle momentary layer keys (MO, LT)."""
        if is_pressed:
            self._momentary_layers.add(layer)
        else:
            self._momentary_layers.discard(layer)
        return True

    def _handle_toggle(self, layer):
        """Handle toggle layer keys (TG, TT)."""
        if layer in self._toggled_layers:
            self._toggled_layers.discard(layer)
        else:
            self._toggled_layers.add(layer)
        return True

    def _handle_switch(self, layer):
        """Handle switch layer keys (TO, DF)."""
        self._current_layer = layer
        self._toggled_layers.clear()
        self._momentary_layers.clear()
        return True

    def _handle_one_shot(self, layer):
        """Handle one-shot layer keys (OSL)."""
        self._current_layer = layer
        return True

    def _handle_tri_layer(self, key_type, is_pressed):
        """Handle Vial tri-layer keys (FN_MO13, FN_MO23)."""
        if is_pressed:
            self._tri_layer_held.add(key_type)
        else:
            self._tri_layer_held.discard(key_type)
        return True

    def _update_effective_layer(self):
        """Calculate and set the effective layer based on active layers."""
        # Handle tri-layer: both FN_MO13 and FN_MO23 held = layer 3
        if 'tri_layer_1' in self._tri_layer_held and 'tri_layer_2' in self._tri_layer_held:
            self._current_layer = 3
            return
        elif 'tri_layer_1' in self._tri_layer_held:
            self._current_layer = 1
            return
        elif 'tri_layer_2' in self._tri_layer_held:
            self._current_layer = 2
            return

        all_active = self._toggled_layers | self._momentary_layers
        if all_active:
            self._current_layer = max(all_active)
        elif not self._toggled_layers and not self._momentary_layers:
            self._current_layer = 0
