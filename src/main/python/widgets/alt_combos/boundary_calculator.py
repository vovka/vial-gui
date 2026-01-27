# SPDX-License-Identifier: GPL-2.0-or-later
"""Calculates outer boundary and evenly spaced slots around keyboard."""

from typing import List
from PyQt5.QtCore import QPointF, QRectF
from .geometry import Slot


class BoundaryCalculator:
    """Computes boundary rectangle and perimeter slots."""

    def __init__(self, margin: float = 30.0):
        self.margin = margin

    def compute_boundary(self, key_rects: List[QRectF]) -> QRectF:
        """Compute outer boundary rectangle with margin."""
        if not key_rects:
            return QRectF(0, 0, 100, 100)

        bbox = key_rects[0]
        for rect in key_rects[1:]:
            bbox = bbox.united(rect)

        return QRectF(
            bbox.left() - self.margin,
            bbox.top() - self.margin,
            bbox.width() + 2 * self.margin,
            bbox.height() + 2 * self.margin
        )

    def compute_slots(self, boundary: QRectF, slot_count: int) -> List[Slot]:
        """Generate evenly spaced slots around boundary perimeter."""
        perimeter = 2 * (boundary.width() + boundary.height())
        slots = []

        for i in range(slot_count):
            t = i / slot_count
            pos, direction, side = self._point_on_perimeter(boundary, t, perimeter)
            slots.append(Slot(position=pos, direction=direction, index=i, side=side))

        return slots

    def _point_on_perimeter(self, b: QRectF, t: float, perimeter: float):
        """Get point at fraction t along perimeter, with inward normal."""
        dist = t * perimeter
        w, h = b.width(), b.height()

        if dist < w:  # Top edge
            return self._top_point(b, dist)
        dist -= w

        if dist < h:  # Right edge
            return self._right_point(b, dist)
        dist -= h

        if dist < w:  # Bottom edge
            return self._bottom_point(b, dist, w)
        dist -= w

        return self._left_point(b, dist, h)

    def _top_point(self, b: QRectF, dist: float):
        return (QPointF(b.left() + dist, b.top()), QPointF(0, 1), 'top')

    def _right_point(self, b: QRectF, dist: float):
        return (QPointF(b.right(), b.top() + dist), QPointF(-1, 0), 'right')

    def _bottom_point(self, b: QRectF, dist: float, w: float):
        return (QPointF(b.right() - dist, b.bottom()), QPointF(0, -1), 'bottom')

    def _left_point(self, b: QRectF, dist: float, h: float):
        return (QPointF(b.left(), b.bottom() - dist), QPointF(1, 0), 'left')
