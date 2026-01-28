# SPDX-License-Identifier: GPL-2.0-or-later

import math
from PyQt5.QtCore import QPointF, QRectF
from widgets.free_slots_grid.slot import Slot, SlotRegionType


class SlotGenerator:
    """Generates candidate slots for combo label placement."""

    def __init__(self, slot_size=10.0):
        self.slot_size = slot_size

    def generate_slots(self, key_widgets, canvas_bounds, padding=5):
        """Generate all candidate slots based on key positions."""
        if not key_widgets:
            return []

        key_rects = [w.polygon.boundingRect() for w in key_widgets]
        keyboard_bounds = self._compute_keyboard_bounds(key_rects)
        avg_key_size = self._compute_avg_key_size(key_rects)
        grid_spacing = avg_key_size * 0.6

        slots = []
        slots.extend(self._generate_inter_key_slots(key_rects, avg_key_size))
        slots.extend(self._generate_interior_slots(key_rects, keyboard_bounds, grid_spacing))
        slots.extend(self._generate_exterior_slots(keyboard_bounds, canvas_bounds, padding, grid_spacing))

        return slots

    def _compute_keyboard_bounds(self, key_rects):
        """Compute the bounding rectangle containing all keys."""
        if not key_rects:
            return QRectF()
        bounds = key_rects[0]
        for rect in key_rects[1:]:
            bounds = bounds.united(rect)
        return bounds

    def _compute_avg_key_size(self, key_rects):
        """Compute average key size for spacing calculations."""
        if not key_rects:
            return 50.0
        total = sum(max(r.width(), r.height()) for r in key_rects)
        return total / len(key_rects)

    def _generate_inter_key_slots(self, key_rects, avg_key_size):
        """Generate slots in gaps between adjacent keys."""
        slots = []
        adjacency_threshold = avg_key_size * 1.5

        for i, rect1 in enumerate(key_rects):
            for rect2 in key_rects[i + 1:]:
                gap_point = self._find_edge_gap(rect1, rect2, adjacency_threshold)
                if gap_point and not self._point_inside_any_key(gap_point, key_rects):
                    clearance = self._min_distance_to_keys(gap_point, key_rects)
                    slots.append(Slot(gap_point, SlotRegionType.INTER_KEY, clearance))

        return slots

    def _find_edge_gap(self, rect1, rect2, threshold):
        """Find the midpoint between edges of two adjacent rectangles."""
        c1, c2 = rect1.center(), rect2.center()
        dist = math.hypot(c1.x() - c2.x(), c1.y() - c2.y())
        if dist > threshold:
            return None

        dx = abs(c1.x() - c2.x())
        dy = abs(c1.y() - c2.y())

        if dx > dy:
            if c1.x() < c2.x():
                edge1_x = rect1.right()
                edge2_x = rect2.left()
            else:
                edge1_x = rect1.left()
                edge2_x = rect2.right()
            gap_x = (edge1_x + edge2_x) / 2
            gap_y = (c1.y() + c2.y()) / 2
        else:
            if c1.y() < c2.y():
                edge1_y = rect1.bottom()
                edge2_y = rect2.top()
            else:
                edge1_y = rect1.top()
                edge2_y = rect2.bottom()
            gap_x = (c1.x() + c2.x()) / 2
            gap_y = (edge1_y + edge2_y) / 2

        return QPointF(gap_x, gap_y)

    def _generate_interior_slots(self, key_rects, keyboard_bounds, grid_spacing):
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
                    if clearance > self.slot_size * 0.3:
                        slots.append(Slot(point, SlotRegionType.INTERIOR, clearance))
                y += grid_spacing
            x += grid_spacing

        return slots

    def _generate_exterior_slots(self, keyboard_bounds, canvas_bounds, padding, grid_spacing):
        """Generate slots outside keyboard bounds but inside canvas."""
        slots = []

        for x in self._range_steps(canvas_bounds.left() + padding,
                                   canvas_bounds.right() - padding,
                                   grid_spacing):
            for y in self._range_steps(canvas_bounds.top() + padding,
                                       canvas_bounds.bottom() - padding,
                                       grid_spacing):
                point = QPointF(x, y)
                if keyboard_bounds.contains(point):
                    continue
                clearance = self._distance_to_rect(point, keyboard_bounds)
                slots.append(Slot(point, SlotRegionType.EXTERIOR, clearance))

        return slots

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
