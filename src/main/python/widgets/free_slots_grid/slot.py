# SPDX-License-Identifier: GPL-2.0-or-later

from enum import Enum, auto
from PyQt5.QtCore import QPointF, QRectF


class SlotRegionType(Enum):
    """Type of region where a slot is located."""
    INTER_KEY = auto()      # Gap between adjacent keys (highest priority)
    INTERIOR = auto()       # Inside keyboard footprint but not on keys
    EXTERIOR = auto()       # Around keyboard perimeter
    SPLIT_MIDDLE = auto()   # Between halves of a split keyboard


class Slot:
    """Represents a candidate position for placing a combo label."""

    def __init__(self, position, region_type, clearance_score=0.0, size=None):
        self.position = position  # QPointF - center of the slot
        self.region_type = region_type  # SlotRegionType
        self.clearance_score = clearance_score  # Distance to nearest key edge
        self.size = size or QPointF(10, 10)  # Default slot size

    @property
    def x(self):
        return self.position.x()

    @property
    def y(self):
        return self.position.y()

    def get_rect(self, width=None, height=None):
        """Get the bounding rectangle for this slot."""
        w = width if width is not None else self.size.x()
        h = height if height is not None else self.size.y()
        return QRectF(
            self.position.x() - w / 2,
            self.position.y() - h / 2,
            w,
            h
        )

    def __repr__(self):
        return f"Slot({self.region_type.name}, pos=({self.x:.1f}, {self.y:.1f}))"
