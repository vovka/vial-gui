# SPDX-License-Identifier: GPL-2.0-or-later

import math
from PyQt5.QtCore import QPointF, QRectF
from widgets.free_slots_grid.slot import Slot, SlotRegionType


class SlotGenerator:
    """Generates candidate slots for combo label placement."""

    def __init__(self, slot_size=10.0, grid_spacing=None):
        self.slot_size = slot_size
        self.grid_spacing = grid_spacing or slot_size * 1.5

    def generate_slots(self, key_widgets, canvas_bounds, padding=5):
        """Generate all candidate slots based on key positions."""
        if not key_widgets:
            return []

        key_rects = [w.polygon.boundingRect() for w in key_widgets]
        keyboard_bounds = self._compute_keyboard_bounds(key_rects)

        slots = []
        slots.extend(self._generate_inter_key_slots(key_rects))
        slots.extend(self._generate_interior_slots(key_rects, keyboard_bounds))
        slots.extend(self._generate_exterior_slots(keyboard_bounds, canvas_bounds, padding))

        return slots

    def _compute_keyboard_bounds(self, key_rects):
        """Compute the bounding rectangle containing all keys."""
        if not key_rects:
            return QRectF()
        bounds = key_rects[0]
        for rect in key_rects[1:]:
            bounds = bounds.united(rect)
        return bounds

    def _generate_inter_key_slots(self, key_rects):
        """Generate slots in gaps between adjacent keys."""
        slots = []
        threshold = self.slot_size * 3

        for i, rect1 in enumerate(key_rects):
            for rect2 in key_rects[i + 1:]:
                gap_center = self._find_gap_center(rect1, rect2, threshold)
                if gap_center and not self._point_inside_any_key(gap_center, key_rects):
                    clearance = self._min_distance_to_keys(gap_center, key_rects)
                    slots.append(Slot(gap_center, SlotRegionType.INTER_KEY, clearance))

        return slots

    def _generate_interior_slots(self, key_rects, keyboard_bounds):
        """Generate slots inside keyboard footprint but not on keys."""
        slots = []
        margin = self.slot_size

        x = keyboard_bounds.left() + margin
        while x < keyboard_bounds.right() - margin:
            y = keyboard_bounds.top() + margin
            while y < keyboard_bounds.bottom() - margin:
                point = QPointF(x, y)
                if not self._point_inside_any_key(point, key_rects):
                    clearance = self._min_distance_to_keys(point, key_rects)
                    if clearance > self.slot_size * 0.5:
                        slots.append(Slot(point, SlotRegionType.INTERIOR, clearance))
                y += self.grid_spacing
            x += self.grid_spacing

        return slots

    def _generate_exterior_slots(self, keyboard_bounds, canvas_bounds, padding):
        """Generate slots around keyboard perimeter."""
        slots = []
        margin = self.slot_size * 2

        for x in self._range_steps(canvas_bounds.left() + padding,
                                   canvas_bounds.right() - padding,
                                   self.grid_spacing):
            for y in self._range_steps(canvas_bounds.top() + padding,
                                       canvas_bounds.bottom() - padding,
                                       self.grid_spacing):
                point = QPointF(x, y)
                if not keyboard_bounds.adjusted(-margin, -margin, margin, margin).contains(point):
                    continue
                if keyboard_bounds.contains(point):
                    continue
                slots.append(Slot(point, SlotRegionType.EXTERIOR, margin))

        return slots

    def _find_gap_center(self, rect1, rect2, threshold):
        """Find the center point of gap between two rectangles if close enough."""
        c1, c2 = rect1.center(), rect2.center()
        dist = math.hypot(c1.x() - c2.x(), c1.y() - c2.y())
        if dist > threshold:
            return None
        return QPointF((c1.x() + c2.x()) / 2, (c1.y() + c2.y()) / 2)

    def _point_inside_any_key(self, point, key_rects):
        """Check if a point is inside any key rectangle."""
        for rect in key_rects:
            if rect.contains(point):
                return True
        return False

    def _min_distance_to_keys(self, point, key_rects):
        """Calculate minimum distance from point to any key edge."""
        min_dist = float('inf')
        for rect in key_rects:
            dist = self._distance_to_rect(point, rect)
            min_dist = min(min_dist, dist)
        return min_dist

    def _distance_to_rect(self, point, rect):
        """Calculate distance from point to rectangle edge."""
        dx = max(rect.left() - point.x(), 0, point.x() - rect.right())
        dy = max(rect.top() - point.y(), 0, point.y() - rect.bottom())
        return math.hypot(dx, dy)

    def _range_steps(self, start, end, step):
        """Generate float range values."""
        values = []
        val = start
        while val < end:
            values.append(val)
            val += step
        return values
