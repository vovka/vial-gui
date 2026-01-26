"""Arc-style dendron routing for combo visualization.

Implements L-shaped paths with rounded corners, similar to keymap-drawer.
"""

import math

from PyQt5.QtCore import QPointF, QRectF
from PyQt5.QtGui import QPainterPath

ARC_RADIUS = 6.0
KEY_PADDING = 4.0


class ComboLineRouter:
    """Routes arc-style dendrons between combo labels and keys."""

    def __init__(self, obstacles, avg_size):
        self.obstacles = obstacles
        self.avg_size = avg_size
        self.arc_radius = min(ARC_RADIUS, avg_size * 0.15)

    def create_path(self, start, end, combo_key_rects, x_first=None):
        """Create an L-shaped arc path from start to end."""
        path = QPainterPath()
        path.moveTo(start)

        dx = end.x() - start.x()
        dy = end.y() - start.y()

        if x_first is None:
            x_first = abs(dy) > abs(dx)

        if abs(dx) < 1 and abs(dy) < 1:
            return path

        if abs(dx) < self.arc_radius * 2 or abs(dy) < self.arc_radius * 2:
            path.lineTo(end)
            return path

        self._draw_arc_dendron(path, start, end, x_first)
        return path

    def _draw_arc_dendron(self, path, start, end, x_first):
        """Draw an L-shaped path with rounded corner."""
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        r = self.arc_radius

        if x_first:
            corner = QPointF(end.x(), start.y())
            self._add_horizontal_then_vertical(path, start, corner, end, dx, dy, r)
        else:
            corner = QPointF(start.x(), end.y())
            self._add_vertical_then_horizontal(path, start, corner, end, dx, dy, r)

    def _add_horizontal_then_vertical(self, path, start, corner, end, dx, dy, r):
        """Draw horizontal line, arc, then vertical line."""
        x_dir = 1 if dx > 0 else -1
        y_dir = 1 if dy > 0 else -1

        arc_start_x = corner.x() - x_dir * r
        arc_end_y = corner.y() + y_dir * r

        path.lineTo(arc_start_x, start.y())

        arc_rect = self._get_arc_rect(corner, x_dir, y_dir, r)
        start_angle = 90 if y_dir < 0 else 270
        sweep = -90 * x_dir * y_dir

        path.arcTo(arc_rect, start_angle, sweep)
        path.lineTo(end)

    def _add_vertical_then_horizontal(self, path, start, corner, end, dx, dy, r):
        """Draw vertical line, arc, then horizontal line."""
        x_dir = 1 if dx > 0 else -1
        y_dir = 1 if dy > 0 else -1

        arc_start_y = corner.y() - y_dir * r
        arc_end_x = corner.x() + x_dir * r

        path.lineTo(start.x(), arc_start_y)

        arc_rect = self._get_arc_rect(corner, x_dir, y_dir, r)
        start_angle = 180 if x_dir > 0 else 0
        sweep = 90 * x_dir * y_dir

        path.arcTo(arc_rect, start_angle, sweep)
        path.lineTo(end)

    def _get_arc_rect(self, corner, x_dir, y_dir, r):
        """Get the bounding rect for the arc."""
        if x_dir > 0 and y_dir > 0:
            return QRectF(corner.x() - r, corner.y(), r * 2, r * 2)
        elif x_dir > 0 and y_dir < 0:
            return QRectF(corner.x() - r, corner.y() - r * 2, r * 2, r * 2)
        elif x_dir < 0 and y_dir > 0:
            return QRectF(corner.x() - r, corner.y(), r * 2, r * 2)
        else:
            return QRectF(corner.x() - r, corner.y() - r * 2, r * 2, r * 2)
