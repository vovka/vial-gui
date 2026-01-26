"""Curved line routing for combo visualization."""

import math

from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainterPath

from widgets.combo_visualization.geometry import ComboGeometry

MIN_CURVE_DISTANCE_FACTOR = 2
CURVE_PERPENDICULAR_FACTOR = 0.15
OBSTACLE_MARGIN_FACTOR = 0.3


class ComboLineRouter:
    """Routes curved lines between labels and keys, avoiding obstacles."""

    def __init__(self, obstacles, avg_size):
        self.obstacles = obstacles
        self.avg_size = avg_size

    def create_path(self, start, end, combo_key_rects):
        """Create a curved path from start to end avoiding obstacles."""
        path = QPainterPath()
        path.moveTo(start)

        blocking = self._find_blocking_rects(start, end, combo_key_rects)

        if not blocking:
            self._add_simple_curve(path, start, end)
            return path

        self._add_routed_curve(path, start, end, blocking)
        return path

    def _find_blocking_rects(self, start, end, combo_key_rects):
        """Find rectangles that block the direct path."""
        blocking = []
        for rect in self.obstacles:
            if rect in combo_key_rects:
                continue
            if ComboGeometry.line_crosses_rect(start, end, rect):
                blocking.append(rect)
        blocking.sort(key=lambda r: math.hypot(r.center().x() - start.x(), r.center().y() - start.y()))
        return blocking

    def _add_simple_curve(self, path, start, end):
        """Add a simple curve or line when no obstacles."""
        dx, dy = end.x() - start.x(), end.y() - start.y()
        dist = math.hypot(dx, dy)

        if dist > self.avg_size * MIN_CURVE_DISTANCE_FACTOR:
            mid_x, mid_y = (start.x() + end.x()) / 2, (start.y() + end.y()) / 2
            perp_x = -dy / dist * self.avg_size * CURVE_PERPENDICULAR_FACTOR
            perp_y = dx / dist * self.avg_size * CURVE_PERPENDICULAR_FACTOR
            path.quadTo(QPointF(mid_x + perp_x, mid_y + perp_y), end)
        else:
            path.lineTo(end)

    def _add_routed_curve(self, path, start, end, blocking):
        """Add a curve that routes around blocking rectangles."""
        current = start
        for rect in blocking:
            waypoint = self._compute_waypoint(current, end, rect)
            self._add_cubic_segment(path, current, waypoint)
            current = waypoint
        self._add_final_segment(path, current, end)

    def _compute_waypoint(self, current, end, rect):
        """Compute a waypoint to route around a rectangle."""
        dx, dy = end.x() - current.x(), end.y() - current.y()
        rect_center = rect.center()
        cross = dx * (rect_center.y() - current.y()) - dy * (rect_center.x() - current.x())
        margin = self.avg_size * OBSTACLE_MARGIN_FACTOR

        if abs(dy) > abs(dx):
            y = rect.top() - margin if cross > 0 else rect.bottom() + margin
            return QPointF(rect_center.x(), y)
        x = rect.left() - margin if cross > 0 else rect.right() + margin
        return QPointF(x, rect_center.y())

    def _add_cubic_segment(self, path, start, end):
        """Add a cubic bezier segment."""
        ctrl1 = QPointF((start.x() + end.x()) / 2, start.y())
        ctrl2 = QPointF(end.x(), (start.y() + end.y()) / 2)
        path.cubicTo(ctrl1, ctrl2, end)

    def _add_final_segment(self, path, current, end):
        """Add the final segment to the destination."""
        ctrl1 = QPointF(current.x(), (current.y() + end.y()) / 2)
        ctrl2 = QPointF((current.x() + end.x()) / 2, end.y())
        path.cubicTo(ctrl1, ctrl2, end)
