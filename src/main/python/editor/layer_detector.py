# SPDX-License-Identifier: GPL-2.0-or-later
import re


class LayerDetector:
    """Detects layer-switching keycodes and extracts target layer information."""

    # Pattern for keycodes with layer number: MO(1), TG(2), TO(3), etc.
    LAYER_PATTERN = re.compile(r'^(MO|TG|TO|TT|OSL|DF|PDF|LT\d+)\((\d+|kc)\)$')

    # Momentary layer keys (active while held)
    MOMENTARY_KEYS = {'MO', 'LT'}

    # Toggle layer keys (toggle on/off)
    TOGGLE_KEYS = {'TG', 'TT'}

    # Layer switch keys (switch to layer)
    SWITCH_KEYS = {'TO', 'DF', 'PDF'}

    # One-shot layer keys
    ONE_SHOT_KEYS = {'OSL'}

    # Vial tri-layer keycodes
    TRI_LAYER_KEYS = {
        'FN_MO13': ('tri_layer_1', 1, 3),  # Layer 1 alone, Layer 3 with FN_MO23
        'FN_MO23': ('tri_layer_2', 2, 3),  # Layer 2 alone, Layer 3 with FN_MO13
    }

    @classmethod
    def get_layer_info(cls, qmk_id):
        """
        Extract layer information from a keycode.

        Returns a tuple (key_type, layer_number) or None if not a layer key.
        key_type is one of: 'momentary', 'toggle', 'switch', 'one_shot',
                           'tri_layer_1', 'tri_layer_2'
        """
        if not qmk_id:
            return None

        # Handle Vial tri-layer keycodes
        if qmk_id in cls.TRI_LAYER_KEYS:
            key_type, layer, _ = cls.TRI_LAYER_KEYS[qmk_id]
            return (key_type, layer)

        # Handle LT keys specially (e.g., LT1(KC_A) -> layer 1)
        lt_match = re.match(r'^LT(\d+)\(', qmk_id)
        if lt_match:
            return ('momentary', int(lt_match.group(1)))

        # Handle standard layer keys
        match = cls.LAYER_PATTERN.match(qmk_id)
        if not match:
            return None

        key_prefix = match.group(1)
        layer_str = match.group(2)

        if layer_str == 'kc':
            return None

        layer_num = int(layer_str)

        if key_prefix in cls.MOMENTARY_KEYS or key_prefix.startswith('LT'):
            return ('momentary', layer_num)
        elif key_prefix in cls.TOGGLE_KEYS:
            return ('toggle', layer_num)
        elif key_prefix in cls.SWITCH_KEYS:
            return ('switch', layer_num)
        elif key_prefix in cls.ONE_SHOT_KEYS:
            return ('one_shot', layer_num)

        return None

    @classmethod
    def is_momentary_layer_key(cls, qmk_id):
        """Check if keycode is a momentary layer key (MO, LT)."""
        info = cls.get_layer_info(qmk_id)
        return info is not None and info[0] == 'momentary'

    @classmethod
    def is_toggle_layer_key(cls, qmk_id):
        """Check if keycode is a toggle layer key (TG, TT)."""
        info = cls.get_layer_info(qmk_id)
        return info is not None and info[0] == 'toggle'

    @classmethod
    def get_target_layer(cls, qmk_id):
        """Get the target layer number for a layer keycode, or None."""
        info = cls.get_layer_info(qmk_id)
        return info[1] if info else None
