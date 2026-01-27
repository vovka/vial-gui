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
        """Stop fading a key."""
        self._fading_keys.pop(key, None)

    def update(self):
        """Update all fading keys. Returns True if any key is still fading."""
        current_time = time.time()
        next_fading_keys = {}

        for key, start_time in self._fading_keys.items():
            elapsed = current_time - start_time
            if elapsed < self.fade_duration:
                intensity = 1.0 - (elapsed / self.fade_duration)
                key.setHighlightIntensity(intensity)
                next_fading_keys[key] = start_time
            else:
                key.setHighlightIntensity(0.0)
                key.setOn(False)

        self._fading_keys = next_fading_keys
        return bool(self._fading_keys)

    def reset(self):
        """Reset all fading keys."""
        for key in self._fading_keys:
            key.setHighlightIntensity(0.0)
            key.setOn(False)
        self._fading_keys.clear()

    def is_fading(self, key):
        """Check if a key is currently fading."""
        return key in self._fading_keys
