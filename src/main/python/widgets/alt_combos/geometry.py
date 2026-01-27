# SPDX-License-Identifier: GPL-2.0-or-later
"""Basic geometry classes for alt combos visualization."""


class Slot:
    """A label slot on the boundary perimeter."""

    def __init__(self, position, direction, index, side):
        self.position = position  # QPointF
        self.direction = direction  # QPointF (inward normal unit vector)
        self.index = index  # int
        self.side = side  # str: 'top', 'right', 'bottom', 'left'


class ComboAnchor:
    """Anchor point for a combo (centroid of involved keys)."""

    def __init__(self, position, combo_index, key_rects, output_label, combo_label):
        self.position = position  # QPointF
        self.combo_index = combo_index  # int
        self.key_rects = key_rects  # List[QRectF]
        self.output_label = output_label  # str
        self.combo_label = combo_label  # str


class Route:
    """A routed path from combo anchor to assigned slot."""

    def __init__(self, combo_index, slot_index, path, simplified_path, cost):
        self.combo_index = combo_index  # int
        self.slot_index = slot_index  # int
        self.path = path  # List[Tuple[int, int]] - Grid coordinates
        self.simplified_path = simplified_path  # List[QPointF] - Canvas coords
        self.cost = cost  # float
