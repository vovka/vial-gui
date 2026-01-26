"""Arc-style dendron routing for combo visualization.

Implements L-shaped paths with rounded corners, similar to keymap-drawer.
"""

import math

from PyQt5.QtCore import QPointF, QRectF
from PyQt5.QtGui import QPainterPath

ARC_RADIUS = 6.0


class ComboLineRouter:
    """Routes arc-style dendrons between combo labels and keys."""

    def __init__(self, obstacles, avg_size):
        self.obstacles = obstacles
        self.avg_size = avg_size
        self.arc_radius = min(ARC_RADIUS, avg_size * 0.12)

    def create_path(self, start, end, combo_key_rects, x_first=True):
        """Create an L-shaped arc path from start to end."""
        path = QPainterPath()
        path.moveTo(start)

        dx = end.x() - start.x()
        dy = end.y() - start.y()

        if abs(dx) < 0.1 and abs(dy) < 0.1:
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
            mid_x = end.x()
            mid_y = start.y()
        else:
            mid_x = start.x()
            mid_y = end.y()

        x_sign = 1 if dx > 0 else -1
        y_sign = 1 if dy > 0 else -1

        if x_first:
            arc_start = QPointF(mid_x - x_sign * r, start.y())
            arc_end = QPointF(mid_x, start.y() + y_sign * r)
        else:
            arc_start = QPointF(start.x(), mid_y - y_sign * r)
            arc_end = QPointF(start.x() + x_sign * r, mid_y)

        path.lineTo(arc_start)

        ctrl = QPointF(mid_x, mid_y)
        path.quadTo(ctrl, arc_end)

        path.lineTo(end)
