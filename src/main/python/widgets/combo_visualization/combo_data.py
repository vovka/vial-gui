"""Data classes for combo visualization."""

from .point import Point
from .combo_box_placer import Alignment


class KeyInfo:
    """Information about a key in a combo."""

    def __init__(self, center, size, widget):
        self.center = center
        self.size = size
        self.widget = widget


class ComboSpec:
    """Specification for a single combo to render."""

    def __init__(self, keys, output_label, combo_label):
        self.keys = keys
        self.output_label = output_label
        self.combo_label = combo_label


class ComboPlacement:
    """Computed placement for a combo box."""

    def __init__(self, position, alignment, width, height, keys, output_label, combo_label):
        self.position = position
        self.alignment = alignment
        self.width = width
        self.height = height
        self.keys = keys
        self.output_label = output_label
        self.combo_label = combo_label
