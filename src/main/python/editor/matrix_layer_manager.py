# SPDX-License-Identifier: GPL-2.0-or-later
from editor.layer_detector import LayerDetector


class MatrixLayerManager:
    """Manages layer state for the Matrix Tester."""

    def __init__(self):
        self._current_layer = 0
        self._toggled_layers = set()
        self._momentary_layers = set()
        self._keyboard = None

    def set_keyboard(self, keyboard):
        """Set the keyboard reference for accessing layout data."""
        self._keyboard = keyboard
        self.reset()

    def reset(self):
        """Reset layer state to defaults."""
        self._current_layer = 0
        self._toggled_layers.clear()
        self._momentary_layers.clear()

    @property
    def current_layer(self):
        """Get the currently active layer."""
        return self._current_layer

    @current_layer.setter
    def current_layer(self, layer):
        """Manually set the current layer."""
        if self._keyboard and 0 <= layer < self._keyboard.layers:
            self._current_layer = layer

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

    def process_key_press(self, widget, is_pressed):
        """Process a key press/release and update layer state if needed."""
        if not self._keyboard:
            return False

        keycode = self.get_keycode_for_widget(widget)
        if not keycode:
            return False

        layer_info = LayerDetector.get_layer_info(keycode)
        if not layer_info:
            return False

        key_type, target_layer = layer_info
        return self._handle_layer_change(key_type, target_layer, is_pressed)

    def _handle_layer_change(self, key_type, target_layer, is_pressed):
        """Handle layer state changes based on key type."""
        if not self._keyboard or target_layer >= self._keyboard.layers:
            return False

        changed = False

        if key_type == 'momentary':
            changed = self._handle_momentary(target_layer, is_pressed)
        elif key_type == 'toggle' and is_pressed:
            changed = self._handle_toggle(target_layer)
        elif key_type == 'switch' and is_pressed:
            changed = self._handle_switch(target_layer)
        elif key_type == 'one_shot' and is_pressed:
            changed = self._handle_one_shot(target_layer)

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

    def _update_effective_layer(self):
        """Calculate and set the effective layer based on active layers."""
        all_active = self._toggled_layers | self._momentary_layers
        if all_active:
            self._current_layer = max(all_active)
        elif not self._toggled_layers and not self._momentary_layers:
            self._current_layer = 0
