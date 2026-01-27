# SPDX-License-Identifier: GPL-2.0-or-later
import time


class KeyFadeManager:
    """Manages fading highlight effect for keys in matrix tester."""

    def __init__(self, fade_duration=2.0):
        self.fade_duration = fade_duration
        self._fading_keys = {}

    def start_fade(self, key):
        """Start fading a key from full intensity."""
        self._fading_keys[key] = time.time()
        key.setHighlightIntensity(1.0)

    def stop_fade(self, key):
        """Stop fading a key and reset its intensity."""
        if key in self._fading_keys:
            del self._fading_keys[key]
        key.setHighlightIntensity(0.0)

    def update(self):
        """Update all fading keys. Returns True if any key is still fading."""
        current_time = time.time()
        keys_to_remove = []

        for key, start_time in self._fading_keys.items():
            elapsed = current_time - start_time
            if elapsed >= self.fade_duration:
                key.setHighlightIntensity(0.0)
                key.setOn(False)
                keys_to_remove.append(key)
            else:
                intensity = 1.0 - (elapsed / self.fade_duration)
                key.setHighlightIntensity(intensity)

        for key in keys_to_remove:
            del self._fading_keys[key]

        return len(self._fading_keys) > 0

    def reset(self):
        """Reset all fading keys."""
        for key in self._fading_keys:
            key.setHighlightIntensity(0.0)
            key.setOn(False)
        self._fading_keys.clear()

    def is_fading(self, key):
        """Check if a key is currently fading."""
        return key in self._fading_keys
