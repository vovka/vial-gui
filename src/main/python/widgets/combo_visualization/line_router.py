"""Arc-style dendron routing for combo visualization.

Implements L-shaped paths with rounded corners, similar to keymap-drawer.
"""

import math

from PyQt5.QtCore import QPointF, QRectF
from PyQt5.QtGui import QPainterPath

from widgets.combo_visualization.geometry import ComboGeometry

ARC_RADIUS = 6.0


class ComboLineRouter:
    """Routes arc-style dendrons between combo labels and keys."""

    def __init__(self, obstacles, avg_size):
        self.obstacles = obstacles
        self.avg_size = avg_size
        self.arc_radius = min(ARC_RADIUS, avg_size * 0.12)

    def create_path(self, start, end, combo_key_rects, x_first=True, offset=0.0, label_rect=None):
        """Create an L-shaped arc path from start to end."""
        start = self._apply_offset(start, end, combo_key_rects, x_first, offset, label_rect)
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

    def _apply_offset(self, start, end, combo_key_rects, x_first, offset, label_rect):
        if abs(offset) < 0.01:
            return start

        clamped = self._clamp_offset(start, end, combo_key_rects, x_first, offset, label_rect)
        if x_first:
            return QPointF(start.x() + clamped, start.y())
        return QPointF(start.x(), start.y() + clamped)

    def _clamp_offset(self, start, end, combo_key_rects, x_first, offset, label_rect):
        if label_rect is not None and isinstance(label_rect, QRectF):
            margin = min(self.avg_size * 0.1, label_rect.width() * 0.25, label_rect.height() * 0.25)
            if x_first:
                min_offset = label_rect.left() + margin - start.x()
                max_offset = label_rect.right() - margin - start.x()
            else:
                min_offset = label_rect.top() + margin - start.y()
                max_offset = label_rect.bottom() - margin - start.y()
            offset = max(min_offset, min(offset, max_offset))

        for _ in range(4):
            if not self._offset_hits_obstacle(start, end, combo_key_rects, x_first, offset, label_rect):
                return offset
            offset *= 0.5
            if abs(offset) < 0.01:
                break
        return 0.0

    def _offset_hits_obstacle(self, start, end, combo_key_rects, x_first, offset, label_rect):
        adjusted_start = QPointF(start.x() + offset, start.y()) if x_first else QPointF(start.x(), start.y() + offset)
        turn = QPointF(end.x(), adjusted_start.y()) if x_first else QPointF(adjusted_start.x(), end.y())

        obstacles = list(self.obstacles)
        if label_rect is not None:
            obstacles.append(label_rect)

        for rect in obstacles:
            if rect in combo_key_rects:
                continue
            if ComboGeometry.line_crosses_rect(adjusted_start, turn, rect):
                return True
            if ComboGeometry.line_crosses_rect(turn, end, rect):
                return True
        return False
